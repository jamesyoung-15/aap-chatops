"""Slack Socket Mode adapter: connects incoming Slack messages to the command registry."""

import asyncio
import re
from dataclasses import dataclass

import truststore

# Some environments (uv-managed Python's bundled cert path, corporate TLS-inspecting proxies
# like Zscaler) leave the default SSL trust store broken or incomplete. This makes the ssl
# module verify against the OS-native trust store instead, so it must run before slack_bolt
# (or anything else that opens an HTTPS/websocket connection) is imported.
truststore.inject_into_ssl()

from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp

from aap_chatops.commands import CommandContext, dispatch, parse_trigger
from aap_chatops.settings import Settings


async def handle_trigger_message(
    text: str, user_id: str, channel_id: str
) -> str | None:
    """Parse a Slack message and return the reply text, or None if there's nothing to send."""
    keyword = parse_trigger(text)
    if keyword is None:
        return None
    ctx = CommandContext(user_id=user_id, channel_id=channel_id, raw_text=text)
    return await dispatch(keyword, ctx)


def build_app(settings: Settings) -> AsyncApp:
    """Construct the Bolt app and register the trigger-message listener."""
    app = AsyncApp(token=settings.slack_bot_token)

    @app.message(re.compile(r"^!"))
    async def on_trigger_message(message, say):
        reply = await handle_trigger_message(
            text=message["text"],
            user_id=message["user"],
            channel_id=message["channel"],
        )
        if reply is not None:
            await say(reply)

    return app


@dataclass
class SlackRuntime:
    """Owns the Bolt app so callers can both serve Socket Mode and post unprompted."""

    app: AsyncApp
    handler: AsyncSocketModeHandler

    async def serve(self) -> None:
        """Connect over Socket Mode and block until interrupted, then disconnect cleanly."""
        try:
            await self.handler.start_async()
        finally:
            await self.handler.close_async()

    async def post_message(self, channel_id: str, text: str) -> None:
        """Post to `channel_id`. Raises on failure: the caller owns the failure policy."""
        await self.app.client.chat_postMessage(channel=channel_id, text=text)


def build_slack_runtime(settings: Settings) -> SlackRuntime:
    """Build the Bolt app and its Socket Mode handler without connecting yet."""
    app = build_app(settings)
    return SlackRuntime(
        app=app, handler=AsyncSocketModeHandler(app, settings.slack_app_token)
    )


async def start_slack(settings: Settings | None = None) -> None:
    """Serve Socket Mode with no scheduler alongside it."""
    await build_slack_runtime(settings or Settings()).serve()


if __name__ == "__main__":
    asyncio.run(start_slack())
