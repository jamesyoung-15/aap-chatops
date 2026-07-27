"""Entrypoint: wires up dependencies, registers commands and alerts, and starts the bot."""

import asyncio

import httpx

from aap_chatops.aap_alerts import register_aap_alert_tasks
from aap_chatops.aap_client import get_aap_user_info
from aap_chatops.aap_commands import register_aap_commands
from aap_chatops.alert_config import ScheduledAlert, load_alert_config, resolve_alerts
from aap_chatops.logging_config import configure_logging
from aap_chatops.scheduler import run_alerts
from aap_chatops.settings import Settings
from aap_chatops.slack_adapter import SlackRuntime, build_slack_runtime

# An AAP request with no ceiling would stall the shared event loop, which would also
# stall the Socket Mode heartbeat and drop the chat connection.
AAP_TIMEOUT_SECONDS = 30.0


async def main() -> None:
    """Entry point that initializes settings and runs program"""
    settings = Settings()
    configure_logging(settings)

    async with httpx.AsyncClient(
        headers=settings.aap_api_headers,
        follow_redirects=True,
        timeout=AAP_TIMEOUT_SECONDS,
    ) as client:
        user = await get_aap_user_info(client, settings.aap_api_url)
        if user is None:
            raise RuntimeError("Failed to fetch current AAP user from /me/ endpoint")
        settings.aap_user = user

        register_aap_commands(client, settings)
        register_aap_alert_tasks(client, settings)

        # Resolve before connecting, so a bad alerts.yaml fails at boot rather than
        # at the moment an alert was due to fire.
        alerts = _resolve_enabled_alerts(settings)

        match settings.chat_platform:
            case "slack":
                runtime: SlackRuntime = build_slack_runtime(settings)
            case _:
                raise NotImplementedError(
                    f"Unsupported chat_platform: {settings.chat_platform!r}"
                )

        # With nothing to schedule, run the listener directly. A TaskGroup would wrap
        # any failure in an ExceptionGroup and bury the actual error.
        if not alerts:
            await runtime.serve()
            return

        async with asyncio.TaskGroup() as task_group:
            task_group.create_task(runtime.serve(), name="chat-listener")
            task_group.create_task(
                run_alerts(alerts, runtime.post_message), name="alert-scheduler"
            )


def _resolve_enabled_alerts(settings: Settings) -> list[ScheduledAlert]:
    """Alert schedules from config, or none when alerts are switched off."""
    if not settings.alerts_enabled:
        return []
    return resolve_alerts(
        load_alert_config(settings.alerts_config_path),
        default_channel_id=settings.default_alert_channel_id,
        default_timezone=settings.alert_timezone,
    )


if __name__ == "__main__":
    asyncio.run(main())
