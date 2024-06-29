from .pipeline import PipelineStep

import os


class SaveConfigPipelineStep(PipelineStep):
    def __init__(self) -> None:
        super().__init__(inputs=("config",))

    def _process(self, input_data: tuple[any]) -> None | str:
        config, currrent_pipeline_input = input_data

        # Determine the name of the file to save to
        json_path = os.path.join(
            config.output_file_folder, config.output_file_name + "-configuration.json"
        )

        currrent_pipeline_input.config_file_path = json_path
        currrent_pipeline_input.save_to_json(json_path)

        return None
