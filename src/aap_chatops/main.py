"""Entrypoint: wires up dependencies, registers commands, and starts the configured chat adapter."""

import asyncio

import httpx

from aap_chatops.aap_commands import register_aap_commands
from aap_chatops.settings import Settings
from aap_chatops.slack_adapter import start_slack


async def main() -> None:
    """Entry point that initializes settings and runs program"""
    settings = Settings()

    async with httpx.AsyncClient(
        headers=settings.aap_api_headers, follow_redirects=True
    ) as client:
        register_aap_commands(client, settings)

        match settings.chat_platform:
            case "slack":
                await start_slack(settings)
            case _:
                raise NotImplementedError(
                    f"Unsupported chat_platform: {settings.chat_platform!r}"
                )


if __name__ == "__main__":
    asyncio.run(main())
