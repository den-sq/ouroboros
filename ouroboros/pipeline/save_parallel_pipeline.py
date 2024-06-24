from ouroboros.slice import generate_coordinate_grid_for_rect, slice_volume_from_grid
from ouroboros.volume_cache import VolumeCache
from .pipeline import PipelineStep
from ouroboros.config import Config
import numpy as np
import shutil
import concurrent.futures
from tifffile import imwrite, imread, TiffWriter
import os
import multiprocessing
from threading import Lock

# TODO: Return errors correctly
# TODO: Add lock to make saving is thread safe
# TODO: Count the number of slices to be processed and display a progress bar
# TODO: Figure out why it seems to freeze (folder exists, files exist, output file exits, memory usage of terminal (memory leak?))

# TODO: Potential algorithmic improvement:
# Store the slice data in a shared memory object and pass the shared memory object to the processing worker
# This way, the data is shared between processes and does not need to be copied
# https://docs.python.org/3/library/multiprocessing.shared_memory.html

# Store slices in a large np array and save in one operation at the end of the processing
# Then recombine the individual tiffs into a single tiff later
# Use tiff writer to do everything so you don't need a large np array

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

        # Create a queue to hold downloaded data for processing
        data_queue = multiprocessing.Queue()
        downloads_completed = 0
        downloads_completed_lock = Lock()

        def increment_downloads_completed(future):
            nonlocal downloads_completed
            with downloads_completed_lock:
                downloads_completed += 1

        # Start the download volumes process and process downloaded volumes as they become available in the queue
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as download_executor, \
             concurrent.futures.ProcessPoolExecutor(max_workers=self.num_processes) as process_executor:
            download_futures = []

            # Download all volumes in parallel
            for i in range(len(volume_cache.volumes)):
                download_future = download_executor.submit(thread_worker, volume_cache, i, data_queue)
                download_future.add_done_callback(increment_downloads_completed)
                download_futures.append(download_future)
            
            processing_futures = []

            print("Starting processing")
            
            # Process downloaded data as it becomes available
            while True:
                try:
                    data = data_queue.get(timeout=1)
                    processing_futures.append(process_executor.submit(process_worker, config, data, slice_rects, self.num_threads))
                except multiprocessing.queues.Empty:
                    if downloads_completed == len(volume_cache.volumes) and data_queue.empty():
                        print("done downloading")
                        break

            print ("Done processing")

        # Wait for all processing to complete
        concurrent.futures.wait(processing_futures)
        print("Actually done processing")

        # Load the saved tifs in numerical order
        tif_files = get_sorted_tif_files(folder_name)

        # Save tifs to a new resulting tif 
        with TiffWriter(config.output_file_path) as tif:
            for filename in tif_files:
                tif_file = imread(f"{config.output_file_path}-slices/{filename}")
                tif.write(tif_file, contiguous=True)

        # Delete slices folder
        shutil.rmtree(folder_name)

        return config.output_file_path, None

def thread_worker(volume_cache, i, data_queue):
    try:
        print(f"Downloading volume {i}")
        # Create a packet of data to process
        data = volume_cache.create_processing_data(i)
        data_queue.put(data)

        # Remove the volume from the cache after the packet is created
        # TODO: Change this if the data the data is shared not copied
        volume_cache.remove_volume(i)
    except Exception as e:
        print(f"Error downloading volume {i}: {e}")

def process_worker(config, processing_data, slice_rects, num_threads):
    volume, bounding_box, slice_indices, volume_index = processing_data

    # Using a ThreadPoolExecutor within the process for saving slices
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as thread_executor:
        futures = []
        for i in slice_indices:
            grid = generate_coordinate_grid_for_rect(slice_rects[i], config.slice_width, config.slice_height)
            slice_i = slice_volume_from_grid(volume, bounding_box, grid, config.slice_width, config.slice_height)
            filename = f"{config.output_file_path}-slices/{i}.tif"
            futures.append(thread_executor.submit(save_thread, filename, slice_i))

        for future in concurrent.futures.as_completed(futures):
            future.result()

    return volume_index

def save_thread(filename, data):
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
