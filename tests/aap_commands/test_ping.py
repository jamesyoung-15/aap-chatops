import httpx

from aap_chatops.aap_commands import register_aap_commands
from aap_chatops.commands import CommandContext, dispatch


async def test_ping_command_reachable(make_settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    register_aap_commands(client, make_settings())

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!ping")
    assert await dispatch("ping", ctx) == "AAP is reachable"


async def test_ping_command_unreachable(make_settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    register_aap_commands(client, make_settings())

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!ping")
    assert await dispatch("ping", ctx) == "AAP is not reachable"
