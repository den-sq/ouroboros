from .config import Config
from .pipeline import (
    Pipeline,
    PipelineInput,
    ParseJSONPipelineStep,
    SlicesGeometryPipelineStep,
    VolumeCachePipelineStep,
    SaveParallelPipelineStep,
    BackprojectPipelineStep,
    SaveConfigPipelineStep,
    LoadConfigPipelineStep,
)

SLICE_WIDTH = 120
SLICE_HEIGHT = 120


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

    if error:
        print(error)

    config_file_path = output.config_file_path

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
