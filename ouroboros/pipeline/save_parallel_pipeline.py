from ouroboros.slice import generate_coordinate_grid_for_rect, slice_volume_from_grid
from ouroboros.volume_cache import VolumeCache
from .pipeline import PipelineStep
from ouroboros.config import Config
import numpy as np
import shutil
import concurrent.futures
from tifffile import imwrite, imread, TiffWriter
import os

class SaveParallelPipelineStep(PipelineStep):
    def __init__(self, threads=None, processes=None) -> None:
        super().__init__()

        self.num_threads = threads
        self.num_processes = processes

    def _process(self, input_data: any) -> tuple[any, None] | tuple[None, any]:
        config, volume_cache, slice_rects = input_data

        # Verify that a config object is provided
        if not isinstance(config, Config):
            return None, "Input data must contain a Config object."
        
        # Verify that a volume cache is given
        if not isinstance(volume_cache, VolumeCache):
            return None, "Input data must contain a VolumeCache object."

        # Verify that slice rects is given
        if not isinstance(slice_rects, np.ndarray):
            return None, "Input data must contain an array of slice rects."
        
        # Create a folder with the same name as the output file
        folder_name = config.output_file_path + "-slices"
        os.makedirs(folder_name, exist_ok=True)
        
        # Create a process pool executor to parallelize generating and writing slices to disk, 
        # and a thread pool executor to parallelize downloading bounding box volumes.
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.num_processes) as process_executor:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as thread_executor:
                futures = [thread_executor.submit(thread_worker, volume_cache, i) for i in range(len(volume_cache.volumes))]
            
                for future in concurrent.futures.as_completed(futures):
                    try:
                        data = future.result()
                    except Exception as e:
                        return None, f"An error occurred while downloading data: {e}"
                    else:
                        process_executor.submit(process_worker, config, data, slice_rects, thread_executor)

        # Load the saved tifs in numerical order
        tif_files = get_sorted_tif_files(folder_name)

        # Save tifs to a new resulting tif 
        with TiffWriter(config.output_file_path) as tif:
            for filename in tif_files:
                tif_file = imread(filename)
                tif.write(tif_file, contiguous=True)

        # Delete slices folder
        # shutil.rmtree(folder_name)

        return config.output_file_path, None
    
def thread_worker(volume_cache, i):
    print(f"Downloading volume {i}")
    return volume_cache.create_processing_data(i) 

def process_worker(config, processing_data, slice_rects, thread_executor):
        volume, bounding_box, slice_indices, remove_volume = processing_data
        # print(f"Processing slices {slice_indices}", flush=True)

        for i in slice_indices:
            grid = generate_coordinate_grid_for_rect(slice_rects[i], config.slice_width, config.slice_height)
            slice_i = slice_volume_from_grid(volume, bounding_box, grid, config.slice_width, config.slice_height)
            filename = f"{config.output_file_path}-slices/{i}.tif"

            thread_executor.submit(save_thread, filename, slice_i)

            # imwrite(f"{config.output_file_path}-slices/{i}.tif", slice_i)

        remove_volume()

def save_thread(filename, data):
    print("saving")
    imwrite(filename, data)

def get_sorted_tif_files(directory):
    # Get all files in the directory
    files = os.listdir(directory)
    
    # Filter to include only .tif files and sort them numerically
    tif_files = sorted(
        (file for file in files if file.endswith('.tif')),
        key=lambda x: int(os.path.splitext(x)[0])
    )
    
    return tif_files