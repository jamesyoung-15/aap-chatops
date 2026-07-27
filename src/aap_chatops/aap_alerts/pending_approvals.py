"""pending_approvals alert: summarises pending workflow approvals on a schedule."""

import httpx

from aap_chatops.aap_client import get_pending_workflow_approvals
from aap_chatops.alerts import alert_task
from aap_chatops.formatting import format_pending_approvals
from aap_chatops.settings import Settings


def register(client: httpx.AsyncClient, settings: Settings) -> None:
    """Register the pending approvals alert, binding the shared client/settings into it."""

    @alert_task(
        "pending_approvals", description="Summary of pending workflow approvals"
    )
    async def pending_approvals() -> str:
        approvals = await get_pending_workflow_approvals(client, settings.aap_api_url)
        # Alerts are unsolicited, so an unreachable AAP is reported rather than passed
        # over in silence, which would read as "nothing pending".
        if approvals is None:
            return "Could not reach AAP"
        if not approvals.results:
            return "No pending workflow approvals"

        return format_pending_approvals(approvals)
