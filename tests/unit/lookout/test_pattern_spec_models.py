"""Tests for hierarchical PatternSpec models (schema_version 2)."""

from __future__ import annotations

import pytest
import yaml
from pydantic import ValidationError

from lookout.models import (
    ForbiddenCheck,
    FrameworkVariant,
    GenericVariant,
    LanguageVariant,
    PatternDiscoveryCheck,
    PatternSpec,
    PatternSpecFile,
    RawCheck,
    RuleReporting,
    VariantExamples,
)


def _minimal_reporting() -> RuleReporting:
    return RuleReporting(
        default_message="Test message",
        confidence="high",
    )


def _minimal_variant() -> LanguageVariant:
    return LanguageVariant(
        language="python",
        generic=GenericVariant(
            check=ForbiddenCheck(type="forbidden", pattern="eval($X)"),
            examples=VariantExamples(
                good=[],
                bad=[],
            ),
        ),
    )


class TestVariantExamples:
    def test_defaults_to_empty_lists(self) -> None:
        examples = VariantExamples()
        assert examples.good == []
        assert examples.bad == []


class TestGenericVariant:
    def test_requires_check_and_examples(self) -> None:
        variant = GenericVariant(
            check=ForbiddenCheck(type="forbidden", pattern="eval($X)"),
            examples=VariantExamples(),
        )
        assert variant.check.type == "forbidden"

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            GenericVariant(
                check=ForbiddenCheck(type="forbidden", pattern="eval($X)"),
                examples=VariantExamples(),
                extra_field="nope",  # type: ignore[call-arg]
            )


class TestFrameworkVariant:
    def test_requires_name_check_examples(self) -> None:
        variant = FrameworkVariant(
            name="django",
            check=ForbiddenCheck(type="forbidden", pattern="eval($X)"),
            examples=VariantExamples(),
        )
        assert variant.name == "django"
        assert variant.version_constraint is None

    def test_accepts_version_constraint(self) -> None:
        variant = FrameworkVariant(
            name="django",
            version_constraint=">=4.0,<5.0",
            check=ForbiddenCheck(type="forbidden", pattern="eval($X)"),
            examples=VariantExamples(),
        )
        assert variant.version_constraint == ">=4.0,<5.0"


class TestLanguageVariant:
    def test_minimal_with_generic(self) -> None:
        variant = _minimal_variant()
        assert variant.language == "python"
        assert variant.generic is not None
        assert variant.frameworks == []

    def test_accepts_version_constraint(self) -> None:
        variant = LanguageVariant(
            language="python",
            version_constraint=">=3.10",
            generic=GenericVariant(
                check=ForbiddenCheck(type="forbidden", pattern="eval($X)"),
                examples=VariantExamples(),
            ),
        )
        assert variant.version_constraint == ">=3.10"

    def test_with_frameworks(self) -> None:
        variant = LanguageVariant(
            language="python",
            generic=None,
            frameworks=[
                FrameworkVariant(
                    name="django",
                    check=ForbiddenCheck(type="forbidden", pattern="eval($X)"),
                    examples=VariantExamples(),
                ),
                FrameworkVariant(
                    name="fastapi",
                    check=ForbiddenCheck(type="forbidden", pattern="eval($X)"),
                    examples=VariantExamples(),
                ),
            ],
        )
        assert len(variant.frameworks) == 2
        assert variant.generic is None

    def test_both_generic_and_frameworks(self) -> None:
        variant = LanguageVariant(
            language="typescript",
            generic=GenericVariant(
                check=ForbiddenCheck(type="forbidden", pattern="eval($X)"),
                examples=VariantExamples(),
            ),
            frameworks=[
                FrameworkVariant(
                    name="angular",
                    check=ForbiddenCheck(type="forbidden", pattern="eval($X)"),
                    examples=VariantExamples(),
                ),
            ],
        )
        assert variant.generic is not None
        assert len(variant.frameworks) == 1


class TestPatternSpec:
    def test_minimal_valid(self) -> None:
        spec = PatternSpec(
            id="DI-001",
            title="Dependency Injection",
            description="Use DI",
            rationale="Testability",
            tier=2,
            category="architecture",
            severity="warning",
            reporting=_minimal_reporting(),
            variants=[_minimal_variant()],
        )
        assert spec.id == "DI-001"
        assert spec.version == "1.0.0"
        assert spec.tags == []
        assert spec.subcategory is None

    def test_full_fields(self) -> None:
        spec = PatternSpec(
            id="DI-001",
            title="Dependency Injection",
            description="Use DI",
            rationale="Testability",
            version="2.0.0",
            tier=2,
            category="architecture",
            subcategory="dependency-injection",
            severity="warning",
            tags=["solid", "testability"],
            reporting=_minimal_reporting(),
            references=["https://example.com"],
            variants=[_minimal_variant()],
        )
        assert spec.version == "2.0.0"
        assert spec.subcategory == "dependency-injection"
        assert spec.tags == ["solid", "testability"]

    def test_tier_validation(self) -> None:
        with pytest.raises(ValidationError):
            PatternSpec(
                id="DI-001",
                title="T",
                description="D",
                rationale="R",
                tier=4,
                category="c",
                severity="warning",
                reporting=_minimal_reporting(),
                variants=[_minimal_variant()],
            )

    def test_multiple_language_variants(self) -> None:
        spec = PatternSpec(
            id="DI-001",
            title="DI",
            description="D",
            rationale="R",
            tier=2,
            category="architecture",
            severity="warning",
            reporting=_minimal_reporting(),
            variants=[
                _minimal_variant(),
                LanguageVariant(
                    language="typescript",
                    generic=GenericVariant(
                        check=ForbiddenCheck(type="forbidden", pattern="new $X()"),
                        examples=VariantExamples(),
                    ),
                ),
            ],
        )
        assert len(spec.variants) == 2
        assert spec.variants[0].language == "python"
        assert spec.variants[1].language == "typescript"


class TestPatternSpecFile:
    def test_schema_version_defaults_to_2(self) -> None:
        spec_file = PatternSpecFile(
            pattern=PatternSpec(
                id="DI-001",
                title="DI",
                description="D",
                rationale="R",
                tier=2,
                category="architecture",
                severity="warning",
                reporting=_minimal_reporting(),
                variants=[_minimal_variant()],
            ),
        )
        assert spec_file.schema_version == 2

    def test_roundtrip_yaml(self, tmp_path) -> None:
        """PatternSpecFile can be serialized to YAML and loaded back."""
        spec_file = PatternSpecFile(
            pattern=PatternSpec(
                id="DI-001",
                title="Dependency Injection",
                description="Use DI",
                rationale="Testability",
                tier=2,
                category="architecture",
                severity="warning",
                reporting=_minimal_reporting(),
                variants=[
                    LanguageVariant(
                        language="python",
                        version_constraint=">=3.10",
                        generic=GenericVariant(
                            check=PatternDiscoveryCheck(
                                type="pattern_discovery",
                                patterns=["class $C: ..."],
                            ),
                            examples=VariantExamples(),
                        ),
                        frameworks=[
                            FrameworkVariant(
                                name="django",
                                version_constraint=">=4.0",
                                check=RawCheck(
                                    type="raw",
                                    config="rules: []",
                                ),
                                examples=VariantExamples(),
                            ),
                        ],
                    ),
                ],
            ),
        )

        path = tmp_path / "DI-001.yaml"
        data = spec_file.model_dump()
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        restored = PatternSpecFile.model_validate(loaded)

        assert restored.schema_version == 2
        assert restored.pattern.id == "DI-001"
        assert len(restored.pattern.variants) == 1
        assert restored.pattern.variants[0].language == "python"
        assert restored.pattern.variants[0].version_constraint == ">=3.10"
        assert len(restored.pattern.variants[0].frameworks) == 1
        assert restored.pattern.variants[0].frameworks[0].name == "django"
