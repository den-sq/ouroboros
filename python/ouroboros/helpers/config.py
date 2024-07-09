from dataclasses import dataclass

import os
import json

from ouroboros.helpers.bounding_boxes import BoundingBoxParams

# TODO: Add all the necessary fields to the Config class
# compression type, output to a single file vs folder, etc.

# Still need to add compression to the thing and detect color based on channels and other data


@dataclass
class Config:
    slice_width: int  # Width of the slice
    slice_height: int  # Height of the slice
    output_file_folder: str  # Folder to save the output file
    output_file_name: str  # Name of the output file
    dist_between_slices: int = 1  # Distance between slices
    flush_cache: bool = False  # Whether to flush the cache after processing
    connect_start_and_end: bool = (
        False  # Whether to connect the start and end of the given annotation points
    )
    backproject_min_bounding_box: bool = (
        True  # Whether to backproject to a minimum bounding box or the entire volume
    )
    make_backprojection_binary: bool = (
        False  # Whether to make the backprojection binary (values of 0 or 1)
    )
    bounding_box_params: BoundingBoxParams = (
        BoundingBoxParams()
    )  # Parameters for generating bounding boxes
    backprojection_compression: str = (
        "zstd"  # Compression type for the backprojected file
    )
    make_single_file: bool = True  # Whether to save the output to a single file
    max_ram_gb: int = 0  # Maximum amount of RAM to use in GB (0 means no limit)

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
            "flush_cache": self.flush_cache,
            "connect_start_and_end": self.connect_start_and_end,
            "backproject_min_bounding_box": self.backproject_min_bounding_box,
            "make_backprojection_binary": self.make_backprojection_binary,
            "bounding_box_params": self.bounding_box_params.to_dict(),
            "backprojection_compression": self.backprojection_compression,
            "make_single_file": self.make_single_file,
            "max_ram_gb": self.max_ram_gb,
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
        flush_cache = data.get("flush_cache", False)
        connect_start_and_end = data.get("connect_start_and_end", False)
        backproject_min_bounding_box = data.get("backproject_min_bounding_box", True)
        make_backprojection_binary = data.get("make_backprojection_binary", False)
        bounding_box_params = BoundingBoxParams.from_dict(data["bounding_box_params"])
        backprojection_compression = data.get("backprojection_compression", "zstd")
        make_single_file = data.get("make_single_file", True)
        max_ram_gb = data.get("max_ram", 0)

        return Config(
            slice_width=slice_width,
            slice_height=slice_height,
            output_file_folder=output_file_folder,
            output_file_name=output_file_name,
            dist_between_slices=dist_between_slices,
            flush_cache=flush_cache,
            connect_start_and_end=connect_start_and_end,
            backproject_min_bounding_box=backproject_min_bounding_box,
            make_backprojection_binary=make_backprojection_binary,
            bounding_box_params=bounding_box_params,
            backprojection_compression=backprojection_compression,
            make_single_file=make_single_file,
            max_ram_gb=max_ram_gb,
        )

    def save_to_json(self, json_path):
        """
        Save the configuration to a JSON file.
        """
        with open(json_path, "w") as f:
            json.dump(self.to_dict(), f, indent=4)

    @staticmethod
    def from_json(json_path) -> "Config | str":
        """
        Create a configuration from a JSON file.
        """
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            return f"Config file not found at {json_path}"
        except json.JSONDecodeError:
            return f"Config file at {json_path} is not a valid JSON file"

        return Config.from_dict(data)
