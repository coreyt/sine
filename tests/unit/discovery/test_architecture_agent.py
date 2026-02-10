"""Unit tests for architecture pattern discovery agent."""

from unittest.mock import AsyncMock, Mock

import pytest

from sine.discovery.agents.architecture import ArchitectureAgent
from sine.discovery.agents.base import SearchConstraints, SearchFocus
from sine.discovery.extractors.base import ExtractionResult
from sine.discovery.models import DiscoveredPattern
from sine.discovery.search import SearchResult


class TestArchitectureAgent:
    """Tests for ArchitectureAgent."""

    @pytest.fixture
    def mock_extractor(self):
        """Create a mock pattern extractor."""
        extractor = Mock()
        return extractor

    @pytest.fixture
    def mock_search_client(self):
        """Create a mock web search client."""
        client = Mock()
        return client

    @pytest.fixture
    def sample_search_result(self):
        """Create a sample search result."""
        return SearchResult(
            url="https://martinfowler.com/articles/dependency-injection.html",
            title="Dependency Injection",
            snippet="Dependency injection is a design pattern...",
            credibility=0.95,
            rank=1,
            metadata={"source": "google"},
        )

    @pytest.fixture
    def sample_pattern(self):
        """Create a sample discovered pattern."""
        from sine.discovery.models import PatternExample, PatternExamples

        return DiscoveredPattern(
            pattern_id="ARCH-DI-001",
            title="Use Dependency Injection for Loose Coupling",
            category="architecture",
            subcategory="dependency-injection",
            description="Dependency injection is a design pattern that allows you to decouple your code by injecting dependencies rather than creating them directly.",
            rationale="This pattern improves testability, maintainability, and flexibility by allowing you to swap implementations without changing the dependent code.",
            severity="info",
            confidence="high",
            discovered_by="architecture-agent",
            languages=["python", "java", "typescript"],
            tags=["solid", "ioc", "testability"],
            examples=PatternExamples(
                good=[
                    PatternExample(
                        language="python",
                        code="class UserService:\n    def __init__(self, repo: UserRepository):\n        self.repo = repo",
                    )
                ],
                bad=[
                    PatternExample(
                        language="python",
                        code="class UserService:\n    def __init__(self):\n        self.repo = UserRepository()",
                    )
                ],
            ),
            evidence={"credibility": "0.95", "rank": "1"},
        )

    @pytest.mark.asyncio
    async def test_discover_patterns_basic(
        self, mock_extractor, mock_search_client, sample_search_result, sample_pattern
    ):
        """Test basic pattern discovery."""
        # Setup mocks
        mock_search_client.search = AsyncMock(return_value=[sample_search_result])
        mock_extractor.extract_patterns = AsyncMock(
            return_value=ExtractionResult(
                patterns=[sample_pattern],
                confidence=0.8,
                method="hybrid",
            )
        )

        # Create agent
        agent = ArchitectureAgent(
            extractor=mock_extractor,
            search_client=mock_search_client,
        )

        # Define focus and constraints
        focus = SearchFocus(
            focus_type="architecture",
            description="Find dependency injection patterns",
            keywords=["dependency injection"],
        )

        constraints = SearchConstraints(max_results=10)

        # Discover patterns
        patterns = await agent.discover_patterns(focus, constraints)

        # Verify
        assert len(patterns) == 1
        assert patterns[0].pattern_id == "ARCH-DI-001"
        assert patterns[0].category == "architecture"

        # Verify search was called
        mock_search_client.search.assert_called_once()

        # Verify extractor was called
        mock_extractor.extract_patterns.assert_called_once()

    @pytest.mark.asyncio
    async def test_discover_patterns_no_search_client(self, mock_extractor):
        """Test that agent returns empty list when no search client."""
        agent = ArchitectureAgent(
            extractor=mock_extractor,
            search_client=None,  # No search client
        )

        focus = SearchFocus(
            focus_type="architecture",
            description="Find patterns",
        )

        constraints = SearchConstraints(max_results=10)

        patterns = await agent.discover_patterns(focus, constraints)

        # Should return empty list
        assert patterns == []

        # Extractor should not be called
        mock_extractor.extract_patterns.assert_not_called()

    @pytest.mark.asyncio
    async def test_filter_by_language(
        self, mock_extractor, mock_search_client, sample_search_result
    ):
        """Test filtering patterns by language."""
        from sine.discovery.models import PatternExamples

        # Create patterns with different languages
        python_pattern = DiscoveredPattern(
            pattern_id="ARCH-DSGN-001",
            title="Python Pattern",
            category="architecture",
            subcategory="design-patterns",
            description="A pattern description that is long enough to pass validation requirements.",
            rationale="This pattern improves code quality and maintainability in Python projects.",
            severity="info",
            confidence="high",
            discovered_by="test",
            languages=["python"],
            examples=PatternExamples(),
        )

        java_pattern = DiscoveredPattern(
            pattern_id="ARCH-DSGN-002",
            title="Java Pattern",
            category="architecture",
            subcategory="design-patterns",
            description="A pattern description that is long enough to pass validation requirements.",
            rationale="This pattern improves code quality and maintainability in Java projects.",
            severity="info",
            confidence="high",
            discovered_by="test",
            languages=["java"],
            examples=PatternExamples(),
        )

        agnostic_pattern = DiscoveredPattern(
            pattern_id="ARCH-DSGN-003",
            title="Language-Agnostic Pattern",
            category="architecture",
            subcategory="design-patterns",
            description="A pattern description that is long enough to pass validation requirements.",
            rationale="This pattern improves code quality and maintainability in any language.",
            severity="info",
            confidence="high",
            discovered_by="test",
            languages=[],  # Language-agnostic
            examples=PatternExamples(),
        )

        # Setup mocks
        mock_search_client.search = AsyncMock(return_value=[sample_search_result])
        mock_extractor.extract_patterns = AsyncMock(
            return_value=ExtractionResult(
                patterns=[python_pattern, java_pattern, agnostic_pattern],
                confidence=0.8,
                method="hybrid",
            )
        )

        agent = ArchitectureAgent(
            extractor=mock_extractor,
            search_client=mock_search_client,
        )

        focus = SearchFocus(
            focus_type="architecture",
            description="Find patterns",
        )

        # Filter for Python only
        constraints = SearchConstraints(
            languages=["python"],
            max_results=10,
        )

        patterns = await agent.discover_patterns(focus, constraints)

        # Should include Python pattern and agnostic pattern
        assert len(patterns) == 2
        pattern_ids = {p.pattern_id for p in patterns}
        assert "ARCH-DSGN-001" in pattern_ids  # Python
        assert "ARCH-DSGN-003" in pattern_ids  # Agnostic
        assert "ARCH-DSGN-002" not in pattern_ids  # Java (filtered out)

    @pytest.mark.asyncio
    async def test_filter_by_framework(
        self, mock_extractor, mock_search_client, sample_search_result
    ):
        """Test filtering patterns by framework."""
        from sine.discovery.models import PatternExamples

        django_pattern = DiscoveredPattern(
            pattern_id="ARCH-DSGN-001",
            title="Django Pattern",
            category="architecture",
            subcategory="design-patterns",
            description="A pattern description that is long enough to pass validation requirements.",
            rationale="This pattern improves code quality and maintainability in Django projects.",
            severity="info",
            confidence="high",
            discovered_by="test",
            framework="django",
            examples=PatternExamples(),
        )

        fastapi_pattern = DiscoveredPattern(
            pattern_id="ARCH-DSGN-002",
            title="FastAPI Pattern",
            category="architecture",
            subcategory="design-patterns",
            description="A pattern description that is long enough to pass validation requirements.",
            rationale="This pattern improves code quality and maintainability in FastAPI projects.",
            severity="info",
            confidence="high",
            discovered_by="test",
            framework="fastapi",
            examples=PatternExamples(),
        )

        # Setup mocks
        mock_search_client.search = AsyncMock(return_value=[sample_search_result])
        mock_extractor.extract_patterns = AsyncMock(
            return_value=ExtractionResult(
                patterns=[django_pattern, fastapi_pattern],
                confidence=0.8,
                method="hybrid",
            )
        )

        agent = ArchitectureAgent(
            extractor=mock_extractor,
            search_client=mock_search_client,
        )

        focus = SearchFocus(
            focus_type="architecture",
            description="Find patterns",
        )

        # Filter for Django only
        constraints = SearchConstraints(
            frameworks=["django"],
            max_results=10,
        )

        patterns = await agent.discover_patterns(focus, constraints)

        # Should include only Django pattern
        assert len(patterns) == 1
        assert patterns[0].pattern_id == "ARCH-DSGN-001"

    @pytest.mark.asyncio
    async def test_filter_by_confidence(
        self, mock_extractor, mock_search_client, sample_search_result
    ):
        """Test filtering patterns by confidence level."""
        from sine.discovery.models import PatternExamples

        high_pattern = DiscoveredPattern(
            pattern_id="ARCH-DSGN-001",
            title="High Confidence Pattern",
            category="architecture",
            subcategory="design-patterns",
            description="A pattern description that is long enough to pass validation requirements.",
            rationale="This pattern improves code quality with high confidence evidence.",
            severity="info",
            confidence="high",
            discovered_by="test",
            examples=PatternExamples(),
        )

        medium_pattern = DiscoveredPattern(
            pattern_id="ARCH-DSGN-002",
            title="Medium Confidence Pattern",
            category="architecture",
            subcategory="design-patterns",
            description="A pattern description that is long enough to pass validation requirements.",
            rationale="This pattern improves code quality with medium confidence evidence.",
            severity="info",
            confidence="medium",
            discovered_by="test",
            examples=PatternExamples(),
        )

        low_pattern = DiscoveredPattern(
            pattern_id="ARCH-DSGN-003",
            title="Low Confidence Pattern",
            category="architecture",
            subcategory="design-patterns",
            description="A pattern description that is long enough to pass validation requirements.",
            rationale="This pattern improves code quality with low confidence evidence.",
            severity="info",
            confidence="low",
            discovered_by="test",
            examples=PatternExamples(),
        )

        # Setup mocks
        mock_search_client.search = AsyncMock(return_value=[sample_search_result])
        mock_extractor.extract_patterns = AsyncMock(
            return_value=ExtractionResult(
                patterns=[high_pattern, medium_pattern, low_pattern],
                confidence=0.8,
                method="hybrid",
            )
        )

        agent = ArchitectureAgent(
            extractor=mock_extractor,
            search_client=mock_search_client,
        )

        focus = SearchFocus(
            focus_type="architecture",
            description="Find patterns",
        )

        # Filter for medium confidence or higher
        constraints = SearchConstraints(
            min_confidence="medium",
            max_results=10,
        )

        patterns = await agent.discover_patterns(focus, constraints)

        # Should include high and medium, exclude low
        assert len(patterns) == 2
        pattern_ids = {p.pattern_id for p in patterns}
        assert "ARCH-DSGN-001" in pattern_ids  # High
        assert "ARCH-DSGN-002" in pattern_ids  # Medium
        assert "ARCH-DSGN-003" not in pattern_ids  # Low (filtered out)

    @pytest.mark.asyncio
    async def test_deduplication(self, mock_extractor, mock_search_client, sample_search_result):
        """Test that duplicate patterns are removed."""
        from sine.discovery.models import PatternExamples

        # Two search results
        results = [sample_search_result, sample_search_result]

        # Same pattern from both results
        pattern1 = DiscoveredPattern(
            pattern_id="ARCH-DI-001",
            title="Dependency Injection",
            category="architecture",
            subcategory="dependency-injection",
            description="A pattern description that is long enough to pass validation requirements.",
            rationale="This pattern improves code quality and maintainability.",
            severity="info",
            confidence="high",
            discovered_by="test",
            examples=PatternExamples(),
            evidence={"credibility": "0.95"},
        )

        pattern2 = DiscoveredPattern(
            pattern_id="ARCH-DI-001",  # Same ID
            title="Dependency Injection",
            category="architecture",
            subcategory="dependency-injection",
            description="A pattern description that is long enough to pass validation requirements.",
            rationale="This pattern improves code quality and maintainability.",
            severity="info",
            confidence="medium",  # Lower confidence
            discovered_by="test",
            examples=PatternExamples(),
            evidence={"credibility": "0.80"},
        )

        # Setup mocks
        mock_search_client.search = AsyncMock(return_value=results)

        # Return different patterns for each call
        call_count = 0

        async def extract_side_effect(context):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return ExtractionResult(patterns=[pattern1], confidence=0.9, method="hybrid")
            else:
                return ExtractionResult(patterns=[pattern2], confidence=0.7, method="hybrid")

        mock_extractor.extract_patterns = AsyncMock(side_effect=extract_side_effect)

        agent = ArchitectureAgent(
            extractor=mock_extractor,
            search_client=mock_search_client,
        )

        focus = SearchFocus(
            focus_type="architecture",
            description="Find patterns",
        )

        constraints = SearchConstraints(max_results=10)

        patterns = await agent.discover_patterns(focus, constraints)

        # Should have only 1 pattern (deduplicated)
        assert len(patterns) == 1
        # Should keep the one with higher confidence
        assert patterns[0].confidence == "high"

    @pytest.mark.asyncio
    async def test_max_results_limit(
        self, mock_extractor, mock_search_client, sample_search_result
    ):
        """Test that max_results is respected."""
        from sine.discovery.models import PatternExamples

        # Create 5 different patterns
        patterns = []
        for i in range(5):
            pattern = DiscoveredPattern(
                pattern_id=f"ARCH-DSGN-{i:03d}",
                title=f"Pattern {i}",
                category="architecture",
                subcategory="design-patterns",
                description="A pattern description that is long enough to pass validation requirements.",
                rationale="This pattern improves code quality and maintainability.",
                severity="info",
                confidence="high",
                discovered_by="test",
                examples=PatternExamples(),
            )
            patterns.append(pattern)

        # Setup mocks
        mock_search_client.search = AsyncMock(return_value=[sample_search_result])
        mock_extractor.extract_patterns = AsyncMock(
            return_value=ExtractionResult(
                patterns=patterns,
                confidence=0.8,
                method="hybrid",
            )
        )

        agent = ArchitectureAgent(
            extractor=mock_extractor,
            search_client=mock_search_client,
        )

        focus = SearchFocus(
            focus_type="architecture",
            description="Find patterns",
        )

        # Limit to 3 results
        constraints = SearchConstraints(max_results=3)

        results = await agent.discover_patterns(focus, constraints)

        # Should have only 3 results
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_query_includes_keywords(self, mock_extractor, mock_search_client):
        """Test that search query includes focus keywords."""
        mock_search_client.search = AsyncMock(return_value=[])

        agent = ArchitectureAgent(
            extractor=mock_extractor,
            search_client=mock_search_client,
        )

        focus = SearchFocus(
            focus_type="architecture",
            description="Find singleton patterns",
            keywords=["singleton", "design pattern"],
        )

        constraints = SearchConstraints(max_results=10)

        await agent.discover_patterns(focus, constraints)

        # Verify search was called
        mock_search_client.search.assert_called_once()

        # Check the search query
        search_query = mock_search_client.search.call_args[0][0]
        assert "singleton" in search_query.query.lower()
        assert search_query.focus_type == "architecture"

    @pytest.mark.asyncio
    async def test_trusted_domains_used(self, mock_extractor, mock_search_client):
        """Test that trusted domains are used in search query."""
        mock_search_client.search = AsyncMock(return_value=[])

        agent = ArchitectureAgent(
            extractor=mock_extractor,
            search_client=mock_search_client,
        )

        focus = SearchFocus(
            focus_type="architecture",
            description="Find patterns",
        )

        constraints = SearchConstraints(max_results=10)

        await agent.discover_patterns(focus, constraints)

        # Check the search query has trusted domains
        search_query = mock_search_client.search.call_args[0][0]
        assert len(search_query.allowed_domains) > 0
        assert "martinfowler.com" in search_query.allowed_domains
        assert "refactoring.guru" in search_query.allowed_domains
