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


def _make_approval_payload(**overrides) -> dict:
    payload = {
        "id": 70459,
        "name": "test",
        "status": "pending",
        "created": "2026-07-26T03:52:14.842717Z",
        "approval_expiration": None,
        "can_approve_or_deny": True,
        "timed_out": False,
        "summary_fields": {
            "workflow_job": {"id": 70458, "name": "(TEST) flow/james_playground"}
        },
    }
    payload.update(overrides)
    return payload


async def test_approvals_command_lists_pending_approvals():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [_make_approval_payload()],
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    register_aap_commands(client, _make_settings())

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!approvals")
    reply = await dispatch("approvals", ctx)

    assert reply is not None
    assert "1 pending workflow approval(s):" in reply
    assert "- (TEST) flow/james_playground" in reply


async def test_approvals_command_reports_no_pending_approvals():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"count": 0, "next": None, "previous": None, "results": []}
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    register_aap_commands(client, _make_settings())

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!approvals")
    assert await dispatch("approvals", ctx) == "No pending workflow approvals"


async def test_approvals_command_reports_unreachable_aap():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    register_aap_commands(client, _make_settings())

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!approvals")
    assert await dispatch("approvals", ctx) == "Could not reach AAP"
