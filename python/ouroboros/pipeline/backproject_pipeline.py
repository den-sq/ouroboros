import concurrent.futures
from dataclasses import astuple
from functools import partial
from multiprocessing import cpu_count
import os
from pathlib import Path
import shutil
import sys
import tifffile
import time
import traceback

import numpy as np
import scipy
import scipy.ndimage

from ouroboros.helpers.memory_usage import (
    calculate_chunk_size,
    calculate_gigabytes_from_dimensions
)
from ouroboros.helpers.slice import (        # noqa: F401
    detect_color_channels_shape,
    make_volume_binary,
    FrontProjStack,
    backproject_slices,
    backproject_box,
    BackProjectIter
)
from ouroboros.helpers.volume_cache import VolumeCache, get_mip_volume_sizes, update_writable_rects
from ouroboros.helpers.bounding_boxes import BoundingBox
from .pipeline import PipelineStep
from ouroboros.helpers.options import BackprojectOptions
from ouroboros.helpers.files import (
    format_backproject_resave_volume,
    format_tiff_name,
    get_sorted_tif_files,
    join_path,
    num_digits_for_n_files,
    parse_tiff_name,
    generate_tiff_write,
    write_from_intermediate,
    write_small_intermediate
)
from ouroboros.helpers.shapes import DataRange, ImgSlice


DEFAULT_CHUNK_SIZE = 128
AXIS = 0


class BackprojectPipelineStep(PipelineStep):
    def __init__(self, processes=cpu_count()) -> None:
        super().__init__(
            inputs=(
                "backproject_options",
                "volume_cache",
                "slice_rects",
            )
        )

        self.num_processes = min(processes, 8)

    def _process(self, input_data: any) -> tuple[any, None] | tuple[None, any]:
        config, volume_cache, slice_rects, pipeline_input = input_data

        # Verify that a config object is provided
        if not isinstance(config, BackprojectOptions):
            return "Input data must contain a BackprojectOptions object."

        # Verify that input_data is a string containing a path to a tif file
        if not isinstance(config.straightened_volume_path, str):
            return "Input data must contain a string containing a path to a tif file."

        # Verify that a volume cache is given
        if not isinstance(volume_cache, VolumeCache):
            return "Input data must contain a VolumeCache object."

        # Verify that slice rects is given
        if not isinstance(slice_rects, np.ndarray):
            return "Input data must contain an array of slice rects."

        straightened_volume_path = config.straightened_volume_path

        # Make sure the straightened volume exists
        if not os.path.exists(straightened_volume_path):
            return (
                f"The straightened volume does not exist at {straightened_volume_path}."
            )

        if Path(straightened_volume_path).is_dir():
            with tifffile.TiffFile(next(Path(straightened_volume_path).iterdir())) as tif:
                is_compressed = bool(tif.pages[0].compression)
                # tiff format check to add
                FPShape = FrontProjStack(D=len(list(Path(straightened_volume_path).iterdir())),
                                         V=tif.pages[0].shape[0], U=tif.pages[0].shape[1])
        else:
            with tifffile.TiffFile(straightened_volume_path) as tif:
                is_compressed = bool(tif.pages[0].compression)
                FPShape = FrontProjStack(D=len(tif.pages), V=tif.pages[0].shape[0], U=tif.pages[0].shape[1])

        if is_compressed:
            print("Input data compressed; Rewriting.")

            # Create a new path for the straightened volume
            new_straightened_volume_path = join_path(
                config.output_file_folder,
                format_backproject_resave_volume(config.output_file_name),
            )

            # Save the straightened volume to a new tif file
            with tifffile.TiffWriter(new_straightened_volume_path) as tif:
                if straightened_volume_path.endswith((".tif", ".tiff")):
                    # Read the single tif file
                    with tifffile.TiffFile(straightened_volume_path) as tif_in:
                        for i in range(len(tif_in.pages)):
                            tif.save(tif_in.pages[i].asarray(), contiguous=True, compression=None)
                else:
                    # Read the tif files from the folder
                    images = get_sorted_tif_files(straightened_volume_path)
                    for image in images:
                        tif.save(tifffile.imread(join_path(straightened_volume_path, image)),
                                 contiguous=True, compression=None)

            straightened_volume_path = new_straightened_volume_path

        # Write huge temp files (need to address)
        full_bounding_box = BoundingBox.bound_boxes(volume_cache.bounding_boxes)
        write_shape = np.flip(full_bounding_box.get_shape()).tolist()
        print(f"\nFront Projection Shape: {FPShape}")
        print(f"\nBack Projection Shape (Z/Y/X):{write_shape}")
        folder_path = Path(config.output_file_folder,
                           config.output_file_name + f"_{'_'.join(map(str, full_bounding_box.get_min(np.uint32)))}")
        folder_path.mkdir(exist_ok=True, parents=True)

        if config.make_single_file:
            is_big_tiff = calculate_gigabytes_from_dimensions(np.prod(write_shape), np.uint16) > 4     # Check Dtype
            single_tiff = tifffile.TiffWriter(folder_path.with_suffix(".tiff"), abigtiff=is_big_tiff)

        bp_offset = pipeline_input.backprojection_offset if config.backproject_min_bounding_box else None
        tif_write = generate_tiff_write(single_tiff.write if config.make_single_file else tifffile.imwrite,
                                        config.backprojection_compression,
                                        volume_cache.get_resolution_um(),
                                        bp_offset)

        # Process each bounding box in parallel, writing the results to the backprojected volume
        try:
            with concurrent.futures.ProcessPoolExecutor(self.num_processes) as executor:
                futures = []

                chunk_range = DataRange(FPShape.make_with(0), FPShape, FPShape.make_with(DEFAULT_CHUNK_SIZE))
                chunk_iter = partial(BackProjectIter, shape=FPShape, slice_rects=np.array(slice_rects))
                processed = np.zeros(astuple(chunk_range.length))
                z_sources = np.zeros((write_shape[0], ) + astuple(chunk_range.length), dtype=bool)

                for chunk, shape, chunk_rects, bbox, index in chunk_range.get_iter(chunk_iter):
                    futures.append(executor.submit(
                        process_chunk,
                        config,
                        bbox,
                        straightened_volume_path,
                        chunk_rects,
                        chunk,
                        shape,
                        index,
                        full_bounding_box
                    ))

                # Track what's written.
                min_dim = full_bounding_box.get_min(int)[2]
                num_pages = full_bounding_box.get_shape()[2]
                writeable = np.zeros(num_pages)
                i_path = Path(config.output_file_folder,
                              config.output_file_name +
                              f"_t_{'_'.join(map(str, full_bounding_box.get_min(np.uint32)))}")
                thread_pool = []
                thread_timings = []

                for future in concurrent.futures.as_completed(futures):
                    # Store the durations for each bounding box
                    durations, index, z_stack = future.result()
                    for key, value in durations.items():
                        self.add_timing_list(key, value)

                    z_sources[(z_stack, ) + index] = True

                    # Update the progress bar
                    processed[index] = 1
                    self.update_progress(np.sum(processed) / (2 * len(chunk_range)) + np.sum(writeable > 1) / num_pages)

                    update_writable_rects(processed, slice_rects, min_dim, writeable, DEFAULT_CHUNK_SIZE)

                    if np.any(writeable == 1):
                        start = time.perf_counter()

                        thread_pool += write_from_intermediate(writeable, tif_write, folder_path, i_path, z_sources,
                                                               ImgSlice(*write_shape[1:]),
                                                               dtype=np.uint16,
                                                               is_single=config.make_single_file,
                                                               write_start=len(writeable > 1),
                                                               use_threads=False)
                        thread_timings.append(time.perf_counter() - start)

                    # Update the progress bar
                    self.update_progress(np.sum(processed) / (2 * len(chunk_range)) + np.sum(writeable > 1) / num_pages)
        except BaseException as e:
            traceback.print_tb(e.__traceback__, file=sys.stderr)
            return f"An error occurred while processing the bounding boxes: {e}"

        self.add_timing_list("Thread Dispatch", thread_timings)

        start = time.perf_counter()

        for thread in thread_pool:
            thread.join()

        if config.make_single_file:
            shutil.rmtree(folder_path)

        # Rescale the backprojected volume to the output mip level
        if pipeline_input.slice_options.output_mip_level != config.output_mip_level:
            output_name = f"{folder_path}-temp"

            error = rescale_mip_volume(
                pipeline_input.source_url,
                pipeline_input.slice_options.output_mip_level,
                config.output_mip_level,
                single_path=(None if config.make_single_file is False else folder_path + ".tif"),
                folder_path=(folder_path if config.make_single_file is False else None),
                output_name=output_name,
                compression=config.backprojection_compression,
                max_ram_gb=config.max_ram_gb,
                order=config.upsample_order,
                binary=config.make_backprojection_binary,
            )

            if error is not None:
                return error

            # Remove the original backprojected volume
            if config.make_single_file:
                os.remove(folder_path + ".tif")
            else:
                shutil.rmtree(folder_path)

            # Rename the rescaled volume
            if config.make_single_file:
                os.rename(output_name + ".tif", folder_path + ".tif")
            else:
                os.rename(output_name, folder_path)

        # Update the pipeline input with the output file path
        pipeline_input.backprojected_folder_path = folder_path

        self.add_timing("export", time.perf_counter() - start)

        return None


def process_chunk(
    config: BackprojectOptions,
    bounding_box: BoundingBox,
    straightened_volume_path: str,
    chunk_rects: list[np.ndarray],
    chunk: tuple[slice],
    shape: tuple[int],
    index: tuple[int],
    full_bounding_box: BoundingBox
) -> tuple[dict, str, int]:
    durations = {
        "total_bytes": [],
        "memmap": [],
        "get_slices": [],
        "generate_grid": [],
        "create_volume": [],
        "back_project": [],
        "update_lookup": [],
        "sort": [],
        "write_intermediate": [],
        "total_process": [],
    }

    start_total = time.perf_counter()

    # Load the straightened volume
    start = time.perf_counter()
    straightened_volume = tifffile.memmap(straightened_volume_path, mode="r")
    durations["memmap"].append(time.perf_counter() - start)

    # Get the slices from the straightened volume  Dumb but maybe bugfix?
    start = time.perf_counter()
    slices = straightened_volume[chunk].squeeze()
    durations["get_slices"].append(time.perf_counter() - start)

    # Close the memmap
    del straightened_volume

    try:
        lookup, values, weights = backproject_box(bounding_box, chunk_rects, slices)
    except BaseException as be:
        print(f"Error on BP: {be}")
        traceback.print_tb(be.__traceback__, file=sys.stderr)
        raise be

    durations["back_project"].append(time.perf_counter() - start)
    durations["total_bytes"].append(int(lookup.nbytes + values.nbytes + weights.nbytes))

    # Save the data
    try:
        start = time.perf_counter()

        lookup += np.array((bounding_box.get_min(np.uint32) - full_bounding_box.get_min(np.uint32))).reshape(3, 1)

        durations["update_lookup"].append(time.perf_counter() - start)

        start = time.perf_counter()

        file_path = Path(config.output_file_folder,
                         config.output_file_name + f"_t_{'_'.join(map(str, full_bounding_box.get_min(np.uint32)))}")

        file_path.mkdir(exist_ok=True, parents=True)

        z_stack = tuple(np.unique(lookup[2]))

        durations["sort"].append(time.perf_counter() - start)
        start = time.perf_counter()

        write_small_intermediate(file_path.joinpath(f"i_{'_'.join(map(str, index))}.tiff"), lookup, values, weights)

        durations["write_intermediate"].append(time.perf_counter() - start)
    except BaseException as be:
        print(f"Error on BP: {be}")
        traceback.print_tb(be.__traceback__, file=sys.stderr)
        raise be

    durations["total_process"].append(time.perf_counter() - start_total)

    return durations, index, z_stack


def rescale_mip_volume(
    source_url: str,
    current_mip: int,
    target_mip: int,
    single_path: str = None,
    folder_path: str = None,
    output_name: str = "out",
    compression: str = None,
    max_ram_gb: int = 0,
    order: int = 2,
    binary: bool = False,
) -> str | None:
    """
    Rescale the volume to the mip level.

    Parameters
    ----------
    source_url : str
        The URL of the volume.
    current_mip : int
        The current mip level of the volume.
    target_mip : int
        The target mip level of the volume.
    single_path : str
        The path to the single tif file.
    folder_path : str
        The path to the folder containing the tif files.
    output_name : str
        The path to the output.
    compression : str, optional
        The compression to use for the resulting tif file.
        The default is None.
    max_ram_gb : int, optional
        The maximum amount of RAM to use in GB.
        The default is 0.
    order : int, optional
        The order of the interpolation.
        The default is 2.
    binary : bool, optional
        Whether to make the backprojected volume binary.

    Returns
    -------
    str | None
        Error message if an error occurred.
    """

    if single_path is None and folder_path is None:
        return "Either single_path or folder_path must be provided."

    if target_mip == current_mip:
        return None

    if single_path is not None:
        return rescale_single_tif(
            source_url,
            current_mip,
            target_mip,
            single_path,
            compression=compression,
            file_name=output_name + ".tif",
            max_ram_gb=max_ram_gb,
            order=order,
            binary=binary,
        )

    return rescale_folder_tif(
        source_url,
        current_mip,
        target_mip,
        folder_path,
        compression=compression,
        folder_name=output_name,
        max_ram_gb=max_ram_gb,
        order=order,
        binary=binary,
    )


def rescale_single_tif(
    source_url: str,
    current_mip: int,
    target_mip: int,
    single_path: str,
    file_name: str = "out.tif",
    compression: str = None,
    max_ram_gb: int = 0,
    order: int = 1,
    binary: bool = False,
) -> str | None:
    with tifffile.TiffFile(single_path) as tif:
        tif_shape = (len(tif.pages),) + tif.pages[0].shape

        scaling_factors, _ = calculate_scaling_factors(
            source_url, current_mip, target_mip, tif_shape
        )

        # Calculate the output tiff shape
        output_shape = tuple(
            int(tif_shape[i] * scaling_factors[i]) for i in range(len(tif_shape))
        )

        # Note: The chunk size is divided by the scaling factor to account for the
        # number of slices that need to be loaded to produce chunk_size slices in the output volume
        chunk_size = max(
            int(
                calculate_chunk_size(
                    output_shape, tif.pages[0].dtype, max_ram_gb=max_ram_gb
                )
                / scaling_factors[0]
            ),
            1,
        )

        with tifffile.TiffWriter(file_name) as output_volume:
            for i in range(0, tif_shape[0], chunk_size):
                # Stack the tif layers along the first axis (chunk_size)
                tif_layer = np.array(
                    [
                        tif.pages[j].asarray()
                        for j in range(i, min(i + chunk_size, tif_shape[0]))
                    ]
                )

                layers = scipy.ndimage.zoom(tif_layer, scaling_factors, order=order)

                if binary:
                    layers = make_volume_binary(layers)

                size = layers.shape[0]

                # Save the layers to the tif file
                for j in range(size):
                    output_volume.write(
                        layers[j],
                        contiguous=compression is None or compression == "none",
                        compression=compression,
                        software="ouroboros",
                    )

    return None


def rescale_folder_tif(
    source_url: str,
    current_mip: int,
    target_mip: int,
    folder_path: str,
    folder_name: str = "out",
    compression: str = None,
    max_ram_gb: int = 0,
    order: int = 1,
    binary: bool = False,
) -> str | None:
    # Create output folder if it doesn't exist
    output_folder = folder_name
    os.makedirs(output_folder, exist_ok=True)

    tifs = get_sorted_tif_files(folder_path)

    if len(tifs) == 0:
        return "No tif files found in the folder."

    sample_tif = tifffile.imread(join_path(folder_path, tifs[0]))

    # Determine the shape of the tif stack
    new_shape = (len(tifs), *sample_tif.shape)

    scaling_factors, resolution_factors = calculate_scaling_factors(
        source_url, current_mip, target_mip, new_shape
    )

    # Note: The chunk size is divided by the scaling factor to account for the
    # number of slices that need to be loaded to produce chunk_size slices in the output volume
    chunk_size = max(
        int(
            calculate_chunk_size(new_shape, sample_tif.dtype, max_ram_gb=max_ram_gb)
            / scaling_factors[0]
        ),
        1,
    )

    num_digits = num_digits_for_n_files(len(tifs))

    first_index = parse_tiff_name(tifs[0])

    output_index = int(first_index * resolution_factors[0])

    # Resize the volume
    for i in range(0, len(tifs), chunk_size):
        # Stack the tif layers along the first axis (chunk_size)
        tif = np.array(
            [
                tifffile.imread(join_path(folder_path, tifs[j]))
                for j in range(i, min(i + chunk_size, len(tifs)))
            ]
        )

        layers = scipy.ndimage.zoom(tif, scaling_factors, order=order)

        if binary:
            layers = make_volume_binary(layers)

        size = layers.shape[0]

        # Write the layers to new tif files
        for j in range(size):
            tifffile.imwrite(
                join_path(output_folder, format_tiff_name(output_index, num_digits)),
                layers[j],
                contiguous=True if compression is None else False,
                compression=compression,
                software="ouroboros",
            )
            output_index += 1

    return None


def calculate_scaling_factors(
    source_url: str, current_mip: int, target_mip: int, tif_shape: tuple
) -> tuple[tuple, tuple]:
    # Determine the current and target resolutions
    mip_sizes = get_mip_volume_sizes(source_url)

    current_resolution = mip_sizes[current_mip]
    target_resolution = mip_sizes[target_mip]

    # Determine the scaling factor for each axis as a tuple
    resolution_factors = tuple(
        max(target_resolution[i] / current_resolution[i], 1)
        for i in range(len(target_resolution))
    )

    has_color_channels, num_channels = detect_color_channels_shape(tif_shape)

    # Determine the scaling factor for each axis as a tuple
    scaling_factors = resolution_factors + (
        (num_channels,) if has_color_channels else ()
    )

    return scaling_factors, resolution_factors
