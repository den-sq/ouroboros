from ouroboros.common.file_system import (
    load_options_for_backproject,
    load_options_for_backproject_docker,
    load_options_for_slice,
    load_options_for_slice_docker,
    save_output_for_backproject_docker,
    save_output_for_slice_docker,
)
from ouroboros.common.logging import logger
from ouroboros.common.pipelines import backproject_pipeline, slice_pipeline
from ouroboros.common.server_types import BackProjectTask, SliceTask, Task


def handle_slice_core(task: SliceTask, slice_options):
    pipeline, input_data = slice_pipeline(slice_options)

    # Store the pipeline in the task
    task.pipeline = pipeline

    # Store the input data in the task
    task.pipeline_input = input_data

    task.status = "started"

    _, error = pipeline.process(input_data)

    if error:
        return error

    # Log the pipeline statistics
    logger.info("Slice Pipeline Statistics:")
    logger.info(pipeline.get_step_statistics())


def handle_slice(task: SliceTask):
    slice_options = load_options_for_slice(task.options)

    slice_result = handle_slice_core(task, slice_options)

    if isinstance(slice_result, str):
        task.error = slice_result
        task.status = "error"
        return


def handle_slice_docker(task: SliceTask):
    load_result = load_options_for_slice_docker(task.options)

    if isinstance(load_result, str):
        task.error = load_result
        task.status = "error"
        return

    slice_options, host_output_file, host_output_config_file, host_output_slices = (
        load_result
    )

    slice_result = handle_slice_core(task, slice_options)

    if isinstance(slice_result, str):
        task.error = slice_result
        task.status = "error"
        return

    save_result = save_output_for_slice_docker(
        host_output_file, host_output_config_file, host_output_slices=host_output_slices
    )

    if save_result:
        task.error = save_result
        task.status = "error"


def handle_backproject_core(task: BackProjectTask, options):
    pipeline, input_data = backproject_pipeline(options)

    # Store the pipeline in the task
    task.pipeline = pipeline

    # Store the input data in the task
    task.pipeline_input = input_data

    task.status = "started"

    _, error = pipeline.process(input_data)

    if error:
        return error

    # Log the pipeline statistics
    logger.info("Backproject Pipeline Statistics:")
    logger.info(pipeline.get_step_statistics())


def handle_backproject(task: BackProjectTask):
    options = load_options_for_backproject(task.options)

    backproject_result = handle_backproject_core(task, options)

    if isinstance(backproject_result, str):
        task.error = backproject_result
        task.status = "error"
        return


def handle_backproject_docker(task: BackProjectTask):
    load_result = load_options_for_backproject_docker(task.options)

    if isinstance(load_result, str):
        task.error = load_result
        task.status = "error"
        return

    options, host_output_file, host_output_config_file, host_output_slices = load_result

    backproject_result = handle_backproject_core(task, options)

    if isinstance(backproject_result, str):
        task.error = backproject_result
        task.status = "error"
        return

    save_result = save_output_for_backproject_docker(
        host_output_file, host_output_config_file, host_output_slices=host_output_slices
    )

    if save_result:
        task.error = save_result
        task.status = "error"


def handle_task(task: Task):
    """
    Handle a server task.

    Parameters
    ----------
    task : Task
        The task to handle.
    """

    try:
        if isinstance(task, SliceTask):
            handle_slice(task)
        elif isinstance(task, BackProjectTask):
            handle_backproject(task)
        else:
            raise ValueError("Invalid task type")
    except BaseException as e:
        task.status = "error"
        task.error = str(e)


def handle_task_docker(task: Task):
    """
    Handle a server task in a docker environment.

    Parameters
    ----------
    task : Task
        The task to handle.
    """

    try:
        if isinstance(task, SliceTask):
            handle_slice_docker(task)
        elif isinstance(task, BackProjectTask):
            handle_backproject_docker(task)
        else:
            raise ValueError("Invalid task type")
    except BaseException as e:
        task.status = "error"
        task.error = str(e)
