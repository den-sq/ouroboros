from ouroboros.bounding_boxes import calculate_bounding_boxes_bsp_link_rects
from ouroboros.volume_cache import VolumeCache
from .pipeline import PipelineStep
from ouroboros.config import Config
import numpy as np

class VolumeCachePipelineStep(PipelineStep):
    def _process(self, input_data: any) -> tuple[any, None] | tuple[None, any]:
        config, slice_rects = input_data

        # Verify that a config object is provided
        if not isinstance(config, Config):
            return None, "Input data must contain a Config object."

        # Verify that slice rects is given
        if not isinstance(slice_rects, np.ndarray):
            return None, "Input data must contain an array of slice rects."
        
        bounding_boxes, link_rects = calculate_bounding_boxes_bsp_link_rects(slice_rects, 
                                                                             min_slices_per_box=config.bouding_box_params.min_slices_per_box,
                                                                             max_depth=config.bouding_box_params.max_depth)
        
        volume_cache = VolumeCache(bounding_boxes, link_rects, config.source_url)

        return (config, volume_cache, slice_rects), None