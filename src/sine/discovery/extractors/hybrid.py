"""Hybrid pattern extraction (keyword + LLM).

This extractor combines the speed of keyword-based extraction with the accuracy
of LLM-powered synthesis:

1. Stage 1 (Keyword): Fast filtering to identify relevant content
2. Stage 2 (LLM): Deep analysis on filtered content only

Benefits:
- Reduces API costs (only process relevant sections)
- Faster than pure LLM (keyword filtering is instant)
- More accurate than pure keyword (LLM provides synthesis)
"""

from __future__ import annotations

import logging

from sine.discovery.extractors.base import (
    ExtractionContext,
    ExtractionResult,
    PatternExtractor,
)
from sine.discovery.extractors.keyword import KeywordExtractor
from sine.discovery.extractors.llm import LLMExtractor, LLMProvider
from sine.discovery.models import DiscoveredPattern

logger = logging.getLogger(__name__)


class HybridExtractor(PatternExtractor):
    """Hybrid pattern extractor combining keyword + LLM approaches.

    Two-stage extraction:
    1. Keyword stage: Quick relevance check and initial patterns
    2. LLM stage: Deep analysis if content is relevant

    The keyword stage acts as a filter - if it finds patterns above the
    confidence threshold, the LLM stage runs for more thorough analysis.

    Example:
        async with HybridExtractor(
            llm_provider=LLMProvider.ANTHROPIC,
            min_keyword_confidence=0.3,
        ) as extractor:
            context = ExtractionContext(...)
            result = await extractor.extract_patterns(context)
    """

    def __init__(
        self,
        llm_provider: LLMProvider = LLMProvider.ANTHROPIC,
        llm_model: str | None = None,
        llm_api_key: str | None = None,
        min_keyword_confidence: float = 0.3,
        keyword_max_results: int = 10,
        llm_temperature: float = 0.0,
        llm_max_tokens: int = 4096,
    ):
        """Initialize the hybrid extractor.

        Args:
            llm_provider: LLM provider for stage 2
            llm_model: LLM model (uses default if not specified)
            llm_api_key: API key for LLM
            min_keyword_confidence: Minimum keyword confidence to trigger LLM stage (0.0-1.0)
            keyword_max_results: Maximum patterns from keyword stage
            llm_temperature: LLM temperature
            llm_max_tokens: LLM max tokens
        """
        self.min_keyword_confidence = min_keyword_confidence
        self.keyword_max_results = keyword_max_results

        # Initialize extractors
        self.keyword_extractor = KeywordExtractor()
        self.llm_extractor = LLMExtractor(
            provider=llm_provider,
            model=llm_model,
            api_key=llm_api_key,
            temperature=llm_temperature,
            max_tokens=llm_max_tokens,
        )

    async def __aenter__(self) -> HybridExtractor:
        """Initialize LLM client."""
        await self.keyword_extractor.__aenter__()
        await self.llm_extractor.__aenter__()
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object
    ) -> None:
        """Cleanup LLM client."""
        await self.keyword_extractor.__aexit__(exc_type, exc_val, exc_tb)
        await self.llm_extractor.__aexit__(exc_type, exc_val, exc_tb)

    async def extract_patterns(self, context: ExtractionContext) -> ExtractionResult:
        """Extract patterns using hybrid approach.

        Strategy:
        1. Run keyword extraction (fast, free)
        2. Check if confidence >= threshold
        3. If yes, run LLM extraction for deeper analysis
        4. Merge and deduplicate results

        Args:
            context: Extraction context

        Returns:
            ExtractionResult with merged patterns
        """
        # Stage 1: Keyword extraction
        logger.debug("Stage 1: Running keyword extraction...")
        keyword_result = await self.keyword_extractor.extract_patterns(context)

        logger.debug(
            f"Keyword stage found {len(keyword_result.patterns)} patterns "
            f"with confidence {keyword_result.confidence:.2f}"
        )

        # Check if we should run LLM stage
        if keyword_result.confidence < self.min_keyword_confidence:
            logger.debug(
                f"Keyword confidence {keyword_result.confidence:.2f} below threshold "
                f"{self.min_keyword_confidence}, skipping LLM stage"
            )
            return ExtractionResult(
                patterns=keyword_result.patterns[: self.keyword_max_results],
                confidence=keyword_result.confidence,
                method="hybrid-keyword-only",
                metadata={
                    "keyword_patterns": len(keyword_result.patterns),
                    "llm_patterns": 0,
                    "llm_skipped": True,
                    "keyword_confidence": keyword_result.confidence,
                },
            )

        # Stage 2: LLM extraction
        logger.debug("Stage 2: Running LLM extraction...")
        llm_result = await self.llm_extractor.extract_patterns(context)

        logger.debug(
            f"LLM stage found {len(llm_result.patterns)} patterns "
            f"with confidence {llm_result.confidence:.2f}"
        )

        # Merge results (deduplicate by pattern_id)
        merged_patterns = self._merge_patterns(keyword_result.patterns, llm_result.patterns)

        # Calculate combined confidence (weighted average)
        combined_confidence = self._calculate_combined_confidence(
            keyword_result.confidence,
            llm_result.confidence,
            len(keyword_result.patterns),
            len(llm_result.patterns),
        )

        return ExtractionResult(
            patterns=merged_patterns,
            confidence=combined_confidence,
            method="hybrid",
            metadata={
                "keyword_patterns": len(keyword_result.patterns),
                "llm_patterns": len(llm_result.patterns),
                "merged_patterns": len(merged_patterns),
                "llm_skipped": False,
                "keyword_confidence": keyword_result.confidence,
                "llm_confidence": llm_result.confidence,
                "llm_token_usage": llm_result.metadata.get("token_usage", {}),
                "llm_provider": llm_result.metadata.get("provider"),
            },
        )

    def _merge_patterns(
        self,
        keyword_patterns: list[DiscoveredPattern],
        llm_patterns: list[DiscoveredPattern],
    ) -> list[DiscoveredPattern]:
        """Merge patterns from both stages, preferring LLM patterns.

        Strategy:
        - LLM patterns are generally more detailed and accurate
        - Keep LLM patterns as primary
        - Add keyword patterns that don't conflict (different pattern_id prefixes)

        Args:
            keyword_patterns: Patterns from keyword extraction
            llm_patterns: Patterns from LLM extraction

        Returns:
            Merged pattern list
        """
        # Start with LLM patterns (higher quality)
        merged = list(llm_patterns)

        # Get pattern ID prefixes from LLM patterns (e.g., "SEC-SQL", "ARCH-DI")
        llm_prefixes = {"-".join(p.pattern_id.split("-")[:2]) for p in llm_patterns}

        # Add keyword patterns that don't overlap
        for kw_pattern in keyword_patterns:
            kw_prefix = "-".join(kw_pattern.pattern_id.split("-")[:2])

            # If this category-subcategory combo not covered by LLM, keep it
            if kw_prefix not in llm_prefixes:
                merged.append(kw_pattern)

        # Sort by category then pattern_id
        merged.sort(key=lambda p: (p.category, p.pattern_id))

        return merged

    def _calculate_combined_confidence(
        self,
        keyword_confidence: float,
        llm_confidence: float,
        keyword_count: int,
        llm_count: int,
    ) -> float:
        """Calculate combined confidence from both stages.

        LLM confidence is weighted more heavily as it's generally more reliable.

        Args:
            keyword_confidence: Keyword stage confidence
            llm_confidence: LLM stage confidence
            keyword_count: Number of keyword patterns
            llm_count: Number of LLM patterns

        Returns:
            Combined confidence (0.0 - 1.0)
        """
        if llm_count == 0 and keyword_count == 0:
            return 0.0

        # Weight LLM confidence 70%, keyword 30%
        if llm_count > 0 and keyword_count > 0:
            return llm_confidence * 0.7 + keyword_confidence * 0.3
        elif llm_count > 0:
            return llm_confidence
        else:
            return keyword_confidence

    def estimate_cost(self, context: ExtractionContext) -> float:
        """Estimate extraction cost (LLM portion only).

        The keyword stage is free. We estimate the LLM cost assuming
        it will run (worst case).

        Args:
            context: Extraction context

        Returns:
            Estimated cost in USD
        """
        # Keyword stage is free, only estimate LLM cost
        return self.llm_extractor.estimate_cost(context)
