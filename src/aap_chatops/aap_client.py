"""Rest API client for interacting with the AAP API"""

import httpx
from pydantic import ValidationError

from aap_chatops.aap_models import WorkflowApprovalListResponse


async def get_request(
    httpx_client: httpx.AsyncClient,
    aap_api_url: str,
    params: dict[str, str] | None = None,
) -> httpx.Response | None:
    """GET url, returning the response on success or None on any AAP/network failure."""

    try:
        response = await httpx_client.get(aap_api_url, params=params)
        response.raise_for_status()
        return response
    except httpx.HTTPStatusError as exc:
        print(
            f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
        )
        return None
    except httpx.TimeoutException:
        print(f"Request to {aap_api_url} timed out.")
        return None
    except httpx.RequestError as exc:
        print(f"An error occurred while requesting {exc.request.url!r}.")
        return None


async def ping_aap_api(httpx_client: httpx.AsyncClient, aap_api_url: str) -> bool:
    """Ping an AAP API endpoint to check if it's reachable"""

    return await get_request(httpx_client, aap_api_url) is not None


async def get_pending_workflow_approvals(
    httpx_client: httpx.AsyncClient, aap_api_url: str
) -> WorkflowApprovalListResponse | None:
    """Fetch the first page of pending workflow approvals, most recently modified first."""

    response = await get_request(
        httpx_client,
        f"{aap_api_url}/workflow_approvals/",
        params={"order_by": "-modified", "status": "pending"},
    )
    if response is None:
        return None

    try:
        return WorkflowApprovalListResponse.model_validate(response.json())
    except ValidationError as exc:
        print(f"Unexpected response shape from workflow_approvals endpoint: {exc}")
        return None
