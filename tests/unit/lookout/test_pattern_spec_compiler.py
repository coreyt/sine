"""Tests for compiling PatternSpecFile (v2) to Semgrep config."""

from __future__ import annotations

from lookout.models import (
    ForbiddenCheck,
    FrameworkVariant,
    GenericVariant,
    LanguageVariant,
    PatternDiscoveryCheck,
    PatternSpec,
    PatternSpecFile,
    RawCheck,
    RuleExamples,
    RuleReporting,
    RuleSpec,
    RuleSpecFile,
    VariantExamples,
)
from lookout.semgrep import compile_semgrep_config
from lookout.specs import SpecUnion


def _v2_spec(
    pattern_id: str = "DI-001",
    variants: list[LanguageVariant] | None = None,
) -> PatternSpecFile:
    if variants is None:
        variants = [
            LanguageVariant(
                language="python",
                generic=GenericVariant(
                    check=ForbiddenCheck(type="forbidden", pattern="self.$X = $Y()"),
                    examples=VariantExamples(),
                ),
            ),
        ]
    return PatternSpecFile(
        pattern=PatternSpec(
            id=pattern_id,
            title="Dependency Injection",
            description="Use DI",
            rationale="Testability",
            tier=2,
            category="architecture",
            severity="warning",
            reporting=RuleReporting(
                default_message=f"DI violation ({pattern_id})",
                confidence="high",
            ),
            variants=variants,
            references=[],
        ),
    )


def _v1_spec(rule_id: str = "ARCH-001") -> RuleSpecFile:
    return RuleSpecFile(
        rule=RuleSpec(
            id=rule_id,
            title="Test",
            description="D",
            rationale="R",
            tier=1,
            category="security",
            severity="error",
            languages=["python"],
            check=ForbiddenCheck(type="forbidden", pattern="eval($X)"),
            reporting=RuleReporting(
                default_message=f"Forbidden ({rule_id})",
                confidence="high",
            ),
            examples=RuleExamples(good=[], bad=[]),
            references=[],
        ),
    )


class TestCompileSemgrepConfigV2:
    def test_single_generic_variant(self) -> None:
        specs: list[SpecUnion] = [_v2_spec()]
        config = compile_semgrep_config(specs)
        rules = config["rules"]
        assert len(rules) == 1
        assert rules[0]["id"] == "di-001-python-impl"
        assert rules[0]["languages"] == ["python"]
        assert rules[0]["severity"] == "WARNING"

    def test_framework_variant_produces_separate_rule(self) -> None:
        specs: list[SpecUnion] = [
            _v2_spec(
                variants=[
                    LanguageVariant(
                        language="python",
                        generic=GenericVariant(
                            check=ForbiddenCheck(type="forbidden", pattern="self.$X = $Y()"),
                            examples=VariantExamples(),
                        ),
                        frameworks=[
                            FrameworkVariant(
                                name="django",
                                check=ForbiddenCheck(type="forbidden", pattern="self.$X = $Y()"),
                                examples=VariantExamples(),
                            ),
                        ],
                    ),
                ],
            ),
        ]
        config = compile_semgrep_config(specs)
        rules = config["rules"]
        assert len(rules) == 2
        rule_ids = {r["id"] for r in rules}
        assert "di-001-python-impl" in rule_ids
        assert "di-001-python-django-impl" in rule_ids

    def test_multiple_languages(self) -> None:
        specs: list[SpecUnion] = [
            _v2_spec(
                variants=[
                    LanguageVariant(
                        language="python",
                        generic=GenericVariant(
                            check=ForbiddenCheck(type="forbidden", pattern="self.$X = $Y()"),
                            examples=VariantExamples(),
                        ),
                    ),
                    LanguageVariant(
                        language="typescript",
                        generic=GenericVariant(
                            check=ForbiddenCheck(type="forbidden", pattern="new $X()"),
                            examples=VariantExamples(),
                        ),
                    ),
                ],
            ),
        ]
        config = compile_semgrep_config(specs)
        rules = config["rules"]
        assert len(rules) == 2
        langs = {r["languages"][0] for r in rules}
        assert langs == {"python", "typescript"}

    def test_mixed_v1_and_v2(self) -> None:
        specs: list[SpecUnion] = [_v1_spec(), _v2_spec()]
        config = compile_semgrep_config(specs)
        rules = config["rules"]
        assert len(rules) == 2

    def test_raw_check_in_v2_variant(self) -> None:
        raw_config = """rules:
  - id: di-001-python-django-raw
    languages: [python]
    severity: WARNING
    message: "DI violation"
    pattern: "self.$X = $Y()"
"""
        specs: list[SpecUnion] = [
            _v2_spec(
                variants=[
                    LanguageVariant(
                        language="python",
                        generic=None,
                        frameworks=[
                            FrameworkVariant(
                                name="django",
                                check=RawCheck(type="raw", config=raw_config),
                                examples=VariantExamples(),
                            ),
                        ],
                    ),
                ],
            ),
        ]
        config = compile_semgrep_config(specs)
        rules = config["rules"]
        assert len(rules) == 1
        assert rules[0]["id"] == "di-001-python-django-raw"

    def test_no_generic_only_frameworks(self) -> None:
        specs: list[SpecUnion] = [
            _v2_spec(
                variants=[
                    LanguageVariant(
                        language="python",
                        generic=None,
                        frameworks=[
                            FrameworkVariant(
                                name="django",
                                check=ForbiddenCheck(type="forbidden", pattern="self.$X = $Y()"),
                                examples=VariantExamples(),
                            ),
                        ],
                    ),
                ],
            ),
        ]
        config = compile_semgrep_config(specs)
        rules = config["rules"]
        assert len(rules) == 1
        assert rules[0]["id"] == "di-001-python-django-impl"

    def test_pattern_discovery_check_in_v2(self) -> None:
        specs: list[SpecUnion] = [
            _v2_spec(
                variants=[
                    LanguageVariant(
                        language="python",
                        generic=GenericVariant(
                            check=PatternDiscoveryCheck(
                                type="pattern_discovery",
                                patterns=["class $C: ..."],
                            ),
                            examples=VariantExamples(),
                        ),
                    ),
                ],
            ),
        ]
        config = compile_semgrep_config(specs)
        rules = config["rules"]
        assert len(rules) == 1
        assert rules[0]["id"] == "di-001-python-impl"


class TestExtractPatternIdFromV2:
    def test_extract_generic_variant_id(self) -> None:
        from lookout.semgrep import _extract_pattern_id

        assert _extract_pattern_id("di-001-python-impl") == "DI-001"

    def test_extract_framework_variant_id(self) -> None:
        from lookout.semgrep import _extract_pattern_id

        assert _extract_pattern_id("di-001-python-django-impl") == "DI-001"

    def test_extract_namespaced_v2_id(self) -> None:
        from lookout.semgrep import _extract_pattern_id

        assert _extract_pattern_id("tmp.config.di-001-python-django-impl") == "DI-001"

    def test_extract_v1_id_still_works(self) -> None:
        from lookout.semgrep import _extract_pattern_id

        assert _extract_pattern_id("arch-001-impl") == "ARCH-001"

    def test_extract_multi_segment_v1_id(self) -> None:
        from lookout.semgrep import _extract_pattern_id

        assert _extract_pattern_id("py-sec-001-impl") == "PY-SEC-001"


class TestIsDiscoverySpec:
    def test_v1_enforcement_spec(self) -> None:
        from lookout.runner import is_discovery_spec

        assert is_discovery_spec(_v1_spec()) is False

    def test_v2_enforcement_generic(self) -> None:
        from lookout.runner import is_discovery_spec

        spec = _v2_spec()  # Uses ForbiddenCheck by default
        assert is_discovery_spec(spec) is False

    def test_v2_discovery_generic(self) -> None:
        from lookout.runner import is_discovery_spec

        spec = _v2_spec(
            variants=[
                LanguageVariant(
                    language="python",
                    generic=GenericVariant(
                        check=PatternDiscoveryCheck(
                            type="pattern_discovery",
                            patterns=["class $C: ..."],
                        ),
                        examples=VariantExamples(),
                    ),
                ),
            ],
        )
        assert is_discovery_spec(spec) is True

    def test_v2_framework_only_enforcement(self) -> None:
        """Framework-only spec (no generic) with enforcement checks should not be discovery."""
        from lookout.runner import is_discovery_spec

        spec = _v2_spec(
            variants=[
                LanguageVariant(
                    language="python",
                    generic=None,
                    frameworks=[
                        FrameworkVariant(
                            name="django",
                            check=ForbiddenCheck(type="forbidden", pattern="eval($X)"),
                            examples=VariantExamples(),
                        ),
                    ],
                ),
            ],
        )
        assert is_discovery_spec(spec) is False

    def test_v2_mixed_enforcement_and_discovery(self) -> None:
        """Spec with both enforcement and discovery variants is NOT discovery-only."""
        from lookout.runner import is_discovery_spec

        spec = _v2_spec(
            variants=[
                LanguageVariant(
                    language="python",
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
                            check=ForbiddenCheck(type="forbidden", pattern="eval($X)"),
                            examples=VariantExamples(),
                        ),
                    ],
                ),
            ],
        )
        assert is_discovery_spec(spec) is False

    def test_v2_empty_variants(self) -> None:
        """Spec with no variants should not be discovery."""
        from lookout.runner import is_discovery_spec

        spec = _v2_spec(variants=[LanguageVariant(language="python")])
        assert is_discovery_spec(spec) is False


class TestBuildSpecIndexV2:
    def test_v2_spec_indexed_by_pattern_id(self) -> None:
        from lookout.semgrep import build_spec_index

        v2 = _v2_spec(pattern_id="DI-001")
        index = build_spec_index([v2])
        assert "DI-001" in index

    def test_mixed_v1_v2_index(self) -> None:
        from lookout.semgrep import build_spec_index

        specs: list[SpecUnion] = [_v1_spec("ARCH-001"), _v2_spec("DI-001")]
        index = build_spec_index(specs)
        assert "ARCH-001" in index
        assert "DI-001" in index
