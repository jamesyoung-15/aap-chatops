"""AAP-backed chat commands: registers `commands.py` triggers backed by `aap_client` calls."""

from datetime import UTC, datetime

import httpx

from aap_chatops.aap_client import (
    get_my_workflow_jobs,
    get_pending_workflow_approvals,
    ping_aap_api,
)
from aap_chatops.commands import CommandContext, command
from aap_chatops.models.workflow_approval import WorkflowApproval
from aap_chatops.models.workflow_job import WorkflowJob
from aap_chatops.settings import Settings


def register_aap_commands(client: httpx.AsyncClient, settings: Settings) -> None:
    """Register AAP-backed commands, binding the shared client/settings into each handler."""

    @command("ping")
    async def handle_ping(ctx: CommandContext) -> str:
        reachable = await ping_aap_api(client, settings.aap_api_url)
        return "AAP is reachable" if reachable else "AAP is not reachable"

    @command("approvals")
    async def handle_approvals(ctx: CommandContext) -> str:
        approvals = await get_pending_workflow_approvals(client, settings.aap_api_url)
        if approvals is None:
            return "Could not reach AAP"
        if not approvals.results:
            return "No pending workflow approvals"

        lines = [f"{approvals.count} pending workflow approval(s):\n"]
        lines.extend(_format_approval(approval) for approval in approvals.results)
        return "\n".join(lines)

    @command("myjobs")
    async def handle_myjobs(ctx: CommandContext) -> str:
        if settings.aap_user is None:
            return "Could not determine your AAP user"

        jobs = await get_my_workflow_jobs(
            client, settings.aap_api_url, settings.aap_user.id
        )
        if jobs is None:
            return "Could not reach AAP"
        if not jobs.results:
            return "No workflow jobs run today"

        lines = [f"{jobs.count} workflow job(s) run today:\n"]
        lines.extend(
            _format_workflow_job(job, settings.aap_base_url) for job in jobs.results
        )
        return "\n".join(lines)


def _format_approval(approval: WorkflowApproval) -> str:
    """Render a single workflow approval as a bulleted Slack message line."""
    workflow = approval.workflow_name or "unknown workflow"
    creator = approval.created_by_username or "unknown user"
    expiration = _format_expiration(approval.approval_expiration)
    if expiration is None:
        response_message = f"- {workflow} - created by {creator}"
    else:
        response_message = (
            f"- {workflow} - created by {creator} - expires: {expiration}"
        )
    return response_message


def _format_expiration(expires_at: datetime | None) -> str | None:
    """Render an approval's expiration as a human-friendly relative time."""
    if expires_at is None:
        return None

    remaining = expires_at - datetime.now(UTC)
    total_minutes = round(remaining.total_seconds() / 60)
    if total_minutes <= 0:
        return "expired"

    days, hours = divmod(total_minutes // 60, 24)
    minutes = total_minutes % 60
    if days:
        return f"expires in {days}d {hours}h"
    if hours:
        return f"expires in {hours}h {minutes}m"
    return f"expires in {minutes}m"


def _format_workflow_job(job: WorkflowJob, aap_base_url: str) -> str:
    """Render a single workflow job as a bulleted Slack message line."""
    return f"- #{job.id} {job.name} - {job.status} - {_workflow_job_ui_url(aap_base_url, job.id)}"


def _workflow_job_ui_url(aap_base_url: str, job_id: int) -> str:
    """AAP UI link for a workflow job. No guarantee this will work in future versions of AAP."""
    return f"https://{aap_base_url}/execution/jobs/workflow/{job_id}/output"
