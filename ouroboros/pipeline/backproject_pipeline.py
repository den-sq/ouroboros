from ouroboros.helpers.slice import generate_coordinate_grid_for_rect, write_slices_to_volume
from ouroboros.helpers.volume_cache import VolumeCache
from .pipeline import PipelineStep
from ouroboros.config import Config

import concurrent.futures
import tifffile
import os
import multiprocessing
import time
import numpy as np

class BackprojectPipelineStep(PipelineStep):
    def __init__(self, processes=multiprocessing.cpu_count()) -> None:
        super().__init__()

        self.num_processes = processes

    def _process(self, input_data: any) -> tuple[any, None] | tuple[None, any]:
        config, input_tiff_path, volume_cache, slice_rects = input_data

        # Verify that a config object is provided
        if not isinstance(config, Config):
            return None, "Input data must contain a Config object."

        # Verify that input_data is a string containing a path to a tif file
        if not isinstance(input_tiff_path, str):
            return None, "Input data must contain a string containing a path to a tif file."
        
        # Verify that a volume cache is given
        if not isinstance(volume_cache, VolumeCache):
            return None, "Input data must contain a VolumeCache object."
        
        # Verify that slice rects is given
        if not isinstance(slice_rects, np.ndarray):
            return None, "Input data must contain an array of slice rects."

        straightened_volume_path = input_tiff_path

        # Make a tif memmap file to store the backprojected volume
        backprojected_volume_path = create_empty_local_tiff_memmap(config, volume_cache)

        ### TESTING ###
        backprojected_volume = make_tiff_memmap(backprojected_volume_path, mode='r+')
        print(f"Backprojected volume shape: {backprojected_volume.shape}")
        
        # Create a lock to prevent multiple processes from writing to the same file
        manager = multiprocessing.Manager()
        lock = manager.Lock()

        # Process each bounding box in parallel, writing the results to the backprojected volume
        try:
            with concurrent.futures.ProcessPoolExecutor(max_workers=self.num_processes) as executor:
                futures = []

                for i in range(len(volume_cache.bounding_boxes)):
                    bounding_box = volume_cache.bounding_boxes[i]
                    slice_indices = volume_cache.get_slice_indices(i)
                    futures.append(executor.submit(process_bounding_box, config, bounding_box, 
                                                straightened_volume_path, backprojected_volume_path, slice_rects, slice_indices, lock))

                # Track the number of completed futures
                completed = 0
                total_futures = len(futures)

                for future in concurrent.futures.as_completed(futures):
                    # Store the durations for each bounding box
                    durations = future.result()
                    for key, value in durations.items():
                        self.add_timing_list(key, value)

                    completed += 1
                    self.update_progress(completed / total_futures)
        except Exception as e:
            return None, f"An error occurred while processing the bounding boxes: {e}"

        # TEMPORARY
        # Load slices from the backprojected volume and write them to individual slices
        # num_digits = len(str(backprojected_volume.shape[0] - 1))
        # with tifffile.TiffFile(backprojected_volume_path) as tif:
        #     for i, page in enumerate(tif.pages):
        #         slice_i = page.asarray()
        #         tifffile.imwrite(f"./data/backprojected/{str(i).zfill(num_digits)}.tif", slice_i, contiguous=True)
        
        return backprojected_volume_path, None

def process_bounding_box(config, bounding_box, straightened_volume_path, backprojected_volume_path, slice_rects, slice_indices, lock):
    durations = {"memmap": [], "get_slices": [], "generate_grid": [], "create_volume": [], "back_project": [], "write_to_memmap": [], "total_process": []}

    start_total = time.perf_counter()

    # Load the straightened volume
    start = time.perf_counter()
    straightened_volume = make_tiff_memmap(straightened_volume_path, mode='r')
    
    # Load the backprojected volume
    backprojected_volume = make_tiff_memmap(backprojected_volume_path, mode='r+')
    durations["memmap"].append(time.perf_counter() - start)

    # Get the slices from the straightened volume
    start = time.perf_counter()
    slices = np.array([straightened_volume[i] for i in slice_indices])
    durations["get_slices"].append(time.perf_counter() - start)

    # Generate a grid for each slice and stack them along the first axis
    start = time.perf_counter()
    grids = np.array([generate_coordinate_grid_for_rect(slice_rects[i], config.slice_width, config.slice_height) for i in slice_indices])
    durations["generate_grid"].append(time.perf_counter() - start)

    # Create a volume for the bounding box
    start = time.perf_counter()
    volume = bounding_box.to_empty_volume()
    durations["create_volume"].append(time.perf_counter() - start)

    # Backproject the slices into the volume
    start = time.perf_counter()
    write_slices_to_volume(volume, bounding_box, grids, slices)
    durations["back_project"].append(time.perf_counter() - start)

    # Write the volume to the backprojected volume
    # TODO: How well is this aligned?
    with lock:
        start = time.perf_counter()
        x_min, x_max, y_min, y_max, z_min, z_max = bounding_box.approx_bounds()
        backprojected_volume[x_min:x_max+1, y_min:y_max+1, z_min:z_max+1] = volume
        durations["write_to_memmap"].append(time.perf_counter() - start)

    durations["total_process"].append(time.perf_counter() - start_total)

    return durations

def make_tiff_memmap(file_name, mode):
    return tifffile.memmap(file_name, mode=mode)
    
def create_empty_local_tiff_memmap(config, volume_cache):
    shape = volume_cache.get_volume_shape()
    shape_per_image = shape[1:]
    n_images = shape[0]
    dtype = volume_cache.get_volume_dtype()

    bigtiff = volume_cache.get_volume_gigabytes() > 4

    # Make a tiff file with the same shape and dtype as the volume
    file_path = os.path.join(config.output_file_folder, config.output_file_name) + "-backprojected.tif"

    if os.path.exists(file_path):
        return file_path
        # os.remove(file_path)

    with tifffile.TiffWriter(file_path, bigtiff=bigtiff) as tif:
        for _ in range(n_images):
            tif.write(np.zeros(shape_per_image, dtype=dtype), contiguous=True)

    return file_path

