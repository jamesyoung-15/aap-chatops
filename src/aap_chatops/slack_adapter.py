"""Slack Socket Mode adapter: connects incoming Slack messages to the command registry."""

import re

import truststore

# Some environments (uv-managed Python's bundled cert path, corporate TLS-inspecting proxies
# like Zscaler) leave the default SSL trust store broken or incomplete. This makes the ssl
# module verify against the OS-native trust store instead, so it must run before slack_bolt
# (or anything else that opens an HTTPS/websocket connection) is imported.
truststore.inject_into_ssl()

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from aap_chatops.commands import CommandContext, dispatch, parse_trigger
from aap_chatops.settings import Settings


def handle_trigger_message(text: str, user_id: str, channel_id: str) -> str | None:
    """Parse a Slack message and return the reply text, or None if there's nothing to send."""
    keyword = parse_trigger(text)
    if keyword is None:
        return None
    ctx = CommandContext(user_id=user_id, channel_id=channel_id, raw_text=text)
    return dispatch(keyword, ctx)


def build_app(settings: Settings) -> App:
    """Construct the Bolt app and register the trigger-message listener."""
    app = App(token=settings.slack_bot_token)

    @app.message(re.compile(r"^!"))
    def on_trigger_message(message, say):
        reply = handle_trigger_message(
            text=message["text"],
            user_id=message["user"],
            channel_id=message["channel"],
        )
        if reply is not None:
            say(reply)

    return app


def start(settings: Settings | None = None) -> None:
    """Connect over Socket Mode and block until interrupted, then disconnect cleanly."""
    settings = settings or Settings()
    app = build_app(settings)
    handler = SocketModeHandler(app, settings.slack_app_token)
    try:
        handler.start()
    finally:
        handler.close()


if __name__ == "__main__":
    start()
