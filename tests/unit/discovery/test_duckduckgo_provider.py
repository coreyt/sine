"""Unit tests for DuckDuckGoSearchProvider."""

from unittest.mock import AsyncMock, MagicMock, Mock

import httpx
import pytest

from lookout.discovery.search.duckduckgo import DuckDuckGoSearchProvider
from lookout.discovery.search.providers import SearchProviderError

FAKE_DDG_HTML = """
<html><body>
<div class="web-result">
    <a class="result__title">Dependency Injection Guide</a>
    <span class="result__url">martinfowler.com/articles/di</span>
    <a class="result__snippet">A comprehensive guide to DI patterns.</a>
</div>
<div class="web-result">
    <a class="result__title">Python DI Tutorial</a>
    <span class="result__url">realpython.com/python-di</span>
    <a class="result__snippet">Learn DI in Python step by step.</a>
</div>
<div class="web-result">
    <a class="result__title">Java DI Framework</a>
    <span class="result__url">spring.io/guides/di</span>
    <a class="result__snippet">Spring DI framework guide.</a>
</div>
</body></html>
"""


class TestDuckDuckGoSearchProvider:
    @pytest.fixture
    def provider(self):
        return DuckDuckGoSearchProvider()

    def _mock_response(self, html: str, status_code: int = 200) -> MagicMock:
        resp = MagicMock()
        resp.text = html
        resp.status_code = status_code
        resp.raise_for_status = Mock()
        if status_code >= 400:
            resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                f"HTTP {status_code}", request=MagicMock(), response=resp
            )
        return resp

    @pytest.mark.asyncio
    async def test_parses_html_results(self, provider):
        """Parses DDG HTML into [{url, title, snippet}]."""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=self._mock_response(FAKE_DDG_HTML))
        provider._client = mock_client

        results = await provider.execute_search("dependency injection")
        assert len(results) == 3
        assert results[0]["title"] == "Dependency Injection Guide"
        assert "martinfowler.com" in results[0]["url"]
        assert results[0]["snippet"] != ""

    @pytest.mark.asyncio
    async def test_max_results_caps_output(self, provider):
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=self._mock_response(FAKE_DDG_HTML))
        provider._client = mock_client

        results = await provider.execute_search("test", max_results=2)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_allowed_domains_filters(self, provider):
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=self._mock_response(FAKE_DDG_HTML))
        provider._client = mock_client

        results = await provider.execute_search("di", allowed_domains=["martinfowler.com"])
        assert len(results) == 1
        assert "martinfowler.com" in results[0]["url"]

    @pytest.mark.asyncio
    async def test_network_error_raises_provider_error(self, provider):
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
        provider._client = mock_client

        with pytest.raises(SearchProviderError, match="refused"):
            await provider.execute_search("test")

    @pytest.mark.asyncio
    async def test_http_error_raises_provider_error(self, provider):
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=self._mock_response("", status_code=503))
        provider._client = mock_client

        with pytest.raises(SearchProviderError, match="503"):
            await provider.execute_search("test")

    @pytest.mark.asyncio
    async def test_empty_html_returns_empty(self, provider):
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            return_value=self._mock_response("<html><body>No results</body></html>")
        )
        provider._client = mock_client

        results = await provider.execute_search("test")
        assert results == []

    @pytest.mark.asyncio
    async def test_close_closes_client(self, provider):
        mock_client = AsyncMock()
        provider._client = mock_client

        await provider.close()
        mock_client.aclose.assert_called_once()
