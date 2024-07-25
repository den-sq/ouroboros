from dataclasses import dataclass, field
from ouroboros.pipeline import PipelineInput, Pipeline


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
