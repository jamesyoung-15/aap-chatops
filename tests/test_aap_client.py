import httpx

from aap_chatops import aap_client
from aap_chatops.aap_client import (
    get_pending_workflow_approvals,
    get_request,
    ping_aap_api,
)


async def test_get_request_success():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    assert await get_request(client, "https://aap.example.com/api") is not None


async def test_get_request_returns_none_on_http_status_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    assert await get_request(client, "https://aap.example.com/api") is None


async def test_get_request_returns_none_on_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    assert await get_request(client, "https://aap.example.com/api") is None


async def test_get_request_returns_none_on_request_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed", request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    assert await get_request(client, "https://aap.example.com/api") is None


async def test_ping_aap_api_returns_true_when_reachable(monkeypatch):
    async def fake_get_request(client: httpx.AsyncClient, url: str) -> httpx.Response:
        return httpx.Response(200)

    monkeypatch.setattr(aap_client, "get_request", fake_get_request)
    client = httpx.AsyncClient()
    assert await ping_aap_api(client, "https://aap.example.com/api") is True


async def test_ping_aap_api_returns_false_when_unreachable(monkeypatch):
    async def fake_get_request(client: httpx.AsyncClient, url: str) -> None:
        return None

    monkeypatch.setattr(aap_client, "get_request", fake_get_request)
    client = httpx.AsyncClient()
    assert await ping_aap_api(client, "https://aap.example.com/api") is False


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


async def test_get_pending_workflow_approvals_returns_parsed_results():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["status"] == "pending"
        assert request.url.params["order_by"] == "-modified"
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
    result = await get_pending_workflow_approvals(client, "https://aap.example.com/api")

    assert result is not None
    assert result.count == 1
    assert result.results[0].name == "test"
    assert result.results[0].workflow_name == "(TEST) flow/james_playground"


async def test_get_pending_workflow_approvals_returns_none_on_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    result = await get_pending_workflow_approvals(client, "https://aap.example.com/api")

    assert result is None


async def test_get_pending_workflow_approvals_returns_none_on_unexpected_shape():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": "shape"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    result = await get_pending_workflow_approvals(client, "https://aap.example.com/api")

    assert result is None
