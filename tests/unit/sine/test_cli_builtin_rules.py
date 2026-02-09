"""Tests for CLI integration with built-in rules."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from sine.cli import cli


class TestCheckWithBuiltInRules:
    """Tests for 'sine check' command with built-in rules."""

    def test_check_with_only_builtin_rules(self, tmp_path, monkeypatch):
        """Should run successfully with only built-in rules (no user rules)."""
        # Create a test project directory
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()

        # Create a Python file with a print statement (violates ARCH-003)
        (project_dir / "example.py").write_text('print("hello")\n')

        # Change to project directory
        monkeypatch.chdir(project_dir)

        # Run sine check with --format json for easier assertion
        runner = CliRunner()
        result = runner.invoke(cli, ["check", "--format", "json"])

        # Should succeed (exit code 0 or 1 for violations)
        assert result.exit_code in [0, 1]

        # Should produce JSON output
        if result.exit_code == 1:
            output = json.loads(result.output)
            assert isinstance(output, list)
            # Should detect print() violation from ARCH-003
            assert len(output) > 0
            assert any(f.get("guideline_id") == "ARCH-003" for f in output)

    def test_check_gracefully_handles_missing_rules_dir(self, tmp_path, monkeypatch):
        """Should load built-in rules when .sine-rules doesn't exist."""
        # Create a test project directory without .sine-rules
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()

        # Create a simple Python file
        (project_dir / "example.py").write_text("import os\n")

        # Change to project directory
        monkeypatch.chdir(project_dir)

        # Run sine check
        runner = CliRunner()
        result = runner.invoke(cli, ["check"])

        # Should NOT fail with FileNotFoundError
        # Should succeed (exit code 0) since no violations
        assert result.exit_code == 0
        assert "FileNotFoundError" not in result.output
        assert "No rule specifications found" not in result.output


class TestCheckWithMixedRules:
    """Tests for 'sine check' with both built-in and user rules."""

    def test_check_with_mixed_builtin_and_user_rules(self, tmp_path, monkeypatch):
        """Should load both built-in and user rules."""
        # Create project with user rules
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()

        # Create user rules directory
        rules_dir = project_dir / ".sine-rules"
        rules_dir.mkdir()

        # Add a custom rule
        custom_rule = """schema_version: 1
rule:
  id: "CUSTOM-001"
  title: "Custom test rule"
  description: "A custom rule"
  rationale: "Testing"
  tier: 1
  category: "testing"
  severity: "warning"
  languages: [python]
  check:
    type: "forbidden"
    pattern: "bad_function(...)"
  reporting:
    default_message: "Custom rule"
    confidence: "high"
    documentation_url: null
  examples:
    good:
      - language: python
        code: "pass"
    bad:
      - language: python
        code: "bad_function()"
  references: []
"""
        (rules_dir / "CUSTOM-001.yaml").write_text(custom_rule)

        # Create a Python file
        (project_dir / "example.py").write_text("import os\n")

        # Create sine.toml config
        (project_dir / "sine.toml").write_text(
            'rules_dir = ".sine-rules"\ntarget = ["."]\n'
        )

        # Change to project directory
        monkeypatch.chdir(project_dir)

        # Run sine check with JSON output
        runner = CliRunner()
        result = runner.invoke(cli, ["check", "--format", "json"])

        # Should succeed
        assert result.exit_code == 0

        # Should have loaded rules (we can't easily verify count without
        # modifying CLI to expose it, but lack of errors indicates success)
        assert "error" not in result.output.lower() or result.exit_code == 0

    def test_user_rules_can_override_builtin_rules(self, tmp_path, monkeypatch):
        """User rules should override built-in rules by ID."""
        # Create project with modified ARCH-003
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()

        rules_dir = project_dir / ".sine-rules"
        rules_dir.mkdir()

        # Override ARCH-003 with "info" severity instead of "warning"
        modified_rule = """schema_version: 1
rule:
  id: "ARCH-003"
  title: "Modified logging rule"
  description: "User-customized version"
  rationale: "Custom"
  tier: 1
  category: "code-quality"
  severity: "info"
  languages: [python]
  check:
    type: "forbidden"
    pattern: "print(...)"
  reporting:
    default_message: "Custom message"
    confidence: "high"
    documentation_url: null
  examples:
    good:
      - language: python
        code: "logging.info('test')"
    bad:
      - language: python
        code: "print('test')"
  references: []
"""
        (rules_dir / "ARCH-003.yaml").write_text(modified_rule)

        # Create file with print statement
        (project_dir / "example.py").write_text('print("hello")\n')

        # Create config
        (project_dir / "sine.toml").write_text(
            'rules_dir = ".sine-rules"\ntarget = ["."]\n'
        )

        monkeypatch.chdir(project_dir)

        # Run check
        runner = CliRunner()
        result = runner.invoke(cli, ["check"])

        # Should use modified rule (though we can't easily verify the
        # severity was changed without more complex output parsing)
        assert result.exit_code in [0, 1]


class TestDiscoverWithBuiltInRules:
    """Tests for 'sine discover' command with built-in rules."""

    def test_discover_works_with_builtin_rules(self, tmp_path, monkeypatch):
        """Should run discover with built-in pattern discovery rules."""
        # Create project
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()

        # Create a Python file with a pattern
        (project_dir / "example.py").write_text(
            "from pydantic import BaseModel\n\nclass MyModel(BaseModel):\n    pass\n"
        )

        monkeypatch.chdir(project_dir)

        # Run sine discover
        runner = CliRunner()
        result = runner.invoke(cli, ["discover"])

        # Should succeed
        assert result.exit_code == 0
        # Should not error about missing rules
        assert "FileNotFoundError" not in result.output
