from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path
from typing import Any

import yaml

from lookout.models import (
    Finding,
    ForbiddenCheck,
    MustWrapCheck,
    PatternDiscoveryCheck,
    PatternInstance,
    PatternSpecFile,
    RawCheck,
    RequiredWithCheck,
    RuleCheck,
    RuleError,
    RuleSpecFile,
)
from lookout.specs import SpecUnion, is_discovery_spec


def _str_presenter(dumper: yaml.BaseDumper, data: str) -> yaml.ScalarNode:
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, _str_presenter)  # type: ignore[arg-type]
yaml.add_representer(str, _str_presenter, Dumper=yaml.SafeDumper)  # type: ignore[arg-type]


def compile_semgrep_config(specs: list[SpecUnion]) -> dict[str, Any]:
    rules: list[dict[str, Any]] = []
    for spec in specs:
        if isinstance(spec, PatternSpecFile):
            rules.extend(_flatten_pattern_spec(spec))
        else:
            _compile_v1_spec(spec, rules)
    return {"rules": rules}


def _expand_raw_check(check: RawCheck) -> list[dict[str, Any]]:
    """Parse a RawCheck config and return its rules list."""
    raw_config = yaml.safe_load(check.config)
    result: list[dict[str, Any]] = raw_config.get("rules", [])
    return result


def _compile_v1_spec(spec: RuleSpecFile, rules: list[dict[str, Any]]) -> None:
    rule = spec.rule
    check = rule.check
    if isinstance(check, RawCheck):
        rules.extend(_expand_raw_check(check))
        return

    compiled: dict[str, Any] = {
        "id": f"{rule.id.lower()}-impl",
        "languages": rule.languages,
        "severity": rule.severity.upper(),
        "message": rule.reporting.default_message,
    }

    compiled["patterns"] = _compile_patterns(check)
    rules.append(compiled)


def _compile_variant(
    rule_id: str, language: str, severity: str, message: str, check: RuleCheck
) -> dict[str, Any]:
    """Compile a single variant check into a Semgrep rule dict."""
    return {
        "id": rule_id,
        "languages": [language],
        "severity": severity.upper(),
        "message": message,
        "patterns": _compile_patterns(check),
    }


def _flatten_pattern_spec(spec: PatternSpecFile) -> list[dict[str, Any]]:
    """Expand a hierarchical PatternSpecFile into flat Semgrep rules."""
    rules: list[dict[str, Any]] = []
    pattern = spec.pattern
    pattern_id = pattern.id.lower()
    severity = pattern.severity
    message = pattern.reporting.default_message

    for variant in pattern.variants:
        language = variant.language

        if variant.generic is not None:
            check = variant.generic.check
            if isinstance(check, RawCheck):
                rules.extend(_expand_raw_check(check))
            else:
                rule_id = f"{pattern_id}-{language}-impl"
                rules.append(_compile_variant(rule_id, language, severity, message, check))

        for fw in variant.frameworks:
            check = fw.check
            if isinstance(check, RawCheck):
                rules.extend(_expand_raw_check(check))
            else:
                rule_id = f"{pattern_id}-{language}-{fw.name}-impl"
                rules.append(_compile_variant(rule_id, language, severity, message, check))

    return rules


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


def build_spec_index(specs: list[SpecUnion]) -> dict[str, SpecUnion]:
    """Build an index from pattern/rule ID to spec for result parsing."""
    return {get_spec_id(spec): spec for spec in specs}


def _get_spec_metadata(spec: SpecUnion) -> tuple[str, str, str, int, str]:
    """Extract (title, category, severity, tier, confidence) from a spec."""
    if isinstance(spec, PatternSpecFile):
        p = spec.pattern
        return p.title, p.category, p.severity, p.tier, p.reporting.confidence
    r = spec.rule
    return r.title, r.category, r.severity, r.tier, r.reporting.confidence


def get_spec_id(spec: SpecUnion) -> str:
    """Extract the ID from either a RuleSpecFile or PatternSpecFile."""
    if isinstance(spec, PatternSpecFile):
        return spec.pattern.id
    return spec.rule.id


def parse_semgrep_output(
    output: str, spec_index: dict[str, SpecUnion]
) -> tuple[list[Finding], list[PatternInstance], list[RuleError]]:
    """Parse Semgrep output into findings (violations), pattern instances, and errors.

    Args:
        output: JSON output from Semgrep
        spec_index: Map of pattern IDs to specs

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
        rule_id = _extract_pattern_id(error.get("rule_id", ""))
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
        pattern_id = _extract_pattern_id(check_id)
        spec = spec_index.get(pattern_id)
        if not spec:
            continue

        extra = result.get("extra", {})
        title, category, severity, tier, confidence = _get_spec_metadata(spec)

        if is_discovery_spec(spec):
            pattern_instances.append(
                PatternInstance(
                    pattern_id=pattern_id,
                    title=title,
                    category=category,
                    file=result.get("path", ""),
                    line=result.get("start", {}).get("line", 0),
                    snippet=_normalize_snippet(extra.get("lines", "")),
                    confidence=confidence,
                )
            )
        else:
            findings.append(
                Finding(
                    pattern_id=pattern_id,
                    title=title,
                    category=category,
                    severity=severity,
                    file=result.get("path", ""),
                    line=result.get("start", {}).get("line", 0),
                    message=extra.get("message", ""),
                    snippet=_normalize_snippet(extra.get("lines", "")),
                    engine="semgrep",
                    tier=tier,
                )
            )

    return findings, pattern_instances, errors


# Pattern ID regex: matches identifiers like "arch-001", "py-sec-001", "di-001"
_PATTERN_ID_RE = re.compile(r"^([a-z]+(?:-[a-z]+)*-\d{3})", re.IGNORECASE)


def _extract_pattern_id(check_id: str) -> str:
    """Extract pattern ID from Semgrep's namespaced check ID.

    Handles both v1 IDs (arch-001-impl) and v2 compound IDs
    (di-001-python-django-impl).

    Examples:
        "tmp.test-abc.arch-003-impl" -> "ARCH-003"
        "arch-003-impl" -> "ARCH-003"
        "di-001-python-impl" -> "DI-001"
        "di-001-python-django-impl" -> "DI-001"
        "py-sec-001-impl" -> "PY-SEC-001"
    """
    if not check_id:
        return ""

    # Remove Semgrep namespace (everything before last dot)
    if "." in check_id:
        check_id = check_id.split(".")[-1]

    # Remove -impl suffix if present
    if check_id.endswith("-impl"):
        check_id = check_id[:-5]

    # Try to extract a pattern ID prefix (e.g., "arch-001" from "arch-001-python-django")
    match = _PATTERN_ID_RE.match(check_id)
    if match:
        return match.group(1).upper()

    return check_id.upper()


def _normalize_snippet(lines: Any) -> str:
    if isinstance(lines, str):
        return lines.strip()
    if isinstance(lines, list):
        return "\n".join(str(line) for line in lines).strip()
    return ""
