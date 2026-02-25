"""Web search integration for pattern discovery.

This module provides web search capabilities for discovering coding patterns
from online sources. It wraps search functionality with:
- Rate limiting to avoid overwhelming services
- Result caching to reduce redundant searches
- Credibility scoring to prioritize high-quality sources
- Result ranking by relevance and credibility
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sine.discovery.search.credibility import SourceCredibilityScorer

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchQuery:
    """Web search query specification.

    Attributes:
        query: Search query string
        focus_type: Type of patterns to find (architecture, security, etc.)
        max_results: Maximum number of results to return
        allowed_domains: Optional list of domains to restrict search to
    """

    query: str
    focus_type: str
    max_results: int = 10
    allowed_domains: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SearchResult:
    """Web search result with credibility score.

    Attributes:
        url: URL of the result
        title: Page title
        snippet: Text snippet/description
        credibility: Credibility score (0.0-1.0)
        rank: Original search rank (1-based)
        metadata: Additional metadata (source, timestamp, etc.)
    """

    url: str
    title: str
    snippet: str
    credibility: float
    rank: int
    metadata: dict[str, str] = field(default_factory=dict)


class WebSearchClient:
    """Client for web search with caching and credibility scoring.

    This client wraps web search functionality and enhances it with:
    - Automatic caching of results
    - Credibility scoring of sources
    - Rate limiting between requests
    - Result ranking by credibility

    Example:
        async with WebSearchClient(credibility_scorer) as client:
            query = SearchQuery(
                query="SQL injection prevention best practices",
                focus_type="security",
                max_results=10,
            )
            results = await client.search(query)
            for result in results:
                print(f"{result.title}: {result.credibility:.2f}")
    """

    def __init__(
        self,
        credibility_scorer: SourceCredibilityScorer,
        rate_limit_seconds: float = 1.0,
        cache_enabled: bool = True,
    ):
        """Initialize the web search client.

        Args:
            credibility_scorer: Scorer for evaluating source credibility
            rate_limit_seconds: Minimum seconds between requests
            cache_enabled: Whether to use result caching
        """
        self.credibility_scorer = credibility_scorer
        self.rate_limit_seconds = rate_limit_seconds
        self.cache_enabled = cache_enabled
        self._last_request_time: datetime | None = None
        self._search_cache: dict[str, list[SearchResult]] = {}

    async def __aenter__(self) -> WebSearchClient:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object
    ) -> None:
        """Async context manager exit."""
        # Cleanup if needed
        pass

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        """Execute web search and return credibility-scored results.

        Strategy:
        1. Check cache for existing results
        2. If not cached, perform search with rate limiting
        3. Score results by source credibility
        4. Rank by credibility score
        5. Cache results

        Args:
            query: Search query specification

        Returns:
            List of search results, ranked by credibility
        """
        # Check cache
        cache_key = self._make_cache_key(query)
        if self.cache_enabled and cache_key in self._search_cache:
            logger.debug(f"Cache hit for query: {query.query}")
            return self._search_cache[cache_key]

        # Apply rate limiting
        await self._apply_rate_limit()

        # Perform search (mock implementation for now)
        # In real usage, this would call the WebSearch tool
        raw_results = await self._execute_search(query)

        # Score and rank results
        scored_results = self._score_results(raw_results)

        # Cache results
        if self.cache_enabled:
            self._search_cache[cache_key] = scored_results
            logger.debug(f"Cached {len(scored_results)} results for: {query.query}")

        return scored_results

    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        if self._last_request_time is None:
            self._last_request_time = datetime.now()
            return

        elapsed = (datetime.now() - self._last_request_time).total_seconds()
        if elapsed < self.rate_limit_seconds:
            wait_time = self.rate_limit_seconds - elapsed
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        self._last_request_time = datetime.now()

    async def _execute_search(self, query: SearchQuery) -> list[dict[str, str]]:
        """Execute web search via DuckDuckGo HTML endpoint.

        Args:
            query: Search query

        Returns:
            Raw search results as list of dicts with url, title, snippet
        """
        import httpx
        from bs4 import BeautifulSoup

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.post(
                    "https://html.duckduckgo.com/html/",
                    data={"q": query.query},
                    headers={"User-Agent": "sine/0.1.0 pattern-discovery"},
                )
                response.raise_for_status()
        except httpx.RequestError as exc:
            logger.warning(f"Web search request failed: {exc}")
            return []
        except httpx.HTTPStatusError as exc:
            logger.warning(f"Web search returned {exc.response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        results: list[dict[str, str]] = []

        for element in soup.select(".web-result"):
            title_el = element.select_one(".result__title")
            url_el = element.select_one(".result__url")
            snippet_el = element.select_one(".result__snippet")
            if not (title_el and url_el):
                continue
            url = url_el.get_text(strip=True)
            # Filter by allowed domains if specified
            if query.allowed_domains and not any(domain in url for domain in query.allowed_domains):
                continue
            results.append(
                {
                    "url": url,
                    "title": title_el.get_text(strip=True),
                    "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                }
            )
            if len(results) >= query.max_results:
                break

        return results

    def _score_results(self, raw_results: list[dict[str, str]]) -> list[SearchResult]:
        """Score search results by credibility and rank them.

        Args:
            raw_results: Raw search results from web search

        Returns:
            Scored and ranked results
        """
        scored_results: list[SearchResult] = []

        for i, result in enumerate(raw_results, start=1):
            url = result.get("url", "")
            title = result.get("title", "")
            snippet = result.get("snippet", "")

            # Score credibility
            credibility = self.credibility_scorer.score_url(url)

            scored_results.append(
                SearchResult(
                    url=url,
                    title=title,
                    snippet=snippet,
                    credibility=credibility,
                    rank=i,
                    metadata={
                        "original_rank": str(i),
                        "scored_at": datetime.now().isoformat(),
                    },
                )
            )

        # Sort by credibility (descending)
        scored_results.sort(key=lambda r: r.credibility, reverse=True)

        return scored_results

    def _make_cache_key(self, query: SearchQuery) -> str:
        """Generate cache key for a query.

        Args:
            query: Search query

        Returns:
            Cache key string
        """
        # Simple key: focus_type:query
        # In real implementation, might use SHA256 hash
        return f"{query.focus_type}:{query.query}"

    def clear_cache(self) -> None:
        """Clear the search result cache."""
        self._search_cache.clear()
        logger.info("Search cache cleared")
