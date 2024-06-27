import numpy as np
import time
from abc import ABC, abstractmethod

from tqdm import tqdm

class Pipeline:
    def __init__(self, steps: list["PipelineStep"]) -> None:
        self.steps = steps

    def process(self, input_data: any) -> tuple[any, None] | tuple[None, any]:
        """
        Run the pipeline on the input data.

        Parameters
        ----------
            input_data (any): The data to process.

        Returns
        -------
            tuple: A tuple containing the processed data and any errors that occurred during processing.
        """

        data = input_data

        for step in self.steps:
            data, errors = step.process(data)

            if errors is not None:
                return (None, errors)

        return (data, None)
    
    def get_step_statistics(self):
        return [step.get_time_statistics() for step in self.steps]

# TODO: Consider adding standard pydantic validation interface

class PipelineStep(ABC):
    def __init__(self) -> None:
        self.step_name = type(self).__name__
        self.timing = {"pipeline": self.step_name, "custom_times": {}}
        self.progress = 0
        self.progress_listener_callables = []
        self.show_progress_bar = False
        self.progress_bar = None

    def process(self, input_data: any) -> tuple[any, None] | tuple[None, any]:
        if self.show_progress_bar:
            tqdm.write(f"Starting step {self.step_name}")
            self.progress_bar = tqdm(total=100)

        # Reset the progress to 0 at the start of the step
        self.update_progress(0)

        start = time.perf_counter()

        result = self._process(input_data)

        # Record the duration of the run
        end = time.perf_counter()
        duration_seconds = end - start
        self.timing["duration_seconds"] = duration_seconds

        # Update the progress to 100% after the step is done
        self.update_progress(1)

        if self.show_progress_bar:
            self.progress_bar.close()

        return result

    @abstractmethod
    def _process(self, input_data: any) -> tuple[any, None] | tuple[None, any]:
        pass

    def get_time_statistics(self):
        # Replace custom timings with statistics about the custom timings
        custom_times = self.timing["custom_times"]
        
        # Remove any empty custom times
        custom_times = {key: value for key, value in custom_times.items() if len(value) > 0}

        # Calculate statistics for each custom time
        custom_times_statistics = {key: {"mean": np.mean(value), "std": np.std(value), "min": np.min(value), "max": np.max(value)} for key, value in custom_times.items()}
        self.timing["custom_times"] = custom_times_statistics

        return self.timing

    def add_timing(self, key: str, value: float):
        if key in self.timing:
            self.timing["custom_times"][key].append(value)
        else:
            self.timing["custom_times"][key] = [value]

    def add_timing_list(self, key: str, values: list[float]):
        if key in self.timing:
            self.timing["custom_times"][key].extend(values)
        else:
            self.timing["custom_times"][key] = values

    def with_progress_bar(self):
        self.show_progress_bar = True
        return self

    def update_progress(self, progress: float):
        self.progress = progress

        for progress_callable in self.progress_listener_callables:
            progress_callable(progress)

        if self.show_progress_bar:
            self.progress_bar.update(progress * 100 - self.progress_bar.n)

    def get_progress(self):
        return self.progress

    def listen_for_progress(self, progress_callable):
        """
        Add a callable that will be called with the progress of the step.

        Receives a float between 0 and 1.

        Parameters
        ----------
            progress_callable : callable (float) -> None

        Returns
        -------
            None
        """
        self.progress_listener_callables.append(progress_callable)