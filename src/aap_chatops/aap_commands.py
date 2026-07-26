"""AAP-backed chat commands: registers `commands.py` triggers backed by `aap_client` calls."""

from datetime import UTC, datetime

import httpx

from aap_chatops.aap_client import get_pending_workflow_approvals, ping_aap_api
from aap_chatops.aap_models import WorkflowApproval
from aap_chatops.commands import CommandContext, command
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

        lines = [f"{approvals.count} pending workflow approval(s):"]
        lines.extend(_format_approval(approval) for approval in approvals.results)
        return "\n".join(lines)


def _format_approval(approval: WorkflowApproval) -> str:
    """Render a single workflow approval as a bulleted Slack message line."""
    workflow = approval.workflow_name or "unknown workflow"
    expiration = _format_expiration(approval.approval_expiration)
    return f"\u2022 [{workflow}] {approval.name} \u2014 {expiration}"


def _format_expiration(expires_at: datetime | None) -> str:
    """Render an approval's expiration as a human-friendly relative time."""
    if expires_at is None:
        return "no timeout"

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
