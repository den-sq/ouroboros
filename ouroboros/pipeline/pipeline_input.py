from dataclasses import astuple, dataclass
import numpy as np
from ouroboros.helpers.config import Config
from ouroboros.helpers.volume_cache import VolumeCache
import json


@dataclass
class PipelineInput:
    """
    Dataclass for the input to the pipeline.
    """

    json_path: str = None
    config: Config = None
    source_url: str = None
    sample_points: np.ndarray = None
    slice_rects: np.ndarray = None
    volume_cache: VolumeCache = None
    output_file_path: str = None
    backprojected_folder_path: str = None
    config_file_path: str = None
    backprojection_offset: str = None

    def __iter__(self):
        return iter(astuple(self))

    def __getitem__(self, keys):
        return iter(getattr(self, k) for k in keys)

    def clear_entry(self, key):
        """
        Clear the entry with the given key.
        """
        setattr(self, key, None)

    def to_dict(self):
        """
        Convert the pipeline input to a dictionary.
        """
        return {
            "json_path": self.json_path,
            "config": self.config.to_dict() if self.config is not None else None,
            "source_url": self.source_url,
            "sample_points": (
                self.sample_points.tolist() if self.sample_points is not None else None
            ),
            "slice_rects": (
                self.slice_rects.tolist() if self.slice_rects is not None else None
            ),
            "volume_cache": (
                self.volume_cache.to_dict() if self.volume_cache is not None else None
            ),
            "output_file_path": self.output_file_path,
            "backprojected_folder_path": self.backprojected_folder_path,
            "config_file_path": self.config_file_path,
            "backprojection_offset": self.backprojection_offset,
        }

    @staticmethod
    def from_dict(data):
        """
        Create a pipeline input from a dictionary.
        """
        json_path = data["json_path"]
        config = (
            Config.from_dict(data["config"]) if data["config"] is not None else None
        )
        source_url = data["source_url"]
        sample_points = (
            np.array(data["sample_points"])
            if data["sample_points"] is not None
            else None
        )
        slice_rects = (
            np.array(data["slice_rects"]) if data["slice_rects"] is not None else None
        )
        volume_cache = (
            VolumeCache.from_dict(data["volume_cache"])
            if data["volume_cache"] is not None
            else None
        )
        output_file_path = data["output_file_path"]
        backprojected_folder_path = data["backprojected_folder_path"]
        config_file_path = data["config_file_path"]
        backprojection_offset = data["backprojection_offset"]

        return PipelineInput(
            json_path,
            config,
            source_url,
            sample_points,
            slice_rects,
            volume_cache,
            output_file_path,
            backprojected_folder_path,
            config_file_path,
            backprojection_offset,
        )

    def copy_values_from_input(self, pipeline_input):
        """
        Copy the values from another pipeline input.
        """
        self.json_path = pipeline_input.json_path
        self.config = pipeline_input.config
        self.source_url = pipeline_input.source_url
        self.sample_points = pipeline_input.sample_points
        self.slice_rects = pipeline_input.slice_rects
        self.volume_cache = pipeline_input.volume_cache
        self.output_file_path = pipeline_input.output_file_path
        self.backprojected_folder_path = pipeline_input.backprojected_folder_path
        self.config_file_path = pipeline_input.config_file_path
        self.backprojection_offset = pipeline_input.backprojection_offset

    def to_json(self):
        """
        Convert the pipeline input to a JSON string.
        """
        return json.dumps(self.to_dict())

    def save_to_json(self, json_path):
        """
        Save the pipeline input to a JSON file.
        """
        with open(json_path, "w") as f:
            json.dump(self.to_dict(), f)

    @staticmethod
    def load_from_json(json_path):
        """
        Load the pipeline input from a JSON file.
        """
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Pipeline input file not found at {json_path}")
            return None
        except json.JSONDecodeError:
            print(f"Pipeline input file at {json_path} is not a valid JSON file")
            return None

        return PipelineInput.from_dict(data)
