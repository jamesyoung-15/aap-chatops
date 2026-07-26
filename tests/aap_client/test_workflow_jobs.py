import httpx

from aap_chatops.aap_client import get_my_workflow_jobs


async def test_get_my_workflow_jobs_returns_parsed_results(make_workflow_job_payload):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["created_by__id"] == "23"
        assert request.url.params["order_by"] == "-modified"
        assert "created__gt" in request.url.params
        return httpx.Response(
            200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [make_workflow_job_payload()],
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    result = await get_my_workflow_jobs(client, "https://aap.example.com/api", 23)

    assert result is not None
    assert result.count == 1
    assert result.results[0].name == "(TEST) flow/james_playground"
    assert result.results[0].status == "running"


async def test_get_my_workflow_jobs_returns_empty_results(make_workflow_job_payload):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"count": 0, "next": None, "previous": None, "results": []}
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    result = await get_my_workflow_jobs(client, "https://aap.example.com/api", 23)

    assert result is not None
    assert result.count == 0
    assert result.results == []


async def test_get_my_workflow_jobs_returns_none_on_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    result = await get_my_workflow_jobs(client, "https://aap.example.com/api", 23)

    assert result is None


async def test_get_my_workflow_jobs_returns_none_on_unexpected_shape():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": "shape"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    result = await get_my_workflow_jobs(client, "https://aap.example.com/api", 23)

    assert result is None
