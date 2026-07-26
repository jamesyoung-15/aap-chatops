"""!help command: lists all registered commands and their descriptions."""

import httpx

from aap_chatops.commands import CommandContext, command, list_commands
from aap_chatops.settings import Settings


def register(client: httpx.AsyncClient, settings: Settings) -> None:
    """Register the !help command."""

    @command("help", description="Show available commands")
    async def handle_help(ctx: CommandContext) -> str:
        lines = [
            f"!{info.name} - {info.description or 'No description available'}"
            for info in list_commands()
        ]
        return "Available commands:\n\n" + "\n".join(lines)
