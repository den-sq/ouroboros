from ouroboros.slice import generate_coordinate_grid_for_rect, slice_volume_from_grids
from ouroboros.volume_cache import VolumeCache
from .pipeline import PipelineStep
from ouroboros.config import Config
import numpy as np
import shutil
import concurrent.futures
from tifffile import imwrite, imread, TiffWriter
import os
import multiprocessing
import time

class SaveParallelAltPipelineStep(PipelineStep):
    def __init__(self, threads=1, processes=None) -> None:
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

        # Calculate the number of digits needed to store the number of slices
        num_digits = len(str(len(slice_rects) - 1))

        # Create a queue to hold downloaded data for processing
        data_queue = multiprocessing.Queue()

        # Start the download volumes process and process downloaded volumes as they become available in the queue
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as download_executor, \
             concurrent.futures.ProcessPoolExecutor(max_workers=self.num_processes) as process_executor:
            download_futures = []

            ranges = np.array_split(np.arange(len(volume_cache.volumes)), self.num_threads)

            # Download all volumes in parallel
            for volumes_range in ranges:
                download_futures.append(download_executor.submit(thread_worker_iterative, volume_cache, volumes_range, data_queue, self.num_threads == 1))
            
            processing_futures = []

            # Check if all downloads are done
            def downloads_done():
                return all([future.done() for future in download_futures])
            
            # Process downloaded data as it becomes available
            while True:
                try:
                    data = data_queue.get(timeout=1)
                    print(f"Processing volume {data[3]}")
                    processing_futures.append(process_executor.submit(process_worker_save_parallel, config, data, slice_rects, self.num_threads, num_digits))
                except multiprocessing.queues.Empty:
                    if downloads_done() and data_queue.empty():
                        break
                except Exception as e:
                    print(f"Error processing data: {e}")

            print ("Done downloading volumes")

        # Wait for all processing to complete
        concurrent.futures.wait(processing_futures)
        print("Done processing")

        # Log the processing durations
        for future in processing_futures:
            _, durations = future.result()
            for key, value in durations.items():
                self.add_timing_list(key, value)

        load_and_save_tiff_from_slices(folder_name, config, delete_intermediate=False)

        return config.output_file_path, None

def thread_worker_iterative(volume_cache, volumes_range, data_queue, single_thread=False):
    try:
        for i in volumes_range:
            print(f"Downloading volume {i}")
            # Create a packet of data to process
            data = volume_cache.create_processing_data(i, parallel=single_thread)            
            data_queue.put(data)

            # Remove the volume from the cache after the packet is created
            # TODO: Change this if the data the data is shared not copied
            volume_cache.remove_volume(i)
    except Exception as e:
        print(f"Error downloading volume {i}: {e}")

def process_worker_save_parallel(config, processing_data, slice_rects, num_threads, num_digits):
    volume, bounding_box, slice_indices, volume_index = processing_data

    durations = {"generate_grid": [], "slice_volume": [], "save": [], "total_process": []}

    start_total = time.perf_counter()

    # Generate a grid for each slice and stack them along the first axis
    start = time.perf_counter()
    grids = np.array([generate_coordinate_grid_for_rect(slice_rects[i], config.slice_width, config.slice_height) for i in slice_indices])
    durations["generate_grid"].append(time.perf_counter() - start)

    # Slice the volume using the grids
    start = time.perf_counter()
    slices = slice_volume_from_grids(volume, bounding_box, grids, config.slice_width, config.slice_height)
    durations["slice_volume"].append(time.perf_counter() - start)

    # Using a ThreadPoolExecutor within the process for saving slices
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as thread_executor:
        futures = []

        for i, slice_i in zip(slice_indices, slices):
            start = time.perf_counter()
            filename = f"{config.output_file_path}-slices/{str(i).zfill(num_digits)}.tif"
            futures.append(thread_executor.submit(save_thread, filename, slice_i))
            durations["save"].append(time.perf_counter() - start)

        for future in concurrent.futures.as_completed(futures):
            future.result()

    durations["total_process"].append(time.perf_counter() - start_total)

    return volume_index, durations

def save_thread(filename, data):
    imwrite(filename, data)

def load_and_save_tiff_from_slices(folder_name, config, delete_intermediate=True):
    # Load the saved tifs in numerical order
    tif_files = get_sorted_tif_files(folder_name)

    # Save tifs to a new resulting tif 
    with TiffWriter(config.output_file_path) as tif:
        for filename in tif_files:
            tif_file = imread(f"{config.output_file_path}-slices/{filename}")
            tif.write(tif_file, contiguous=True)

    # Delete slices folder
    if delete_intermediate:
        shutil.rmtree(folder_name)

def get_sorted_tif_files(directory):
    # Get all files in the directory
    files = os.listdir(directory)
    
    # Filter to include only .tif files and sort them numerically
    tif_files = sorted(
        (file for file in files if file.endswith('.tif')),
        key=lambda x: int(os.path.splitext(x)[0])
    )
    
    return tif_files
