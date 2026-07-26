"""Rest API client for interacting with the AAP API"""

import httpx


async def ping_aap_api(httpx_client: httpx.AsyncClient, aap_api_url: str) -> bool:
    """Ping an AAP API endpoint to check if it's reachable"""
    try:
        response = await httpx_client.get(aap_api_url)
        response.raise_for_status()
        return True
    except httpx.HTTPStatusError as exc:
        print(
            f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
        )
        return False
    except httpx.TimeoutException:
        print(f"Request to {aap_api_url} timed out.")
        return False
    except httpx.RequestError as exc:
        print(f"An error occurred while requesting {exc.request.url!r}.")
        return False
