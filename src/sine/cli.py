"""Command-line interface for Sine."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from sine.runner import (
    format_findings_text,
    format_pattern_instances_text,
    run_sine,
)
from sine.specs import load_rule_specs


@click.group()
@click.version_option()
def cli():
    """Sine: Intelligent code pattern enforcement and discovery tool."""
    pass


@cli.command()
@click.option(
    "--rules-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("rules"),
    help="Directory containing rule specifications",
)
@click.option(
    "--update-baseline",
    is_flag=True,
    help="Update baseline with current findings",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show compiled Semgrep rules without running",
)
@click.option(
    "--target",
    type=click.Path(exists=True, path_type=Path),
    multiple=True,
    help="Paths to analyze (defaults to current directory)",
)
def check(rules_dir: Path, update_baseline: bool, dry_run: bool, target: tuple[Path, ...]):
    """Run pattern enforcement checks on your codebase."""
    # Load rule specifications
    try:
        specs = load_rule_specs(rules_dir)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if not specs:
        click.echo(f"No rule specifications found in {rules_dir}", err=True)
        sys.exit(1)

    # Default to current directory if no targets specified
    targets = list(target) if target else [Path(".")]

    # Run the enforcement engine
    findings, new_findings, _, dry_output = run_sine(
        specs=specs,
        targets=targets,
        dry_run=dry_run,
        update_baseline=update_baseline,
        discovery_only=False,
    )

    # Report results
    if dry_run:
        click.echo(dry_output)
        return

    if update_baseline:
        click.echo(f"✓ Baseline updated with {len(findings)} findings")
        return

    # Show findings
    click.echo(format_findings_text(findings))

    # Exit with error code if there are new findings
    if new_findings:
        click.echo(f"\n❌ {len(new_findings)} new violation(s) found", err=True)
        sys.exit(1)
    else:
        click.echo("\n✓ No new violations")


@cli.command()
@click.option(
    "--rules-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("rules"),
    help="Directory containing pattern discovery specifications",
)
@click.option(
    "--target",
    type=click.Path(exists=True, path_type=Path),
    multiple=True,
    help="Paths to analyze (defaults to current directory)",
)
def discover(rules_dir: Path, target: tuple[Path, ...]):
    """Discover pattern instances in your codebase."""
    # Load discovery specs
    try:
        specs = load_rule_specs(rules_dir)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Filter to only discovery specs
    discovery_specs = [s for s in specs if s.rule.check.type == "pattern_discovery"]

    if not discovery_specs:
        click.echo(f"No pattern discovery specifications found in {rules_dir}", err=True)
        sys.exit(1)

    # Default to current directory if no targets specified
    targets = list(target) if target else [Path(".")]

    # Run pattern discovery
    _, _, instances, _ = run_sine(
        specs=discovery_specs,
        targets=targets,
        discovery_only=True,
    )

    # Report discovered patterns
    click.echo(format_pattern_instances_text(instances))


if __name__ == "__main__":
    cli()
