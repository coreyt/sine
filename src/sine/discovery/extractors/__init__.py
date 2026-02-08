"""Pattern extraction engines.

This module provides three extraction methods for discovering coding patterns
from web sources:

- LLM-powered extraction (llm.py): Uses LLM APIs for accurate synthesis
- Keyword-based extraction (keyword.py): Uses rule templates and keyword matching
- Hybrid extraction (hybrid.py): Combines keyword filtering with LLM synthesis

Public API:
    Base Classes:
        - ExtractionContext: Input for extraction
        - ExtractionResult: Output from extraction
        - PatternExtractor: Abstract base class for extractors

    Extractors (to be implemented):
        - LLMExtractor: LLM-powered extraction
        - KeywordExtractor: Keyword-based extraction
        - HybridExtractor: Hybrid extraction
"""

from sine.discovery.extractors.base import (
    ExtractionContext,
    ExtractionResult,
    PatternExtractor,
)
from sine.discovery.extractors.hybrid import HybridExtractor
from sine.discovery.extractors.keyword import KeywordExtractor
from sine.discovery.extractors.llm import LLMExtractor, LLMProvider

__all__ = [
    # Base classes
    "ExtractionContext",
    "ExtractionResult",
    "PatternExtractor",
    # Extractors
    "KeywordExtractor",
    "LLMExtractor",
    "HybridExtractor",
    # LLM types
    "LLMProvider",
]
