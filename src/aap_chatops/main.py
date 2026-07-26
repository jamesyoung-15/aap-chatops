"""Entrypoint: wires up dependencies, registers commands, and starts the configured chat adapter."""

import asyncio

import httpx

from aap_chatops.aap_client import get_aap_user_info
from aap_chatops.aap_commands import register_aap_commands
from aap_chatops.logging_config import configure_logging
from aap_chatops.settings import Settings
from aap_chatops.slack_adapter import start_slack


async def main() -> None:
    """Entry point that initializes settings and runs program"""
    settings = Settings()
    configure_logging(settings)

    async with httpx.AsyncClient(
        headers=settings.aap_api_headers, follow_redirects=True
    ) as client:
        user = await get_aap_user_info(client, settings.aap_api_url)
        if user is None:
            raise RuntimeError("Failed to fetch current AAP user from /me/ endpoint")
        settings.aap_user = user

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
