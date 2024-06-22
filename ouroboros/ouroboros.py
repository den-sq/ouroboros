from .config import Config
from .pipeline import Pipeline, ParseJSONPipelineStep, RenderSlicesPipelineStep, SlicesGeometryPipelineStep, VolumeCachePipelineStep, SaveTiffPipelineStep

from .bounding_boxes import BoundingBoxParams

SLICE_WIDTH = 50
SLICE_HEIGHT = 50

def spline_demo():
    bounding_box_params = BoundingBoxParams(min_slices_per_box=30, max_depth=4)

    config = Config(SLICE_WIDTH, SLICE_HEIGHT, output_file_path="./data/sample.tif", bouding_box_params=bounding_box_params, dist_between_slices=5)

    pipeline = Pipeline([
        ParseJSONPipelineStep(),
        RenderSlicesPipelineStep()
    ])

    input_data = (config, "./data/sample-data.json")

    pipeline.process(input_data)

def slice_demo():
    config = Config(SLICE_WIDTH, SLICE_HEIGHT, output_file_path="./data/sample.tif")

    pipeline = Pipeline([
        ParseJSONPipelineStep(),
        SlicesGeometryPipelineStep(),
        VolumeCachePipelineStep(),
        SaveTiffPipelineStep()
    ])

    input_data = (config, "./data/sample-data.json")

    pipeline.process(input_data)

    print(pipeline.get_step_statistics())