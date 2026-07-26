import httpx

from aap_chatops import aap_client
from aap_chatops.aap_client import get_request, ping_aap_api


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
