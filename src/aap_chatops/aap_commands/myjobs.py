"""!myjobs command: lists workflow jobs the calling AAP user has run today."""

import httpx

from aap_chatops.aap_client import get_my_workflow_jobs
from aap_chatops.commands import CommandContext, command
from aap_chatops.formatting import format_count_reply
from aap_chatops.models.workflow_job import WorkflowJob
from aap_chatops.settings import Settings


def register(client: httpx.AsyncClient, settings: Settings) -> None:
    """Register the !myjobs command, binding the shared client/settings into the handler."""

    @command("myjobs", description="List workflow jobs you've run today")
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

        lines = [
            _format_workflow_job(job, settings.aap_base_url) for job in jobs.results
        ]
        return format_count_reply(jobs.count, "workflow job(s) run today", lines)


def _format_workflow_job(job: WorkflowJob, aap_base_url: str) -> str:
    """Render a single workflow job as a bulleted Slack message line."""
    return f"- #{job.id} {job.name} - {job.status} - {_workflow_job_ui_url(aap_base_url, job.id)}"


def _workflow_job_ui_url(aap_base_url: str, job_id: int) -> str:
    """AAP UI link for a workflow job. No guarantee this will work in future versions of AAP."""
    return f"https://{aap_base_url}/execution/jobs/workflow/{job_id}/output"
