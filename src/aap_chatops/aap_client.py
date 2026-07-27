"""Rest API client for interacting with the AAP API"""

import logging
from datetime import UTC, datetime

import httpx
from pydantic import ValidationError

from aap_chatops.models.aap_user import AAPUser
from aap_chatops.models.base import AapListResponse
from aap_chatops.models.workflow_approval import WorkflowApproval
from aap_chatops.models.workflow_job import WorkflowJob

logger = logging.getLogger(__name__)


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
        logger.warning(
            "Error response %s while requesting %r.",
            exc.response.status_code,
            exc.request.url,
        )
        return None
    except httpx.TimeoutException:
        logger.warning("Request to %s timed out.", aap_api_url)
        return None
    except httpx.RequestError as exc:
        logger.warning("An error occurred while requesting %r.", exc.request.url)
        return None


async def get_aap_user_info(
    httpx_client: httpx.AsyncClient, aap_api_url: str
) -> AAPUser | None:
    """Fetch the current user's info from the AAP API."""
    response = await get_request(httpx_client, f"{aap_api_url}/me/")
    if response is None:
        return None

    try:
        results = AapListResponse[AAPUser].model_validate(response.json()).results
    except ValueError as exc:
        logger.error("Unexpected response shape from /me/ endpoint: %s", exc)
        return None

    if not results:
        logger.error(
            "Unexpected response shape from /me/ endpoint: no results returned"
        )
        return None

    return results[0]


async def ping_aap_api(httpx_client: httpx.AsyncClient, aap_api_url: str) -> bool:
    """Ping an AAP API endpoint to check if it's reachable"""

    return await get_request(httpx_client, aap_api_url) is not None


async def get_pending_workflow_approvals(
    httpx_client: httpx.AsyncClient, aap_api_url: str
) -> AapListResponse[WorkflowApproval] | None:
    """Fetch the first page of pending workflow approvals, most recently modified first."""

    response = await get_request(
        httpx_client,
        f"{aap_api_url}/workflow_approvals/",
        params={"order_by": "-modified", "status": "pending"},
    )
    if response is None:
        return None

    try:
        return AapListResponse[WorkflowApproval].model_validate(response.json())
    except ValidationError as exc:
        logger.error(
            "Unexpected response shape from workflow_approvals endpoint: %s", exc
        )
        return None


async def get_my_workflow_jobs(
    httpx_client: httpx.AsyncClient, aap_api_url: str, user_id: int
) -> AapListResponse[WorkflowJob] | None:
    """Fetch the first page of today's workflow jobs created by `user_id`."""

    start_of_today = datetime.now(UTC).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    response = await get_request(
        httpx_client,
        f"{aap_api_url}/workflow_jobs/",
        params={
            "order_by": "-modified",
            "created_by__id": str(user_id),
            "created__gt": start_of_today.isoformat(),
        },
    )
    if response is None:
        return None

    try:
        return AapListResponse[WorkflowJob].model_validate(response.json())
    except ValidationError as exc:
        logger.error("Unexpected response shape from workflow_jobs endpoint: %s", exc)
        return None
