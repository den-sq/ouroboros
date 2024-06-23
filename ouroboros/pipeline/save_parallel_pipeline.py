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

# TODO: Return errors correctly
# TODO: Add lock to make saving is thread safe

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

        # Queue to hold downloaded data for processing
        data_queue = multiprocessing.Queue()
        download_done_event = multiprocessing.Event()

        # Thread pool executor to download the data
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as download_executor:
            download_futures = []

            for i in range(len(volume_cache.volumes)):
                download_future = download_executor.submit(thread_worker, volume_cache, i, data_queue, download_done_event)
                download_futures.append(download_future)
            
            # Process pool executor to process the data
            with concurrent.futures.ProcessPoolExecutor(max_workers=self.num_processes) as process_executor:
                futures = []
                
                while True:
                    try:
                        print("Starting process")
                        data = data_queue.get(timeout=1)
                        futures.append(process_executor.submit(process_worker, config, data, slice_rects, self.num_threads))
                    except multiprocessing.queues.Empty:
                        if download_done_event.is_set() and data_queue.empty():
                            print("done")
                            break
                
                for future in concurrent.futures.as_completed(futures):
                    try:
                        vol_index = future.result()
                    except Exception as e:
                        print("Error processing data!!!")
                        return None, f"An error occurred while processing data: {e}"
                    else:
                        # Delete the volume used in the child process
                        volume_cache.remove_volume(vol_index)
                        print(f"Remove volume {vol_index}")

                print ("Done processing")

            for download_future in concurrent.futures.as_completed(download_futures):
                download_future.result()
            print("Done 2")

        print("Done 3")

        # Load the saved tifs in numerical order
        tif_files = get_sorted_tif_files(folder_name)
        print(tif_files)

        # Save tifs to a new resulting tif 
        with TiffWriter(config.output_file_path) as tif:
            for filename in tif_files:
                tif_file = imread(filename)
                tif.write(tif_file, contiguous=True)

        # Delete slices folder
        # shutil.rmtree(folder_name)

        return config.output_file_path, None

def thread_worker(volume_cache, i, data_queue, download_done_event):
    try:
        print(f"Downloading volume {i}")
        data = volume_cache.create_processing_data(i)
        data_queue.put(data)
    except Exception as e:
        print(f"Error downloading volume {i}: {e}")
    finally:
        if i == (len(volume_cache.volumes) - 1):
            download_done_event.set()

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
    # print("saving", filename)
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
