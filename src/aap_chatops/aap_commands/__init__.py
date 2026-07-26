"""AAP-backed chat commands: registers `commands.py` triggers backed by `aap_client` calls."""

import httpx

from aap_chatops.aap_commands import approvals, myjobs, ping
from aap_chatops.settings import Settings


def register_aap_commands(client: httpx.AsyncClient, settings: Settings) -> None:
    """Register all AAP-backed commands, binding the shared client/settings into each handler."""
    ping.register(client, settings)
    approvals.register(client, settings)
    myjobs.register(client, settings)
