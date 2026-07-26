"""!ping command: checks whether the AAP API is reachable."""

import httpx

from aap_chatops.aap_client import ping_aap_api
from aap_chatops.commands import CommandContext, command
from aap_chatops.settings import Settings


def register(client: httpx.AsyncClient, settings: Settings) -> None:
    """Register the !ping command, binding the shared client/settings into the handler."""

    @command("ping")
    async def handle_ping(ctx: CommandContext) -> str:
        reachable = await ping_aap_api(client, settings.aap_api_url)
        return "AAP is reachable" if reachable else "AAP is not reachable"
