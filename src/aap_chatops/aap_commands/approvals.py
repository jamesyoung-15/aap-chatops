"""!approvals command: lists pending workflow approvals."""

from datetime import UTC, datetime

import httpx

from aap_chatops.aap_client import get_pending_workflow_approvals
from aap_chatops.aap_commands.shared import format_count_reply
from aap_chatops.commands import CommandContext, command
from aap_chatops.models.workflow_approval import WorkflowApproval
from aap_chatops.settings import Settings


def register(client: httpx.AsyncClient, settings: Settings) -> None:
    """Register the !approvals command, binding the shared client/settings into the handler."""

    @command("approvals")
    async def handle_approvals(ctx: CommandContext) -> str:
        approvals = await get_pending_workflow_approvals(client, settings.aap_api_url)
        if approvals is None:
            return "Could not reach AAP"
        if not approvals.results:
            return "No pending workflow approvals"

        lines = [_format_approval(approval) for approval in approvals.results]
        return format_count_reply(
            approvals.count, "pending workflow approval(s)", lines
        )


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
