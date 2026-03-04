"""Unit tests for BraveSearchProvider."""

from unittest.mock import AsyncMock, MagicMock, Mock

import httpx
import pytest

from lookout.discovery.search.brave import BraveSearchProvider
from lookout.discovery.search.providers import SearchProviderError


class TestBraveSearchProvider:
    """Tests for BraveSearchProvider."""

    SAMPLE_RESPONSE = {
        "web": {
            "results": [
                {
                    "url": "https://martinfowler.com/articles/injection.html",
                    "title": "Inversion of Control Containers and the DI pattern",
                    "description": "Dependency Injection is a useful pattern...",
                },
                {
                    "url": "https://refactoring.guru/design-patterns/strategy",
                    "title": "Strategy Pattern",
                    "description": "Strategy is a behavioral design pattern...",
                },
                {
                    "url": "https://example.com/third",
                    "title": "Third Result",
                    "description": "Another result",
                },
            ]
        }
    }

    @pytest.fixture
    def provider(self):
        return BraveSearchProvider(api_key="test-key")

    def _mock_httpx_response(self, json_data: dict, status_code: int = 200) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        resp.raise_for_status = Mock()
        if status_code >= 400:
            resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                f"HTTP {status_code}",
                request=MagicMock(),
                response=resp,
            )
        return resp

    @pytest.mark.asyncio
    async def test_parses_brave_json(self, provider, monkeypatch):
        """Maps web.results[] to [{url, title, snippet}]."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=self._mock_httpx_response(self.SAMPLE_RESPONSE))
        provider._client = mock_client

        results = await provider.execute_search("dependency injection")
        assert len(results) == 3
        assert results[0]["url"] == "https://martinfowler.com/articles/injection.html"
        assert results[0]["title"] == "Inversion of Control Containers and the DI pattern"
        assert results[0]["snippet"] == "Dependency Injection is a useful pattern..."

    @pytest.mark.asyncio
    async def test_max_results_caps_output(self, provider):
        """Only returns up to max_results items."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=self._mock_httpx_response(self.SAMPLE_RESPONSE))
        provider._client = mock_client

        results = await provider.execute_search("test", max_results=2)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_allowed_domains_rewrites_query(self, provider):
        """Prepends site: operators and post-filters results."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=self._mock_httpx_response(self.SAMPLE_RESPONSE))
        provider._client = mock_client

        results = await provider.execute_search(
            "design patterns",
            allowed_domains=["martinfowler.com"],
        )

        # Should have called with site: prefix in query
        call_kwargs = mock_client.get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert "site:martinfowler.com" in params["q"]

        # Post-filter: only martinfowler.com results should remain
        for r in results:
            assert "martinfowler.com" in r["url"]

    @pytest.mark.asyncio
    async def test_sends_api_key_header(self, provider):
        """X-Subscription-Token header is set."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=self._mock_httpx_response(self.SAMPLE_RESPONSE))
        provider._client = mock_client

        await provider.execute_search("test")

        call_kwargs = mock_client.get.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert headers["X-Subscription-Token"] == "test-key"

    @pytest.mark.asyncio
    async def test_http_error_raises_provider_error(self, provider):
        """HTTP errors are wrapped in SearchProviderError."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=self._mock_httpx_response({}, status_code=429))
        provider._client = mock_client

        with pytest.raises(SearchProviderError, match="429"):
            await provider.execute_search("test")

    @pytest.mark.asyncio
    async def test_network_error_raises_provider_error(self, provider):
        """Network errors are wrapped in SearchProviderError."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        provider._client = mock_client

        with pytest.raises(SearchProviderError, match="refused"):
            await provider.execute_search("test")

    @pytest.mark.asyncio
    async def test_close_closes_client(self, provider):
        """close() closes the underlying httpx client."""
        mock_client = AsyncMock()
        provider._client = mock_client

        await provider.close()
        mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_web_results(self, provider):
        """Handles response with no web results gracefully."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            return_value=self._mock_httpx_response({"web": {"results": []}})
        )
        provider._client = mock_client

        results = await provider.execute_search("test")
        assert results == []

    @pytest.mark.asyncio
    async def test_missing_web_key(self, provider):
        """Handles response with no 'web' key gracefully."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=self._mock_httpx_response({}))
        provider._client = mock_client

        results = await provider.execute_search("test")
        assert results == []

    @pytest.mark.asyncio
    async def test_multiple_allowed_domains(self, provider):
        """Multiple allowed_domains are joined with OR in site: query."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=self._mock_httpx_response(self.SAMPLE_RESPONSE))
        provider._client = mock_client

        await provider.execute_search(
            "patterns",
            allowed_domains=["martinfowler.com", "refactoring.guru"],
        )

        call_kwargs = mock_client.get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        q = params["q"]
        assert "site:martinfowler.com" in q or "site:refactoring.guru" in q
