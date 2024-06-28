from ouroboros.helpers.parse import parse_neuroglancer_json, neuroglancer_config_to_annotation, neuroglancer_config_to_source
from .pipeline import PipelineStep
from ouroboros.config import Config

# TODO: Consider making an abstract parse step
class ParseJSONPipelineStep(PipelineStep):
    def __init__(self) -> None:
        super().__init__(inputs=("config", "json_path"))

    def _process(self, input_data: tuple[any]) -> None | str:
        config, json_path, pipeline_input = input_data

        # Verify that a config object is provided
        if not isinstance(config, Config):
            return "Input data must contain a Config object."

        # Verify that input_data is a string containing a path to a JSON file
        if not isinstance(json_path, str):
            return "Input data must contain a string containing a path to a JSON file."

        ng_config, error = parse_neuroglancer_json(json_path)

        self.update_progress(0.5)

        if error:
            return error
        
        sample_points, error = neuroglancer_config_to_annotation(ng_config)

        if error:
            return error
        
        source_url, error = neuroglancer_config_to_source(ng_config)

        if error:
            return error
        
        # Store the source url in config for later use
        config.source_url = source_url

        # Update the pipeline input with the sample points
        pipeline_input.sample_points = sample_points
        
        return None