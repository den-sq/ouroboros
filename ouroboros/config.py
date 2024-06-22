from dataclasses import dataclass

from ouroboros.bounding_boxes import BoundingBoxParams

@dataclass
class Config:
    slice_width: int
    slice_height: int
    output_file_path: str
    dist_between_slices: int = 1
    source_url: str = ""
    flush_cache: bool = False
    bouding_box_params: BoundingBoxParams = BoundingBoxParams()