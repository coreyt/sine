"""Dashboard home screen (S11.1 Dashboard archetype).

Provides orientation and status overview when the TUI launches.
Shows pattern counts, coverage metrics, and quick-action guidance.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from lookout_tui.index.builder import build_index
from lookout_tui.index.models import PatternIndex
from lookout_tui.keys import ci


@dataclass
class DashboardStats:
    """Computed metrics for the dashboard header cards."""

    total_patterns: int = 0
    built_in_count: int = 0
    user_count: int = 0
    enforcement_count: int = 0
    discovery_count: int = 0
    languages: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    llm_configured: bool = False
    llm_model: str = ""

    @classmethod
    def from_index(cls, index: PatternIndex) -> DashboardStats:
        """Build stats from a pattern index."""
        languages: set[str] = set()
        categories: set[str] = set()
        enforcement = 0
        discovery = 0

        for entry in index.entries:
            languages.update(entry.languages)
            categories.add(entry.category)
            if entry.severity == "info":
                discovery += 1
            else:
                enforcement += 1

        return cls(
            total_patterns=index.total,
            built_in_count=index.built_in_count,
            user_count=index.user_count,
            enforcement_count=enforcement,
            discovery_count=discovery,
            languages=sorted(languages),
            categories=sorted(categories),
        )


class DashboardScreen(Screen[None]):
    """Home screen — status overview and navigation launchpad (S11.1)."""

    BINDINGS = [
        *ci("r", "refresh", "Refresh"),
        Binding("f5", "refresh", "Refresh", show=False),
        Binding("escape", "noop", "Home", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._stats = DashboardStats()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(" Lookout Dashboard", id="screen-title")

        # S11.1 Zone 1: Header metric cards (1-3 rows)
        with Horizontal(id="dashboard-metrics"):
            yield Static("", id="metric-patterns")
            yield Static("", id="metric-languages")
            yield Static("", id="metric-status")

        # S11.1 Zone 2: Data area (flex)
        with Horizontal(id="dashboard-main"):
            with Vertical(id="dashboard-guide"):
                yield Static("", id="guide-content")
            with Vertical(id="dashboard-quick-ref"):
                yield Static("", id="quick-ref-content")

        yield Footer()

    def on_mount(self) -> None:
        self._refresh_stats()

    def _refresh_stats(self) -> None:
        from lookout_tui.app import LookoutApp

        patterns_dirs = None
        if isinstance(self.app, LookoutApp):
            patterns_dir = self.app.tui_config.patterns_dir
            if patterns_dir.exists():
                patterns_dirs = [patterns_dir]

        index = build_index(patterns_dirs=patterns_dirs, include_built_in=True)
        self._stats = DashboardStats.from_index(index)

        if isinstance(self.app, LookoutApp):
            self._stats.llm_model = self.app.tui_config.llm_model
            self._stats.llm_configured = bool(self.app.tui_config.llm_model)

        self._render_metrics()
        self._render_guide()
        self._render_quick_ref()

    def _render_metrics(self) -> None:
        s = self._stats
        self.query_one("#metric-patterns", Static).update(
            f" Patterns: {s.total_patterns}  "
            f"({s.built_in_count} built-in, {s.user_count} user)"
        )
        self.query_one("#metric-languages", Static).update(
            f" Languages: {len(s.languages)}  "
            f"({', '.join(s.languages) if s.languages else 'none'})"
        )
        model_display = s.llm_model if s.llm_configured else "not configured"
        self.query_one("#metric-status", Static).update(
            f" LLM: {model_display}"
        )

    def _render_guide(self) -> None:
        s = self._stats
        lines = [
            "Getting Started",
            "=" * 40,
            "",
        ]

        if s.total_patterns == 0:
            lines.append("No patterns loaded. Check your configuration.")
        else:
            lines.append(
                f"Lookout has {s.total_patterns} patterns ready "
                f"({s.enforcement_count} enforcement, "
                f"{s.discovery_count} discovery)."
            )
            lines.append("")

        lines.extend([
            "What would you like to do?",
            "",
            "  b  Browse Patterns     View all built-in and user patterns",
            "  e  Registry            Create and manage pattern specs",
            "  g  Generate            Run the LLM generation pipeline",
            "  c  Config              Set LLM provider and model",
            "  t  Batch               Bulk-generate checks across languages",
            "",
        ])

        if not s.llm_configured:
            lines.extend([
                "Tip: Press c to configure your LLM provider before",
                "     using Generate (g) or Batch (t).",
            ])
        elif s.user_count == 0:
            lines.extend([
                "Tip: Press e to create your first custom pattern,",
                "     then g to generate Semgrep checks with LLM.",
            ])

        self.query_one("#guide-content", Static).update("\n".join(lines))

    def _render_quick_ref(self) -> None:
        lines = [
            "Quick Reference",
            "=" * 30,
            "",
            "Navigation",
            "  b/e/g/c/t Switch screens",
            "  q         Quit",
            "  ?/F1      Help",
            "  Esc/F3    Back",
            "",
            "On this screen",
            "  r/F5      Refresh stats",
            "",
            "CLI Commands",
            "  lookout check        Enforce patterns",
            "  lookout discover     Find patterns in code",
            "  lookout research     AI-discover patterns",
            "  lookout init         Set up a project",
        ]
        self.query_one("#quick-ref-content", Static).update("\n".join(lines))

    def action_noop(self) -> None:
        """Dashboard is already home — Esc does nothing."""

    def action_refresh(self) -> None:
        self._refresh_stats()
        self.notify("Dashboard refreshed")
