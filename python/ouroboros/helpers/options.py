from dataclasses import dataclass

import os

from ouroboros.helpers.bounding_boxes import BoundingBoxParams
from ouroboros.helpers.dataclasses import dataclass_with_json

# Still need to detect color based on channels and other data


@dataclass(kw_only=True)
class CommonOptions:
    slice_width: int  # Width of the slice
    slice_height: int  # Height of the slice
    output_file_folder: str  # Folder to save the output file
    output_file_name: str  # Name of the output file
    dist_between_slices: int = 1  # Distance between slices
    flush_cache: bool = False  # Whether to flush the cache after processing
    connect_start_and_end: bool = (
        False  # Whether to connect the start and end of the given annotation points
    )
    make_single_file: bool = True  # Whether to save the output to a single file
    max_ram_gb: int = 0  # Maximum amount of RAM to use in GB (0 means no limit)

    @property
    def output_file_path(self):
        return os.path.join(self.output_file_folder, self.output_file_name + ".tif")


@dataclass_with_json
@dataclass(kw_only=True)
class SliceOptions(CommonOptions):
    bounding_box_params: BoundingBoxParams = (
        BoundingBoxParams()
    )  # Parameters for generating bounding boxes


@dataclass_with_json
@dataclass(kw_only=True)
class BackprojectOptions(CommonOptions):
    backproject_min_bounding_box: bool = (
        True  # Whether to backproject to a minimum bounding box or the entire volume
    )
    make_backprojection_binary: bool = (
        False  # Whether to make the backprojection binary (values of 0 or 1)
    )
    backprojection_compression: str = (
        "zstd"  # Compression type for the backprojected file
    )
