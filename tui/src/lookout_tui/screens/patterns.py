"""Patterns screen — browse, create, edit, generate, review, save."""

from __future__ import annotations

import asyncio
from typing import Literal

from lookout.models import PatternSpecFile
from lookout.registry import (
    add_framework_variant,
    add_language_variant,
    approve_pattern,
    create_pattern,
    deprecate_pattern,
    save_pattern,
)
from lookout.rules_loader import load_built_in_patterns
from lookout.specs import load_specs
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import ContentSwitcher, Footer, Header, Input, Static

from lookout_tui.clients.litellm_client import LiteLLMClient
from lookout_tui.clients.protocol import LLMClient
from lookout_tui.config import TUIConfig
from lookout_tui.keys import ci
from lookout_tui.pipeline.generator import GenerationPipeline
from lookout_tui.pipeline.models import (
    GenerationJob,
    GenerationStage,
    StageResult,
    StageStatus,
)
from lookout_tui.prompts.loader import PromptTemplate
from lookout_tui.widgets.context_panel import ContextPanel
from lookout_tui.widgets.diff_view import DiffView
from lookout_tui.widgets.input_dialog import SelectDialog
from lookout_tui.widgets.model_selector import ModelSelector
from lookout_tui.widgets.registry_tree import (
    FrameworkNodeData,
    LanguageNodeData,
    NodeData,
    PatternNodeData,
    RegistryTree,
)
from lookout_tui.widgets.stage_progress import StageProgress


class PatternsScreen(Screen[None]):
    """Single hub for all pattern work — browse, create, edit, generate, review, save."""

    BINDINGS = [
        # Tier 2 standard keys
        *ci("a", "add", "Add"),
        *ci("g", "generate", "Generate"),
        *ci("d", "deprecate", "Deprecate"),
        *ci("w", "write_pattern", "Write"),
        *ci("y", "yank_id", "Yank"),
        # Approve/reject
        Binding("ctrl+a", "approve_action", "Approve", key_display="^a"),
        Binding("ctrl+x", "reject", "Reject", key_display="^x"),
        # Navigation
        Binding("slash", "focus_filter", "Filter", key_display="/"),
        *ci("r", "refresh", "Refresh"),
        Binding("f5", "refresh", "Refresh", show=False),
        Binding("escape", "escape_action", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._patterns: list[PatternSpecFile] = []
        self._built_in_specs: list[PatternSpecFile] | None = None
        self._built_in_ids: set[str] = set()
        self._user_ids: set[str] = set()
        self._current_node: NodeData | None = None
        self._generation_result: StageResult | None = None
        self._pipeline: GenerationPipeline | None = None
        self._client: LLMClient | None = None
        self._pipeline_lock = asyncio.Lock()
        self._new_pattern_counter = 0
        self._mode: Literal["detail", "generate"] = "detail"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(" Lookout — Patterns", id="screen-title")
        from lookout_tui.app import LookoutApp

        model = (
            self.app.tui_config.llm_model
            if isinstance(self.app, LookoutApp)
            else TUIConfig().llm_model
        )
        yield ModelSelector(current_model=model, id="model-selector")
        yield Input(placeholder="Filter patterns...", id="filter-input")
        with Horizontal(id="patterns-main"):
            with Vertical(id="patterns-tree-panel"):
                yield RegistryTree(id="registry-tree")
            with ContentSwitcher(id="content-switcher", initial="detail"):
                with Vertical(id="detail"):
                    yield ContextPanel(id="context-panel")
                with Vertical(id="generate"):
                    yield StageProgress(id="stage-progress")
                    yield DiffView(id="diff-view")
        yield Footer()

    def on_mount(self) -> None:
        self._load_and_refresh()

    async def on_unmount(self) -> None:
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None
            self._pipeline = None

    # ── Mode switching ────────────────────────────────────────────

    def _switch_mode(self, mode: Literal["detail", "generate"]) -> None:
        self._mode = mode
        self.query_one("#content-switcher", ContentSwitcher).current = mode

    # ── Data loading ──────────────────────────────────────────────

    def _load_and_refresh(self) -> None:
        from lookout_tui.app import LookoutApp

        if self._built_in_specs is None:
            self._built_in_specs = [
                s for s in load_built_in_patterns() if isinstance(s, PatternSpecFile)
            ]
        built_in_specs = self._built_in_specs
        built_in_ids = {s.pattern.id for s in built_in_specs}

        user_specs: list[PatternSpecFile] = []
        if isinstance(self.app, LookoutApp):
            rules_dir = self.app.tui_config.patterns_dir
            if rules_dir.exists():
                user_specs = [
                    s for s in load_specs(rules_dir) if isinstance(s, PatternSpecFile)
                ]

        user_ids = {s.pattern.id for s in user_specs}
        merged = {s.pattern.id: s for s in built_in_specs}
        for s in user_specs:
            merged[s.pattern.id] = s
        self._patterns = list(merged.values())
        self._built_in_ids = built_in_ids - user_ids
        self._user_ids = user_ids
        self._refresh_tree()

    def _refresh_tree(self, filter_text: str = "") -> None:
        tree = self.query_one("#registry-tree", RegistryTree)
        patterns = self._patterns
        if filter_text:
            patterns = [
                p
                for p in patterns
                if filter_text in p.pattern.id.lower()
                or filter_text in p.pattern.title.lower()
                or filter_text in p.pattern.category.lower()
            ]
        tree.populate(patterns, built_in_ids=self._built_in_ids)
        title = self.query_one("#screen-title", Static)
        title.update(f" Lookout — Patterns ({len(patterns)} patterns)")

    # ── Event handlers ────────────────────────────────────────────

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "filter-input":
            self._refresh_tree(event.value.lower())

    def on_registry_tree_node_selected(
        self, event: RegistryTree.NodeSelected
    ) -> None:
        self._current_node = event.node_data
        self._generation_result = None
        self._switch_mode("detail")
        panel = self.query_one("#context-panel", ContextPanel)

        if isinstance(event.node_data, PatternNodeData):
            panel.show_pattern(event.node_data.spec)
        elif isinstance(event.node_data, LanguageNodeData):
            panel.show_variant(
                event.node_data.spec,
                event.node_data.language,
            )
        elif isinstance(event.node_data, FrameworkNodeData):
            panel.show_variant(
                event.node_data.spec,
                event.node_data.language,
                event.node_data.framework,
            )

    async def on_model_selector_model_changed(
        self, event: ModelSelector.ModelChanged
    ) -> None:
        from lookout_tui.app import LookoutApp

        if isinstance(self.app, LookoutApp):
            self.app.tui_config.llm_model = event.model
        async with self._pipeline_lock:
            self._client = None
            self._pipeline = None

    def action_focus_filter(self) -> None:
        self.query_one("#filter-input", Input).focus()

    def action_refresh(self) -> None:
        self._load_and_refresh()
        self.notify("Patterns refreshed")

    def action_escape_action(self) -> None:
        if self._mode == "generate":
            self._switch_mode("detail")
        # If already in detail mode, no-op (we're the main screen)

    def action_yank_id(self) -> None:
        node = self._current_node
        if node is None:
            self.notify("Nothing selected", severity="warning")
            return
        pattern_id = node.spec.pattern.id
        self.app.copy_to_clipboard(pattern_id)
        self.notify(f"Copied {pattern_id}")

    # ── Add action (context-sensitive) ────────────────────────────

    def action_add(self) -> None:
        node = self._current_node
        if isinstance(node, LanguageNodeData):
            self._add_framework()
        elif isinstance(node, PatternNodeData):
            self._add_language()
        else:
            self._new_pattern()

    def _new_pattern(self) -> None:
        self._new_pattern_counter += 1
        spec = create_pattern(
            id=f"NEW-{self._new_pattern_counter:03d}",
            title="New Pattern",
            description="Describe the pattern.",
            rationale="Why this pattern matters.",
            category="uncategorized",
            severity="warning",
        )
        self._patterns.append(spec)
        self._refresh_tree()
        self.notify(f"Created draft pattern {spec.pattern.id}")

    def _add_language(self) -> None:
        node = self._current_node
        if not isinstance(node, PatternNodeData):
            self.notify("Select a pattern node first", severity="warning")
            return
        spec = node.spec
        config = self._get_config()

        existing = {v.language for v in spec.pattern.variants}
        choices: dict[str, list[str]] = {}
        for lang_name in config.get_language_names():
            if lang_name not in existing:
                choices[lang_name] = config.get_language_versions(lang_name)

        if not choices:
            self.notify("All configured languages already added", severity="warning")
            return

        def _on_result(result: tuple[str, str | None] | None) -> None:
            if result is None:
                return
            lang_name, version = result
            from lookout.models import PatternDiscoveryCheck

            check = PatternDiscoveryCheck(type="pattern_discovery", patterns=["$X(...)"])
            version_constraint = f">={version}" if version else None
            updated = add_language_variant(
                spec, lang_name, check, version_constraint=version_constraint
            )
            self._replace_pattern(spec, updated)
            self._refresh_tree()
            label = f"{lang_name} {version}" if version else lang_name
            self.notify(f"Added {label} to {spec.pattern.id}")

        self.app.push_screen(
            SelectDialog(
                "Add Language Variant",
                choices,
                name_prompt="Language",
                version_prompt="Version",
            ),
            _on_result,
        )

    def _add_framework(self) -> None:
        node = self._current_node
        if not isinstance(node, LanguageNodeData):
            self.notify("Select a language node first", severity="warning")
            return
        spec = node.spec
        lang = node.language
        config = self._get_config()

        variant = next((v for v in spec.pattern.variants if v.language == lang), None)
        existing = {f.name for f in variant.frameworks} if variant else set()

        choices: dict[str, list[str]] = {}
        for fw_name in config.get_framework_names(lang):
            if fw_name not in existing:
                choices[fw_name] = config.get_framework_versions(fw_name, lang)

        if not choices:
            self.notify(
                f"No more frameworks configured for {lang}. Add in Settings.",
                severity="warning",
            )
            return

        def _on_result(result: tuple[str, str | None] | None) -> None:
            if result is None:
                return
            fw_name, version = result
            from lookout.models import PatternDiscoveryCheck

            check = PatternDiscoveryCheck(type="pattern_discovery", patterns=["$X(...)"])
            version_constraint = f">={version}" if version else None
            updated = add_framework_variant(
                spec, lang, fw_name, check, version_constraint=version_constraint
            )
            self._replace_pattern(spec, updated)
            self._refresh_tree()
            label = f"{fw_name} {version}" if version else fw_name
            self.notify(f"Added {label} to {spec.pattern.id}/{lang}")

        self.app.push_screen(
            SelectDialog(
                f"Add Framework for {lang}",
                choices,
                name_prompt="Framework",
                version_prompt="Version",
            ),
            _on_result,
        )

    # ── Deprecate / Approve / Reject ──────────────────────────────

    def action_deprecate(self) -> None:
        node = self._current_node
        if not isinstance(node, PatternNodeData):
            self.notify("Select a pattern node first", severity="warning")
            return
        spec = node.spec
        if spec.pattern.status == "deprecated":
            self.notify("Already deprecated", severity="warning")
            return
        updated = deprecate_pattern(spec)
        self._replace_pattern(spec, updated)
        self._refresh_tree()
        self.notify(f"Deprecated {spec.pattern.id}")

    def action_approve_action(self) -> None:
        result = self._generation_result
        if result and result.status == StageStatus.AWAITING_REVIEW:
            result.status = StageStatus.APPROVED
            panel = self.query_one("#context-panel", ContextPanel)
            panel.show_generation(result)
            self.notify("Generation approved")
            return

        node = self._current_node
        if not isinstance(node, PatternNodeData):
            self.notify("Select a pattern node first", severity="warning")
            return
        spec = node.spec
        if spec.pattern.status == "active":
            self.notify("Already active", severity="warning")
            return
        updated = approve_pattern(spec)
        self._replace_pattern(spec, updated)
        self._refresh_tree()
        self.notify(f"Approved {spec.pattern.id}")

    def action_reject(self) -> None:
        result = self._generation_result
        if result and result.status == StageStatus.AWAITING_REVIEW:
            result.status = StageStatus.REJECTED
            panel = self.query_one("#context-panel", ContextPanel)
            panel.show_generation(result)
            self.notify("Generation rejected. Press 'g' to retry.")
            return
        self.notify("No generation result to reject", severity="warning")

    def action_write_pattern(self) -> None:
        node = self._current_node
        if node is None:
            self.notify("Select a pattern node first", severity="warning")
            return
        spec = node.spec
        from lookout_tui.app import LookoutApp

        if not isinstance(self.app, LookoutApp):
            self.notify("Cannot determine patterns directory", severity="error")
            return
        rules_dir = self.app.tui_config.patterns_dir
        path = save_pattern(spec, rules_dir)
        self.notify(f"Saved to {path}")

    # ── Generation ────────────────────────────────────────────────

    def action_generate(self) -> None:
        node = self._current_node
        if node is None:
            self.notify("Select a node first", severity="warning")
            return

        self._switch_mode("generate")

        spec: PatternSpecFile
        if isinstance(node, PatternNodeData):
            spec = node.spec
            job = GenerationJob(
                pattern_id=spec.pattern.id,
                title=spec.pattern.title,
                description_hint=spec.pattern.description,
                target_languages=[v.language for v in spec.pattern.variants],
            )
            job.initialize_stages()
            self._run_generation(job)
        elif isinstance(node, (LanguageNodeData, FrameworkNodeData)):
            spec = node.spec
            language = node.language
            framework = node.framework if isinstance(node, FrameworkNodeData) else None

            if framework and framework != "generic":
                job = GenerationJob(
                    pattern_id=spec.pattern.id,
                    title=spec.pattern.title,
                    description_hint=spec.pattern.description,
                    target_languages=[language],
                    target_frameworks={language: [framework]},
                )
            else:
                job = GenerationJob(
                    pattern_id=spec.pattern.id,
                    title=spec.pattern.title,
                    description_hint=spec.pattern.description,
                    target_languages=[language],
                )
            job.initialize_stages()
            self._run_generation(job)

    @work(thread=False)
    async def _run_generation(self, job: GenerationJob) -> None:
        pipeline = await self._ensure_pipeline()
        progress = self.query_one("#stage-progress", StageProgress)
        diff = self.query_one("#diff-view", DiffView)

        progress.show_job(job)

        for stage in job.stages:
            if stage.status != StageStatus.PENDING:
                continue

            if stage.stage == GenerationStage.TOP_LEVEL:
                await pipeline.run_top_level(job)
            elif stage.stage == GenerationStage.LANGUAGE_GENERIC:
                top = job.top_level_result
                top_output = top.output if top and top.status == StageStatus.APPROVED else ""
                await pipeline.run_language_generic(job, top_output, stage.language)
            elif stage.stage == GenerationStage.LANGUAGE_FRAMEWORK:
                top = job.top_level_result
                top_output = top.output if top and top.status == StageStatus.APPROVED else ""
                await pipeline.run_language_framework(
                    job, top_output, "", stage.language, stage.framework
                )

            self._generation_result = stage
            progress.show_job(job)
            diff.show_stage(stage)
            break

    async def _ensure_pipeline(self) -> GenerationPipeline:
        async with self._pipeline_lock:
            if self._pipeline:
                return self._pipeline

            from lookout_tui.app import LookoutApp

            assert isinstance(self.app, LookoutApp)
            config = self.app.tui_config

            self._client = LiteLLMClient(
                model=config.llm_model,
                temperature=config.llm_temperature,
                max_tokens=config.llm_max_tokens,
                timeout=config.llm_timeout,
                max_retries=config.llm_max_retries,
            )
            await self._client.__aenter__()

            templates = PromptTemplate(config.prompts_dir)
            self._pipeline = GenerationPipeline(self._client, templates)
            return self._pipeline

    # ── Helpers ───────────────────────────────────────────────────

    def _get_config(self) -> TUIConfig:
        from lookout_tui.app import LookoutApp

        if isinstance(self.app, LookoutApp):
            return self.app.tui_config
        return TUIConfig()

    def _replace_pattern(
        self, old: PatternSpecFile, new: PatternSpecFile
    ) -> None:
        for i, p in enumerate(self._patterns):
            if p.pattern.id == old.pattern.id:
                self._patterns[i] = new
                break
        else:
            self._patterns.append(new)

        node = self._current_node
        if node is not None and node.spec.pattern.id == old.pattern.id:
            if isinstance(node, PatternNodeData):
                self._current_node = PatternNodeData(spec=new)
            elif isinstance(node, LanguageNodeData):
                self._current_node = LanguageNodeData(
                    spec=new, language=node.language
                )
            elif isinstance(node, FrameworkNodeData):
                self._current_node = FrameworkNodeData(
                    spec=new, language=node.language, framework=node.framework
                )
