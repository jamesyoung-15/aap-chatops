"""AAP-backed scheduled alerts: registers `alerts.py` tasks backed by `aap_client` calls."""

import httpx

from aap_chatops.aap_alerts import pending_approvals
from aap_chatops.settings import Settings


def register_aap_alert_tasks(client: httpx.AsyncClient, settings: Settings) -> None:
    """Register all AAP-backed alert tasks, binding the shared client/settings into each."""
    pending_approvals.register(client, settings)
