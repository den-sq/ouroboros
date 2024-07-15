from ouroboros.helpers.memory_usage import calculate_gigabytes_from_dimensions
from ouroboros.helpers.slice import (
    generate_coordinate_grid_for_rect,
    make_volume_binary,
    write_slices_to_volume,
)
from ouroboros.helpers.volume_cache import VolumeCache
from ouroboros.helpers.bounding_boxes import BoundingBox
from .pipeline import PipelineStep
from ouroboros.helpers.options import BackprojectOptions
from ouroboros.helpers.files import load_and_save_tiff_from_slices

import concurrent.futures
import tifffile
import os
import multiprocessing
import time
import numpy as np
import shutil

DEFAULT_CHUNK_SIZE = 128


class BackprojectPipelineStep(PipelineStep):
    def __init__(self, processes=multiprocessing.cpu_count()) -> None:
        super().__init__(
            inputs=(
                "backproject_options",
                "output_file_path",
                "volume_cache",
                "slice_rects",
            )
        )

        self.num_processes = processes

    def _process(self, input_data: any) -> tuple[any, None] | tuple[None, any]:
        config, input_tiff_path, volume_cache, slice_rects, pipeline_input = input_data

        # Verify that a config object is provided
        if not isinstance(config, BackprojectOptions):
            return "Input data must contain a BackprojectOptions object."

        # Verify that input_data is a string containing a path to a tif file
        if not isinstance(input_tiff_path, str):
            return "Input data must contain a string containing a path to a tif file."

        # Verify that a volume cache is given
        if not isinstance(volume_cache, VolumeCache):
            return "Input data must contain a VolumeCache object."

        # Verify that slice rects is given
        if not isinstance(slice_rects, np.ndarray):
            return "Input data must contain an array of slice rects."

        straightened_volume_path = input_tiff_path

        volume_paths = [None] * len(volume_cache.bounding_boxes)
        volume_memmaps = [None] * len(volume_cache.bounding_boxes)

        # Create a folder to hold the temporary volume files
        temp_folder_path = os.path.join(
            config.output_file_folder, config.output_file_name + "-tempvolumes"
        )
        os.makedirs(temp_folder_path, exist_ok=True)

        # Process each bounding box in parallel, writing the results to the backprojected volume
        try:
            with concurrent.futures.ProcessPoolExecutor(
                max_workers=self.num_processes
            ) as executor:
                futures = []

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
                        )
                    )

                # Track the number of completed futures
                completed = 0
                total_futures = len(futures)

                for future in concurrent.futures.as_completed(futures):
                    # Store the durations for each bounding box
                    durations, volume_file_path, index = future.result()
                    for key, value in durations.items():
                        self.add_timing_list(key, value)

                    # Update the progress bar
                    completed += 1
                    self.update_progress(completed / total_futures / 2)

                    # Load the volume from the file
                    volume_paths[index] = volume_file_path
                    volume_memmaps[index] = tifffile.memmap(volume_file_path, mode="r")

        except BaseException as e:
            return f"An error occurred while processing the bounding boxes: {e}"

        start = time.perf_counter()

        # Divide the backprojected volume into chunks
        chunk_size = (
            DEFAULT_CHUNK_SIZE
            if config.max_ram_gb == 0
            else int(
                (config.max_ram_gb * 1024**3)
                / calculate_chunk_size(config, volume_cache)
            )
        )

        axis = 0

        chunks_and_boxes = create_volume_chunks(
            volume_cache, chunk_size, config.backproject_min_bounding_box, axis=axis
        )

        # Save the offset of the minimum bounding box, if that option is enabled
        if config.backproject_min_bounding_box:
            min_bounding_box = chunks_and_boxes[0][
                0
            ]  # The first chunk bounding box has the same offset as the minimum bounding box
            pipeline_input.backprojection_offset = f"{min_bounding_box.x_min},{min_bounding_box.y_min},{min_bounding_box.z_min}"

        # Save the backprojected volume to a series of tif files
        folder_path = os.path.join(
            config.output_file_folder, config.output_file_name + "-backprojected"
        )
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        os.makedirs(folder_path, exist_ok=True)

        dtype = volume_cache.get_volume_dtype()
        volume_shape = volume_cache.get_volume_shape()

        num_digits = len(str(volume_shape[axis] - 1))

        for i, (chunk_bounding_box, bounding_boxes) in enumerate(chunks_and_boxes):
            chunk_volume = chunk_bounding_box.to_empty_volume(dtype=dtype)

            min_dim = (
                chunk_bounding_box.x_min
                if axis == 0
                else chunk_bounding_box.y_min if axis == 1 else chunk_bounding_box.z_min
            )
            max_dim = (
                chunk_bounding_box.x_max
                if axis == 0
                else chunk_bounding_box.y_max if axis == 1 else chunk_bounding_box.z_max
            )

            slice_range = range(min_dim, max_dim + 1)

            # If there are no bounding boxes in the chunk, write the empty volume to a series of tif files
            if len(bounding_boxes) == 0:
                slice_index = 0
                for j in slice_range:
                    tifffile.imwrite(
                        os.path.join(folder_path, f"{str(j).zfill(num_digits)}.tif"),
                        np.take(chunk_volume, slice_index, axis=axis),
                        contiguous=True,
                        compression=config.backprojection_compression,
                        software="ouroboros",
                    )
                    slice_index += 1
                continue

            for box_index, bbox in bounding_boxes:
                volume = volume_memmaps[box_index]

                # Calculate the intersection of the bounding box with the chunk bounding box
                intersection_box = chunk_bounding_box.intersection(bbox)

                # Calculate the bounding box coordinates
                bbox_x_min, _, bbox_y_min, _, bbox_z_min, _ = bbox.approx_bounds()
                int_x_min, int_x_max, int_y_min, int_y_max, int_z_min, int_z_max = (
                    intersection_box.approx_bounds()
                )

                # Calculate the coordinates of the intersection box in the volume
                x_min, x_max = int_x_min - bbox_x_min, int_x_max - bbox_x_min
                y_min, y_max = int_y_min - bbox_y_min, int_y_max - bbox_y_min
                z_min, z_max = int_z_min - bbox_z_min, int_z_max - bbox_z_min

                # Calculate the coordinates of the intersection box in the chunk volume
                int_x_min, int_x_max = (
                    int_x_min - chunk_bounding_box.x_min,
                    int_x_max - chunk_bounding_box.x_min,
                )
                int_y_min, int_y_max = (
                    int_y_min - chunk_bounding_box.y_min,
                    int_y_max - chunk_bounding_box.y_min,
                )
                int_z_min, int_z_max = (
                    int_z_min - chunk_bounding_box.z_min,
                    int_z_max - chunk_bounding_box.z_min,
                )

                # Copy the intersection volume to the chunk volume
                intersection_volume = volume[
                    x_min : x_max + 1, y_min : y_max + 1, z_min : z_max + 1
                ]
                non_zero_mask = intersection_volume != 0

                chunk_volume[
                    int_x_min : int_x_max + 1,
                    int_y_min : int_y_max + 1,
                    int_z_min : int_z_max + 1,
                ][non_zero_mask] = intersection_volume[non_zero_mask]

            # If make_backprojection_binary, set all non-zero values to 1
            if config.make_backprojection_binary:
                chunk_volume = make_volume_binary(chunk_volume)

            # Write the chunk volume to a series of tif files
            slice_index = 0
            for j in slice_range:
                tifffile.imwrite(
                    os.path.join(folder_path, f"{str(j).zfill(num_digits)}.tif"),
                    np.take(chunk_volume, slice_index, axis=axis),
                    contiguous=True,
                    compression=config.backprojection_compression,
                    software="ouroboros",
                )
                slice_index += 1

            # Update the progress bar
            self.update_progress(0.5 + i / len(chunks_and_boxes) / 2)

        # Close all the memmaps
        for volume_memmap in volume_memmaps:
            del volume_memmap

        # Delete the temporary volume files
        shutil.rmtree(
            os.path.join(
                config.output_file_folder, config.output_file_name + "-tempvolumes"
            )
        )

        self.add_timing("export", time.perf_counter() - start)

        # Save the backprojected volume to a single tif file
        if config.make_single_file:
            try:
                metadata = {}

                if config.backproject_min_bounding_box:
                    metadata["backprojection_offset_min_xyz"] = (
                        pipeline_input.backprojection_offset
                    )

                resolution = volume_cache.get_resolution_um()[:2]
                resolutionunit = "MICROMETER"

                load_and_save_tiff_from_slices(
                    folder_path,
                    folder_path + ".tif",
                    delete_intermediate=False,
                    compression=config.backprojection_compression,
                    metadata=metadata,
                    resolution=resolution,
                    resolutionunit=resolutionunit,
                )
            except BaseException as e:
                return f"Error creating single tif file: {e}"

        # Update the pipeline input with the output file path
        pipeline_input.backprojected_folder_path = folder_path

        return None


def process_bounding_box(
    config, bounding_box, straightened_volume_path, slice_rects, slice_indices, index
):
    durations = {
        "memmap": [],
        "get_slices": [],
        "generate_grid": [],
        "create_volume": [],
        "back_project": [],
        "write_to_tiff": [],
        "total_process": [],
    }

    start_total = time.perf_counter()

    # Load the straightened volume
    start = time.perf_counter()
    straightened_volume = make_tiff_memmap(straightened_volume_path, mode="r")

    # Get the slices from the straightened volume
    start = time.perf_counter()
    slices = np.array([straightened_volume[i] for i in slice_indices])
    durations["get_slices"].append(time.perf_counter() - start)

    # Close the memmap
    del straightened_volume

    # Generate a grid for each slice and stack them along the first axis
    start = time.perf_counter()
    grids = np.array(
        [
            generate_coordinate_grid_for_rect(
                slice_rects[i], config.slice_width, config.slice_height
            )
            for i in slice_indices
        ]
    )
    durations["generate_grid"].append(time.perf_counter() - start)

    # Create a volume for the bounding box
    start = time.perf_counter()
    volume = bounding_box.to_empty_volume()
    durations["create_volume"].append(time.perf_counter() - start)

    # Backproject the slices into the volume
    start = time.perf_counter()
    write_slices_to_volume(volume, bounding_box, grids, slices)
    durations["back_project"].append(time.perf_counter() - start)

    # Save the volume locally as a tif file
    start = time.perf_counter()
    file_path = os.path.join(
        config.output_file_folder,
        config.output_file_name + "-tempvolumes",
        f"{index}.tif",
    )
    tifffile.imwrite(file_path, volume, software="ouroboros")
    durations["write_to_tiff"].append(time.perf_counter() - start)

    durations["total_process"].append(time.perf_counter() - start_total)

    return durations, file_path, index


def make_tiff_memmap(file_name, mode):
    return tifffile.memmap(file_name, mode=mode)


def calculate_min_bounding_box(volume_cache):
    return BoundingBox.bound_boxes(volume_cache.bounding_boxes)


def calculate_chunk_size(config, volume_cache, axis=0):
    if config.max_ram_gb == 0:
        return DEFAULT_CHUNK_SIZE

    bounding_box_shape = (
        calculate_min_bounding_box(volume_cache).get_shape()[:axis]
        + calculate_min_bounding_box(volume_cache).get_shape()[axis + 1 :]
        if config.backproject_min_bounding_box
        else volume_cache.get_volume_shape()[:axis]
        + volume_cache.get_volume_shape()[axis + 1 :]
    )

    bounding_box_memory_usage = calculate_gigabytes_from_dimensions(
        bounding_box_shape,
        volume_cache.get_volume_dtype(),
    )

    return int((config.max_ram_gb * 1024**3) / bounding_box_memory_usage)


def create_volume_chunks(
    volume_cache, chunk_size=128, backproject_min_bounding_box=False, axis=0
):
    # Find the dimensions of the volume
    volume_shape = volume_cache.get_volume_shape()

    # Create bounding boxes along the first axis each containing chunk_size slices
    chunks_and_boxes = []

    # If backproject_min_bounding_box is True, create a bounding box that contains the minimum bounding box of the volume
    min_bounding_box = None

    # Calculate the range of slices to process
    volume_end = volume_shape[axis]
    process_range = range(0, volume_end, chunk_size)

    if backproject_min_bounding_box:
        min_bounding_box = calculate_min_bounding_box(volume_cache)
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
