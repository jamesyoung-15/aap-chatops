import httpx

from aap_chatops.aap_client import get_aap_user_info


async def test_get_aap_user_info_returns_parsed_user(make_aap_user_payload):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [make_aap_user_payload()],
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    result = await get_aap_user_info(client, "https://aap.example.com/api")

    assert result is not None
    assert result.id == 23
    assert result.username == "YoungJamesY"


async def test_get_aap_user_info_returns_none_on_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    result = await get_aap_user_info(client, "https://aap.example.com/api")

    assert result is None


async def test_get_aap_user_info_returns_none_on_unexpected_shape():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"count": 0, "results": []})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    result = await get_aap_user_info(client, "https://aap.example.com/api")

    assert result is None
