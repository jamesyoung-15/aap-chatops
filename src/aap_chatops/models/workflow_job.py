"""Models for the AAP `/workflow_jobs/` endpoint."""

from datetime import datetime

from pydantic import BaseModel


class WorkflowJob(BaseModel):
    """A single item from the `/workflow_jobs/` list endpoint."""

    id: int
    name: str
    status: str
    created: datetime
    started: datetime | None = None
    finished: datetime | None = None
    elapsed: float
