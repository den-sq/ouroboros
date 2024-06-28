from dataclasses import dataclass

import os
import stat

from ouroboros.helpers.bounding_boxes import BoundingBoxParams

# TODO: Add all the necessary fields to the Config class

@dataclass
class Config:
    slice_width: int
    slice_height: int
    output_file_folder: str
    output_file_name: str
    dist_between_slices: int = 1
    source_url: str = ""
    flush_cache: bool = False
    bouding_box_params: BoundingBoxParams = BoundingBoxParams()

    @property
    def output_file_path(self):
        return os.path.join(self.output_file_folder, self.output_file_name + ".tif")
    
    def to_dict(self):
        """
        Convert the configuration to a dictionary.
        """
        return {
            "slice_width": self.slice_width,
            "slice_height": self.slice_height,
            "output_file_folder": self.output_file_folder,
            "output_file_name": self.output_file_name,
            "dist_between_slices": self.dist_between_slices,
            "source_url": self.source_url,
            "flush_cache": self.flush_cache,
            "bouding_box_params": self.bouding_box_params.to_dict()
        }
    
    @staticmethod
    def from_dict(data):
        """
        Create a configuration from a dictionary.
        """
        slice_width = data["slice_width"]
        slice_height = data["slice_height"]
        output_file_folder = data["output_file_folder"]
        output_file_name = data["output_file_name"]
        dist_between_slices = data.get("dist_between_slices", 1)
        source_url = data.get("source_url", "")
        flush_cache = data.get("flush_cache", False)
        bouding_box_params = BoundingBoxParams.from_dict(data["bouding_box_params"])

        return Config(slice_width, slice_height, output_file_folder, output_file_name, dist_between_slices, source_url, flush_cache, bouding_box_params)