"""CLI entry point for Lookout TUI."""

from __future__ import annotations

import click


@click.command()
@click.version_option(package_name="lookout-tui")
def main() -> None:
    """Launch the Lookout TUI."""
    from lookout_tui.app import LookoutApp

    app = LookoutApp()
    app.run()
