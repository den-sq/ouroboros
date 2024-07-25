from concurrent.futures import Executor, ThreadPoolExecutor
from dataclasses import dataclass, field
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from ouroboros.common.file_system import (
    load_options_for_backproject,
    load_options_for_backproject_docker,
    load_options_for_slice,
    load_options_for_slice_docker,
    save_output_for_backproject_docker,
    save_output_for_slice_docker,
)
from ouroboros.common.pipelines import backproject_pipeline, slice_pipeline
from ouroboros.pipeline import PipelineInput, Pipeline


HOST = "127.0.0.1"
PORT = 8000

DOCKER_HOST = "0.0.0.0"
DOCKER_PORT = 8000


# Note: kw_only=True is used to make the fields keyword-only,
# which is required for the parent dataclass to have default values
@dataclass(kw_only=True)
class Task:
    task_id: str
    pipeline_input: PipelineInput = None
    pipeline: Pipeline = None
    last_progress: list[tuple[str, float]] = field(default_factory=list)
    status: str = "enqueued"
    error: str = None


@dataclass(kw_only=True)
class SliceTask(Task):
    options: str


@dataclass(kw_only=True)
class BackProjectTask(Task):
    options: str


####### SERVER #######


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

    slice_options, host_output_file, host_output_config_file = load_result

    slice_result = handle_slice_core(task, slice_options)

    if isinstance(slice_result, str):
        task.error = slice_result
        task.status = "error"
        return

    save_result = save_output_for_slice_docker(
        host_output_file, host_output_config_file
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

    options, host_output_file, host_output_config_file = load_result

    backproject_result = handle_backproject_core(task, options)

    if isinstance(backproject_result, str):
        task.error = backproject_result
        task.status = "error"
        return

    save_result = save_output_for_backproject_docker(
        host_output_file, host_output_config_file
    )

    if save_result:
        task.error = save_result
        task.status = "error"


def handle_task(task: Task):
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


def create_server(docker=False):
    task_handler = handle_task_docker if docker else handle_task

    async def process_requests(queue: asyncio.Queue, pool: Executor):
        while True:
            task = await queue.get()
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(pool, task_handler, task)
            queue.task_done()
            if task.status != "error":
                task.status = "done"

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        queue = asyncio.Queue()  # note that asyncio.Queue() is not thread safe
        pool = ThreadPoolExecutor()
        asyncio.create_task(process_requests(queue, pool))
        yield {"queue": queue, "pool": pool}
        pool.shutdown()

    app = FastAPI(lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
