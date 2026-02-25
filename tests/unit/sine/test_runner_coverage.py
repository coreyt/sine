"""Additional tests for runner.py to cover missing lines."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from sine.models import (
    Finding,
    ForbiddenCheck,
    PatternInstance,
    RuleExamples,
    RuleReporting,
    RuleSpec,
    RuleSpecFile,
)
from sine.runner import (
    check_semgrep_version,
    format_findings_json,
    format_findings_text,
    format_pattern_instances_json,
    format_pattern_instances_text,
    run_sine,
)


def _finding(guideline_id: str = "ARCH-001", file: str = "src/app.py", line: int = 10) -> Finding:
    return Finding(
        guideline_id=guideline_id,
        title="Test Rule",
        category="architecture",
        severity="error",
        file=file,
        line=line,
        message=f"Violation of {guideline_id}",
        snippet="some_call()",
        engine="semgrep",
        tier=1,
    )


def _instance(pattern_id: str = "ARCH-DI-001", file: str = "src/app.py", line: int = 5) -> PatternInstance:
    return PatternInstance(
        pattern_id=pattern_id,
        title="Dependency Injection",
        category="architecture",
        file=file,
        line=line,
        snippet="class Service:",
        confidence="high",
    )


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


class TestCheckSemgrepVersion:
    def test_returns_version_string_when_semgrep_available(self, monkeypatch) -> None:
        fake_result = subprocess.CompletedProcess(
            args=["semgrep", "--version"],
            returncode=0,
            stdout="1.50.0\n",
            stderr="",
        )
        monkeypatch.setattr("sine.runner.subprocess.run", lambda *args, **kwargs: fake_result)

        version = check_semgrep_version()

        assert version == "1.50.0"

    def test_returns_none_when_semgrep_not_found(self, monkeypatch) -> None:
        def _raise(*args, **kwargs):
            raise FileNotFoundError("semgrep not found")

        monkeypatch.setattr("sine.runner.subprocess.run", _raise)

        version = check_semgrep_version()

        assert version is None


class TestRunSineRuntimeError:
    def test_raises_runtime_error_on_unexpected_returncode(self, monkeypatch) -> None:
        fake_result = subprocess.CompletedProcess(
            args=["semgrep"],
            returncode=99,
            stdout="",
            stderr="fatal error",
        )
        monkeypatch.setattr("sine.runner.subprocess.run", lambda *args, **kwargs: fake_result)

        with pytest.raises(RuntimeError, match="Semgrep execution failed"):
            run_sine(specs=[_spec()], targets=[Path("src")])


class TestFormatFindingsText:
    def test_empty_findings_returns_no_violations_message(self) -> None:
        result = format_findings_text([])
        assert result == "No violations found."

    def test_formats_each_finding_with_location_and_id(self) -> None:
        findings = [_finding(guideline_id="ARCH-001", file="src/app.py", line=42)]
        result = format_findings_text(findings)

        assert "src/app.py:42" in result
        assert "ARCH-001" in result

    def test_multiple_findings_each_on_own_line(self) -> None:
        findings = [
            _finding(file="src/a.py", line=1),
            _finding(file="src/b.py", line=2),
        ]
        result = format_findings_text(findings)
        lines = result.strip().splitlines()

        assert len(lines) == 2
        assert "src/a.py:1" in lines[0]
        assert "src/b.py:2" in lines[1]


class TestFormatFindingsJson:
    def test_returns_json_array_string(self) -> None:
        import json

        result = format_findings_json([_finding()])
        parsed = json.loads(result)

        assert isinstance(parsed, list)
        assert len(parsed) == 1

    def test_empty_findings_returns_empty_array(self) -> None:
        import json

        result = format_findings_json([])
        assert json.loads(result) == []


class TestFormatPatternInstancesText:
    def test_empty_instances_returns_no_patterns_message(self) -> None:
        result = format_pattern_instances_text([])
        assert result == "No patterns discovered."

    def test_output_contains_pattern_id_and_title(self) -> None:
        instances = [_instance(pattern_id="ARCH-DI-001")]
        result = format_pattern_instances_text(instances)

        assert "ARCH-DI-001" in result
        assert "Dependency Injection" in result

    def test_output_contains_instance_count(self) -> None:
        instances = [_instance(), _instance(file="src/b.py")]
        result = format_pattern_instances_text(instances)

        assert "Instances found: 2" in result

    def test_output_shows_at_most_five_locations(self) -> None:
        instances = [_instance(file=f"src/file{i}.py", line=i) for i in range(6)]
        result = format_pattern_instances_text(instances)

        assert "... and 1 more" in result

    def test_no_ellipsis_when_five_or_fewer_instances(self) -> None:
        instances = [_instance(file=f"src/file{i}.py", line=i) for i in range(5)]
        result = format_pattern_instances_text(instances)

        assert "more" not in result

    def test_total_count_in_footer(self) -> None:
        instances = [_instance(), _instance(file="src/b.py")]
        result = format_pattern_instances_text(instances)

        assert "Total: 2 pattern instances discovered" in result

    def test_multiple_patterns_grouped_separately(self) -> None:
        instances = [
            _instance(pattern_id="ARCH-DI-001"),
            _instance(pattern_id="ARCH-DI-002", file="src/b.py"),
        ]
        result = format_pattern_instances_text(instances)

        assert "ARCH-DI-001" in result
        assert "ARCH-DI-002" in result

    def test_category_is_shown(self) -> None:
        instances = [_instance()]
        result = format_pattern_instances_text(instances)

        assert "architecture" in result


class TestFormatPatternInstancesJson:
    def test_returns_json_array(self) -> None:
        import json

        instances = [_instance()]
        result = format_pattern_instances_json(instances)
        parsed = json.loads(result)

        assert isinstance(parsed, list)
        assert len(parsed) == 1

    def test_empty_instances_returns_empty_array(self) -> None:
        import json

        result = format_pattern_instances_json([])
        assert json.loads(result) == []

    def test_instance_fields_are_serialized(self) -> None:
        import json

        inst = _instance(pattern_id="ARCH-DI-001", file="src/service.py", line=99)
        result = format_pattern_instances_json([inst])
        parsed = json.loads(result)

        assert parsed[0]["pattern_id"] == "ARCH-DI-001"
        assert parsed[0]["file"] == "src/service.py"
        assert parsed[0]["line"] == 99
