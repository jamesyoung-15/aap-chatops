import httpx

from aap_chatops.aap_client import get_pending_workflow_approvals


async def test_get_pending_workflow_approvals_returns_parsed_results(
    make_approval_payload,
):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["status"] == "pending"
        assert request.url.params["order_by"] == "-modified"
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


async def test_get_pending_workflow_approvals_parses_created_by(make_approval_payload):
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
    result = await get_pending_workflow_approvals(client, "https://aap.example.com/api")

    assert result is not None
    assert result.results[0].created_by_username == "YoungJamesY"


async def test_get_pending_workflow_approvals_handles_missing_created_by(
    make_approval_payload,
):
    def handler(request: httpx.Request) -> httpx.Response:
        payload = make_approval_payload()
        del payload["summary_fields"]["created_by"]
        return httpx.Response(
            200,
            json={"count": 1, "next": None, "previous": None, "results": [payload]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    result = await get_pending_workflow_approvals(client, "https://aap.example.com/api")

    assert result is not None
    assert result.results[0].created_by_username is None
