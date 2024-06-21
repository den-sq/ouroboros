from dataclasses import dataclass

@dataclass
class Config:
    slice_width: int
    slice_height: int
    output_file_path: str
    dist_between_slices: int = 1
    source_url: str = ""