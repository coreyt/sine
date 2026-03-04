"""Google Custom Search JSON API provider."""

from __future__ import annotations

import logging

import httpx

from lookout.discovery.search.providers import SearchProviderError

logger = logging.getLogger(__name__)

GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"


class GoogleSearchProvider:
    """Search provider backed by Google Custom Search JSON API.

    Requires a Google API key and a Custom Search Engine (CSE) ID.
    Free tier: 100 queries/day.

    Sign up:
      1. https://console.cloud.google.com/ — enable Custom Search JSON API
      2. https://programmablesearchengine.google.com/ — create a CSE

    Args:
        api_key: Google API key
        cse_id: Custom Search Engine ID
        timeout: HTTP request timeout in seconds
    """

    def __init__(self, api_key: str, cse_id: str, timeout: float = 15.0) -> None:
        self._api_key = api_key
        self._cse_id = cse_id
        self._client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)

    async def execute_search(
        self,
        query: str,
        *,
        max_results: int = 10,
        allowed_domains: list[str] | None = None,
    ) -> list[dict[str, str]]:
        """Execute a search via Google Custom Search API.

        Args:
            query: Search query string
            max_results: Maximum results to return (API max per request is 10)
            allowed_domains: Optional domain allowlist (uses siteSearch param)

        Returns:
            List of dicts with keys: url, title, snippet

        Raises:
            SearchProviderError: On HTTP or network errors
        """
        params: dict[str, str] = {
            "key": self._api_key,
            "cx": self._cse_id,
            "q": query,
            "num": str(min(max_results, 10)),  # Google API max is 10 per request
        }

        if allowed_domains:
            # siteSearch only supports one domain; for multiple, use OR in query
            if len(allowed_domains) == 1:
                params["siteSearch"] = allowed_domains[0]
            else:
                site_filter = " OR ".join(f"site:{d}" for d in allowed_domains)
                params["q"] = f"{query} ({site_filter})"
                params["siteSearch"] = allowed_domains[0]

        try:
            response = await self._client.get(
                GOOGLE_SEARCH_URL,
                params=params,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise SearchProviderError(
                f"Google Search returned HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise SearchProviderError(f"Google Search request failed: {exc}") from exc

        data = response.json()
        raw_items = data.get("items", [])

        results: list[dict[str, str]] = []
        for item in raw_items:
            url = item.get("link", "")
            if allowed_domains and not any(d in url for d in allowed_domains):
                continue
            results.append(
                {
                    "url": url,
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                }
            )
            if len(results) >= max_results:
                break

        return results

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
