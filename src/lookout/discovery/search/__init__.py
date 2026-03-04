"""Web search infrastructure for pattern discovery.

This module provides web search capabilities with:
- Pluggable search providers (Brave, Google, DuckDuckGo)
- Source credibility scoring
- Result caching
- Rate limiting

Public API:
    Search Client:
        - WebSearchClient: Main search interface
        - SearchQuery: Search query specification
        - SearchResult: Search result with credibility score

    Providers:
        - SearchProvider: Protocol for search backends
        - SearchProviderError: Base exception for provider errors
        - BraveSearchProvider: Brave Search API backend
        - GoogleSearchProvider: Google Custom Search API backend
        - DuckDuckGoSearchProvider: DuckDuckGo HTML backend (free, no key)

    Credibility:
        - SourceCredibilityScorer: Domain credibility scoring
"""

from lookout.discovery.search.brave import BraveSearchProvider
from lookout.discovery.search.credibility import SourceCredibilityScorer
from lookout.discovery.search.duckduckgo import DuckDuckGoSearchProvider
from lookout.discovery.search.google import GoogleSearchProvider
from lookout.discovery.search.providers import SearchProvider, SearchProviderError
from lookout.discovery.search.web_search import (
    SearchQuery,
    SearchResult,
    WebSearchClient,
)

__all__ = [
    # Web search
    "WebSearchClient",
    "SearchQuery",
    "SearchResult",
    # Providers
    "SearchProvider",
    "SearchProviderError",
    "BraveSearchProvider",
    "GoogleSearchProvider",
    "DuckDuckGoSearchProvider",
    # Credibility
    "SourceCredibilityScorer",
]
