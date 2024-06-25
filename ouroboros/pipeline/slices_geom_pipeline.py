from ouroboros.helpers.slice import calculate_slice_rects
from ouroboros.helpers.spline import Spline
from .pipeline import PipelineStep
from ouroboros.config import Config
import numpy as np

class SlicesGeometryPipelineStep(PipelineStep):
    def _process(self, input_data: any) -> tuple[any, None] | tuple[None, any]:
        config, sample_points = input_data

        # Verify that a config object is provided
        if not isinstance(config, Config):
            return None, "Input data must contain a Config object."

        # Verify that sample points is given
        if not isinstance(sample_points, np.ndarray):
            return None, "Input data must contain an array of sample points."
        
        spline = Spline(sample_points, degree=3)

        # Plot equidistant points along the spline
        equidistant_params = spline.calculate_equidistant_parameters(config.dist_between_slices)
        equidistant_points = spline(equidistant_params)

        self.update_progress(0.5)

        # Calculate the slice rects for each t value
        slice_rects = calculate_slice_rects(equidistant_params, spline, config.slice_width, config.slice_height, spline_points=equidistant_points)

        return (config, slice_rects), None