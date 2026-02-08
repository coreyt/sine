"""Unit tests for hybrid pattern extraction."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from sine.discovery.agents.base import SearchFocus
from sine.discovery.extractors.base import (
    ExtractionContext,
    ExtractionResult,
)
from sine.discovery.extractors.hybrid import HybridExtractor
from sine.discovery.extractors.llm import LLMProvider
from sine.discovery.models import DiscoveredPattern


@pytest.fixture
def sample_context():
    """Create a sample extraction context."""
    focus = SearchFocus(
        focus_type="security",
        description="Find security patterns",
    )
    return ExtractionContext(
        source_url="https://example.com",
        source_text="Use parameterized queries to prevent SQL injection attacks.",
        focus=focus,
    )


@pytest.fixture
def sample_keyword_pattern(sample_discovered_pattern):
    """Create a sample keyword-extracted pattern."""
    return sample_discovered_pattern.model_copy(
        update={
            "pattern_id": "SEC-SQL-001",
            "discovered_by": "keyword-extractor",
            "title": "Prevent SQL Injection",
        }
    )


@pytest.fixture
def sample_llm_pattern(sample_discovered_pattern):
    """Create a sample LLM-extracted pattern."""
    return sample_discovered_pattern.model_copy(
        update={
            "pattern_id": "SEC-XSS-001",
            "discovered_by": "llm-anthropic",
            "title": "Prevent XSS Attacks",
        }
    )


class TestHybridExtractor:
    """Tests for HybridExtractor."""

    @pytest.mark.asyncio
    async def test_both_stages_run_when_keyword_confident(
        self, sample_context, sample_keyword_pattern, sample_llm_pattern
    ):
        """Test that both stages run when keyword confidence is high enough."""
        async with HybridExtractor(
            llm_provider=LLMProvider.ANTHROPIC,
            llm_api_key="test-key",
            min_keyword_confidence=0.3,
        ) as extractor:
            # Mock keyword stage (high confidence)
            keyword_result = ExtractionResult(
                patterns=[sample_keyword_pattern],
                confidence=0.8,
                method="keyword",
                metadata={},
            )
            extractor.keyword_extractor.extract_patterns = AsyncMock(
                return_value=keyword_result
            )

            # Mock LLM stage
            llm_result = ExtractionResult(
                patterns=[sample_llm_pattern],
                confidence=0.9,
                method="llm",
                metadata={"token_usage": {"input_tokens": 100, "output_tokens": 50}},
            )
            extractor.llm_extractor.extract_patterns = AsyncMock(return_value=llm_result)

            result = await extractor.extract_patterns(sample_context)

            # Both stages should run
            assert extractor.keyword_extractor.extract_patterns.called
            assert extractor.llm_extractor.extract_patterns.called

            # Result should be hybrid
            assert result.method == "hybrid"
            assert len(result.patterns) == 2  # Both patterns included
            assert result.metadata["llm_skipped"] is False
            assert result.metadata["keyword_patterns"] == 1
            assert result.metadata["llm_patterns"] == 1

    @pytest.mark.asyncio
    async def test_llm_stage_skipped_when_keyword_low_confidence(
        self, sample_context, sample_keyword_pattern
    ):
        """Test that LLM stage is skipped when keyword confidence is low."""
        async with HybridExtractor(
            llm_provider=LLMProvider.ANTHROPIC,
            llm_api_key="test-key",
            min_keyword_confidence=0.5,  # Higher threshold
        ) as extractor:
            # Mock keyword stage (low confidence)
            keyword_result = ExtractionResult(
                patterns=[sample_keyword_pattern],
                confidence=0.3,  # Below threshold
                method="keyword",
                metadata={},
            )
            extractor.keyword_extractor.extract_patterns = AsyncMock(
                return_value=keyword_result
            )

            # Mock LLM stage
            extractor.llm_extractor.extract_patterns = AsyncMock()

            result = await extractor.extract_patterns(sample_context)

            # Keyword stage should run
            assert extractor.keyword_extractor.extract_patterns.called

            # LLM stage should NOT run
            assert not extractor.llm_extractor.extract_patterns.called

            # Result should be keyword-only
            assert result.method == "hybrid-keyword-only"
            assert result.metadata["llm_skipped"] is True
            assert result.confidence == 0.3

    @pytest.mark.asyncio
    async def test_pattern_merging_prefers_llm(
        self, sample_context, sample_discovered_pattern
    ):
        """Test that pattern merging prefers LLM patterns over keyword patterns."""
        # Create patterns with same category/subcategory
        keyword_pattern = DiscoveredPattern(
            **{
                **sample_discovered_pattern.model_dump(),
                "pattern_id": "SEC-SQL-001",
                "discovered_by": "keyword-extractor",
            }
        )
        llm_pattern = DiscoveredPattern(
            **{
                **sample_discovered_pattern.model_dump(),
                "pattern_id": "SEC-SQL-002",
                "discovered_by": "llm-anthropic",
                "title": "Better SQL Injection Prevention",
            }
        )

        async with HybridExtractor(
            llm_provider=LLMProvider.ANTHROPIC,
            llm_api_key="test-key",
        ) as extractor:
            # Mock both stages
            keyword_result = ExtractionResult(
                patterns=[keyword_pattern],
                confidence=0.6,
                method="keyword",
                metadata={},
            )
            llm_result = ExtractionResult(
                patterns=[llm_pattern],
                confidence=0.9,
                method="llm",
                metadata={},
            )

            extractor.keyword_extractor.extract_patterns = AsyncMock(
                return_value=keyword_result
            )
            extractor.llm_extractor.extract_patterns = AsyncMock(return_value=llm_result)

            result = await extractor.extract_patterns(sample_context)

            # Should have only LLM pattern (same category prefix)
            assert len(result.patterns) == 1
            assert result.patterns[0].discovered_by == "llm-anthropic"

    @pytest.mark.asyncio
    async def test_pattern_merging_keeps_different_categories(
        self, sample_context, sample_discovered_pattern
    ):
        """Test that patterns from different categories are both kept."""
        # Create patterns with different categories
        keyword_pattern = DiscoveredPattern(
            **{
                **sample_discovered_pattern.model_dump(),
                "pattern_id": "SEC-SQL-001",
                "category": "security",
                "discovered_by": "keyword-extractor",
            }
        )
        llm_pattern = DiscoveredPattern(
            **{
                **sample_discovered_pattern.model_dump(),
                "pattern_id": "ARCH-DI-001",
                "category": "architecture",
                "discovered_by": "llm-anthropic",
            }
        )

        async with HybridExtractor(
            llm_provider=LLMProvider.ANTHROPIC,
            llm_api_key="test-key",
        ) as extractor:
            keyword_result = ExtractionResult(
                patterns=[keyword_pattern],
                confidence=0.6,
                method="keyword",
                metadata={},
            )
            llm_result = ExtractionResult(
                patterns=[llm_pattern],
                confidence=0.9,
                method="llm",
                metadata={},
            )

            extractor.keyword_extractor.extract_patterns = AsyncMock(
                return_value=keyword_result
            )
            extractor.llm_extractor.extract_patterns = AsyncMock(return_value=llm_result)

            result = await extractor.extract_patterns(sample_context)

            # Should have both patterns (different categories)
            assert len(result.patterns) == 2
            categories = {p.category for p in result.patterns}
            assert "security" in categories
            assert "architecture" in categories

    @pytest.mark.asyncio
    async def test_confidence_calculation_weighted(
        self, sample_context, sample_keyword_pattern, sample_llm_pattern
    ):
        """Test that combined confidence is weighted average (70% LLM, 30% keyword)."""
        async with HybridExtractor(
            llm_provider=LLMProvider.ANTHROPIC,
            llm_api_key="test-key",
        ) as extractor:
            # Mock both stages with known confidences
            keyword_result = ExtractionResult(
                patterns=[sample_keyword_pattern],
                confidence=0.6,  # 60%
                method="keyword",
                metadata={},
            )
            llm_result = ExtractionResult(
                patterns=[sample_llm_pattern],
                confidence=1.0,  # 100%
                method="llm",
                metadata={},
            )

            extractor.keyword_extractor.extract_patterns = AsyncMock(
                return_value=keyword_result
            )
            extractor.llm_extractor.extract_patterns = AsyncMock(return_value=llm_result)

            result = await extractor.extract_patterns(sample_context)

            # Combined: 1.0 * 0.7 + 0.6 * 0.3 = 0.88
            expected = 1.0 * 0.7 + 0.6 * 0.3
            assert abs(result.confidence - expected) < 0.01

    @pytest.mark.asyncio
    async def test_keyword_max_results_respected(
        self, sample_context, sample_discovered_pattern
    ):
        """Test that keyword_max_results limits patterns when LLM is skipped."""
        # Create 5 keyword patterns
        keyword_patterns = [
            DiscoveredPattern(
                **{
                    **sample_discovered_pattern.model_dump(),
                    "pattern_id": f"SEC-SQL-{i:03d}",
                }
            )
            for i in range(1, 6)
        ]

        async with HybridExtractor(
            llm_provider=LLMProvider.ANTHROPIC,
            llm_api_key="test-key",
            min_keyword_confidence=0.5,
            keyword_max_results=3,  # Limit to 3
        ) as extractor:
            # Low confidence -> LLM skipped
            keyword_result = ExtractionResult(
                patterns=keyword_patterns,
                confidence=0.2,  # Below threshold
                method="keyword",
                metadata={},
            )
            extractor.keyword_extractor.extract_patterns = AsyncMock(
                return_value=keyword_result
            )

            result = await extractor.extract_patterns(sample_context)

            # Should only have 3 patterns (max_results)
            assert len(result.patterns) == 3
            assert result.method == "hybrid-keyword-only"

    @pytest.mark.asyncio
    async def test_cost_estimation(self, sample_context):
        """Test that cost estimation delegates to LLM extractor."""
        async with HybridExtractor(
            llm_provider=LLMProvider.ANTHROPIC,
            llm_api_key="test-key",
        ) as extractor:
            # Mock LLM cost estimation
            extractor.llm_extractor.estimate_cost = MagicMock(return_value=0.05)

            cost = extractor.estimate_cost(sample_context)

            assert cost == 0.05
            assert extractor.llm_extractor.estimate_cost.called

    @pytest.mark.asyncio
    async def test_metadata_includes_token_usage(
        self, sample_context, sample_keyword_pattern, sample_llm_pattern
    ):
        """Test that result metadata includes LLM token usage."""
        async with HybridExtractor(
            llm_provider=LLMProvider.ANTHROPIC,
            llm_api_key="test-key",
        ) as extractor:
            keyword_result = ExtractionResult(
                patterns=[sample_keyword_pattern],
                confidence=0.8,
                method="keyword",
                metadata={},
            )
            llm_result = ExtractionResult(
                patterns=[sample_llm_pattern],
                confidence=0.9,
                method="llm",
                metadata={
                    "token_usage": {"input_tokens": 500, "output_tokens": 200},
                    "provider": "anthropic",
                },
            )

            extractor.keyword_extractor.extract_patterns = AsyncMock(
                return_value=keyword_result
            )
            extractor.llm_extractor.extract_patterns = AsyncMock(return_value=llm_result)

            result = await extractor.extract_patterns(sample_context)

            # Check metadata
            assert "llm_token_usage" in result.metadata
            assert result.metadata["llm_token_usage"]["input_tokens"] == 500
            assert result.metadata["llm_token_usage"]["output_tokens"] == 200
            assert result.metadata["llm_provider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_no_patterns_returns_zero_confidence(self, sample_context):
        """Test handling when no patterns are found."""
        async with HybridExtractor(
            llm_provider=LLMProvider.ANTHROPIC,
            llm_api_key="test-key",
        ) as extractor:
            # Both stages return empty
            keyword_result = ExtractionResult(
                patterns=[],
                confidence=0.0,
                method="keyword",
                metadata={},
            )
            llm_result = ExtractionResult(
                patterns=[],
                confidence=0.0,
                method="llm",
                metadata={},
            )

            extractor.keyword_extractor.extract_patterns = AsyncMock(
                return_value=keyword_result
            )
            extractor.llm_extractor.extract_patterns = AsyncMock(return_value=llm_result)

            result = await extractor.extract_patterns(sample_context)

            assert len(result.patterns) == 0
            assert result.confidence == 0.0
