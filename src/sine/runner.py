from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import yaml

from sine.baseline import BASELINE_PATH, Baseline, filter_findings, load_baseline, write_baseline
from sine.models import Finding, PatternInstance, RuleError, RuleSpecFile
from sine.semgrep import (
    build_semgrep_command,
    compile_semgrep_config,
    parse_semgrep_output,
    render_dry_run,
)


def check_semgrep_version() -> str | None:
    try:
        result = subprocess.run(
            ["semgrep", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None
    return result.stdout.strip()


def run_sine(
    specs: list[RuleSpecFile],
    targets: list[Path],
    dry_run: bool = False,
    update_baseline: bool = False,
    discovery_only: bool = False,
) -> tuple[list[Finding], list[Finding], list[PatternInstance], list[RuleError], str | None]:
    """Run Sine checks (enforcement and/or discovery).

    Args:
        specs: List of rule specifications to check
        targets: Paths to analyze
        dry_run: If True, show compiled rules without running
        update_baseline: If True, update baseline with current findings
        discovery_only: If True, only run pattern discovery rules

    Returns:
        Tuple of (all_findings, new_findings, pattern_instances, errors, dry_run_output)
    """
    # Filter specs based on mode
    if discovery_only:
        specs = [s for s in specs if s.rule.check.type == "pattern_discovery"]

    config = compile_semgrep_config(specs)
    with tempfile.TemporaryDirectory(prefix="sine-") as temp_dir:
        config_path = Path(temp_dir) / "semgrep.yaml"
        if dry_run:
            dry_output = render_dry_run(config, config_path, targets)
            return [], [], [], [], dry_output

        config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        command = build_semgrep_command(config_path, targets)
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        # Semgrep returns:
        # 0: Success, no issues found (unless --error is set)
        # 1: Issues found (if --error is set or implied)
        # 2: Semgrep failed (e.g. parse error in rules) - but may still have results
        if result.returncode not in (0, 1, 2):
            raise RuntimeError(
                f"Semgrep execution failed with code {result.returncode}:\n{result.stderr.strip()}"
            )

        spec_index = {spec.rule.id: spec for spec in specs}
        findings, pattern_instances, errors = parse_semgrep_output(result.stdout, spec_index)
        baseline = load_baseline(BASELINE_PATH)
        new_findings = filter_findings(findings, baseline)

        if update_baseline:
            write_baseline(Baseline.from_findings(findings), BASELINE_PATH)
            return findings, [], pattern_instances, errors, None

        return findings, new_findings, pattern_instances, errors, None


def format_findings_text(findings: list[Finding]) -> str:
    if not findings:
        return "No violations found."
    lines = []
    for finding in findings:
        lines.append(f"{finding.file}:{finding.line} [{finding.guideline_id}] {finding.message}")
    return "\n".join(lines)


def format_findings_json(findings: list[Finding]) -> str:
    return json.dumps([finding.__dict__ for finding in findings], indent=2)


def format_pattern_instances_text(instances: list[PatternInstance]) -> str:
    """Format pattern instances for text output (discovery mode)."""
    if not instances:
        return "No patterns discovered."

    # Group by pattern ID
    by_pattern: dict[str, list[PatternInstance]] = {}
    for instance in instances:
        if instance.pattern_id not in by_pattern:
            by_pattern[instance.pattern_id] = []
        by_pattern[instance.pattern_id].append(instance)

    lines = ["", "Pattern Discovery Results", "=" * 60, ""]

    for pattern_id in sorted(by_pattern.keys()):
        pattern_instances = by_pattern[pattern_id]
        first = pattern_instances[0]
        lines.append(f"{pattern_id}: {first.title}")
        lines.append(f"  Category: {first.category}")
        lines.append(f"  Instances found: {len(pattern_instances)}")
        lines.append("")

        # Show first 5 instances
        for instance in pattern_instances[:5]:
            lines.append(f"  - {instance.file}:{instance.line}")

        if len(pattern_instances) > 5:
            lines.append(f"  ... and {len(pattern_instances) - 5} more")

        lines.append("")

    lines.append(f"Total: {len(instances)} pattern instances discovered")
    return "\n".join(lines)


def format_pattern_instances_json(instances: list[PatternInstance]) -> str:
    """Format pattern instances for JSON output."""
    return json.dumps([instance.__dict__ for instance in instances], indent=2)
