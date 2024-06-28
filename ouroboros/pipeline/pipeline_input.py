from dataclasses import astuple, dataclass
import numpy as np
from ouroboros.config import Config
from ouroboros.helpers.volume_cache import VolumeCache
import json

@dataclass
class PipelineInput:
    """
    Dataclass for the input to the pipeline.
    """
    json_path: str = None
    config: Config = None
    sample_points: np.ndarray = None
    slice_rects: np.ndarray = None
    volume_cache: VolumeCache = None
    output_file_path: str = None
    backprojected_folder_path: str = None

    def __iter__(self):
        return iter(astuple(self))
    
    def __getitem__(self, keys):
        return iter(getattr(self, k) for k in keys)
    
    def to_dict(self):
        """
        Convert the pipeline input to a dictionary.
        """
        return {
            "json_path": self.json_path,
            "config": self.config.to_dict(),
            "sample_points": self.sample_points.tolist(),
            "slice_rects": self.slice_rects.tolist(),
            "volume_cache": self.volume_cache.to_dict(),
            "output_file_path": self.output_file_path,
            "backprojected_folder_path": self.backprojected_folder_path
        }
    
    @staticmethod
    def from_dict(data):
        """
        Create a pipeline input from a dictionary.
        """
        json_path = data["json_path"]
        config = Config.from_dict(data["config"])
        sample_points = np.array(data["sample_points"])
        slice_rects = np.array(data["slice_rects"])
        volume_cache = VolumeCache.from_dict(data["volume_cache"])
        output_file_path = data["output_file_path"]
        backprojected_folder_path = data["backprojected_folder_path"]
        
        return PipelineInput(json_path, config, sample_points, slice_rects, volume_cache, output_file_path, backprojected_folder_path)
    
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
        with open(json_path, "r") as f:
            data = json.load(f)
        return PipelineInput.from_dict(data)
