"""Registry management screen — browse, create, and generate pattern specs."""

from __future__ import annotations

import asyncio

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
from textual.widgets import Footer, Header, Input, Static

from lookout_tui.clients.litellm_client import LiteLLMClient
from lookout_tui.clients.protocol import LLMClient
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
from lookout_tui.widgets.model_selector import ModelSelector
from lookout_tui.widgets.registry_tree import (
    FrameworkNodeData,
    LanguageNodeData,
    NodeData,
    PatternNodeData,
    RegistryTree,
)


class RegistryScreen(Screen[None]):
    """Browse, create, and generate pattern registry entries."""

    BINDINGS = [
        # Tier 2 standard keys (§2.2)
        *ci("a", "new_pattern", "Add"),
        *ci("d", "deprecate", "Deprecate"),
        *ci("e", "edit_pattern", "Edit"),
        *ci("y", "yank_id", "Yank"),
        # Screen-specific keys
        *ci("l", "add_language", "Add Lang"),
        *ci("f", "add_framework", "Add FW"),
        *ci("n", "generate", "Generate"),
        *ci("w", "write_pattern", "Write"),
        Binding("ctrl+a", "approve_action", "Approve", key_display="^a"),
        Binding("ctrl+x", "reject", "Reject", key_display="^x"),
        # Tier 1 keys (§2.2)
        Binding("slash", "focus_filter", "Filter", key_display="/"),
        *ci("r", "refresh_registry", "Refresh"),
        Binding("f5", "refresh_registry", "Refresh", show=False),
        Binding("escape", "app.go_home", "Home"),
        Binding("f3", "app.go_home", "Home", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._patterns: list[PatternSpecFile] = []
        self._built_in_ids: set[str] = set()
        self._user_ids: set[str] = set()
        self._current_node: NodeData | None = None
        self._generation_result: StageResult | None = None
        self._pipeline: GenerationPipeline | None = None
        self._client: LLMClient | None = None
        self._pipeline_lock = asyncio.Lock()
        self._new_pattern_counter = 0

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(" Lookout — Pattern Registry", id="screen-title")
        from lookout_tui.app import LookoutApp

        default_model = "gemini/gemini-3.1-pro-tools"
        model = (
            self.app.tui_config.llm_model
            if isinstance(self.app, LookoutApp)
            else default_model
        )
        yield ModelSelector(current_model=model, id="model-selector")
        yield Input(placeholder="Filter patterns...", id="filter-input")
        with Horizontal(id="registry-main"):
            with Vertical(id="registry-tree-panel"):
                yield RegistryTree(id="registry-tree")
            with Vertical(id="registry-context-panel"):
                yield ContextPanel(id="context-panel")
        yield Footer()

    def on_mount(self) -> None:
        self._load_and_refresh()

    async def on_unmount(self) -> None:
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None
            self._pipeline = None

    # ── Data loading ──────────────────────────────────────────────

    def _load_and_refresh(self) -> None:
        from lookout_tui.app import LookoutApp

        # Load built-in v2 patterns
        built_in_specs = [
            s for s in load_built_in_patterns() if isinstance(s, PatternSpecFile)
        ]
        built_in_ids = {s.pattern.id for s in built_in_specs}

        # Load user v2 patterns (override built-in by ID)
        user_specs: list[PatternSpecFile] = []
        if isinstance(self.app, LookoutApp):
            rules_dir = self.app.tui_config.patterns_dir
            if rules_dir.exists():
                user_specs = [
                    s for s in load_specs(rules_dir) if isinstance(s, PatternSpecFile)
                ]

        user_ids = {s.pattern.id for s in user_specs}
        # Merge: user overrides built-in by ID
        merged = {s.pattern.id: s for s in built_in_specs}
        for s in user_specs:
            merged[s.pattern.id] = s
        self._patterns = list(merged.values())

        # Track which IDs are built-in vs user-provided
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
        title.update(f" Lookout — Pattern Registry ({len(patterns)} patterns)")

    # ── Event handlers ────────────────────────────────────────────

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "filter-input":
            self._refresh_tree(event.value.lower())

    def on_registry_tree_node_selected(
        self, event: RegistryTree.NodeSelected
    ) -> None:
        self._current_node = event.node_data
        self._generation_result = None
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

    def action_refresh_registry(self) -> None:
        self._load_and_refresh()
        self.notify("Registry refreshed")

    def action_edit_pattern(self) -> None:
        self.notify("Edit not yet implemented", severity="warning")

    def action_yank_id(self) -> None:
        node = self._current_node
        if node is None:
            self.notify("Nothing selected", severity="warning")
            return
        pattern_id = node.spec.pattern.id
        self.app.copy_to_clipboard(pattern_id)
        self.notify(f"Copied {pattern_id}")

    # ── Create / mutate actions ───────────────────────────────────

    def action_new_pattern(self) -> None:
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

    def action_add_language(self) -> None:
        node = self._current_node
        if not isinstance(node, PatternNodeData):
            self.notify("Select a pattern node first", severity="warning")
            return
        # For now, add a stub language. A real implementation would prompt.
        spec = node.spec
        lang = "python"  # placeholder — in real UI, prompt user
        existing = {v.language for v in spec.pattern.variants}
        if lang in existing:
            self.notify(f"Language '{lang}' already exists", severity="warning")
            return
        from lookout.models import PatternDiscoveryCheck

        check = PatternDiscoveryCheck(type="pattern_discovery", patterns=["$X(...)"])
        updated = add_language_variant(spec, lang, check)
        self._replace_pattern(spec, updated)
        self._refresh_tree()
        self.notify(f"Added {lang} to {spec.pattern.id}")

    def action_add_framework(self) -> None:
        node = self._current_node
        if not isinstance(node, LanguageNodeData):
            self.notify("Select a language node first", severity="warning")
            return
        spec = node.spec
        lang = node.language
        fw = "django"  # placeholder — in real UI, prompt user
        existing = set()
        for v in spec.pattern.variants:
            if v.language == lang:
                existing = {f.name for f in v.frameworks}
        if fw in existing:
            self.notify(f"Framework '{fw}' already exists", severity="warning")
            return
        from lookout.models import PatternDiscoveryCheck

        check = PatternDiscoveryCheck(type="pattern_discovery", patterns=["$X(...)"])
        updated = add_framework_variant(spec, lang, fw, check)
        self._replace_pattern(spec, updated)
        self._refresh_tree()
        self.notify(f"Added {fw} to {spec.pattern.id}/{lang}")

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
        # If generation result awaiting review, approve it
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

        spec: PatternSpecFile
        if isinstance(node, PatternNodeData):
            spec = node.spec
            # Generate top-level for all languages
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
        panel = self.query_one("#context-panel", ContextPanel)

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
            panel.show_generation(stage)
            # Stop after first stage to let user review
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

    def _replace_pattern(
        self, old: PatternSpecFile, new: PatternSpecFile
    ) -> None:
        """Replace a pattern in the in-memory list."""
        for i, p in enumerate(self._patterns):
            if p.pattern.id == old.pattern.id:
                self._patterns[i] = new
                return
        self._patterns.append(new)
