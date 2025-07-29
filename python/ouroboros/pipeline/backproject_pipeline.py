import concurrent.futures
from functools import partial
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
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
)
from ouroboros.helpers.slice import (
    detect_color_channels,
    detect_color_channels_shape,
    make_volume_binary,
    backproject_slices,
)
from ouroboros.helpers.volume_cache import VolumeCache, get_mip_volume_sizes
from ouroboros.helpers.bounding_boxes import BoundingBox
from .pipeline import PipelineStep
from ouroboros.helpers.options import BackprojectOptions
from ouroboros.helpers.files import (
    format_backproject_resave_volume,
    format_tiff_name,
    get_sorted_tif_files,
    join_path,
    load_and_save_tiff_from_slices,
    num_digits_for_n_files,
    parse_tiff_name,
    write_memmap_with_create
)


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

        self.num_processes = min(processes, 4)

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
        else:
            with tifffile.TiffFile(straightened_volume_path) as tif:
                is_compressed = bool(tif.pages[0].compression)

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
                            tif.save(
                                tif_in.pages[i].asarray(),
                                contiguous=True,
                                compression=None,
                            )
                else:
                    # Read the tif files from the folder
                    images = get_sorted_tif_files(straightened_volume_path)
                    for image in images:
                        tif.save(
                            tifffile.imread(join_path(straightened_volume_path, image)),
                            contiguous=True,
                            compression=None,
                        )

            straightened_volume_path = new_straightened_volume_path

        def boxes_dim_range(boxes: list[BoundingBox], dim="z"):
            if len(boxes):
                return np.arange(int(np.min([getattr(box, f"{dim}_min") for box in boxes])),
                                 int(np.max([getattr(box, f"{dim}_max") for box in boxes])) + 1)
            else:
                return np.arange(0)

        # Write huge temp files (need to address)
        full_bounding_box = BoundingBox.bound_boxes(volume_cache.bounding_boxes)
        write_shape = np.flip(full_bounding_box.get_shape()).tolist()
        pipeline_input.output_file_path = f"{config.output_file_name}_zyx_{'_'.join(map(str, full_bounding_box.get_min(np.uint32)))}"
        file_path = Path(config.output_file_folder, pipeline_input.output_file_path)
        file_path.mkdir(exist_ok=True, parents=True)

        with ThreadPool(12) as pool:
            pool.map(partial(tifffile.memmap, shape=write_shape[1:], dtype=np.float32),
                     [file_path.joinpath(f"{i:05}.tiff") for i in range(write_shape[0])])

        # Process each bounding box in parallel, writing the results to the backprojected volume
        try:
            with concurrent.futures.ProcessPoolExecutor(
                max_workers=self.num_processes
            ) as executor:
                futures = []

                # Process each bounding box in parallel
                for i in range(len(volume_cache.bounding_boxes)):
                    bounding_box = volume_cache.bounding_boxes[i]
                    slice_indices = volume_cache.get_slice_indices(i)
                    futures.append(
                        executor.submit(
                            process_bounding_box,
                            config,
                            bounding_box,
                            straightened_volume_path,
                            slice_rects,
                            slice_indices,
                            i,
                            full_bounding_box
                        )
                    )

                # Track the completed futures
                remaining = volume_cache.bounding_boxes.copy()
                total_futures = len(futures)

                for future in concurrent.futures.as_completed(futures):
                    # Store the durations for each bounding box
                    durations, index = future.result()
                    for key, value in durations.items():
                        self.add_timing_list(key, value)

                    _ = boxes_dim_range([volume_cache.bounding_boxes[index]])
                    remaining.remove(volume_cache.bounding_boxes[index])
                    # Update the progress bar
                    self.update_progress((1 - (len(remaining) / total_futures)) / 2)

                    # Check for completed z-stacks
#                     writeable = box_z[np.isin(box_z, boxes_dim_range(remaining), invert=True)]
#                     for dim in writeable:
#                         Thread(target=tf.imwrite, args=(base_path.joinpath(f"{dim:05}"), data[:, :, dim])
#                                kwargs={"compression": "zlib"})

                    # Hand over to writer
                    # shrink the existing array(s)

        except BaseException as e:
            traceback.print_tb(e.__traceback__, file=sys.stderr)
            return f"An error occurred while processing the bounding boxes: {e}"

        start = time.perf_counter()

        min_point = BoundingBox.bound_boxes(volume_cache.bounding_boxes).get_min(np.uint32)

        folder_path = Path(config.output_file_folder,
                           config.output_file_name + f"_zyx_{'_'.join(map(str, min_point))}")

        # Volume cache resolution is in voxel size, but .tiff XY resolution is in voxels per unit, so we invert.
        resolution = [1.0 / voxel_size for voxel_size in volume_cache.get_resolution_um()[:2] * 0.0001]
        resolutionunit = "CENTIMETER"
        # However, Z Resolution doesn't have an inbuilt property or strong convention, so going with this atm.
        metadata = {
            "spacing": volume_cache.get_resolution_um()[2],
            "unit": "um"
        }

        if config.backproject_min_bounding_box:
            metadata["backprojection_offset_min_xyz"] = (
                pipeline_input.backprojection_offset
            )

        if config.make_single_file:
            pipeline_input.output_file_path += ".tif"
            # Save the backprojected volume to a single tif file
            try:

                load_and_save_tiff_from_slices(
                    folder_path,
                    folder_path.with_suffix(".tif"),
                    delete_intermediate=False,
                    compression=config.backprojection_compression,
                    metadata=metadata,
                    resolution=resolution,     # XY Resolution
                    resolutionunit=resolutionunit,
                )
            except BaseException as e:
                return f"Error creating single tif file: {e}"
        else:
            for tif in folder_path.iterdir():
                tifffile.imwrite(
                    tif,
                    tifffile.imread(tif),
                    contiguous=config.backprojection_compression is None,
                    compression=config.backprojection_compression,
                    metadata=metadata,
                    resolution=resolution,
                    resolutionunit=resolutionunit,
                    software="ouroboros")

        # Rescale the backprojected volume to the output mip level
        if pipeline_input.slice_options.output_mip_level != config.output_mip_level:
            output_name = f"{folder_path}-temp"

            error = rescale_mip_volume(
                pipeline_input.source_url,
                pipeline_input.slice_options.output_mip_level,
                config.output_mip_level,
                single_path=(
                    None if config.make_single_file is False else folder_path + ".tif"
                ),
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


def process_bounding_box(
    config: BackprojectOptions,
    bounding_box: BoundingBox,
    straightened_volume_path: str,
    slice_rects: list[np.ndarray],
    slice_indices: list[int],
    index: int,
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
        "write_direct": [],
        "write_volume": [],
        "total_process": [],
    }

    start_total = time.perf_counter()

    # Load the straightened volume
    start = time.perf_counter()
    straightened_volume = tifffile.memmap(straightened_volume_path, mode="r")
    _, num_channels = detect_color_channels(straightened_volume, none_value=None)
    durations["memmap"].append(time.perf_counter() - start)

    # Get the slices from the straightened volume
    start = time.perf_counter()
    slices = np.array([straightened_volume[i] for i in slice_indices])
    durations["get_slices"].append(time.perf_counter() - start)

    # Close the memmap
    del straightened_volume

    try:
        lookup, values, weights = backproject_slices(bounding_box, slice_rects[slice_indices], slices)
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
                         config.output_file_name + f"_zyx_{'_'.join(map(str, full_bounding_box.get_min(np.uint32)))}")

        write_shape = np.flip(full_bounding_box.get_shape()).tolist()

#         if config.make_single_file:
#
#             write_memmap_with_create(file_path.with_suffix(".tiff"), (lookup[2], lookup[1], lookup[0]),
#                                      (values // weights).astype(np.uint16),
#                                      shape=write_shape, dtype=np.uint16)
#         else:
        file_path.mkdir(exist_ok=True, parents=True)
        sort = lookup[2, :].argsort()
        lookup = lookup[:, sort]
        values = values[sort]
        weights = weights[sort]

        # is presorted so maybe can do other way
        img, points = np.unique(lookup[2], return_counts=True)
        sections = [np.s_[np.sum(points[0:i]): np.sum(points[0:i + 1])] for i in range(len(points))]

        durations["sort"].append(time.perf_counter() - start)
        start = time.perf_counter()

        with ThreadPool(12) as pool:
            pool.starmap(write_memmap_with_create, [(file_path.joinpath(f"{i:05}.tiff"),
                                                    (lookup[1, sect], lookup[0, sect]),
                                                    (values[sect] / weights[sect]),
                                                    write_shape[1:], np.float32)
                                                    for i, sect in zip(img, sections)])
    except BaseException as be:
        print(f"Error on BP: {be}")
        traceback.print_tb(be.__traceback__, file=sys.stderr)
        raise be

    durations["write_direct"].append(time.perf_counter() - start)

    durations["total_process"].append(time.perf_counter() - start_total)

    return durations, index


def calculate_backproject_chunk_size(config, volume_cache, axis=0):
    if config.max_ram_gb == 0:
        return DEFAULT_CHUNK_SIZE

    bounding_box_shape = (
        BoundingBox.bound_boxes(volume_cache.bounding_boxes).get_shape()
        if config.backproject_min_bounding_box
        else volume_cache.get_volume_shape()
    )

    chunk_size = calculate_chunk_size(
        bounding_box_shape,
        volume_cache.get_volume_dtype(),
        config.max_ram_gb,
        axis=axis,
    )

    return chunk_size


def create_volume_chunks(
    volume_cache, chunk_size=128, backproject_min_bounding_box=False, axis=0
):
    # Find the dimensions of the volume
    volume_shape = volume_cache.get_volume_shape()

    # Create bounding boxes along the first axis each containing chunk_size slices
    chunks_and_boxes = []

    # If backproject_min_bounding_box is True,
    # create a bounding box that contains the minimum bounding box of the volume.
    min_bounding_box = None

    # Calculate the range of slices to process
    volume_end = volume_shape[axis]
    process_range = range(0, volume_end, chunk_size)

    if backproject_min_bounding_box:
        min_bounding_box = BoundingBox.bound_boxes(volume_cache.bounding_boxes)
        min_x_min, min_x_max, min_y_min, min_y_max, min_z_min, min_z_max = (
            min_bounding_box.approx_bounds()
        )

        min_dim_min = min_x_min if axis == 0 else min_y_min if axis == 1 else min_z_min
        min_dim_max = min_x_max if axis == 0 else min_y_max if axis == 1 else min_z_max

        process_range = range(min_dim_min, min_dim_max + 1, chunk_size)
        volume_end = min_dim_max + 1

    for i in process_range:
        end = min(i + chunk_size, volume_end)

        x_min = i if axis == 0 else 0
        x_max = end if axis == 0 else volume_shape[0]
        y_min = i if axis == 1 else 0
        y_max = end if axis == 1 else volume_shape[1]
        z_min = i if axis == 2 else 0
        z_max = end if axis == 2 else volume_shape[2]

        # Create a bounding box that contains the chunk of slices
        bounding_box = BoundingBox(
            BoundingBox.bounds_to_rect(
                x_min, x_max - 1, y_min, y_max - 1, z_min, z_max - 1
            )
        )

        # If backproject_min_bounding_box is True, intersect the bounding box with the minimum bounding box
        if backproject_min_bounding_box:
            bounding_box = bounding_box.intersection(min_bounding_box)

        # Determine which bounding boxes are in the chunk
        chunk_boxes = [
            (j, bbox)
            for j, bbox in enumerate(volume_cache.bounding_boxes)
            if bbox.intersects(bounding_box)
        ]

        chunks_and_boxes.append((bounding_box, chunk_boxes))

    return chunks_and_boxes


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
