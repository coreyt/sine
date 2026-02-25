"""Command-line interface for Sine."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from sine.discovery.models import DiscoveredPattern

from sine.config import SineConfig
from sine.rules_loader import load_all_rules
from sine.runner import (
    format_findings_json,
    format_findings_text,
    format_pattern_instances_text,
    run_sine,
)
from sine.sarif import format_findings_sarif


@click.group()
@click.version_option()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Sine: Structural Governance Engine for code pattern enforcement."""
    # Load config
    config = SineConfig.load()

    # Store config in context (though default_map is easier)
    ctx.ensure_object(dict)
    ctx.obj["config"] = config

    # Set defaults for subcommands
    # Note: Click's default_map expects keys to match command names if they are nested,
    # or parameter names if we are setting them directly.
    # Since we have flat commands, we map them directly.

    ctx.default_map = {
        "check": {
            "rules_dir": config.rules_dir,
            "target": config.target,
            "format": config.format,
            "fail_on_rule_error": config.fail_on_rule_error,
        },
        "discover": {
            "rules_dir": config.rules_dir,
            "target": config.target,
            "fail_on_rule_error": config.fail_on_rule_error,
        },
        "promote": {
            "patterns_dir": config.patterns_dir,
            "output_dir": config.rules_dir,  # Default output to rules_dir
        },
        "research": {
            "patterns_dir": config.patterns_dir,
        },
        "validate": {
            "patterns_dir": config.patterns_dir,
        },
    }


@cli.command()
@click.option(
    "--rules-dir",
    type=click.Path(path_type=Path),
    help="Directory containing rule specifications",
)
@click.option(
    "--update-baseline",
    is_flag=True,
    help="Update baseline with current findings",
)
@click.option(
    "--format",
    type=click.Choice(["text", "json", "sarif"]),
    help="Output format",
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
@click.option(
    "--fail-on-rule-error",
    is_flag=True,
    help="Exit with error if any rules fail to execute",
)
def check(
    rules_dir: Path | None,
    update_baseline: bool,
    format: str | None,
    dry_run: bool,
    target: tuple[Path, ...],
    fail_on_rule_error: bool,
) -> None:
    """Run structural governance checks on your codebase."""
    # Note: Click injects defaults from default_map, so values shouldn't be None
    # unless they are missing from config AND CLI. But we have Pydantic defaults.
    # However, targets coming from default_map might be a list, while CLI gives a tuple.

    # If parameters are None, it means they weren't in config OR CLI (shouldn't happen with our setup).
    # But for safety:

    config = click.get_current_context().obj["config"]

    final_rules_dir = rules_dir or config.rules_dir
    final_format = format or config.format
    final_target = list(target) if target else config.target
    final_fail_on_rule_error = fail_on_rule_error  # Default map handles the config fallback

    # Load rule specifications (built-in + user rules)
    specs = load_all_rules(user_rules_dir=final_rules_dir if final_rules_dir.exists() else None)

    if not specs:
        click.echo("No rule specifications found (neither built-in nor user rules)", err=True)
        sys.exit(1)

    # Run the enforcement engine
    findings, new_findings, _, errors, dry_output = run_sine(
        specs=specs,
        targets=final_target,
        dry_run=dry_run,
        update_baseline=update_baseline,
        discovery_only=False,
    )

    # Report rule execution errors
    if errors:
        click.echo(f"Warning: {len(errors)} rules failed to execute:", err=True)
        for error in errors:
            click.echo(f"  [{error.rule_id}] {error.message}", err=True)
        click.echo("", err=True)
        if final_fail_on_rule_error:
            sys.exit(1)

    # Report results
    if dry_run:
        click.echo(dry_output)
        return

    if update_baseline:
        click.echo(f"✓ Baseline updated with {len(findings)} findings")
        return

    # Show findings in requested format
    if final_format == "json":
        click.echo(format_findings_json(findings))
    elif final_format == "sarif":
        click.echo(format_findings_sarif(findings))
    else:
        click.echo(format_findings_text(findings))

    # Exit with error code if there are new findings
    if new_findings:
        if final_format == "text":
            click.echo(f"\n❌ {len(new_findings)} new violation(s) found", err=True)
        sys.exit(1)
    else:
        if final_format == "text":
            click.echo("\n✓ No new violations")


@cli.command()
@click.option(
    "--rules-dir",
    type=click.Path(path_type=Path),
    help="Directory containing pattern discovery specifications",
)
@click.option(
    "--target",
    type=click.Path(exists=True, path_type=Path),
    multiple=True,
    help="Paths to analyze (defaults to current directory)",
)
@click.option(
    "--fail-on-rule-error",
    is_flag=True,
    help="Exit with error if any rules fail to execute",
)
def discover(rules_dir: Path | None, target: tuple[Path, ...], fail_on_rule_error: bool) -> None:
    """Discover pattern instances in your codebase."""
    config = click.get_current_context().obj["config"]
    final_rules_dir = rules_dir or config.rules_dir
    final_target = list(target) if target else config.target
    final_fail_on_rule_error = fail_on_rule_error

    # Load discovery specs (built-in + user rules)
    specs = load_all_rules(user_rules_dir=final_rules_dir if final_rules_dir.exists() else None)

    # Filter to only discovery specs
    discovery_specs = [s for s in specs if s.rule.check.type == "pattern_discovery"]

    if not discovery_specs:
        click.echo(f"No pattern discovery specifications found in {final_rules_dir}", err=True)
        sys.exit(1)

    # Run pattern discovery
    _, _, instances, errors, _ = run_sine(
        specs=discovery_specs,
        targets=final_target,
        discovery_only=True,
    )

    # Report rule execution errors
    if errors:
        click.echo(f"Warning: {len(errors)} discovery rules failed to execute:", err=True)
        for error in errors:
            click.echo(f"  [{error.rule_id}] {error.message}", err=True)
        click.echo("", err=True)
        if final_fail_on_rule_error:
            sys.exit(1)

    # Report discovered patterns
    click.echo(format_pattern_instances_text(instances))


@cli.command()
@click.option(
    "--rules-dir",
    type=click.Path(path_type=Path),
    default=".sine-rules",
    help="Directory to create for local rules",
)
@click.option(
    "--copy-built-in-rules",
    is_flag=True,
    help="Copy all built-in rules to local rules directory",
)
@click.option(
    "--non-interactive",
    is_flag=True,
    help="Skip interactive prompts and use defaults",
)
def init(rules_dir: Path, copy_built_in_rules: bool, non_interactive: bool) -> None:
    """Initialize Sine configuration for your project.

    Creates a configuration file (sine.toml or pyproject.toml) and sets up
    the rules directory. Built-in rules are always available; this command
    optionally copies them locally for customization.

    Examples:

        # Interactive setup (recommended)
        sine init

        # Non-interactive with defaults
        sine init --non-interactive

        # Copy built-in rules for customization
        sine init --copy-built-in-rules
    """
    from sine.init import run_init

    run_init(
        rules_dir=rules_dir,
        copy_built_in_rules=copy_built_in_rules,
        interactive=not non_interactive,
    )


@cli.command()
@click.argument("pattern-id")
@click.option(
    "--patterns-dir",
    type=click.Path(exists=True, path_type=Path),
    help="Directory containing discovered patterns",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    help="Directory to save the promoted rule spec",
)
def promote(pattern_id: str, patterns_dir: Path | None, output_dir: Path | None) -> None:
    """Promote a validated pattern to an enforcement rule."""
    config = click.get_current_context().obj["config"]
    final_patterns_dir = patterns_dir or config.patterns_dir
    final_output_dir = output_dir or config.rules_dir

    from sine.discovery.models import ValidatedPattern
    from sine.discovery.storage import PatternStorage
    from sine.promotion import promote_to_spec, save_spec

    storage = PatternStorage(final_patterns_dir)

    # Try to load from validated stage
    pattern = storage.load_pattern(pattern_id, stage="validated", model_class=ValidatedPattern)

    if not pattern:
        click.echo(
            f"Error: Validated pattern {pattern_id} not found in {final_patterns_dir}", err=True
        )
        sys.exit(1)

    # Promote to spec
    spec = promote_to_spec(pattern)

    # Save to rules directory
    save_path = save_spec(spec, final_output_dir)

    click.echo(f"✓ Promoted {pattern_id} to {save_path}")


@cli.command()
@click.option(
    "--focus",
    required=True,
    help="What patterns to look for (e.g. 'dependency injection patterns')",
)
@click.option(
    "--category",
    default="architecture",
    help="Pattern category to search",
)
@click.option(
    "--languages",
    multiple=True,
    help="Programming languages to filter by (can be repeated)",
)
@click.option(
    "--provider",
    default="anthropic",
    help="LLM provider for extraction (anthropic, openai, gemini)",
)
@click.option(
    "--patterns-dir",
    type=click.Path(path_type=Path),
    help="Directory to save discovered patterns",
)
@click.option(
    "--max-results",
    default=10,
    help="Maximum number of patterns to discover",
)
@click.option(
    "--no-llm",
    is_flag=True,
    help="Use keyword-only extraction (no LLM API key required)",
)
def research(
    focus: str,
    category: str,
    languages: tuple[str, ...],
    provider: str,
    patterns_dir: Path | None,
    max_results: int,
    no_llm: bool,
) -> None:
    """Discover architectural patterns via AI-powered web research.

    Searches trusted sources and extracts coding patterns, saving them
    to the patterns directory for later validation and promotion.

    Examples:

        # Search with keyword-only extraction (no API key needed)
        sine research --focus "dependency injection" --no-llm

        # Search with LLM extraction (requires ANTHROPIC_API_KEY)
        sine research --focus "error handling patterns" --languages python
    """
    config = click.get_current_context().obj["config"]
    final_patterns_dir = patterns_dir or config.patterns_dir

    patterns = asyncio.run(
        _run_research(
            focus=focus,
            category=category,
            languages=list(languages),
            provider=provider,
            no_llm=no_llm,
            max_results=max_results,
        )
    )

    if not patterns:
        click.echo("No patterns discovered.")
        return

    from sine.discovery.storage import PatternStorage

    storage = PatternStorage(final_patterns_dir)
    for pattern in patterns:
        storage.save_pattern(pattern, "raw")

    click.echo(f"✓ {len(patterns)} patterns saved to {final_patterns_dir}/raw/")


async def _run_research(
    focus: str,
    category: str,
    languages: list[str],
    provider: str,
    no_llm: bool,
    max_results: int,
) -> list[DiscoveredPattern]:
    """Async helper that runs the discovery pipeline."""
    from sine.discovery.agents.architecture import ArchitectureAgent
    from sine.discovery.agents.base import SearchConstraints, SearchFocus
    from sine.discovery.search.credibility import SourceCredibilityScorer
    from sine.discovery.search.web_search import WebSearchClient

    scorer = SourceCredibilityScorer()

    if no_llm:
        from sine.discovery.extractors.keyword import KeywordExtractor

        extractor_ctx: object = KeywordExtractor()
    else:
        from sine.discovery.extractors.hybrid import HybridExtractor
        from sine.discovery.extractors.llm import LLMProvider

        extractor_ctx = HybridExtractor(llm_provider=LLMProvider(provider))

    from sine.discovery.extractors.base import PatternExtractor

    async with (  # noqa: SIM117
        WebSearchClient(scorer) as search_client,
        extractor_ctx as extractor,  # type: ignore[attr-defined]
    ):
        assert isinstance(extractor, PatternExtractor)
        agent = ArchitectureAgent(extractor=extractor, search_client=search_client)

        focus_obj = SearchFocus(
            focus_type=category,
            description=focus,
            keywords=[focus],
        )
        constraints = SearchConstraints(
            languages=languages,
            max_results=max_results,
        )

        return await agent.discover_patterns(focus_obj, constraints)


@cli.command()
@click.argument("pattern-id")
@click.option(
    "--patterns-dir",
    type=click.Path(path_type=Path),
    help="Directory containing discovered patterns",
)
@click.option(
    "--notes",
    default="",
    help="Review notes to attach to the validated pattern",
)
@click.option(
    "--tier",
    type=click.IntRange(1, 3),
    default=None,
    help="Override the inferred tier (1=Non-Negotiable, 2=Strong Recommendation, 3=Contextual)",
)
def validate(
    pattern_id: str,
    patterns_dir: Path | None,
    notes: str,
    tier: int | None,
) -> None:
    """Validate a discovered pattern and promote it to the validated stage.

    Loads a raw pattern from the patterns directory, attaches validation
    metadata, and saves it to the validated stage for later promotion.

    Examples:

        sine validate ARCH-DI-001
        sine validate ARCH-DI-001 --tier 1 --notes "Confirmed by team review"
    """
    config = click.get_current_context().obj["config"]
    final_patterns_dir = patterns_dir or config.patterns_dir

    from sine.discovery.models import DiscoveredPattern, ValidatedPattern
    from sine.discovery.storage import PatternStorage

    storage = PatternStorage(final_patterns_dir)

    raw = storage.load_pattern(pattern_id, stage="raw", model_class=DiscoveredPattern)

    if not raw:
        click.echo(
            f"Error: Raw pattern {pattern_id} not found in {final_patterns_dir}",
            err=True,
        )
        sys.exit(1)

    validated_by = os.getenv("USER", "unknown")
    validated = ValidatedPattern.from_discovered(
        raw,
        validated_by=validated_by,
        review_notes=notes,
        tier_override=tier,
    )

    storage.save_pattern(validated, "validated")

    click.echo(
        f"✓ Validated {pattern_id} (tier {validated.effective_tier})"
        f" — run 'sine promote {pattern_id}' to create enforcement rule"
    )


if __name__ == "__main__":
    cli()
