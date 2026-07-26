"""Rest API client for interacting with the AAP API"""

import httpx


async def get_request(
    httpx_client: httpx.AsyncClient, aap_api_url: str
) -> httpx.Response | None:
    """GET url, returning the response on success or None on any AAP/network failure."""

    try:
        response = await httpx_client.get(aap_api_url)
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
