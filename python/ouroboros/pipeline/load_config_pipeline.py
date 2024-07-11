from ouroboros.helpers.options import BackprojectOptions
from .pipeline import PipelineStep
from .pipeline_input import PipelineInput


class LoadConfigPipelineStep(PipelineStep):
    def __init__(self) -> None:
        super().__init__(inputs=("config_file_path",))

        self.custom_output_file_path = None
        self.custom_options = None

    def with_custom_output_file_path(self, path: str):
        self.custom_output_file_path = path
        return self

    def with_custom_options(self, options: BackprojectOptions):
        self.custom_options = options
        return self

    def _process(self, input_data: tuple[any]) -> None | str:
        config_file_path, currrent_pipeline_input = input_data

        pipeline_input = PipelineInput.load_from_json(config_file_path)
        currrent_pipeline_input.copy_values_from_other(pipeline_input)

        if self.custom_output_file_path is not None:
            currrent_pipeline_input.output_file_path = self.custom_output_file_path

        if self.custom_options is not None:
            currrent_pipeline_input.backproject_options = self.custom_options

        return None
