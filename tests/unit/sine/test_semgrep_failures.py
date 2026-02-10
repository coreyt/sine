from __future__ import annotations

import json
import subprocess
from pathlib import Path

from sine.models import (
    ForbiddenCheck,
    RuleExamples,
    RuleReporting,
    RuleSpec,
    RuleSpecFile,
)
from sine.runner import run_sine


def _spec() -> RuleSpecFile:
    return RuleSpecFile(
        schema_version=1,
        rule=RuleSpec(
            id="ARCH-010",
            title="Avoid eval",
            description="Desc",
            rationale="Because",
            tier=1,
            category="security",
            severity="error",
            languages=["python"],
            check=ForbiddenCheck(type="forbidden", pattern="eval($X)"),
            reporting=RuleReporting(
                default_message="eval forbidden (ARCH-010)",
                confidence="high",
                documentation_url=None,
            ),
            examples=RuleExamples(good=[], bad=[]),
            references=[],
        ),
    )


def test_run_sine_reports_parse_errors(monkeypatch) -> None:
    # Simulate Semgrep output with both results and errors
    semgrep_output = json.dumps(
        {
            "results": [],
            "errors": [
                {
                    "code": 2,
                    "level": "error",
                    "type": "Rule parse error",
                    "rule_id": "arch-010-impl",
                    "message": "Invalid pattern",
                }
            ],
        }
    )

    fake_result = subprocess.CompletedProcess(
        args=["semgrep"], returncode=2, stdout=semgrep_output, stderr=""
    )

    monkeypatch.setattr("sine.runner.subprocess.run", lambda *args, **kwargs: fake_result)

    # Mock other dependencies
    monkeypatch.setattr("sine.runner.load_baseline", lambda *args, **kwargs: None)
    monkeypatch.setattr("sine.runner.filter_findings", lambda f, b: f)

    # Expecting run_sine to return: (findings, new_findings, instances, errors, dry_output)
    findings, new_findings, instances, errors, dry_output = run_sine(
        specs=[_spec()],
        targets=[Path("src")],
    )

    # Assert that we captured the error
    assert len(errors) == 1
    assert errors[0].rule_id == "ARCH-010"
    assert "Invalid pattern" in errors[0].message
