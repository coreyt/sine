"""Tests for pattern discovery models.

Test cases:
- TC-PD-001: DiscoveredPattern validation
- TC-PD-002: Pattern ID format validation
- TC-PD-003: Tier inference
- TC-PD-004: ValidatedPattern creation
- TC-PD-005: CompiledPattern creation
"""

import pytest
from pydantic import ValidationError

from sine.discovery.models import (
    CompiledPattern,
    DiscoveredPattern,
    PatternExample,
    PatternExamples,
    SemgrepRule,
    ValidatedPattern,
)


class TestDiscoveredPattern:
    """TC-PD-001: DiscoveredPattern validation."""

    def test_valid_pattern_parses(self) -> None:
        """Test that a valid pattern passes validation."""
        pattern = DiscoveredPattern(
            pattern_id="ARCH-DI-001",
            title="Use Dependency Injection",
            category="architecture",
            subcategory="dependency-injection",
            description="Services should use constructor injection.",
            rationale="Improves testability and loose coupling.",
            severity="warning",
            confidence="high",
            examples=PatternExamples(
                good=[PatternExample(language="python", code="def __init__(self, repo: IRepo):")],
                bad=[PatternExample(language="python", code="self.repo = ConcreteRepo()")],
            ),
            discovered_by="codebase-analyzer",
        )

        assert pattern.pattern_id == "ARCH-DI-001"
        assert pattern.category == "architecture"
        assert pattern.severity == "warning"
        assert pattern.confidence == "high"

    def test_invalid_pattern_id_fails(self) -> None:
        """Test that invalid pattern ID format fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            DiscoveredPattern(
                pattern_id="INVALID",  # Wrong format
                title="Test Pattern",
                category="test",
                description="Test pattern that is long enough for validation",
                rationale="Testing pattern validation with proper length",
                confidence="high",
                examples=PatternExamples(),
                discovered_by="test",
            )

        # Pydantic regex validation happens first
        assert "pattern" in str(exc_info.value).lower()

    def test_extra_fields_forbidden(self) -> None:
        """Test that extra fields are rejected (extra=forbid)."""
        with pytest.raises(ValidationError) as exc_info:
            DiscoveredPattern(
                pattern_id="ARCH-DI-001",
                title="Test",
                category="test",
                description="Test description that is long enough",
                rationale="Test rationale that is long enough",
                confidence="high",
                examples=PatternExamples(),
                discovered_by="test",
                unknown_field="value",  # Should fail
            )

        assert "Extra inputs are not permitted" in str(exc_info.value)

    def test_title_too_short_fails(self) -> None:
        """Test that title < 5 chars fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            DiscoveredPattern(
                pattern_id="ARCH-DI-001",
                title="ABC",  # Too short
                category="test",
                description="Test description that is long enough",
                rationale="Test rationale that is long enough",
                confidence="high",
                examples=PatternExamples(),
                discovered_by="test",
            )

        assert "at least 5 characters" in str(exc_info.value).lower()

    def test_description_too_short_fails(self) -> None:
        """Test that description < 20 chars fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            DiscoveredPattern(
                pattern_id="ARCH-DI-001",
                title="Test Pattern",
                category="test",
                description="Short",  # Too short
                rationale="Test rationale that is long enough",
                confidence="high",
                examples=PatternExamples(),
                discovered_by="test",
            )

        assert "at least 20 characters" in str(exc_info.value).lower()


class TestPatternIDValidation:
    """TC-PD-002: Pattern ID format validation."""

    @pytest.mark.parametrize(
        "pattern_id",
        [
            "ARCH-DI-001",
            "SEC-AUTH-042",
            "PY-DJANGO-999",
            "PERF-CACHE-123",
        ],
    )
    def test_valid_pattern_ids(self, pattern_id: str) -> None:
        """Test valid pattern ID formats."""
        pattern = DiscoveredPattern(
            pattern_id=pattern_id,
            title="Test Pattern",
            category="test",
            description="Test description that is long enough",
            rationale="Test rationale that is long enough",
            confidence="high",
            examples=PatternExamples(),
            discovered_by="test",
        )
        assert pattern.pattern_id == pattern_id

    @pytest.mark.parametrize(
        "pattern_id",
        [
            "ARCH-001",  # Missing third part
            "ARCH-DI-1",  # Only 1 digit
            "ARCH-DI-ABCD",  # Letters instead of numbers
            "arch-di-001",  # Lowercase
            "ARCH_DI_001",  # Underscore instead of hyphen
        ],
    )
    def test_invalid_pattern_ids(self, pattern_id: str) -> None:
        """Test invalid pattern ID formats."""
        with pytest.raises(ValidationError) as exc_info:
            DiscoveredPattern(
                pattern_id=pattern_id,
                title="Test Pattern",
                category="test",
                description="Test description that is long enough",
                rationale="Test rationale that is long enough",
                confidence="high",
                examples=PatternExamples(),
                discovered_by="test",
            )

        # All should fail Pydantic's regex pattern validation
        error_str = str(exc_info.value).lower()
        assert "pattern" in error_str or "string_pattern_mismatch" in error_str


class TestTierInference:
    """TC-PD-003: Tier inference logic."""

    def test_tier_1_inferred_from_high_confidence_error(self) -> None:
        """Test that error + high confidence → Tier 1."""
        pattern = DiscoveredPattern(
            pattern_id="SEC-AUTH-001",
            title="Test Security Pattern",
            category="security",
            description="Test description that is long enough",
            rationale="Test rationale that is long enough",
            severity="error",
            confidence="high",
            examples=PatternExamples(),
            discovered_by="test",
        )

        assert pattern.infer_tier() == 1

    def test_tier_3_inferred_from_framework(self) -> None:
        """Test that framework-specific patterns → Tier 3."""
        pattern = DiscoveredPattern(
            pattern_id="PY-DJANGO-001",
            title="Test Django Pattern",
            category="frameworks",
            description="Test description that is long enough",
            rationale="Test rationale that is long enough",
            framework="django",
            confidence="medium",
            examples=PatternExamples(),
            discovered_by="test",
        )

        assert pattern.infer_tier() == 3

    def test_tier_2_default(self) -> None:
        """Test that other patterns default to Tier 2."""
        pattern = DiscoveredPattern(
            pattern_id="ARCH-DI-001",
            title="Test Architecture Pattern",
            category="architecture",
            description="Test description that is long enough",
            rationale="Test rationale that is long enough",
            severity="warning",
            confidence="medium",
            examples=PatternExamples(),
            discovered_by="test",
        )

        assert pattern.infer_tier() == 2

    def test_tier_2_for_error_with_low_confidence(self) -> None:
        """Test that error + low confidence → Tier 2 (not Tier 1)."""
        pattern = DiscoveredPattern(
            pattern_id="SEC-AUTH-001",
            title="Test Security Pattern",
            category="security",
            description="Test description that is long enough",
            rationale="Test rationale that is long enough",
            severity="error",
            confidence="low",  # Not high
            examples=PatternExamples(),
            discovered_by="test",
        )

        assert pattern.infer_tier() == 2


class TestValidatedPattern:
    """TC-PD-004: ValidatedPattern creation."""

    def test_from_discovered_creates_validated_pattern(
        self, sample_discovered_pattern: DiscoveredPattern
    ) -> None:
        """Test creating a validated pattern from discovered."""
        validated = ValidatedPattern.from_discovered(
            pattern=sample_discovered_pattern,
            validated_by="reviewer@example.com",
            review_notes="Looks good",
        )

        assert validated.discovered.pattern_id == "ARCH-DI-001"
        assert validated.validation.validated_by == "reviewer@example.com"
        assert validated.validation.review_notes == "Looks good"
        assert validated.effective_tier == 2

    def test_tier_override_takes_precedence(
        self, sample_discovered_pattern: DiscoveredPattern
    ) -> None:
        """Test that manual tier override is respected."""
        validated = ValidatedPattern.from_discovered(
            pattern=sample_discovered_pattern,
            validated_by="reviewer",
            tier_override=1,  # Override to Tier 1
        )

        assert validated.effective_tier == 1
        assert validated.validation.tier_override == 1

    def test_inferred_tier_used_when_no_override(
        self, sample_discovered_pattern: DiscoveredPattern
    ) -> None:
        """Test that inferred tier is used when no override provided."""
        validated = ValidatedPattern.from_discovered(
            pattern=sample_discovered_pattern,
            validated_by="reviewer",
        )

        expected_tier = sample_discovered_pattern.infer_tier()
        assert validated.effective_tier == expected_tier


class TestCompiledPattern:
    """TC-PD-005: CompiledPattern creation."""

    def test_from_validated_creates_compiled_pattern(
        self, sample_validated_pattern: ValidatedPattern
    ) -> None:
        """Test creating a compiled pattern from validated."""
        semgrep_rule = SemgrepRule(
            rule_id="arch-di-001-python",
            language="python",
            pattern="class $CLASS: ...",
            message="Use dependency injection",
            severity="WARNING",
        )

        compiled = CompiledPattern.from_validated(
            pattern=sample_validated_pattern,
            semgrep_rules=[semgrep_rule],
            compilation_notes="Compiled successfully",
        )

        assert compiled.validated.discovered.pattern_id == "ARCH-DI-001"
        assert len(compiled.semgrep_rules) == 1
        assert compiled.semgrep_rules[0].rule_id == "arch-di-001-python"
        assert compiled.compilation.compilation_notes == "Compiled successfully"

    def test_compiled_pattern_preserves_tier(
        self, sample_validated_pattern: ValidatedPattern
    ) -> None:
        """Test that compiled pattern preserves effective tier."""
        compiled = CompiledPattern.from_validated(
            pattern=sample_validated_pattern,
            semgrep_rules=[],
        )

        assert compiled.validated.effective_tier == sample_validated_pattern.effective_tier


class TestPatternExamples:
    """Test PatternExample and PatternExamples models."""

    def test_pattern_example_creation(self) -> None:
        """Test creating a pattern example."""
        example = PatternExample(
            language="python",
            code="def __init__(self, repo):",
            description="Constructor injection",
        )

        assert example.language == "python"
        assert example.code == "def __init__(self, repo):"
        assert example.description == "Constructor injection"

    def test_pattern_examples_with_good_and_bad(self) -> None:
        """Test PatternExamples with good and bad examples."""
        examples = PatternExamples(
            good=[PatternExample(language="python", code="good_code()")],
            bad=[PatternExample(language="python", code="bad_code()")],
        )

        assert len(examples.good) == 1
        assert len(examples.bad) == 1
        assert examples.good[0].code == "good_code()"
        assert examples.bad[0].code == "bad_code()"

    def test_pattern_examples_can_be_empty(self) -> None:
        """Test that PatternExamples can have empty lists."""
        examples = PatternExamples()

        assert examples.good == []
        assert examples.bad == []


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


@pytest.fixture
def sample_validated_pattern(sample_discovered_pattern: DiscoveredPattern) -> ValidatedPattern:
    """Sample validated pattern for testing."""
    return ValidatedPattern.from_discovered(
        pattern=sample_discovered_pattern,
        validated_by="reviewer@example.com",
        review_notes="Approved",
    )
