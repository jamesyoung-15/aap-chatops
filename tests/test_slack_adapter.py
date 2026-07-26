from aap_chatops import commands
from aap_chatops.slack_adapter import handle_trigger_message


async def test_handle_trigger_message_dispatches_registered_command():
    @commands.command("ping")
    async def handle_ping(ctx):
        return f"pong to {ctx.user_id}"

    reply = await handle_trigger_message("!ping", user_id="U1", channel_id="C1")
    assert reply == "pong to U1"


async def test_handle_trigger_message_returns_none_for_non_trigger_text():
    assert (
        await handle_trigger_message("hello there", user_id="U1", channel_id="C1")
        is None
    )


async def test_handle_trigger_message_returns_fallback_for_unknown_command():
    reply = await handle_trigger_message("!nope", user_id="U1", channel_id="C1")
    assert reply == "Unknown command: !nope. Try !help for a list of commands."
