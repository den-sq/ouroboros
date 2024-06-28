from ouroboros.helpers.slice import generate_coordinate_grid_for_rect, slice_volume_from_grid
from ouroboros.helpers.volume_cache import VolumeCache
from .pipeline import PipelineStep
from ouroboros.config import Config
import numpy as np

import os
from tifffile import TiffWriter

class SaveTiffPipelineStep(PipelineStep):
    def __init__(self) -> None:
        super().__init__(inputs=("config", "volume_cache", "slice_rects"))

    def _process(self, input_data: tuple[any]) -> None | str:
        config, volume_cache, slice_rects, pipeline_input = input_data

        # Verify that a config object is provided
        if not isinstance(config, Config):
            return "Input data must contain a Config object."
        
        # Verify that a volume cache is given
        if not isinstance(volume_cache, VolumeCache):
            return "Input data must contain a VolumeCache object."

        # Verify that slice rects is given
        if not isinstance(slice_rects, np.ndarray):
            return "Input data must contain an array of slice rects."
        
        file_name = os.path.join(config.output_file_folder, config.output_file_name) + ".tif"
        
        # Write the slices to a TIFF file one slice at a time
        with TiffWriter(file_name) as tif:
            for i in range(len(slice_rects)):
                if i % 10 == 0:
                    print(f"Generating slice {i}...")

                grid = generate_coordinate_grid_for_rect(slice_rects[i], config.slice_width, config.slice_height)

                volume, bounding_box = volume_cache.request_volume_for_slice(i)

                slice_i = slice_volume_from_grid(volume, bounding_box, grid, config.slice_width, config.slice_height)

                tif.write(slice_i, contiguous=True)

        # Update the pipeline input with the file name
        pipeline_input.output_file_path = file_name

        return None