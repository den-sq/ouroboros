import numpy as np
import time
from abc import ABC, abstractmethod

class Pipeline:
    def __init__(self, steps: list["PipelineStep"]) -> None:
        self.steps = steps

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
        self.timing = {"pipeline": type(self).__name__, "custom_times": {}}

    def process(self, input_data: any) -> tuple[any, None] | tuple[None, any]:
        start = time.perf_counter()

        result = self._process(input_data)

        # Record the duration of the run
        end = time.perf_counter()
        duration_seconds = end - start
        self.timing["duration_seconds"] = duration_seconds

        return result

    @abstractmethod
    def _process(self, input_data: any) -> tuple[any, None] | tuple[None, any]:
        pass

    def get_time_statistics(self):
        # Replace custom timings with statistics about the custom timings
        custom_times = self.timing["custom_times"]
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