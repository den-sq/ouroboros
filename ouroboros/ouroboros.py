from .config import Config
from .pipeline import Pipeline, ParseJSONPipelineStep, RenderSlicesPipelineStep, SlicesGeometryPipelineStep, VolumeCachePipelineStep, SaveTiffPipelineStep

SLICE_WIDTH = 50
SLICE_HEIGHT = 50

def spline_demo():
    config = Config(SLICE_WIDTH, SLICE_HEIGHT, output_file_path="./data/sample.tif")

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