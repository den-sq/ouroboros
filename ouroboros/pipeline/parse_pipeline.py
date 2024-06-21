from ouroboros.parse import parse_neuroglancer_json, neuroglancer_config_to_annotation, neuroglancer_config_to_source
from .pipeline import PipelineStep
from ouroboros.config import Config

# TODO: Consider making an abstract parse step
class ParseJSONPipelineStep(PipelineStep):
    def _process(self, input_data: any) -> tuple[any, None] | tuple[None, any]:
        config, json_path = input_data

        # Verify that a config object is provided
        if not isinstance(config, Config):
            return None, "Input data must contain a Config object."

        # Verify that input_data is a string containing a path to a JSON file
        if not isinstance(json_path, str):
            return None, "Input data must contain a string containing a path to a JSON file."

        ng_config, error = parse_neuroglancer_json(json_path)

        if error:
            return None, error
        
        sample_points, error = neuroglancer_config_to_annotation(ng_config)

        if error:
            return None, error
        
        source_url, error = neuroglancer_config_to_source(ng_config)

        if error:
            return None, error
        
        # Store the source url in config for later use
        config.source_url = source_url
        
        return (config, sample_points), None