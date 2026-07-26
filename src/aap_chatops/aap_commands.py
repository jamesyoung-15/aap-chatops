"""AAP-backed chat commands: registers `commands.py` triggers backed by `aap_client` calls."""

import httpx

from aap_chatops.aap_client import ping_aap_api
from aap_chatops.commands import CommandContext, command
from aap_chatops.settings import Settings


def register_aap_commands(client: httpx.AsyncClient, settings: Settings) -> None:
    """Register AAP-backed commands, binding the shared client/settings into each handler."""

    @command("ping")
    async def handle_ping(ctx: CommandContext) -> str:
        reachable = await ping_aap_api(client, settings.aap_api_url)
        return "AAP is reachable" if reachable else "AAP is not reachable"
