from concurrent.futures import Executor, ThreadPoolExecutor
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from ouroboros.common.server_handlers import handle_task, handle_task_docker


HOST = "127.0.0.1"
PORT = 8000

DOCKER_HOST = "0.0.0.0"
DOCKER_PORT = 8000


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
