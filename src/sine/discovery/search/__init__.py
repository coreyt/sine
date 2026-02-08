"""Web search infrastructure for pattern discovery.

This module provides web search capabilities with:
- Source credibility scoring
- Result caching
- Rate limiting

Public API:
    Search Client:
        - WebSearchClient: Main search interface
        - SearchQuery: Search query specification
        - SearchResult: Search result with credibility score

    Credibility:
        - SourceCredibilityScorer: Domain credibility scoring

    Caching (to be implemented):
        - SearchCache: TTL-based result caching
"""

from sine.discovery.search.credibility import SourceCredibilityScorer
from sine.discovery.search.web_search import (
    SearchQuery,
    SearchResult,
    WebSearchClient,
)

__all__ = [
    # Web search
    "WebSearchClient",
    "SearchQuery",
    "SearchResult",
    # Credibility
    "SourceCredibilityScorer",
    # Caching - to be implemented
    # "SearchCache",
]
