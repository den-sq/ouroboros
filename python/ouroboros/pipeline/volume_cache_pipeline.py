from ouroboros.helpers.bounding_boxes import calculate_bounding_boxes_bsp_link_rects
from ouroboros.helpers.volume_cache import VolumeCache
from .pipeline import PipelineStep
from ouroboros.helpers.config import Config
import numpy as np


class VolumeCachePipelineStep(PipelineStep):
    def __init__(self) -> None:
        super().__init__(inputs=("config", "slice_rects", "source_url"))

    def _process(self, input_data: tuple[any]) -> None | str:
        config, slice_rects, source_url, pipeline_input = input_data

        # Verify that a config object is provided
        if not isinstance(config, Config):
            return "Input data must contain a Config object."

        # Verify that slice rects is given
        if not isinstance(slice_rects, np.ndarray):
            return "Input data must contain an array of slice rects."

        bounding_boxes, link_rects = calculate_bounding_boxes_bsp_link_rects(
            slice_rects,
            target_slices_per_box=config.bounding_box_params.target_slices_per_box,
            max_depth=config.bounding_box_params.max_depth,
        )

        self.update_progress(0.5)

        volume_cache = VolumeCache(
            bounding_boxes,
            link_rects,
            source_url,
            flush_cache=config.flush_cache,
        )

        # Update the pipeline input with the volume cache
        pipeline_input.volume_cache = volume_cache

        return None
