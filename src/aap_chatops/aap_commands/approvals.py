"""!approvals command: lists pending workflow approvals."""

import httpx

from aap_chatops.aap_client import get_pending_workflow_approvals
from aap_chatops.commands import CommandContext, command
from aap_chatops.formatting import format_pending_approvals
from aap_chatops.settings import Settings


def register(client: httpx.AsyncClient, settings: Settings) -> None:
    """Register the !approvals command, binding the shared client/settings into the handler."""

    @command("approvals", description="List pending workflow approvals")
    async def handle_approvals(ctx: CommandContext) -> str:
        approvals = await get_pending_workflow_approvals(client, settings.aap_api_url)
        if approvals is None:
            return "Could not reach AAP"
        if not approvals.results:
            return "No pending workflow approvals"

        return format_pending_approvals(approvals)
