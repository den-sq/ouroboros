from .pipeline import PipelineStep
from .pipeline_input import PipelineInput

class LoadConfigPipelineStep(PipelineStep):
    def __init__(self) -> None:
        super().__init__(inputs=("config_file_path",))

    def _process(self, input_data: tuple[any]) -> None | str:
        config_file_path, currrent_pipeline_input = input_data

        pipeline_input = PipelineInput.load_from_json(config_file_path)
        currrent_pipeline_input.copy_values_from_input(pipeline_input)
        
        return None