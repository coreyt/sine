"""Base interface and data models for pattern extraction.

Pattern extractors analyze web content and extract coding patterns into
DiscoveredPattern objects. Three extraction methods are supported:

1. LLM-powered: Uses LLM APIs to synthesize patterns from text
2. Keyword-based: Uses rule templates and keyword matching
3. Hybrid: Combines keyword filtering with LLM synthesis

All extractors implement the PatternExtractor ABC and support async
context managers for resource cleanup.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from sine.discovery.agents.base import SearchFocus
from sine.discovery.models import DiscoveredPattern


@dataclass(frozen=True)
class ExtractionContext:
    """Input context for pattern extraction.

    Contains the source material and metadata needed for extractors
    to discover patterns.
    """

    source_url: str
    """URL of the source document"""

    source_text: str
    """Full text content of the source"""

    focus: SearchFocus
    """Search focus defining what patterns to look for"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata (credibility score, author, date, etc.)"""


@dataclass(frozen=True)
class ExtractionResult:
    """Output from pattern extraction.

    Contains discovered patterns and metadata about the extraction process.
    """

    patterns: list[DiscoveredPattern]
    """Patterns discovered from the source"""

    confidence: float
    """Overall confidence in extraction quality (0.0 - 1.0)"""

    method: str
    """Extraction method used (llm, keyword, hybrid)"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Extraction-specific metadata (token_count, processing_time, etc.)"""


class PatternExtractor(ABC):
    """Abstract base class for pattern extraction engines.

    Extractors analyze web content and produce DiscoveredPattern objects.
    All extractors support async context managers for resource cleanup
    (HTTP clients, API connections, etc.).

    Example:
        async with LLMExtractor(provider="anthropic") as extractor:
            context = ExtractionContext(
                source_url="https://example.com/patterns",
                source_text="...",
                focus=SearchFocus(...),
            )
            result = await extractor.extract_patterns(context)
            for pattern in result.patterns:
                print(pattern.pattern_id, pattern.title)
    """

    @abstractmethod
    async def extract_patterns(self, context: ExtractionContext) -> ExtractionResult:
        """Extract patterns from source content.

        This is the main extraction method. Implementations should:
        1. Analyze the source text in the context
        2. Identify relevant patterns based on the search focus
        3. Generate DiscoveredPattern objects with proper metadata
        4. Return ExtractionResult with patterns and quality metrics

        Args:
            context: Extraction context with source material and focus

        Returns:
            ExtractionResult containing discovered patterns

        Raises:
            ExtractionError: If extraction fails
        """
        ...

    @abstractmethod
    def estimate_cost(self, context: ExtractionContext) -> float:
        """Estimate the cost of extracting patterns from this context.

        For LLM extractors, this estimates API costs based on token count.
        For keyword extractors, this returns 0.0 (no cost).
        For hybrid extractors, this estimates the LLM portion cost.

        Args:
            context: Extraction context

        Returns:
            Estimated cost in USD (0.0 for free methods)
        """
        ...

    # Async context manager support

    async def __aenter__(self) -> PatternExtractor:
        """Enter async context manager.

        Subclasses can override to initialize resources (HTTP clients, etc.).
        Default implementation does nothing.

        Returns:
            Self for context manager protocol
        """
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object
    ) -> None:  # noqa: B027
        """Exit async context manager.

        Subclasses can override to cleanup resources (close connections, etc.).
        Default implementation does nothing.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        pass
