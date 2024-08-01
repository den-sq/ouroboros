from ouroboros.helpers.files import join_path
from .pipeline import PipelineStep


class SaveConfigPipelineStep(PipelineStep):
    def __init__(self) -> None:
        super().__init__(
            inputs=(
                "slice_options",
                "backproject_options",
            )
        )

    def _process(self, input_data: tuple[any]) -> None | str:
        slice_options, backproject_options, currrent_pipeline_input = input_data

        config = slice_options if slice_options is not None else backproject_options

        # Determine the name of the file to save to
        json_path = join_path(
            config.output_file_folder, config.output_file_name + "-configuration.json"
        )

        currrent_pipeline_input.config_file_path = json_path
        currrent_pipeline_input.save_to_json(json_path)

        return None
