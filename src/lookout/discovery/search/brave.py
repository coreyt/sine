"""Brave Search API provider."""

from __future__ import annotations

import logging

import httpx

from lookout.discovery.search.providers import SearchProviderError

logger = logging.getLogger(__name__)

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


class BraveSearchProvider:
    """Search provider backed by Brave Search API.

    Free tier: 2,000 queries/month, no credit card required.
    Sign up at https://brave.com/search/api/

    Args:
        api_key: Brave Search API subscription token
        timeout: HTTP request timeout in seconds
    """

    def __init__(self, api_key: str, timeout: float = 15.0) -> None:
        self._api_key = api_key
        self._client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)

    async def execute_search(
        self,
        query: str,
        *,
        max_results: int = 10,
        allowed_domains: list[str] | None = None,
    ) -> list[dict[str, str]]:
        """Execute a search via Brave Search API.

        Args:
            query: Search query string
            max_results: Maximum results to return
            allowed_domains: Optional domain allowlist (uses site: rewriting)

        Returns:
            List of dicts with keys: url, title, snippet

        Raises:
            SearchProviderError: On HTTP or network errors
        """
        # Rewrite query with site: operators for allowed domains
        effective_query = query
        if allowed_domains:
            site_filter = " OR ".join(f"site:{d}" for d in allowed_domains)
            effective_query = f"{query} ({site_filter})"

        params = {
            "q": effective_query,
            "count": str(min(max_results, 20)),  # Brave max is 20
        }

        try:
            response = await self._client.get(
                BRAVE_SEARCH_URL,
                params=params,
                headers={"X-Subscription-Token": self._api_key},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise SearchProviderError(
                f"Brave Search returned HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise SearchProviderError(f"Brave Search request failed: {exc}") from exc

        data = response.json()
        raw_results = data.get("web", {}).get("results", [])

        results: list[dict[str, str]] = []
        for item in raw_results:
            url = item.get("url", "")
            # Post-filter by allowed domains as safety net
            if allowed_domains and not any(d in url for d in allowed_domains):
                continue
            results.append(
                {
                    "url": url,
                    "title": item.get("title", ""),
                    "snippet": item.get("description", ""),
                }
            )
            if len(results) >= max_results:
                break

        return results

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
