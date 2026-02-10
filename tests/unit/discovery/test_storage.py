"""Tests for pattern storage.

Test cases:
- TC-PD-010: Save and load patterns
- TC-PD-011: Pattern ID to path mapping
- TC-PD-012: List patterns by category
- TC-PD-013: Error handling for corrupted files
- TC-PD-014: Pattern existence checks
"""

from pathlib import Path

import pytest

from sine.discovery.models import (
    DiscoveredPattern,
    PatternExample,
    PatternExamples,
    ValidatedPattern,
)
from sine.discovery.storage import PatternStorage


class TestPatternStorage:
    """TC-PD-010: Save and load patterns."""

    def test_save_and_load_pattern(self, tmp_path: Path) -> None:
        """Test saving and loading a pattern."""
        storage = PatternStorage(tmp_path)

        pattern = DiscoveredPattern(
            pattern_id="ARCH-DI-001",
            title="Use DI Pattern",
            category="architecture",
            description="Use dependency injection for better testability",
            rationale="Testability and maintainability",
            confidence="high",
            examples=PatternExamples(),
            discovered_by="test",
        )

        storage.save_pattern(pattern, stage="raw")
        loaded = storage.load_pattern("ARCH-DI-001", stage="raw", model_class=DiscoveredPattern)

        assert loaded is not None
        assert loaded.pattern_id == "ARCH-DI-001"
        assert loaded.title == "Use DI Pattern"

    def test_load_nonexistent_pattern_returns_none(self, tmp_path: Path) -> None:
        """Test loading nonexistent pattern returns None."""
        storage = PatternStorage(tmp_path)

        result = storage.load_pattern(
            "NONEXISTENT-XXX-999", stage="raw", model_class=DiscoveredPattern
        )

        assert result is None

    def test_save_creates_directory_structure(self, tmp_path: Path) -> None:
        """Test that saving creates the necessary directory structure."""
        storage = PatternStorage(tmp_path)

        pattern = DiscoveredPattern(
            pattern_id="SEC-AUTH-001",
            title="Test Security Pattern",
            category="security",
            description="Test description that is long enough",
            rationale="Test rationale that is long enough",
            confidence="high",
            examples=PatternExamples(),
            discovered_by="test",
        )

        storage.save_pattern(pattern, stage="raw")

        # Check directory exists
        expected_path = tmp_path / "raw" / "security" / "authentication"
        assert expected_path.exists()
        assert expected_path.is_dir()


class TestPatternIDMapping:
    """TC-PD-011: Pattern ID to path mapping."""

    @pytest.mark.parametrize(
        "pattern_id,expected_category,expected_subcat",
        [
            ("ARCH-DI-001", "architecture", "dependency-injection"),
            ("SEC-AUTH-042", "security", "authentication"),
            ("PY-DJANGO-001", "languages/python/frameworks", "django"),
            ("PERF-CACHE-001", "performance", "caching"),
        ],
    )
    def test_parse_pattern_id(
        self, tmp_path: Path, pattern_id: str, expected_category: str, expected_subcat: str
    ) -> None:
        """Test pattern ID parsing into category paths."""
        storage = PatternStorage(tmp_path)

        category, subcategory = storage._parse_pattern_id(pattern_id)

        assert category == expected_category
        assert subcategory == expected_subcat

    def test_pattern_path_creation(self, tmp_path: Path) -> None:
        """Test that pattern paths are created correctly."""
        storage = PatternStorage(tmp_path)

        path = storage._get_pattern_path("ARCH-DI-001", stage="raw", create_dirs=True)

        assert path.parent.exists()
        assert "architecture" in str(path)
        assert "dependency-injection" in str(path)
        assert path.name == "ARCH-DI-001.json"

    def test_invalid_pattern_id_raises_error(self, tmp_path: Path) -> None:
        """Test that invalid pattern IDs raise ValueError."""
        storage = PatternStorage(tmp_path)

        with pytest.raises(ValueError, match="Invalid pattern ID format"):
            storage._parse_pattern_id("INVALID")


class TestListPatterns:
    """TC-PD-012: List patterns by category."""

    def test_list_all_patterns(self, tmp_path: Path) -> None:
        """Test listing all patterns in a stage."""
        storage = PatternStorage(tmp_path)

        # Create multiple patterns
        for i in range(3):
            pattern = DiscoveredPattern(
                pattern_id=f"ARCH-DI-{i:03d}",
                title=f"Pattern {i}",
                category="architecture",
                description="Test description that is long enough",
                rationale="Test rationale that is long enough",
                confidence="high",
                examples=PatternExamples(),
                discovered_by="test",
            )
            storage.save_pattern(pattern, stage="raw")

        results = storage.list_patterns(stage="raw")

        assert len(results) == 3
        assert all(r.category == "architecture" for r in results)

    def test_list_patterns_by_category(self, tmp_path: Path) -> None:
        """Test filtering patterns by category."""
        storage = PatternStorage(tmp_path)

        # Create patterns in different categories
        arch_pattern = DiscoveredPattern(
            pattern_id="ARCH-DI-001",
            title="Arch Pattern",
            category="architecture",
            description="Test description that is long enough",
            rationale="Test rationale that is long enough",
            confidence="high",
            examples=PatternExamples(),
            discovered_by="test",
        )
        sec_pattern = DiscoveredPattern(
            pattern_id="SEC-AUTH-001",
            title="Sec Pattern",
            category="security",
            description="Test description that is long enough",
            rationale="Test rationale that is long enough",
            confidence="high",
            examples=PatternExamples(),
            discovered_by="test",
        )

        storage.save_pattern(arch_pattern, stage="raw")
        storage.save_pattern(sec_pattern, stage="raw")

        # List only architecture patterns
        results = storage.list_patterns(stage="raw", category="architecture")

        assert len(results) == 1
        assert results[0].pattern_id == "ARCH-DI-001"

    def test_list_patterns_empty_directory(self, tmp_path: Path) -> None:
        """Test listing patterns from empty directory."""
        storage = PatternStorage(tmp_path)

        results = storage.list_patterns(stage="raw")

        assert results == []

    def test_list_patterns_with_tier_and_confidence(self, tmp_path: Path) -> None:
        """Test that listed patterns include tier and confidence."""
        storage = PatternStorage(tmp_path)

        pattern = DiscoveredPattern(
            pattern_id="SEC-AUTH-001",
            title="Security Pattern",
            category="security",
            description="Test description that is long enough",
            rationale="Test rationale that is long enough",
            severity="error",
            confidence="high",
            examples=PatternExamples(),
            discovered_by="test",
        )

        storage.save_pattern(pattern, stage="raw")
        results = storage.list_patterns(stage="raw")

        assert len(results) == 1
        assert results[0].tier == 1  # error + high confidence
        assert results[0].confidence == "high"


class TestErrorHandling:
    """TC-PD-013: Error handling for corrupted files."""

    def test_load_corrupted_json_returns_none(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test loading corrupted JSON returns None and logs warning."""
        storage = PatternStorage(tmp_path)

        # Create corrupted file
        corrupted_path = storage._get_pattern_path("ARCH-DI-001", stage="raw", create_dirs=True)
        corrupted_path.write_text("{ invalid json", encoding="utf-8")

        result = storage.load_pattern("ARCH-DI-001", stage="raw", model_class=DiscoveredPattern)

        assert result is None
        assert "Failed to load pattern" in caplog.text

    def test_list_patterns_skips_corrupted_files(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that list_patterns skips corrupted files and logs warnings."""
        storage = PatternStorage(tmp_path)

        # Create one valid pattern
        valid_pattern = DiscoveredPattern(
            pattern_id="ARCH-DI-001",
            title="Valid",
            category="architecture",
            description="Test description that is long enough",
            rationale="Test rationale that is long enough",
            confidence="high",
            examples=PatternExamples(),
            discovered_by="test",
        )
        storage.save_pattern(valid_pattern, stage="raw")

        # Create one corrupted file
        corrupted_path = storage._get_pattern_path("ARCH-DI-002", stage="raw", create_dirs=True)
        corrupted_path.write_text("{ corrupted }", encoding="utf-8")

        results = storage.list_patterns(stage="raw")

        # Should only return the valid pattern
        assert len(results) == 1
        assert results[0].pattern_id == "ARCH-DI-001"

        # Should log warning about corrupted file
        assert "Failed to load pattern" in caplog.text


class TestPatternExistence:
    """TC-PD-014: Pattern existence checks."""

    def test_pattern_exists_returns_true_when_present(self, tmp_path: Path) -> None:
        """Test that pattern_exists returns True for existing patterns."""
        storage = PatternStorage(tmp_path)

        pattern = DiscoveredPattern(
            pattern_id="ARCH-DI-001",
            title="Test Pattern",
            category="architecture",
            description="Test description that is long enough",
            rationale="Test rationale that is long enough",
            confidence="high",
            examples=PatternExamples(),
            discovered_by="test",
        )
        storage.save_pattern(pattern, stage="raw")

        assert storage.pattern_exists("ARCH-DI-001", stage="raw") is True

    def test_pattern_exists_returns_false_when_absent(self, tmp_path: Path) -> None:
        """Test that pattern_exists returns False for missing patterns."""
        storage = PatternStorage(tmp_path)

        assert storage.pattern_exists("NONEXISTENT-XXX-999", stage="raw") is False


class TestDeletePattern:
    """Test pattern deletion."""

    def test_delete_existing_pattern(self, tmp_path: Path) -> None:
        """Test deleting an existing pattern."""
        storage = PatternStorage(tmp_path)

        pattern = DiscoveredPattern(
            pattern_id="ARCH-DI-001",
            title="Test Pattern",
            category="architecture",
            description="Test description that is long enough",
            rationale="Test rationale that is long enough",
            confidence="high",
            examples=PatternExamples(),
            discovered_by="test",
        )
        storage.save_pattern(pattern, stage="raw")

        result = storage.delete_pattern("ARCH-DI-001", stage="raw")

        assert result is True
        assert not storage.pattern_exists("ARCH-DI-001", stage="raw")

    def test_delete_nonexistent_pattern(self, tmp_path: Path) -> None:
        """Test deleting a nonexistent pattern returns False."""
        storage = PatternStorage(tmp_path)

        result = storage.delete_pattern("NONEXISTENT-XXX-999", stage="raw")

        assert result is False


class TestLoadCategory:
    """Test loading patterns by category."""

    def test_load_category_patterns(self, tmp_path: Path) -> None:
        """Test loading all patterns in a category."""
        storage = PatternStorage(tmp_path)

        # Create patterns in architecture category
        for i in range(2):
            pattern = DiscoveredPattern(
                pattern_id=f"ARCH-DI-{i:03d}",
                title=f"Pattern {i}",
                category="architecture",
                description="Test description that is long enough",
                rationale="Test rationale that is long enough",
                confidence="high",
                examples=PatternExamples(),
                discovered_by="test",
            )
            storage.save_pattern(pattern, stage="raw")

        # Create pattern in security category
        sec_pattern = DiscoveredPattern(
            pattern_id="SEC-AUTH-001",
            title="Security Pattern",
            category="security",
            description="Test description that is long enough",
            rationale="Test rationale that is long enough",
            confidence="high",
            examples=PatternExamples(),
            discovered_by="test",
        )
        storage.save_pattern(sec_pattern, stage="raw")

        # Load only architecture patterns
        patterns = storage.load_category("architecture", stage="raw", model_class=DiscoveredPattern)

        assert len(patterns) == 2
        assert all(p.category == "architecture" for p in patterns)

    def test_load_category_empty(self, tmp_path: Path) -> None:
        """Test loading from empty category."""
        storage = PatternStorage(tmp_path)

        patterns = storage.load_category("architecture", stage="raw", model_class=DiscoveredPattern)

        assert patterns == []


class TestValidatedPatternStorage:
    """Test storage operations for ValidatedPattern."""

    def test_save_and_load_validated_pattern(
        self, tmp_path: Path, sample_discovered_pattern: DiscoveredPattern
    ) -> None:
        """Test saving and loading a validated pattern."""
        storage = PatternStorage(tmp_path)

        validated = ValidatedPattern.from_discovered(
            pattern=sample_discovered_pattern,
            validated_by="reviewer@example.com",
            review_notes="Approved",
        )

        storage.save_pattern(validated, stage="validated")
        loaded = storage.load_pattern(
            "ARCH-DI-001", stage="validated", model_class=ValidatedPattern
        )

        assert loaded is not None
        assert loaded.discovered.pattern_id == "ARCH-DI-001"
        assert loaded.validation.validated_by == "reviewer@example.com"

    def test_list_validated_patterns_includes_tier(
        self, tmp_path: Path, sample_discovered_pattern: DiscoveredPattern
    ) -> None:
        """Test that listing validated patterns includes effective tier."""
        storage = PatternStorage(tmp_path)

        validated = ValidatedPattern.from_discovered(
            pattern=sample_discovered_pattern,
            validated_by="reviewer",
            tier_override=1,
        )

        storage.save_pattern(validated, stage="validated")
        results = storage.list_patterns(stage="validated")

        assert len(results) == 1
        assert results[0].tier == 1


# ============================================================================
# Fixtures
# ============================================================================


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
