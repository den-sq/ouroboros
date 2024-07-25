from multiprocessing import freeze_support

from fastapi import Request
from sse_starlette.sse import EventSourceResponse
from fastapi.responses import JSONResponse
import asyncio
import uvicorn
import uuid
import json

from ouroboros.common.server import (
    DOCKER_HOST,
    DOCKER_PORT,
    BackProjectTask,
    SliceTask,
    create_server,
)

app = create_server(docker=True)

tasks = {}


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
    uvicorn.run(app, host=DOCKER_HOST, port=DOCKER_PORT)


if __name__ == "__main__":
    # Necessary to run multiprocessing in child processes
    freeze_support()

    main()
