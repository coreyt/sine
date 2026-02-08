from __future__ import annotations

import json

from sine.models import (
    ForbiddenCheck,
    MustWrapCheck,
    RequiredWithCheck,
    RuleCheck,
    RuleExamples,
    RuleReporting,
    RuleSpec,
    RuleSpecFile,
)
from sine.semgrep import compile_semgrep_config, parse_semgrep_output


def _spec_for(check: RuleCheck) -> RuleSpecFile:
    return RuleSpecFile(
        schema_version=1,
        rule=RuleSpec(
            id="ARCH-001",
            title="HTTP calls require resilience wrappers",
            description="Desc",
            rationale="Because",
            tier=1,
            category="resilience",
            severity="error",
            languages=["python"],
            check=check,
            reporting=RuleReporting(
                default_message="HTTP call outside resilience wrapper (ARCH-001)",
                confidence="high",
                documentation_url=None,
            ),
            examples=RuleExamples(good=[], bad=[]),
            references=[],
        ),
    )


def test_compile_must_wrap() -> None:
    spec = _spec_for(
        MustWrapCheck(
            type="must_wrap",
            target=["requests.get"],
            wrapper=["circuit_breaker", "@resilient"],
        )
    )
    config = compile_semgrep_config([spec])
    rule = config["rules"][0]

    assert "arch-001" in rule["id"]
    assert "ARCH-001" in rule["message"]
    assert rule["languages"] == ["python"]
    assert any("pattern-not-inside" in entry for entry in rule["patterns"])


def test_compile_required_with() -> None:
    spec = _spec_for(
        RequiredWithCheck(
            type="required_with",
            if_present="@service",
            must_have="@health_check",
        )
    )
    config = compile_semgrep_config([spec])
    rule = config["rules"][0]
    patterns = [entry for entry in rule["patterns"] if "pattern-not-inside" in entry]

    assert len(patterns) == 2


def test_parse_semgrep_output_normalizes_string_snippet() -> None:
    spec = _spec_for(ForbiddenCheck(type="forbidden", pattern="eval($X)"))
    output = json.dumps(
        {
            "results": [
                {
                    "check_id": "arch-001-impl",
                    "path": "src/app.py",
                    "start": {"line": 12},
                    "extra": {
                        "message": "HTTP call outside resilience wrapper (ARCH-001)",
                        "lines": "requests.get(url)\n",
                    },
                }
            ]
        }
    )

    findings, pattern_instances = parse_semgrep_output(output, {"ARCH-001": spec})
    assert len(findings) == 1
    assert findings[0].snippet == "requests.get(url)"


def test_parse_semgrep_output_maps_multi_segment_guideline_ids() -> None:
    spec = RuleSpecFile(
        schema_version=1,
        rule=RuleSpec(
            id="PY-SEC-001",
            title="No eval",
            description="Desc",
            rationale="Because",
            tier=1,
            category="security",
            severity="error",
            languages=["python"],
            check=ForbiddenCheck(type="forbidden", pattern="eval($X)"),
            reporting=RuleReporting(
                default_message="No eval (PY-SEC-001)",
                confidence="high",
                documentation_url=None,
            ),
            examples=RuleExamples(good=[], bad=[]),
            references=[],
        ),
    )
    output = json.dumps(
        {
            "results": [
                {
                    "check_id": "py-sec-001-impl",
                    "path": "src/app.py",
                    "start": {"line": 3},
                    "extra": {"message": "No eval (PY-SEC-001)", "lines": ["eval(x)"]},
                }
            ]
        }
    )

    findings, pattern_instances = parse_semgrep_output(output, {"PY-SEC-001": spec})
    assert len(findings) == 1
    assert findings[0].guideline_id == "PY-SEC-001"
