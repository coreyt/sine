"""Pattern detail panel widget."""

from __future__ import annotations

from rich.text import Text
from textual.widgets import Static

from lookout_tui.index.models import PatternIndexEntry


class PatternDetailPanel(Static):
    """Shows detailed information about a selected pattern."""

    def clear_detail(self) -> None:
        self.update("Select a pattern to view details.")

    def show_entry(self, entry: PatternIndexEntry) -> None:
        """Display pattern entry details."""
        lines = Text()
        lines.append(f"  {entry.id}\n", style="bold cyan")
        lines.append(f"  {entry.title}\n\n", style="bold")
        lines.append("  Category: ", style="dim")
        lines.append(f"{entry.category}\n")
        if entry.subcategory:
            lines.append("  Subcategory: ", style="dim")
            lines.append(f"{entry.subcategory}\n")
        lines.append("  Severity: ", style="dim")
        lines.append(f"{entry.severity}\n")
        lines.append("  Tier: ", style="dim")
        lines.append(f"{entry.tier}\n")
        lines.append("  Schema: ", style="dim")
        lines.append(f"v{entry.schema_version}\n")
        if entry.tags:
            lines.append("  Tags: ", style="dim")
            lines.append(f"{', '.join(entry.tags)}\n")
        lines.append("\n  Languages: ", style="dim")
        lines.append(f"{', '.join(entry.languages) or 'none'}\n")
        lines.append("  Variants: ", style="dim")
        lines.append(f"{entry.variant_count}\n")
        lines.append("  Frameworks: ", style="dim")
        lines.append(f"{entry.framework_count}\n")
        lines.append("\n  Source: ", style="dim")
        lines.append(f"{entry.source_file}\n")
        self.update(lines)
