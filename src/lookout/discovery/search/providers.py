"""Search provider protocol and base exceptions."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


class SearchProviderError(Exception):
    """Base exception for search provider errors."""


@runtime_checkable
class SearchProvider(Protocol):
    """Protocol for pluggable search backends.

    Implementations must provide:
    - execute_search: Run a query and return raw results
    - close: Release resources (HTTP clients, etc.)
    """

    async def execute_search(
        self,
        query: str,
        *,
        max_results: int = 10,
        allowed_domains: list[str] | None = None,
    ) -> list[dict[str, str]]:
        """Execute a search query.

        Args:
            query: Search query string
            max_results: Maximum results to return
            allowed_domains: Optional domain allowlist

        Returns:
            List of dicts with keys: url, title, snippet
        """
        ...

    async def close(self) -> None:
        """Release provider resources."""
        ...
