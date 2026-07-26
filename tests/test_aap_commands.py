import httpx
import pytest

from aap_chatops import commands
from aap_chatops.aap_commands import register_aap_commands
from aap_chatops.commands import CommandContext, dispatch
from aap_chatops.settings import Settings


@pytest.fixture(autouse=True)
def _clear_registry():
    commands._commands.clear()
    yield
    commands._commands.clear()


def _make_settings() -> Settings:
    # _env_file=None to avoid using local .env
    return Settings(
        _env_file=None,  # pyright: ignore[reportCallIssue]
        aap_base_url="aap.example.com",
        aap_api_token="test-token",
        slack_bot_token="xoxb-test",
        slack_app_token="xapp-test",
    )


async def test_ping_command_reachable():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    register_aap_commands(client, _make_settings())

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!ping")
    assert await dispatch("ping", ctx) == "AAP is reachable"


async def test_ping_command_unreachable():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    register_aap_commands(client, _make_settings())

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!ping")
    assert await dispatch("ping", ctx) == "AAP is not reachable"
