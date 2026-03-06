"""Keyboard binding helpers for Monospace TUI §2.2 compliance."""

from __future__ import annotations

from textual.binding import Binding


def ci(
    key: str,
    action: str,
    description: str,
    *,
    priority: bool = False,
    show: bool = True,
    key_display: str | None = None,
) -> list[Binding]:
    """Create case-insensitive binding pair per Monospace TUI §2.2.

    Binds both lower and upper case; only lowercase shown in footer.
    """
    lower = Binding(
        key.lower(),
        action,
        description,
        priority=priority,
        show=show,
        key_display=key_display,
    )
    upper = Binding(
        key.upper(),
        action,
        description,
        priority=priority,
        show=False,
        key_display=key_display,
    )
    return [lower, upper]
