from ouroboros.helpers.slice import (
    generate_coordinate_grid_for_rect,
    slice_volume_from_grids,
)
from ouroboros.helpers.volume_cache import VolumeCache
from ouroboros.helpers.files import load_and_save_tiff_from_slices
from .pipeline import PipelineStep
from ouroboros.config import Config
import numpy as np
import concurrent.futures
from tifffile import imwrite
import os
import multiprocessing
import time


class SaveParallelPipelineStep(PipelineStep):
    def __init__(
        self,
        threads=1,
        processes=multiprocessing.cpu_count(),
        delete_intermediate=False,
    ) -> None:
        super().__init__(inputs=("config", "volume_cache", "slice_rects"))

        self.num_threads = threads
        self.num_processes = processes
        self.delete_intermediate = delete_intermediate

    def with_delete_intermediate(self) -> "SaveParallelPipelineStep":
        self.delete_intermediate = True
        return self

    def with_processes(self, processes: int) -> "SaveParallelPipelineStep":
        self.num_processes = processes
        return self

    def _process(self, input_data: tuple[any]) -> None | str:
        config, volume_cache, slice_rects, pipeline_input = input_data

        # Verify that a config object is provided
        if not isinstance(config, Config):
            return "Input data must contain a Config object."

        # Verify that a volume cache is given
        if not isinstance(volume_cache, VolumeCache):
            return "Input data must contain a VolumeCache object."

        # Verify that slice rects is given
        if not isinstance(slice_rects, np.ndarray):
            return "Input data must contain an array of slice rects."

        # Create a folder with the same name as the output file
        folder_name = os.path.join(
            config.output_file_folder, f"{config.output_file_name}-slices"
        )
        os.makedirs(folder_name, exist_ok=True)
        output_file_path = config.output_file_path

        # Calculate the number of digits needed to store the number of slices
        num_digits = len(str(len(slice_rects) - 1))

        # Create a queue to hold downloaded data for processing
        data_queue = multiprocessing.Queue()

        # Start the download volumes process and process downloaded volumes as they become available in the queue
        try:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.num_threads
            ) as download_executor, concurrent.futures.ProcessPoolExecutor(
                max_workers=self.num_processes
            ) as process_executor:
                download_futures = []

                ranges = np.array_split(
                    np.arange(len(volume_cache.volumes)), self.num_threads
                )

                # Download all volumes in parallel
                for volumes_range in ranges:
                    download_futures.append(
                        download_executor.submit(
                            thread_worker_iterative,
                            volume_cache,
                            volumes_range,
                            data_queue,
                            self.num_threads == 1,
                        )
                    )

                processing_futures = []

                # Check if all downloads are done
                def downloads_done():
                    return all([future.done() for future in download_futures])

                # Process downloaded data as it becomes available
                while True:
                    try:
                        data = data_queue.get(timeout=1)

                        # Process the data in a separate process
                        # Note: If the maximum number of processes is reached, this will enqueue the arguments
                        # and wait for a process to become available
                        # TODO: Avoid passing in all of slice rects, rather pass in either a smaller version
                        # or use shared memory
                        processing_futures.append(
                            process_executor.submit(
                                process_worker_save_parallel,
                                config,
                                folder_name,
                                data,
                                slice_rects,
                                self.num_threads,
                                num_digits,
                            )
                        )

                        # Update progress
                        self.update_progress(
                            len(
                                [
                                    future
                                    for future in processing_futures
                                    if future.done()
                                ]
                            )
                            / len(volume_cache.volumes)
                        )
                    except multiprocessing.queues.Empty:
                        if downloads_done() and data_queue.empty():
                            break
                    except Exception as e:
                        download_executor.shutdown(wait=False, cancel_futures=True)
                        process_executor.shutdown(wait=False, cancel_futures=True)
                        return f"Error processing data: {e}"
        except Exception as e:
            return f"Error downloading data: {e}"

        # Wait for all processing to complete
        concurrent.futures.wait(processing_futures)

        # Log the processing durations
        for future in processing_futures:
            _, durations = future.result()
            for key, value in durations.items():
                self.add_timing_list(key, value)

        try:
            load_and_save_tiff_from_slices(
                folder_name,
                output_file_path,
                delete_intermediate=self.delete_intermediate,
            )
        except Exception as e:
            return f"Error creating single tif file: {e}"

        # Update the pipeline input with the output file path
        pipeline_input.output_file_path = output_file_path

        return None


def thread_worker_iterative(
    volume_cache, volumes_range, data_queue, single_thread=False
):
    for i in volumes_range:
        # Create a packet of data to process
        data = volume_cache.create_processing_data(i, parallel=single_thread)
        data_queue.put(data)

        # Remove the volume from the cache after the packet is created
        # TODO: Change this if the data the data is shared not copied
        volume_cache.remove_volume(i)


def process_worker_save_parallel(
    config, folder_name, processing_data, slice_rects, num_threads, num_digits
):
    volume, bounding_box, slice_indices, volume_index = processing_data

    durations = {
        "generate_grid": [],
        "slice_volume": [],
        "save": [],
        "total_process": [],
    }

    start_total = time.perf_counter()

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

    # Slice the volume using the grids
    start = time.perf_counter()
    slices = slice_volume_from_grids(
        volume, bounding_box, grids, config.slice_width, config.slice_height
    )
    durations["slice_volume"].append(time.perf_counter() - start)

    # Using a ThreadPoolExecutor within the process for saving slices
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=num_threads
    ) as thread_executor:
        futures = []

        for i, slice_i in zip(slice_indices, slices):
            start = time.perf_counter()
            filename = f"{folder_name}/{str(i).zfill(num_digits)}.tif"
            futures.append(thread_executor.submit(save_thread, filename, slice_i))
            durations["save"].append(time.perf_counter() - start)

        for future in concurrent.futures.as_completed(futures):
            future.result()

    durations["total_process"].append(time.perf_counter() - start_total)

    return volume_index, durations


def save_thread(filename, data):
    imwrite(filename, data)
