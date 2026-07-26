import pytest

from aap_chatops import commands
from aap_chatops.slack_adapter import handle_trigger_message


@pytest.fixture(autouse=True)
def _clear_registry():
    commands._commands.clear()
    yield
    commands._commands.clear()


def test_handle_trigger_message_dispatches_registered_command():
    @commands.command("ping")
    def handle_ping(ctx):
        return f"pong to {ctx.user_id}"

    reply = handle_trigger_message("!ping", user_id="U1", channel_id="C1")
    assert reply == "pong to U1"


def test_handle_trigger_message_returns_none_for_non_trigger_text():
    assert handle_trigger_message("hello there", user_id="U1", channel_id="C1") is None


def test_handle_trigger_message_returns_none_for_unknown_command():
    assert handle_trigger_message("!nope", user_id="U1", channel_id="C1") is None
