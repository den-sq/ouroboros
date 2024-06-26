from dataclasses import dataclass

import os

from ouroboros.helpers.bounding_boxes import BoundingBoxParams

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