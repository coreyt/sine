"""Unit tests for GoogleSearchProvider."""

from unittest.mock import AsyncMock, MagicMock, Mock

import httpx
import pytest

from lookout.discovery.search.google import GoogleSearchProvider
from lookout.discovery.search.providers import SearchProviderError


class TestGoogleSearchProvider:
    SAMPLE_RESPONSE = {
        "items": [
            {
                "link": "https://martinfowler.com/articles/injection.html",
                "title": "Inversion of Control and DI",
                "snippet": "Dependency Injection is a useful pattern...",
            },
            {
                "link": "https://refactoring.guru/design-patterns/strategy",
                "title": "Strategy Pattern",
                "snippet": "Strategy is a behavioral design pattern...",
            },
            {
                "link": "https://example.com/third",
                "title": "Third Result",
                "snippet": "Another result",
            },
        ]
    }

    @pytest.fixture
    def provider(self):
        return GoogleSearchProvider(api_key="test-key", cse_id="test-cse")

    def _mock_response(self, json_data: dict, status_code: int = 200) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        resp.raise_for_status = Mock()
        if status_code >= 400:
            resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                f"HTTP {status_code}", request=MagicMock(), response=resp
            )
        return resp

    @pytest.mark.asyncio
    async def test_parses_google_json(self, provider):
        """Maps items[] to [{url, title, snippet}]."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=self._mock_response(self.SAMPLE_RESPONSE))
        provider._client = mock_client

        results = await provider.execute_search("dependency injection")
        assert len(results) == 3
        assert results[0]["url"] == "https://martinfowler.com/articles/injection.html"
        assert results[0]["title"] == "Inversion of Control and DI"
        assert results[0]["snippet"] == "Dependency Injection is a useful pattern..."

    @pytest.mark.asyncio
    async def test_max_results_caps_output(self, provider):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=self._mock_response(self.SAMPLE_RESPONSE))
        provider._client = mock_client

        results = await provider.execute_search("test", max_results=2)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_sends_api_key_and_cse_id(self, provider):
        """API key and CSE ID are sent as query params."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=self._mock_response(self.SAMPLE_RESPONSE))
        provider._client = mock_client

        await provider.execute_search("test")

        call_kwargs = mock_client.get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["key"] == "test-key"
        assert params["cx"] == "test-cse"

    @pytest.mark.asyncio
    async def test_allowed_domains_uses_site_restrict(self, provider):
        """allowed_domains maps to siteSearch param."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=self._mock_response(self.SAMPLE_RESPONSE))
        provider._client = mock_client

        results = await provider.execute_search("patterns", allowed_domains=["martinfowler.com"])

        call_kwargs = mock_client.get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert "siteSearch" in params

        # Post-filter should apply
        for r in results:
            assert "martinfowler.com" in r["url"]

    @pytest.mark.asyncio
    async def test_http_error_raises_provider_error(self, provider):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=self._mock_response({}, status_code=403))
        provider._client = mock_client

        with pytest.raises(SearchProviderError, match="403"):
            await provider.execute_search("test")

    @pytest.mark.asyncio
    async def test_network_error_raises_provider_error(self, provider):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        provider._client = mock_client

        with pytest.raises(SearchProviderError, match="refused"):
            await provider.execute_search("test")

    @pytest.mark.asyncio
    async def test_empty_items(self, provider):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=self._mock_response({"items": []}))
        provider._client = mock_client

        results = await provider.execute_search("test")
        assert results == []

    @pytest.mark.asyncio
    async def test_missing_items_key(self, provider):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=self._mock_response({}))
        provider._client = mock_client

        results = await provider.execute_search("test")
        assert results == []

    @pytest.mark.asyncio
    async def test_close_closes_client(self, provider):
        mock_client = AsyncMock()
        provider._client = mock_client

        await provider.close()
        mock_client.aclose.assert_called_once()
