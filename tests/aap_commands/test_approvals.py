import httpx

from aap_chatops.aap_commands import register_aap_commands
from aap_chatops.commands import CommandContext, dispatch


async def test_approvals_command_lists_pending_approvals(
    make_settings, make_approval_payload
):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [make_approval_payload()],
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    register_aap_commands(client, make_settings())

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!approvals")
    reply = await dispatch("approvals", ctx)

    assert reply is not None
    assert "1 pending workflow approval(s):" in reply
    assert "- (TEST) flow/james_playground" in reply


async def test_approvals_command_reports_no_pending_approvals(make_settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"count": 0, "next": None, "previous": None, "results": []}
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    register_aap_commands(client, make_settings())

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!approvals")
    assert await dispatch("approvals", ctx) == "No pending workflow approvals"


async def test_approvals_command_reports_unreachable_aap(make_settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    register_aap_commands(client, make_settings())

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!approvals")
    assert await dispatch("approvals", ctx) == "Could not reach AAP"


async def test_approvals_command_includes_created_by_username(
    make_settings, make_approval_payload
):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [make_approval_payload()],
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    register_aap_commands(client, make_settings())

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!approvals")
    reply = await dispatch("approvals", ctx)

    assert reply is not None
    assert "created by YoungJamesY" in reply


async def test_approvals_command_falls_back_to_unknown_user(
    make_settings, make_approval_payload
):
    def handler(request: httpx.Request) -> httpx.Response:
        payload = make_approval_payload()
        del payload["summary_fields"]["created_by"]
        return httpx.Response(
            200,
            json={"count": 1, "next": None, "previous": None, "results": [payload]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    register_aap_commands(client, make_settings())

    ctx = CommandContext(user_id="U1", channel_id="C1", raw_text="!approvals")
    reply = await dispatch("approvals", ctx)

    assert reply is not None
    assert "created by unknown user" in reply
