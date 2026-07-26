"""Models for the AAP `/workflow_approvals/` endpoint."""

from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowJobSummary(BaseModel):
    """Subset of `summary_fields.workflow_job` on a workflow approval."""

    id: int
    name: str


class WorkflowCreatedBySummary(BaseModel):
    """Subset of `summary_fields.created_by` on a workflow approval."""

    id: int
    username: str
    first_name: str | None = None
    last_name: str | None = None


class WorkflowApprovalSummaryFields(BaseModel):
    """Subset of `summary_fields` on a workflow approval we care about."""

    workflow_job: WorkflowJobSummary | None = None
    created_by: WorkflowCreatedBySummary | None = None


class WorkflowApprovalRelated(BaseModel):
    """
    Subset of `related` on a workflow approval we care about.
    These give the subpaths to the API endpoints.
    """

    source_workflow_job: str | None = None
    approve: str | None = None
    deny: str | None = None


class WorkflowApproval(BaseModel):
    """A single item from the `/workflow_approvals/` list endpoint."""

    id: int
    name: str
    status: str
    created: datetime
    approval_expiration: datetime | None = None
    can_approve_or_deny: bool
    timed_out: bool
    url: str | None = None
    summary_fields: WorkflowApprovalSummaryFields = Field(
        default_factory=WorkflowApprovalSummaryFields
    )
    related: WorkflowApprovalRelated = Field(default_factory=WorkflowApprovalRelated)

    @property
    def workflow_name(self) -> str | None:
        """Name of the workflow job this approval node belongs to, if known."""
        workflow_job = self.summary_fields.workflow_job  # pylint: disable=no-member
        return workflow_job.name if workflow_job else None

    @property
    def created_by_username(self) -> str | None:
        """Username of the user who created this approval, if known."""
        created_by = self.summary_fields.created_by  # pylint: disable=no-member
        return created_by.username if created_by else None
