from __future__ import annotations

import subprocess
from pathlib import Path

from sine.baseline import Baseline
from sine.models import (
    Finding,
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


def _finding(message: str = "eval forbidden (ARCH-010)") -> Finding:
    return Finding(
        guideline_id="ARCH-010",
        title="Avoid eval",
        category="security",
        severity="error",
        file="src/app.py",
        line=7,
        message=message,
        snippet="eval(x)",
        engine="semgrep",
        tier=1,
    )


def test_run_sine_dry_run_returns_preview() -> None:
    findings, new_findings, instances, errors, dry_output = run_sine(
        specs=[_spec()],
        targets=[Path("src")],
        dry_run=True,
    )

    assert findings == []
    assert new_findings == []
    assert instances == []
    assert errors == []
    assert dry_output is not None
    assert "Would execute:" in dry_output


def test_run_sine_update_baseline_writes_current_findings(monkeypatch) -> None:
    fake_result = subprocess.CompletedProcess(
        args=["semgrep"], returncode=1, stdout='{"results":[]}', stderr=""
    )
    findings = [_finding()]
    captured = {}

    monkeypatch.setattr("sine.runner.subprocess.run", lambda *args, **kwargs: fake_result)
    monkeypatch.setattr(
        "sine.runner.parse_semgrep_output", lambda *args, **kwargs: (findings, [], [])
    )
    monkeypatch.setattr("sine.runner.load_baseline", lambda *args, **kwargs: None)

    def _capture_write(baseline: Baseline, path: Path) -> None:
        captured["baseline"] = baseline
        captured["path"] = path

    monkeypatch.setattr("sine.runner.write_baseline", _capture_write)

    all_findings, new_findings, instances, errors, dry_output = run_sine(
        specs=[_spec()],
        targets=[Path("src")],
        update_baseline=True,
    )

    assert all_findings == findings
    assert new_findings == []
    assert instances == []
    assert errors == []
    assert dry_output is None
    assert "baseline" in captured
    assert captured["baseline"] == Baseline.from_findings(findings)


def test_run_sine_filters_existing_baseline(monkeypatch) -> None:
    fake_result = subprocess.CompletedProcess(
        args=["semgrep"], returncode=1, stdout='{"results":[]}', stderr=""
    )
    known = _finding("known")
    fresh = _finding("new")
    baseline = Baseline.from_findings([known])

    monkeypatch.setattr("sine.runner.subprocess.run", lambda *args, **kwargs: fake_result)
    monkeypatch.setattr(
        "sine.runner.parse_semgrep_output", lambda *args, **kwargs: ([known, fresh], [], [])
    )
    monkeypatch.setattr("sine.runner.load_baseline", lambda *args, **kwargs: baseline)

    all_findings, new_findings, instances, errors, dry_output = run_sine(
        specs=[_spec()],
        targets=[Path("src")],
    )

    assert all_findings == [known, fresh]
    assert new_findings == [fresh]
    assert instances == []
    assert errors == []
    assert dry_output is None
