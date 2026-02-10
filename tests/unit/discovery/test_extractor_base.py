"""Unit tests for extractor base classes and data models."""

import pytest

from sine.discovery.agents.base import SearchFocus
from sine.discovery.extractors.base import (
    ExtractionContext,
    ExtractionResult,
    PatternExtractor,
)


class TestExtractionContext:
    """Tests for ExtractionContext dataclass."""

    def test_creation_with_required_fields(self):
        """Test creating ExtractionContext with required fields."""
        focus = SearchFocus(
            focus_type="architecture",
            description="Test focus",
        )
        context = ExtractionContext(
            source_url="https://example.com",
            source_text="Test content",
            focus=focus,
        )

        assert context.source_url == "https://example.com"
        assert context.source_text == "Test content"
        assert context.focus == focus
        assert context.metadata == {}

    def test_creation_with_metadata(self):
        """Test creating ExtractionContext with metadata."""
        focus = SearchFocus(
            focus_type="security",
            description="Test focus",
        )
        metadata = {"credibility": 0.95, "author": "John Doe"}
        context = ExtractionContext(
            source_url="https://example.com",
            source_text="Test content",
            focus=focus,
            metadata=metadata,
        )

        assert context.metadata == metadata
        assert context.metadata["credibility"] == 0.95

    def test_immutability(self):
        """Test that ExtractionContext is immutable (frozen)."""
        focus = SearchFocus(
            focus_type="architecture",
            description="Test focus",
        )
        context = ExtractionContext(
            source_url="https://example.com",
            source_text="Test content",
            focus=focus,
        )

        with pytest.raises(AttributeError):
            context.source_url = "https://different.com"  # type: ignore


class TestExtractionResult:
    """Tests for ExtractionResult dataclass."""

    def test_creation_with_required_fields(self, sample_discovered_pattern):
        """Test creating ExtractionResult with required fields."""
        result = ExtractionResult(
            patterns=[sample_discovered_pattern],
            confidence=0.85,
            method="keyword",
        )

        assert len(result.patterns) == 1
        assert result.patterns[0] == sample_discovered_pattern
        assert result.confidence == 0.85
        assert result.method == "keyword"
        assert result.metadata == {}

    def test_creation_with_metadata(self, sample_discovered_pattern):
        """Test creating ExtractionResult with metadata."""
        metadata = {"token_count": 1500, "processing_time": 2.5}
        result = ExtractionResult(
            patterns=[sample_discovered_pattern],
            confidence=0.90,
            method="llm",
            metadata=metadata,
        )

        assert result.metadata == metadata
        assert result.metadata["token_count"] == 1500

    def test_empty_patterns_list(self):
        """Test ExtractionResult with no patterns found."""
        result = ExtractionResult(
            patterns=[],
            confidence=0.0,
            method="keyword",
        )

        assert result.patterns == []
        assert result.confidence == 0.0

    def test_immutability(self, sample_discovered_pattern):
        """Test that ExtractionResult is immutable (frozen)."""
        result = ExtractionResult(
            patterns=[sample_discovered_pattern],
            confidence=0.85,
            method="keyword",
        )

        with pytest.raises(AttributeError):
            result.confidence = 0.95  # type: ignore


class TestPatternExtractor:
    """Tests for PatternExtractor abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that PatternExtractor cannot be instantiated directly."""
        with pytest.raises(TypeError):
            PatternExtractor()  # type: ignore

    def test_subclass_must_implement_abstract_methods(self):
        """Test that subclasses must implement all abstract methods."""

        class IncompleteExtractor(PatternExtractor):
            """Extractor missing required methods."""

        with pytest.raises(TypeError):
            IncompleteExtractor()  # type: ignore

    @pytest.mark.asyncio
    async def test_concrete_implementation(self, sample_discovered_pattern):
        """Test a concrete implementation of PatternExtractor."""

        class ConcreteExtractor(PatternExtractor):
            """Minimal concrete extractor for testing."""

            async def extract_patterns(self, context: ExtractionContext) -> ExtractionResult:
                return ExtractionResult(
                    patterns=[sample_discovered_pattern],
                    confidence=1.0,
                    method="test",
                )

            def estimate_cost(self, context: ExtractionContext) -> float:
                return 0.0

        extractor = ConcreteExtractor()
        focus = SearchFocus(focus_type="test", description="Test")
        context = ExtractionContext(
            source_url="https://example.com",
            source_text="Test",
            focus=focus,
        )

        result = await extractor.extract_patterns(context)
        assert len(result.patterns) == 1
        assert result.confidence == 1.0
        assert result.method == "test"

        cost = extractor.estimate_cost(context)
        assert cost == 0.0

    @pytest.mark.asyncio
    async def test_async_context_manager_protocol(self, sample_discovered_pattern):
        """Test that PatternExtractor supports async context manager."""

        class ContextManagedExtractor(PatternExtractor):
            """Extractor with context manager support."""

            def __init__(self):
                self.initialized = False
                self.cleaned_up = False

            async def __aenter__(self):
                self.initialized = True
                return await super().__aenter__()

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                self.cleaned_up = True
                await super().__aexit__(exc_type, exc_val, exc_tb)

            async def extract_patterns(self, context: ExtractionContext) -> ExtractionResult:
                return ExtractionResult(
                    patterns=[sample_discovered_pattern],
                    confidence=1.0,
                    method="test",
                )

            def estimate_cost(self, context: ExtractionContext) -> float:
                return 0.0

        extractor = ContextManagedExtractor()
        assert not extractor.initialized
        assert not extractor.cleaned_up

        async with extractor:
            assert extractor.initialized
            assert not extractor.cleaned_up

        assert extractor.cleaned_up

    @pytest.mark.asyncio
    async def test_default_context_manager_implementation(self, sample_discovered_pattern):
        """Test that default __aenter__ and __aexit__ work."""

        class MinimalExtractor(PatternExtractor):
            """Extractor using default context manager."""

            async def extract_patterns(self, context: ExtractionContext) -> ExtractionResult:
                return ExtractionResult(
                    patterns=[sample_discovered_pattern],
                    confidence=1.0,
                    method="test",
                )

            def estimate_cost(self, context: ExtractionContext) -> float:
                return 0.0

        # Should work without errors
        async with MinimalExtractor() as extractor:
            focus = SearchFocus(focus_type="test", description="Test")
            context = ExtractionContext(
                source_url="https://example.com",
                source_text="Test",
                focus=focus,
            )
            result = await extractor.extract_patterns(context)
            assert len(result.patterns) == 1
