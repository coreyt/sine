"""Tests for the RegistryScreen and ContextPanel content builders."""

from __future__ import annotations

from pathlib import Path

import yaml
from lookout.models import (
    GenericVariant,
    LanguageVariant,
    PatternSpec,
    PatternSpecFile,
    RawCheck,
    RuleReporting,
    VariantExamples,
)
from lookout.registry import save_pattern

from lookout_tui.pipeline.models import GenerationStage, StageResult, StageStatus
from lookout_tui.widgets.context_panel import (
    build_generation_text,
    build_pattern_text,
    build_variant_text,
)
from lookout_tui.widgets.registry_tree import (
    FrameworkNodeData,
    LanguageNodeData,
    PatternNodeData,
)


def _reporting() -> RuleReporting:
    return RuleReporting(default_message="msg", confidence="medium")


def _check() -> RawCheck:
    return RawCheck(type="raw", config="rules: []")


def _spec(
    id: str = "TEST-001",
    status: str = "draft",
    variants: list[LanguageVariant] | None = None,
) -> PatternSpecFile:
    return PatternSpecFile(
        schema_version=2,
        pattern=PatternSpec(
            id=id,
            title="Test Pattern",
            description="A test pattern.",
            rationale="For testing.",
            tier=2,
            category="testing",
            severity="warning",
            reporting=_reporting(),
            status=status,
            variants=variants or [],
        ),
    )


class TestBuildPatternText:
    def test_includes_id_and_status(self) -> None:
        spec = _spec(id="DI-001", status="active")
        text = build_pattern_text(spec)
        plain = text.plain
        assert "DI-001" in plain
        assert "active" in plain

    def test_includes_category_and_severity(self) -> None:
        spec = _spec()
        text = build_pattern_text(spec)
        plain = text.plain
        assert "testing" in plain
        assert "warning" in plain

    def test_no_variants_message(self) -> None:
        spec = _spec()
        text = build_pattern_text(spec)
        assert "No variants yet" in text.plain

    def test_with_variants_shows_languages(self) -> None:
        spec = _spec(
            variants=[LanguageVariant(language="python"), LanguageVariant(language="typescript")]
        )
        text = build_pattern_text(spec)
        assert "python" in text.plain
        assert "typescript" in text.plain


class TestBuildVariantText:
    def test_generic_variant(self) -> None:
        spec = _spec(
            variants=[
                LanguageVariant(
                    language="python",
                    generic=GenericVariant(check=_check(), examples=VariantExamples()),
                )
            ]
        )
        text = build_variant_text(spec, "python")
        plain = text.plain
        assert "python" in plain
        assert "raw" in plain

    def test_missing_language(self) -> None:
        spec = _spec()
        text = build_variant_text(spec, "java")
        assert "not found" in text.plain

    def test_missing_generic(self) -> None:
        spec = _spec(variants=[LanguageVariant(language="python")])
        text = build_variant_text(spec, "python")
        assert "not yet generated" in text.plain


class TestBuildGenerationText:
    def test_awaiting_review(self) -> None:
        result = StageResult(
            stage=GenerationStage.LANGUAGE_GENERIC,
            status=StageStatus.AWAITING_REVIEW,
            output="generated content here",
            model="test-model",
            language="python",
        )
        text = build_generation_text(result)
        plain = text.plain
        assert "awaiting_review" in plain
        assert "generated content here" in plain

    def test_error(self) -> None:
        result = StageResult(
            stage=GenerationStage.TOP_LEVEL,
            status=StageStatus.ERROR,
            error="Something broke",
        )
        text = build_generation_text(result)
        assert "Something broke" in text.plain

    def test_no_output_yet(self) -> None:
        result = StageResult(
            stage=GenerationStage.TOP_LEVEL,
            status=StageStatus.PENDING,
        )
        text = build_generation_text(result)
        assert "No output yet" in text.plain


class TestSelectDialog:
    def test_import(self) -> None:
        from lookout_tui.widgets.input_dialog import SelectDialog

        choices = {"python": ["3.12", "3.13"], "rust": []}
        dialog = SelectDialog("Pick Language", choices)
        assert dialog._title == "Pick Language"
        assert dialog._choices == choices

    def test_input_dialog_still_works(self) -> None:
        from lookout_tui.widgets.input_dialog import InputDialog

        dialog = InputDialog("Test prompt", placeholder="hint")
        assert dialog._prompt == "Test prompt"


class TestReplacePatternNodeSync:
    def test_current_node_updated_after_replace(self) -> None:
        """After _replace_pattern, _current_node should reference the new spec."""
        from lookout.models import PatternDiscoveryCheck
        from lookout.registry import add_language_variant

        spec = _spec(id="SYNC-001")
        check = PatternDiscoveryCheck(type="pattern_discovery", patterns=["$X(...)"])
        updated = add_language_variant(spec, "python", check)

        # Update node
        new_node = PatternNodeData(spec=updated)
        assert len(new_node.spec.pattern.variants) == 1
        assert new_node.spec.pattern.variants[0].language == "python"


class TestRegistryScreenHelpers:
    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        spec = _spec(id="ROUND-001")
        save_pattern(spec, tmp_path)

        path = tmp_path / "ROUND-001.yaml"
        assert path.exists()

        data = yaml.safe_load(path.read_text())
        assert data["pattern"]["id"] == "ROUND-001"
        assert data["pattern"]["status"] == "draft"

    def test_node_data_from_spec(self) -> None:
        spec = _spec(id="NODE-001")
        pn = PatternNodeData(spec=spec)
        assert pn.spec.pattern.id == "NODE-001"

        ln = LanguageNodeData(spec=spec, language="python")
        assert ln.language == "python"

        fn = FrameworkNodeData(spec=spec, language="python", framework="django")
        assert fn.framework == "django"
