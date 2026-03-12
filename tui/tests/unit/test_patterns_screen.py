"""Tests for the PatternsScreen."""

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
from lookout_tui.screens.patterns import PatternsScreen
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


class TestPatternsScreenBindings:
    def test_has_generate_binding(self) -> None:
        bindings = {b.key for b in PatternsScreen.BINDINGS}
        assert "g" in bindings

    def test_has_add_binding(self) -> None:
        bindings = {b.key for b in PatternsScreen.BINDINGS}
        assert "a" in bindings

    def test_has_write_binding(self) -> None:
        bindings = {b.key for b in PatternsScreen.BINDINGS}
        assert "w" in bindings

    def test_has_deprecate_binding(self) -> None:
        bindings = {b.key for b in PatternsScreen.BINDINGS}
        assert "d" in bindings

    def test_has_yank_binding(self) -> None:
        bindings = {b.key for b in PatternsScreen.BINDINGS}
        assert "y" in bindings

    def test_has_approve_reject_bindings(self) -> None:
        bindings = {b.key for b in PatternsScreen.BINDINGS}
        assert "ctrl+a" in bindings
        assert "ctrl+x" in bindings

    def test_has_filter_binding(self) -> None:
        bindings = {b.key for b in PatternsScreen.BINDINGS}
        assert "slash" in bindings

    def test_has_refresh_binding(self) -> None:
        bindings = {b.key for b in PatternsScreen.BINDINGS}
        assert "r" in bindings
        assert "f5" in bindings

    def test_has_escape_binding(self) -> None:
        bindings = {b.key for b in PatternsScreen.BINDINGS}
        assert "escape" in bindings

    def test_case_insensitive_bindings(self) -> None:
        bindings = {b.key for b in PatternsScreen.BINDINGS}
        for key in ("g", "a", "d", "w", "y", "r"):
            assert key in bindings, f"Missing lowercase {key}"
            assert key.upper() in bindings, f"Missing uppercase {key}"


class TestPatternsScreenInit:
    def test_initial_mode_is_detail(self) -> None:
        screen = PatternsScreen()
        assert screen._mode == "detail"

    def test_initial_state(self) -> None:
        screen = PatternsScreen()
        assert screen._current_node is None
        assert screen._generation_result is None
        assert screen._pipeline is None
        assert screen._new_pattern_counter == 0


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
        from lookout.models import PatternDiscoveryCheck
        from lookout.registry import add_language_variant

        spec = _spec(id="SYNC-001")
        check = PatternDiscoveryCheck(type="pattern_discovery", patterns=["$X(...)"])
        updated = add_language_variant(spec, "python", check)

        new_node = PatternNodeData(spec=updated)
        assert len(new_node.spec.pattern.variants) == 1
        assert new_node.spec.pattern.variants[0].language == "python"


class TestPatternsScreenHelpers:
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


class TestReplacePattern:
    def test_replace_updates_list(self) -> None:
        screen = PatternsScreen()
        spec1 = _spec(id="REP-001", status="draft")
        spec2 = _spec(id="REP-001", status="active")
        screen._patterns = [spec1]
        screen._replace_pattern(spec1, spec2)
        assert screen._patterns[0].pattern.status == "active"

    def test_replace_appends_if_not_found(self) -> None:
        screen = PatternsScreen()
        spec = _spec(id="NEW-001")
        screen._patterns = []
        screen._replace_pattern(spec, spec)
        assert len(screen._patterns) == 1

    def test_replace_syncs_current_node(self) -> None:
        screen = PatternsScreen()
        spec1 = _spec(id="SYNC-002", status="draft")
        spec2 = _spec(id="SYNC-002", status="active")
        screen._patterns = [spec1]
        screen._current_node = PatternNodeData(spec=spec1)
        screen._replace_pattern(spec1, spec2)
        assert screen._current_node is not None
        assert screen._current_node.spec.pattern.status == "active"
