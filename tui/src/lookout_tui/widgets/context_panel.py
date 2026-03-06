"""Context panel widget — detail view for registry nodes."""

from __future__ import annotations

from lookout.models import PatternSpecFile
from rich.text import Text
from textual.widgets import Static

from lookout_tui.pipeline.models import StageResult, StageStatus


def build_pattern_text(spec: PatternSpecFile) -> Text:
    """Build Rich Text for pattern-level metadata."""
    p = spec.pattern
    lines = Text()
    lines.append(f"  {p.id}\n", style="bold cyan")
    lines.append(f"  {p.title}\n\n", style="bold")

    lines.append("  Status: ", style="dim")
    status_style = {"active": "green", "draft": "yellow", "deprecated": "red"}.get(
        p.status, ""
    )
    lines.append(f"{p.status}\n", style=status_style)

    lines.append("  Category: ", style="dim")
    lines.append(f"{p.category}\n")
    if p.subcategory:
        lines.append("  Subcategory: ", style="dim")
        lines.append(f"{p.subcategory}\n")
    lines.append("  Severity: ", style="dim")
    lines.append(f"{p.severity}\n")
    lines.append("  Tier: ", style="dim")
    lines.append(f"{p.tier}\n")
    if p.tags:
        lines.append("  Tags: ", style="dim")
        lines.append(f"{', '.join(p.tags)}\n")
    lines.append("\n  Description:\n", style="dim")
    lines.append(f"  {p.description.strip()}\n")
    lines.append("\n  Rationale:\n", style="dim")
    lines.append(f"  {p.rationale.strip()}\n")

    if p.variants:
        lines.append("\n  Languages: ", style="dim")
        langs = [v.language for v in p.variants]
        lines.append(f"{', '.join(langs)}\n")
        total_fw = sum(len(v.frameworks) for v in p.variants)
        lines.append("  Frameworks: ", style="dim")
        lines.append(f"{total_fw}\n")
    else:
        lines.append("\n  No variants yet.\n", style="dim")

    return lines


def build_variant_text(
    spec: PatternSpecFile,
    language: str,
    framework: str | None = None,
) -> Text:
    """Build Rich Text for language or framework variant detail."""
    p = spec.pattern
    lines = Text()
    lines.append(f"  {p.id}", style="bold cyan")
    lines.append(f" > {language}", style="bold")
    if framework:
        lines.append(f" > {framework}", style="bold")
    lines.append("\n\n")

    variant = next((v for v in p.variants if v.language == language), None)
    if not variant:
        lines.append("  Language variant not found.\n", style="red")
        return lines

    if framework and framework != "generic":
        fw = next((f for f in variant.frameworks if f.name == framework), None)
        if not fw:
            lines.append(f"  Framework '{framework}' not yet created.\n", style="yellow")
        else:
            lines.append("  Check type: ", style="dim")
            lines.append(f"{fw.check.type}\n")
            if fw.version_constraint:
                lines.append("  Version: ", style="dim")
                lines.append(f"{fw.version_constraint}\n")
            if fw.examples.good:
                lines.append(f"\n  Good examples: {len(fw.examples.good)}\n", style="dim")
            if fw.examples.bad:
                lines.append(f"  Bad examples: {len(fw.examples.bad)}\n", style="dim")
    else:
        if variant.generic:
            lines.append("  Check type: ", style="dim")
            lines.append(f"{variant.generic.check.type}\n")
            if variant.version_constraint:
                lines.append("  Version: ", style="dim")
                lines.append(f"{variant.version_constraint}\n")
            if variant.generic.examples.good:
                lines.append(
                    f"\n  Good examples: {len(variant.generic.examples.good)}\n",
                    style="dim",
                )
            if variant.generic.examples.bad:
                lines.append(
                    f"  Bad examples: {len(variant.generic.examples.bad)}\n",
                    style="dim",
                )
        else:
            lines.append("  Generic variant not yet generated.\n", style="yellow")

    return lines


def build_generation_text(result: StageResult) -> Text:
    """Build Rich Text for generation output review."""
    lines = Text()
    lines.append("  Generation Result\n\n", style="bold")

    if result.language:
        lines.append("  Target: ", style="dim")
        label = result.language
        if result.framework:
            label += f"/{result.framework}"
        lines.append(f"{label}\n")

    if result.model:
        lines.append("  Model: ", style="dim")
        lines.append(f"{result.model}\n")

    lines.append("  Status: ", style="dim")
    status_style = {
        StageStatus.AWAITING_REVIEW: "cyan",
        StageStatus.APPROVED: "green",
        StageStatus.REJECTED: "red",
        StageStatus.ERROR: "red bold",
    }.get(result.status, "")
    lines.append(f"{result.status.value}\n\n", style=status_style)

    if result.status == StageStatus.ERROR:
        lines.append(f"  Error: {result.error}\n", style="red")
    elif result.output:
        lines.append("─" * 60 + "\n")
        lines.append(result.output)
    else:
        lines.append("  No output yet.\n", style="dim")

    return lines


class ContextPanel(Static):
    """Shows pattern/language/framework detail or generation output."""

    def show_pattern(self, spec: PatternSpecFile) -> None:
        self.update(build_pattern_text(spec))

    def show_variant(
        self,
        spec: PatternSpecFile,
        language: str,
        framework: str | None = None,
    ) -> None:
        self.update(build_variant_text(spec, language, framework))

    def show_generation(self, result: StageResult) -> None:
        self.update(build_generation_text(result))

    def clear_panel(self) -> None:
        self.update("Select a node in the registry tree.")
