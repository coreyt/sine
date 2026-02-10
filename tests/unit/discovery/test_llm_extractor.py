"""Unit tests for LLM-powered pattern extraction."""

import json
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from sine.discovery.agents.base import SearchFocus
from sine.discovery.extractors.base import ExtractionContext
from sine.discovery.extractors.llm import LLMExtractor, LLMProvider


# Helper to create valid pattern data
def make_pattern_data(pattern_id, title, category, subcategory="test-sub"):
    """Create validation-compliant pattern data."""
    return {
        "pattern_id": pattern_id,
        "title": title,
        "category": category,
        "subcategory": subcategory,
        "description": "This is a detailed description of the pattern that is long enough to pass validation",
        "rationale": "This pattern exists to improve code quality and maintainability in the codebase",
        "confidence": "high",
        "severity": "warning",
        "languages": ["python"],
        "framework": None,
        "examples_good": [],
        "examples_bad": [],
        "tags": ["test"],
    }


class TestLLMExtractor:
    """Tests for LLMExtractor."""

    @pytest.mark.asyncio
    async def test_anthropic_extraction(self):
        """Test extraction using Anthropic provider."""
        # Mock Anthropic API response
        mock_response = {
            "id": "msg_123",
            "content": [
                {
                    "text": json.dumps(
                        [
                            make_pattern_data(
                                "SEC-SQL-001", "Prevent SQL Injection", "security", "injection"
                            )
                        ]
                    )
                }
            ],
            "usage": {"input_tokens": 500, "output_tokens": 200},
        }

        async with LLMExtractor(
            provider=LLMProvider.ANTHROPIC,
            api_key="test-key",
        ) as extractor:
            # Mock the HTTP client
            mock_post = AsyncMock(
                return_value=Mock(
                    status_code=200,
                    json=lambda: mock_response,
                    raise_for_status=lambda: None,
                )
            )
            extractor._client.post = mock_post

            focus = SearchFocus(
                focus_type="security",
                description="Find security patterns",
            )
            context = ExtractionContext(
                source_url="https://example.com",
                source_text="Use parameterized queries to prevent SQL injection.",
                focus=focus,
            )

            result = await extractor.extract_patterns(context)

            assert result.method == "llm"
            assert result.confidence > 0.0
            assert len(result.patterns) == 1

            pattern = result.patterns[0]
            assert pattern.pattern_id == "SEC-SQL-001"
            assert pattern.title == "Prevent SQL Injection"
            assert pattern.category == "security"
            assert pattern.confidence == "high"

            # Check metadata
            assert result.metadata["provider"] == "anthropic"
            assert result.metadata["token_usage"]["input_tokens"] == 500
            assert result.metadata["token_usage"]["output_tokens"] == 200

    @pytest.mark.asyncio
    async def test_openai_extraction(self):
        """Test extraction using OpenAI provider."""
        # Mock OpenAI API response
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            [
                                make_pattern_data(
                                    "ARCH-DI-001",
                                    "Use Dependency Injection",
                                    "architecture",
                                    "dependency-injection",
                                )
                            ]
                        )
                    }
                }
            ],
            "usage": {"prompt_tokens": 400, "completion_tokens": 150},
        }

        async with LLMExtractor(
            provider=LLMProvider.OPENAI,
            api_key="test-key",
        ) as extractor:
            mock_post = AsyncMock(
                return_value=Mock(
                    status_code=200,
                    json=lambda: mock_response,
                    raise_for_status=lambda: None,
                )
            )
            extractor._client.post = mock_post

            focus = SearchFocus(
                focus_type="architecture",
                description="Find architecture patterns",
            )
            context = ExtractionContext(
                source_url="https://example.com",
                source_text="Use dependency injection for better testability.",
                focus=focus,
            )

            result = await extractor.extract_patterns(context)

            assert result.method == "llm"
            assert len(result.patterns) == 1
            assert result.patterns[0].pattern_id == "ARCH-DI-001"
            assert result.metadata["provider"] == "openai"
            assert result.metadata["token_usage"]["input_tokens"] == 400

    @pytest.mark.asyncio
    async def test_gemini_extraction(self):
        """Test extraction using Gemini provider."""
        # Mock Gemini API response
        mock_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    [
                                        make_pattern_data(
                                            "PERF-CACHE-001",
                                            "Use Caching Strategically",
                                            "performance",
                                            "caching",
                                        )
                                    ]
                                )
                            }
                        ]
                    }
                }
            ],
            "usageMetadata": {"promptTokenCount": 300, "candidatesTokenCount": 100},
        }

        async with LLMExtractor(
            provider=LLMProvider.GEMINI,
            api_key="test-key",
        ) as extractor:
            mock_post = AsyncMock(
                return_value=Mock(
                    status_code=200,
                    json=lambda: mock_response,
                    raise_for_status=lambda: None,
                )
            )
            extractor._client.post = mock_post

            focus = SearchFocus(
                focus_type="performance",
                description="Find performance patterns",
            )
            context = ExtractionContext(
                source_url="https://example.com",
                source_text="Cache frequently accessed data.",
                focus=focus,
            )

            result = await extractor.extract_patterns(context)

            assert result.method == "llm"
            assert len(result.patterns) == 1
            assert result.metadata["provider"] == "gemini"

    @pytest.mark.asyncio
    async def test_markdown_wrapped_json(self):
        """Test parsing of markdown-wrapped JSON response."""
        # Some LLMs may wrap JSON in markdown code blocks
        pattern_data = make_pattern_data("TEST-TST-001", "Test Pattern Name", "test")
        mock_response = {
            "content": [{"text": f"```json\n{json.dumps([pattern_data])}\n```"}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }

        async with LLMExtractor(
            provider=LLMProvider.ANTHROPIC,
            api_key="test-key",
        ) as extractor:
            mock_post = AsyncMock(
                return_value=Mock(
                    status_code=200,
                    json=lambda: mock_response,
                    raise_for_status=lambda: None,
                )
            )
            extractor._client.post = mock_post

            focus = SearchFocus(focus_type="test", description="Test")
            context = ExtractionContext(
                source_url="https://example.com",
                source_text="Test content",
                focus=focus,
            )

            result = await extractor.extract_patterns(context)

            assert len(result.patterns) == 1
            assert result.patterns[0].pattern_id == "TEST-TST-001"

    @pytest.mark.asyncio
    async def test_rate_limit_retry(self):
        """Test retry logic on rate limit error (429)."""
        # Mock responses: first 429, then success
        mock_responses = [
            Mock(
                status_code=429,
                raise_for_status=Mock(
                    side_effect=httpx.HTTPStatusError(
                        "Rate limited",
                        request=Mock(),
                        response=Mock(status_code=429),
                    )
                ),
            ),
            Mock(
                status_code=200,
                json=lambda: {
                    "content": [{"text": "[]"}],
                    "usage": {"input_tokens": 100, "output_tokens": 50},
                },
                raise_for_status=lambda: None,
            ),
        ]

        async with LLMExtractor(
            provider=LLMProvider.ANTHROPIC,
            api_key="test-key",
            max_retries=2,
        ) as extractor:
            mock_post = AsyncMock(side_effect=mock_responses)
            extractor._client.post = mock_post

            # Mock sleep to avoid waiting in tests
            with patch("asyncio.sleep", new_callable=AsyncMock):
                focus = SearchFocus(focus_type="test", description="Test")
                context = ExtractionContext(
                    source_url="https://example.com",
                    source_text="Test",
                    focus=focus,
                )

                result = await extractor.extract_patterns(context)

                # Should succeed after retry
                assert result.method == "llm"
                assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_malformed_json_returns_empty(self):
        """Test that malformed JSON returns empty pattern list."""
        mock_response = {
            "content": [{"text": "This is not valid JSON"}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }

        async with LLMExtractor(
            provider=LLMProvider.ANTHROPIC,
            api_key="test-key",
        ) as extractor:
            mock_post = AsyncMock(
                return_value=Mock(
                    status_code=200,
                    json=lambda: mock_response,
                    raise_for_status=lambda: None,
                )
            )
            extractor._client.post = mock_post

            focus = SearchFocus(focus_type="test", description="Test")
            context = ExtractionContext(
                source_url="https://example.com",
                source_text="Test",
                focus=focus,
            )

            result = await extractor.extract_patterns(context)

            # Should return empty list on parse error
            assert result.patterns == []
            assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_cost_estimation(self):
        """Test cost estimation for different providers."""
        focus = SearchFocus(focus_type="test", description="Test")
        context = ExtractionContext(
            source_url="https://example.com",
            source_text="Test content " * 1000,  # ~10K chars
            focus=focus,
        )

        # Anthropic
        async with LLMExtractor(
            provider=LLMProvider.ANTHROPIC,
            model="claude-sonnet-4-20250514",
            api_key="test-key",
        ) as extractor:
            cost = extractor.estimate_cost(context)
            assert cost > 0.0
            assert cost < 1.0  # Should be pennies for this size

        # OpenAI (cheaper)
        async with LLMExtractor(
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            api_key="test-key",
        ) as extractor:
            cost = extractor.estimate_cost(context)
            assert cost > 0.0
            assert cost < 0.01  # Very cheap for mini model

        # Gemini (free tier)
        async with LLMExtractor(
            provider=LLMProvider.GEMINI,
            model="gemini-2.0-flash-exp",
            api_key="test-key",
        ) as extractor:
            cost = extractor.estimate_cost(context)
            assert cost == 0.0  # Free tier

    @pytest.mark.asyncio
    async def test_missing_api_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(ValueError, match="API key required"),
        ):
            LLMExtractor(provider=LLMProvider.ANTHROPIC)

    @pytest.mark.asyncio
    async def test_multiple_patterns_in_response(self):
        """Test parsing multiple patterns from single response."""
        patterns = [
            make_pattern_data("SEC-SQL-001", "Prevent SQL Injection", "security", "injection"),
            make_pattern_data("SEC-XSS-001", "Prevent XSS Attacks", "security", "injection"),
        ]
        mock_response = {
            "content": [{"text": json.dumps(patterns)}],
            "usage": {"input_tokens": 500, "output_tokens": 300},
        }

        async with LLMExtractor(
            provider=LLMProvider.ANTHROPIC,
            api_key="test-key",
        ) as extractor:
            mock_post = AsyncMock(
                return_value=Mock(
                    status_code=200,
                    json=lambda: mock_response,
                    raise_for_status=lambda: None,
                )
            )
            extractor._client.post = mock_post

            focus = SearchFocus(focus_type="security", description="Test")
            context = ExtractionContext(
                source_url="https://example.com",
                source_text="Security content",
                focus=focus,
            )

            result = await extractor.extract_patterns(context)

            assert len(result.patterns) == 2
            assert result.patterns[0].pattern_id == "SEC-SQL-001"
            assert result.patterns[1].pattern_id == "SEC-XSS-001"

    @pytest.mark.asyncio
    async def test_confidence_calculation(self):
        """Test confidence score calculation from pattern confidences."""
        # High confidence pattern
        pattern = make_pattern_data("TEST-TST-001", "Test Pattern Name", "test")
        pattern["confidence"] = "high"

        mock_response = {
            "content": [{"text": json.dumps([pattern])}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }

        async with LLMExtractor(
            provider=LLMProvider.ANTHROPIC,
            api_key="test-key",
        ) as extractor:
            mock_post = AsyncMock(
                return_value=Mock(
                    status_code=200,
                    json=lambda: mock_response,
                    raise_for_status=lambda: None,
                )
            )
            extractor._client.post = mock_post

            focus = SearchFocus(focus_type="test", description="Test")
            context = ExtractionContext(
                source_url="https://example.com",
                source_text="Test",
                focus=focus,
            )

            result = await extractor.extract_patterns(context)

            # High confidence patterns should give 1.0
            assert result.confidence == 1.0
