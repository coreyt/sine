"""Unit tests for web search client."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from sine.discovery.search.credibility import SourceCredibilityScorer
from sine.discovery.search.web_search import (
    SearchQuery,
    SearchResult,
    WebSearchClient,
)


class TestSearchQuery:
    """Tests for SearchQuery dataclass."""

    def test_search_query_creation(self):
        """Test creating a search query."""
        query = SearchQuery(
            query="SQL injection prevention",
            focus_type="security",
            max_results=10,
        )

        assert query.query == "SQL injection prevention"
        assert query.focus_type == "security"
        assert query.max_results == 10
        assert query.allowed_domains == []

    def test_search_query_with_domains(self):
        """Test search query with domain restrictions."""
        query = SearchQuery(
            query="design patterns",
            focus_type="architecture",
            allowed_domains=["martinfowler.com", "refactoring.guru"],
        )

        assert len(query.allowed_domains) == 2
        assert "martinfowler.com" in query.allowed_domains

    def test_search_query_immutable(self):
        """Test that SearchQuery is immutable."""
        query = SearchQuery(query="test", focus_type="test")

        with pytest.raises(AttributeError):
            query.query = "modified"  # type: ignore


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating a search result."""
        result = SearchResult(
            url="https://example.com",
            title="Example Title",
            snippet="This is a snippet",
            credibility=0.95,
            rank=1,
        )

        assert result.url == "https://example.com"
        assert result.title == "Example Title"
        assert result.credibility == 0.95
        assert result.rank == 1

    def test_search_result_with_metadata(self):
        """Test search result with metadata."""
        result = SearchResult(
            url="https://example.com",
            title="Title",
            snippet="Snippet",
            credibility=0.8,
            rank=2,
            metadata={"source": "google", "timestamp": "2024-01-01"},
        )

        assert "source" in result.metadata
        assert result.metadata["source"] == "google"


class TestWebSearchClient:
    """Tests for WebSearchClient."""

    @pytest.fixture
    def mock_scorer(self):
        """Create a mock credibility scorer."""
        scorer = Mock(spec=SourceCredibilityScorer)
        # Default: return 0.75 for any URL
        scorer.score_url.return_value = 0.75
        return scorer

    @pytest.mark.asyncio
    async def test_search_with_mocked_results(self, mock_scorer):
        """Test basic search with mocked results."""
        async with WebSearchClient(mock_scorer, rate_limit_seconds=0.0) as client:
            # Mock the _execute_search method
            mock_results = [
                {
                    "url": "https://example.com/1",
                    "title": "Result 1",
                    "snippet": "First result",
                },
                {
                    "url": "https://example.com/2",
                    "title": "Result 2",
                    "snippet": "Second result",
                },
            ]
            client._execute_search = AsyncMock(return_value=mock_results)

            query = SearchQuery(query="test query", focus_type="test")
            results = await client.search(query)

            assert len(results) == 2
            assert all(isinstance(r, SearchResult) for r in results)
            assert results[0].title == "Result 1"

    @pytest.mark.asyncio
    async def test_results_scored_by_credibility(self, mock_scorer):
        """Test that results are scored by credibility."""

        # Configure mock to return different scores
        def score_side_effect(url):
            if "high-cred.com" in url:
                return 0.95
            elif "low-cred.com" in url:
                return 0.50
            return 0.75

        mock_scorer.score_url.side_effect = score_side_effect

        async with WebSearchClient(mock_scorer, rate_limit_seconds=0.0) as client:
            mock_results = [
                {"url": "https://low-cred.com", "title": "Low", "snippet": ""},
                {"url": "https://high-cred.com", "title": "High", "snippet": ""},
            ]
            client._execute_search = AsyncMock(return_value=mock_results)

            query = SearchQuery(query="test", focus_type="test")
            results = await client.search(query)

            # Results should be sorted by credibility (high first)
            assert results[0].credibility == 0.95
            assert results[0].title == "High"
            assert results[1].credibility == 0.50
            assert results[1].title == "Low"

    @pytest.mark.asyncio
    async def test_caching_enabled(self, mock_scorer):
        """Test that caching prevents duplicate searches."""
        async with WebSearchClient(
            mock_scorer, cache_enabled=True, rate_limit_seconds=0.0
        ) as client:
            mock_results = [{"url": "https://example.com", "title": "Result", "snippet": ""}]
            client._execute_search = AsyncMock(return_value=mock_results)

            query = SearchQuery(query="test", focus_type="test")

            # First search
            results1 = await client.search(query)
            assert len(results1) == 1

            # Second search (should hit cache)
            results2 = await client.search(query)
            assert len(results2) == 1

            # _execute_search should only be called once
            assert client._execute_search.call_count == 1

    @pytest.mark.asyncio
    async def test_caching_disabled(self, mock_scorer):
        """Test that caching can be disabled."""
        async with WebSearchClient(
            mock_scorer, cache_enabled=False, rate_limit_seconds=0.0
        ) as client:
            mock_results = [{"url": "https://example.com", "title": "Result", "snippet": ""}]
            client._execute_search = AsyncMock(return_value=mock_results)

            query = SearchQuery(query="test", focus_type="test")

            # First search
            await client.search(query)

            # Second search (should NOT hit cache)
            await client.search(query)

            # _execute_search should be called twice
            assert client._execute_search.call_count == 2

    @pytest.mark.asyncio
    async def test_rate_limiting(self, mock_scorer):
        """Test that rate limiting delays requests."""
        async with WebSearchClient(
            mock_scorer, rate_limit_seconds=0.1, cache_enabled=False
        ) as client:
            mock_results = [{"url": "https://example.com", "title": "Result", "snippet": ""}]
            client._execute_search = AsyncMock(return_value=mock_results)

            query = SearchQuery(query="test", focus_type="test")

            start = datetime.now()

            # First request (no delay)
            await client.search(query)

            # Second request (should be delayed)
            await client.search(query)

            elapsed = (datetime.now() - start).total_seconds()

            # Should take at least 0.1 seconds due to rate limiting
            assert elapsed >= 0.1

    @pytest.mark.asyncio
    async def test_cache_key_includes_focus_type(self, mock_scorer):
        """Test that cache key differentiates by focus type."""
        async with WebSearchClient(
            mock_scorer, cache_enabled=True, rate_limit_seconds=0.0
        ) as client:
            mock_results = [{"url": "https://example.com", "title": "Result", "snippet": ""}]
            client._execute_search = AsyncMock(return_value=mock_results)

            # Same query but different focus types
            query1 = SearchQuery(query="patterns", focus_type="architecture")
            query2 = SearchQuery(query="patterns", focus_type="security")

            await client.search(query1)
            await client.search(query2)

            # Should execute search twice (different cache keys)
            assert client._execute_search.call_count == 2

    @pytest.mark.asyncio
    async def test_clear_cache(self, mock_scorer):
        """Test that clear_cache removes cached results."""
        async with WebSearchClient(
            mock_scorer, cache_enabled=True, rate_limit_seconds=0.0
        ) as client:
            mock_results = [{"url": "https://example.com", "title": "Result", "snippet": ""}]
            client._execute_search = AsyncMock(return_value=mock_results)

            query = SearchQuery(query="test", focus_type="test")

            # First search
            await client.search(query)
            assert client._execute_search.call_count == 1

            # Clear cache
            client.clear_cache()

            # Second search (should execute again)
            await client.search(query)
            assert client._execute_search.call_count == 2

    @pytest.mark.asyncio
    async def test_result_metadata_populated(self, mock_scorer):
        """Test that result metadata is properly populated."""
        async with WebSearchClient(mock_scorer, rate_limit_seconds=0.0) as client:
            mock_results = [{"url": "https://example.com", "title": "Result", "snippet": ""}]
            client._execute_search = AsyncMock(return_value=mock_results)

            query = SearchQuery(query="test", focus_type="test")
            results = await client.search(query)

            assert len(results) == 1
            result = results[0]

            # Metadata should include original rank and timestamp
            assert "original_rank" in result.metadata
            assert "scored_at" in result.metadata
            assert result.metadata["original_rank"] == "1"

    @pytest.mark.asyncio
    async def test_empty_results(self, mock_scorer):
        """Test handling of empty search results."""
        async with WebSearchClient(mock_scorer, rate_limit_seconds=0.0) as client:
            client._execute_search = AsyncMock(return_value=[])

            query = SearchQuery(query="test", focus_type="test")
            results = await client.search(query)

            assert results == []

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_scorer):
        """Test async context manager protocol."""
        client = WebSearchClient(mock_scorer)

        # Enter context
        async with client as ctx_client:
            assert ctx_client is client

        # Context should exit cleanly (no errors)
