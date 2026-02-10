import pytest
from sine.discovery.models import (
    DiscoveredPattern,
    PatternExample,
    PatternExamples,
    ValidatedPattern,
)

@pytest.fixture
def sample_discovered_pattern() -> DiscoveredPattern:
    """Sample discovered pattern for testing."""
    return DiscoveredPattern(
        pattern_id="ARCH-DI-001",
        title="Use Dependency Injection",
        category="architecture",
        subcategory="dependency-injection",
        description="Services should use constructor injection for dependencies.",
        rationale="Improves testability and enables loose coupling.",
        severity="warning",
        confidence="high",
        examples=PatternExamples(
            good=[PatternExample(language="python", code="def __init__(self, repo):")],
            bad=[PatternExample(language="python", code="self.repo = ConcreteRepo()")],
        ),
        discovered_by="codebase-analyzer",
    )


@pytest.fixture
def sample_validated_pattern(sample_discovered_pattern: DiscoveredPattern) -> ValidatedPattern:
    """Sample validated pattern for testing."""
    return ValidatedPattern.from_discovered(
        pattern=sample_discovered_pattern,
        validated_by="reviewer@example.com",
        review_notes="Approved",
    )
