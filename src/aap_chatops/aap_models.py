"""Pydantic models representing AAP API response shapes."""

from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowJobSummary(BaseModel):
    """Subset of `summary_fields.workflow_job` on a workflow approval."""

    id: int
    name: str


class WorkflowApprovalSummaryFields(BaseModel):
    """Subset of `summary_fields` on a workflow approval we care about."""

    workflow_job: WorkflowJobSummary | None = None


class WorkflowApproval(BaseModel):
    """A single item from the `/workflow_approvals/` list endpoint."""

    id: int
    name: str
    status: str
    created: datetime
    approval_expiration: datetime | None = None
    can_approve_or_deny: bool
    timed_out: bool
    summary_fields: WorkflowApprovalSummaryFields = Field(
        default_factory=WorkflowApprovalSummaryFields
    )

    @property
    def workflow_name(self) -> str | None:
        """Name of the workflow job this approval node belongs to, if known."""
        workflow_job = self.summary_fields.workflow_job
        return workflow_job.name if workflow_job else None


class WorkflowApprovalListResponse(BaseModel):
    """The paginated envelope returned by the `/workflow_approvals/` list endpoint."""

    count: int
    next: str | None = None
    previous: str | None = None
    results: list[WorkflowApproval]
