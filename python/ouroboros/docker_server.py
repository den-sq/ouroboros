import json
from multiprocessing import freeze_support

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from concurrent.futures import Executor, ThreadPoolExecutor
import asyncio
import uvicorn
import uuid

from ouroboros.helpers.options import BackprojectOptions, SliceOptions
from ouroboros.pipeline import (
    BackprojectPipelineStep,
    LoadConfigPipelineStep,
    ParseJSONPipelineStep,
    Pipeline,
    PipelineInput,
    SaveConfigPipelineStep,
    SliceParallelPipelineStep,
    SlicesGeometryPipelineStep,
    VolumeCachePipelineStep,
)

HOST = "0.0.0.0"
PORT = 8000


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


def handle_slice(task: SliceTask):
    options_path = task.options

    slice_options = SliceOptions.load_from_json(options_path)

    pipeline = Pipeline(
        [
            ParseJSONPipelineStep(),
            SlicesGeometryPipelineStep(),
            VolumeCachePipelineStep(),
            SliceParallelPipelineStep(),
            SaveConfigPipelineStep(),
        ]
    )

    # Store the pipeline in the task
    task.pipeline = pipeline

    input_data = PipelineInput(
        slice_options=slice_options, json_path=slice_options.neuroglancer_json
    )

    # Store the input data in the task
    task.pipeline_input = input_data

    task.status = "started"

    _, error = pipeline.process(input_data)

    if error:
        task.error = error
        task.status = "error"


def handle_backproject(task: BackProjectTask):
    options_path = task.options

    options = BackprojectOptions.load_from_json(options_path)

    pipeline = Pipeline(
        [
            LoadConfigPipelineStep()
            .with_custom_output_file_path(options.straightened_volume_path)
            .with_custom_options(options),
            BackprojectPipelineStep(),
            SaveConfigPipelineStep(),
        ]
    )

    # Store the pipeline in the task
    task.pipeline = pipeline

    input_data = PipelineInput(config_file_path=options.config_path)

    # Store the input data in the task
    task.pipeline_input = input_data

    task.status = "started"

    _, error = pipeline.process(input_data)

    if error:
        task.error = error
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


async def process_requests(queue: asyncio.Queue, pool: Executor):
    while True:
        task = await queue.get()
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(pool, handle_task, task)
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


tasks = {}
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def server_active():
    return JSONResponse("Server is active")


@app.post("/slice/")
async def add_slice_task(options: str, request: Request):
    task_id = str(uuid.uuid4())
    task = SliceTask(task_id=task_id, options=options)
    tasks[task_id] = task
    request.state.queue.put_nowait(task)  # Add request to the queue
    return {"task_id": task_id}


@app.get("/slice_visualization/")
async def get_slice_visualization(task_id: str):
    result = {
        "data": None,
        "error": None,
    }

    if task_id in tasks:
        task = tasks[task_id]
        if task.status == "done":
            data = {
                "rects": task.pipeline_input.slice_rects.tolist(),
                "bounding_boxes": [
                    {
                        "min": [bbox.x_min, bbox.y_min, bbox.z_min],
                        "max": [bbox.x_max, bbox.y_max, bbox.z_max],
                    }
                    for bbox in task.pipeline_input.volume_cache.bounding_boxes
                ],
                "link_rects": task.pipeline_input.volume_cache.link_rects,
            }
            result["data"] = data

            return JSONResponse(result, status_code=200)
        else:
            result["error"] = "Task is not done."
            return JSONResponse(result, status_code=400)
    else:
        result["error"] = "Item ID Not Found"
        return JSONResponse(result, status_code=404)


@app.post("/backproject/")
async def add_backproject_task(
    request: Request,
    options: str,
):
    task_id = str(uuid.uuid4())
    task = BackProjectTask(
        task_id=task_id,
        options=options,
    )
    tasks[task_id] = task
    request.state.queue.put_nowait(task)  # Add request to the queue
    return {"task_id": task_id}


def get_status(task_id: str):
    if task_id in tasks:
        task = tasks[task_id]
        if task.status == "started" or task.status == "done":
            try:
                task.last_progress = tasks[task_id].pipeline.get_steps_progress()
            except BaseException as e:
                task.status = "error"
                task.error = f"Error occurred while getting progress details: {str(e)}."
                task.last_progress = []
        return {
            "status": task.status,
            "progress": task.last_progress,
            "error": task.error,
        }
    else:
        return {
            "status": "error",
            "progress": [],
            "error": "Item ID Not Found",
        }


@app.get("/status/{task_id}")
async def check_status(task_id: str):
    result = get_status(task_id)

    if result["error"] == "Item ID Not Found":
        return JSONResponse(result, status_code=404)
    elif result["error"]:
        return JSONResponse(result, status_code=500)
    else:
        return JSONResponse(result, status_code=200)


@app.get("/slice_status_stream/")
async def slice_status_stream(request: Request, task_id: str, update_freq: int = 1000):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break

            result = get_status(task_id)

            event = ""

            match result["status"]:
                case "error":
                    event = "error_event"
                case "done":
                    event = "done_event"
                case _:
                    event = "update_event"

            yield {
                "event": event,
                "id": task_id,
                "retry": update_freq,
                "data": json.dumps(result),
            }

            if event == "done":
                break

            await asyncio.sleep(update_freq / 1000.0)

    return EventSourceResponse(event_generator())


@app.get("/backproject_status_stream/")
async def backproject_status_stream(
    request: Request, task_id: str, update_freq: int = 2000
):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break

            result = get_status(task_id)

            event = ""

            match result["status"]:
                case "error":
                    event = "error_event"
                case "done":
                    event = "done_event"
                case _:
                    event = "update_event"

            yield {
                "event": event,
                "id": task_id,
                "retry": update_freq,
                "data": json.dumps(result),
            }

            if event == "done":
                break

            await asyncio.sleep(update_freq / 1000.0)

    return EventSourceResponse(event_generator())


@app.post("/delete/")
async def delete_task(task_id: str):
    if task_id in tasks:
        del tasks[task_id]
        return JSONResponse({"success": True}, status_code=200)
    else:
        return JSONResponse({"success": False}, status_code=404)


def main():
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    # Necessary to run multiprocessing in child processes
    freeze_support()

    main()
