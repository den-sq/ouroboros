from .pipeline import PipelineStep
from .pipeline_input import PipelineInput


class LoadConfigPipelineStep(PipelineStep):
    def __init__(self) -> None:
        super().__init__(inputs=("config_file_path",))

        self.custom_output_file_path = None

    def with_custom_output_file_path(self, path: str):
        self.custom_output_file_path = path
        return self

    def _process(self, input_data: tuple[any]) -> None | str:
        config_file_path, currrent_pipeline_input = input_data

        pipeline_input = PipelineInput.load_from_json(config_file_path)
        currrent_pipeline_input.copy_values_from_input(pipeline_input)

        if self.custom_output_file_path is not None:
            currrent_pipeline_input.output_file_path = self.custom_output_file_path

        return None
