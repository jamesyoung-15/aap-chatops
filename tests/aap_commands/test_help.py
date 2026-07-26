import httpx

from aap_chatops.aap_commands import register_aap_commands
from aap_chatops.commands import CommandContext, dispatch


async def test_help_command_lists_all_registered_commands(make_settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    register_aap_commands(client, make_settings())

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!help")
    reply = await dispatch("help", ctx)

    assert "!ping - Check if AAP is reachable" in reply
    assert "!approvals - List pending workflow approvals" in reply
    assert "!myjobs - List workflow jobs you've run today" in reply
    assert "!help - Show available commands" in reply


async def test_help_command_lists_commands_alphabetically(make_settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    register_aap_commands(client, make_settings())

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!help")
    reply = await dispatch("help", ctx)

    names_in_order = [
        line.split(" ")[0] for line in reply.splitlines() if line.startswith("!")
    ]
    assert names_in_order == sorted(names_in_order)
