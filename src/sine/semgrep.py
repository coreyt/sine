from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any

import yaml

from sine.models import (
    Finding,
    ForbiddenCheck,
    MustWrapCheck,
    PatternDiscoveryCheck,
    PatternInstance,
    RawCheck,
    RequiredWithCheck,
    RuleCheck,
    RuleError,
    RuleSpecFile,
)


def _str_presenter(dumper: yaml.BaseDumper, data: str) -> yaml.ScalarNode:
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, _str_presenter)  # type: ignore[arg-type]
yaml.add_representer(str, _str_presenter, Dumper=yaml.SafeDumper)  # type: ignore[arg-type]


def compile_semgrep_config(specs: list[RuleSpecFile]) -> dict[str, Any]:
    rules: list[dict[str, Any]] = []
    for spec in specs:
        rule = spec.rule
        check = rule.check
        if isinstance(check, RawCheck):
            raw_config = yaml.safe_load(check.config)
            rules.extend(raw_config.get("rules", []))
            continue

        compiled: dict[str, Any] = {
            "id": f"{rule.id.lower()}-impl",
            "languages": rule.languages,
            "severity": rule.severity.upper(),
            "message": rule.reporting.default_message,
        }

        compiled["patterns"] = _compile_patterns(check)
        rules.append(compiled)

    return {"rules": rules}


def _compile_patterns(check: RuleCheck) -> list[dict[str, Any]]:
    if isinstance(check, MustWrapCheck):
        return _compile_must_wrap(check)
    if isinstance(check, ForbiddenCheck):
        return [{"pattern": check.pattern}]
    if isinstance(check, RequiredWithCheck):
        return _compile_required_with(check)
    if isinstance(check, PatternDiscoveryCheck):
        return _compile_pattern_discovery(check)
    raise ValueError(f"Unsupported check type: {type(check)}")


def _compile_must_wrap(check: MustWrapCheck) -> list[dict[str, Any]]:
    patterns: list[dict[str, Any]] = [
        {"pattern-either": [{"pattern": target + "(...)"} for target in check.target]}
    ]
    for wrapper in check.wrapper:
        patterns.append({"pattern-not-inside": _wrapper_pattern(wrapper)})
    return patterns


def _compile_required_with(check: RequiredWithCheck) -> list[dict[str, Any]]:
    if_present = check.if_present
    must_have = check.must_have

    patterns = [
        {
            "pattern": textwrap.dedent(
                f"""
                {if_present}
                def $FUNC(...):
                  ...
                """
            ).strip()
        }
    ]
    patterns.append({"pattern-not-inside": _decorator_pair(must_have, if_present)})
    patterns.append({"pattern-not-inside": _decorator_pair(if_present, must_have)})
    return patterns


def _compile_pattern_discovery(check: PatternDiscoveryCheck) -> list[dict[str, Any]]:
    """Compile pattern discovery check to Semgrep patterns.

    Pattern discovery finds instances of patterns (descriptive), not violations (prescriptive).
    """
    # Use pattern-either to match any of the provided patterns
    patterns: list[dict[str, Any]] = [{"pattern-either": [{"pattern": p} for p in check.patterns]}]

    if check.metavariable_regex:
        for mr in check.metavariable_regex:
            patterns.append(
                {
                    "metavariable-regex": {
                        "metavariable": mr.metavariable,
                        "regex": mr.regex,
                    }
                }
            )
    return patterns


def _wrapper_pattern(wrapper: str) -> str:
    if wrapper.startswith("@"):
        return textwrap.dedent(
            f"""
            {wrapper}
            def $FUNC(...):
              ...
            """
        ).strip()
    return textwrap.dedent(
        f"""
        with {wrapper}(...):
          ...
        """
    ).strip()


def _decorator_pair(first: str, second: str) -> str:
    return textwrap.dedent(
        f"""
        {first}
        {second}
        def $FUNC(...):
          ...
        """
    ).strip()


def build_semgrep_command(config_path: Path, targets: list[Path]) -> list[str]:
    return [
        "semgrep",
        "--config",
        str(config_path),
        "--json",
        "--metrics=off",
        *[str(target) for target in targets],
    ]


def render_dry_run(config: dict[str, Any], config_path: Path, targets: list[Path]) -> str:
    compiled_yaml = yaml.safe_dump(config, sort_keys=False)
    command = " ".join(build_semgrep_command(config_path, targets))
    return "\n".join(
        [
            "[Tier 1: Semgrep Rules]",
            f"Would write to: {config_path}",
            "",
            compiled_yaml.strip(),
            "",
            "Would execute:",
            f"  {command}",
        ]
    )


def parse_semgrep_output(
    output: str, spec_index: dict[str, RuleSpecFile]
) -> tuple[list[Finding], list[PatternInstance], list[RuleError]]:
    """Parse Semgrep output into findings (violations), pattern instances, and errors.

    Args:
        output: JSON output from Semgrep
        spec_index: Map of guideline IDs to rule specs

    Returns:
        Tuple of (findings, pattern_instances, errors)
    """
    data = json.loads(output)
    results = data.get("results", [])
    errors_data = data.get("errors", [])
    findings: list[Finding] = []
    pattern_instances: list[PatternInstance] = []
    errors: list[RuleError] = []

    for error in errors_data:
        # We generally care about rule parse errors or execution errors
        # that are tied to specific rules.
        rule_id = _extract_guideline_id(error.get("rule_id", ""))
        errors.append(
            RuleError(
                rule_id=rule_id,
                message=error.get("message", "Unknown error"),
                level=error.get("level", "error"),
                type=error.get("type", "SemgrepError"),
            )
        )

    for result in results:
        check_id = result.get("check_id", "")
        guideline_id = _extract_guideline_id(check_id)
        spec = spec_index.get(guideline_id)
        if not spec:
            continue

        extra = result.get("extra", {})

        # Check if this is pattern discovery or enforcement
        if spec.rule.check.type == "pattern_discovery":
            # This is a pattern instance, not a violation
            pattern_instances.append(
                PatternInstance(
                    pattern_id=guideline_id,
                    title=spec.rule.title,
                    category=spec.rule.category,
                    file=result.get("path", ""),
                    line=result.get("start", {}).get("line", 0),
                    snippet=_normalize_snippet(extra.get("lines", "")),
                    confidence=spec.rule.reporting.confidence,
                )
            )
        else:
            # This is a violation finding
            findings.append(
                Finding(
                    guideline_id=guideline_id,
                    title=spec.rule.title,
                    category=spec.rule.category,
                    severity=spec.rule.severity,
                    file=result.get("path", ""),
                    line=result.get("start", {}).get("line", 0),
                    message=extra.get("message", ""),
                    snippet=_normalize_snippet(extra.get("lines", "")),
                    engine="semgrep",
                    tier=spec.rule.tier,
                )
            )

    return findings, pattern_instances, errors


def _extract_guideline_id(check_id: str) -> str:
    """Extract guideline ID from Semgrep's namespaced check ID.

    Semgrep namespaces rule IDs based on config file path.
    This function extracts just the base rule ID.

    Examples:
        "tmp.test-abc.arch-003-impl" -> "ARCH-003"
        "arch-003-impl" -> "ARCH-003"
        "path.to.config.arch-001-impl" -> "ARCH-001"
    """
    if not check_id:
        return ""

    # Remove -impl suffix if present
    if check_id.endswith("-impl"):
        check_id = check_id[:-5]

    # Remove Semgrep namespace (everything before last dot)
    if "." in check_id:
        check_id = check_id.split(".")[-1]

    return check_id.upper()


def _normalize_snippet(lines: Any) -> str:
    if isinstance(lines, str):
        return lines.strip()
    if isinstance(lines, list):
        return "\n".join(str(line) for line in lines).strip()
    return ""
