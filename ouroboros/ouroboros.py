from ouroboros.pipeline.load_config_pipeline import LoadConfigPipelineStep
from ouroboros.pipeline.pipeline_input import PipelineInput
from ouroboros.pipeline.save_config_pipeline import SaveConfigPipelineStep
from .config import Config
from .pipeline import (
    Pipeline,
    ParseJSONPipelineStep,
    RenderSlicesPipelineStep,
    SlicesGeometryPipelineStep,
    VolumeCachePipelineStep,
    SaveParallelPipelineStep,
    BackprojectPipelineStep,
)

from .helpers.bounding_boxes import BoundingBoxParams
from .pipeline import (
    Pipeline,
    ParseJSONPipelineStep,
    RenderSlicesPipelineStep,
    SlicesGeometryPipelineStep,
    VolumeCachePipelineStep,
    SaveParallelPipelineStep,
    BackprojectPipelineStep,
)

SLICE_WIDTH = 120
SLICE_HEIGHT = 120


def spline_demo():
    bounding_box_params = BoundingBoxParams(min_slices_per_box=30, max_depth=4)

    config = Config(
        SLICE_WIDTH,
        SLICE_HEIGHT,
        output_file_folder="./data",
        output_file_name="sample",
        bouding_box_params=bounding_box_params,
        dist_between_slices=5,
    )

    pipeline = Pipeline([ParseJSONPipelineStep(), RenderSlicesPipelineStep()])

    input_data = PipelineInput(config=config, json_path="./data/sample-data.json")

    pipeline.process(input_data)


def slice_demo():
    config = Config(
        SLICE_WIDTH,
        SLICE_HEIGHT,
        output_file_folder="./data",
        output_file_name="sample",
        backproject_min_bounding_box=True,
    )

    pipeline = Pipeline(
        [
            ParseJSONPipelineStep(),
            SlicesGeometryPipelineStep(),
            VolumeCachePipelineStep(),
            SaveParallelPipelineStep().with_progress_bar(),
            SaveConfigPipelineStep(),
        ]
    )

    input_data = PipelineInput(config=config, json_path="./data/sample-data.json")

    output, error = pipeline.process(input_data)
    config_file_path = output.config_file_path

    if error:
        print(error)

    print(f"Output file: {config.output_file_path}")

    print("Pipeline statistics:")

    for stat in pipeline.get_step_statistics():
        print(stat)

    # Create a second pipeline to load in the configuration and backproject
    pipeline = Pipeline(
        [
            LoadConfigPipelineStep(),
            BackprojectPipelineStep().with_progress_bar(),
            SaveConfigPipelineStep(),
        ]
    )

    output, error = pipeline.process(PipelineInput(config_file_path=config_file_path))

    print("Pipeline statistics:")

    for stat in pipeline.get_step_statistics():
        print(stat)
