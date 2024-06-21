import numpy as np
import time
from abc import ABC, abstractmethod

class Pipeline:
    def __init__(self, steps: list["PipelineStep"]) -> None:
        self.steps = steps
        self.current_step = 0

    def process(self, input_data: any) -> tuple[any, None] | tuple[None, any]:
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
        self.run_durations = []

    def process(self, input_data: any) -> tuple[any, None] | tuple[None, any]:
        start = time.perf_counter()

        self._process(input_data)

        # Record the duration of the run
        end = time.perf_counter()
        duration_seconds = end - start
        self.run_durations.append(duration_seconds)

    @abstractmethod
    def _process(self, input_data: any) -> tuple[any, None] | tuple[None, any]:
        pass

    def get_time_statistics(self):
        return {
            "average": np.mean(self.run_durations),
            "median": np.median(self.run_durations),
            "min": np.min(self.run_durations),
            "max": np.max(self.run_durations)
        }