"""Tests for sine init command."""

from __future__ import annotations

from pathlib import Path

import pytest

from sine.init import (
    copy_built_in_rules_to_local,
    detect_project_type,
    generate_config_content,
    run_init,
)


class TestDetectProjectType:
    """Tests for project type detection."""

    def test_detect_project_type_identifies_python(self, tmp_path, monkeypatch):
        """Should detect Python project from pyproject.toml."""
        project_dir = tmp_path / "python-project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        monkeypatch.chdir(project_dir)
        result = detect_project_type()

        assert result["python"] is True

    def test_detect_project_type_identifies_python_from_setup_py(self, tmp_path, monkeypatch):
        """Should detect Python project from setup.py."""
        project_dir = tmp_path / "python-project"
        project_dir.mkdir()
        (project_dir / "setup.py").write_text("from setuptools import setup\n")

        monkeypatch.chdir(project_dir)
        result = detect_project_type()

        assert result["python"] is True

    def test_detect_project_type_identifies_javascript(self, tmp_path, monkeypatch):
        """Should detect JavaScript project from package.json."""
        project_dir = tmp_path / "js-project"
        project_dir.mkdir()
        (project_dir / "package.json").write_text('{"name": "test"}\n')

        monkeypatch.chdir(project_dir)
        result = detect_project_type()

        assert result["javascript"] is True

    def test_detect_project_type_identifies_typescript(self, tmp_path, monkeypatch):
        """Should detect TypeScript project from tsconfig.json."""
        project_dir = tmp_path / "ts-project"
        project_dir.mkdir()
        (project_dir / "tsconfig.json").write_text('{"compilerOptions": {}}\n')

        monkeypatch.chdir(project_dir)
        result = detect_project_type()

        assert result["typescript"] is True

    def test_detect_project_type_identifies_git(self, tmp_path, monkeypatch):
        """Should detect git repository from .git directory."""
        project_dir = tmp_path / "git-project"
        project_dir.mkdir()
        (project_dir / ".git").mkdir()

        monkeypatch.chdir(project_dir)
        result = detect_project_type()

        assert result["git"] is True

    def test_detect_project_type_returns_false_for_missing(self, tmp_path, monkeypatch):
        """Should return False for non-existent markers."""
        project_dir = tmp_path / "empty-project"
        project_dir.mkdir()

        monkeypatch.chdir(project_dir)
        result = detect_project_type()

        assert result["python"] is False
        assert result["javascript"] is False
        assert result["typescript"] is False
        assert result["git"] is False


class TestGenerateConfigContent:
    """Tests for config content generation."""

    def test_generate_config_for_pyproject_toml(self):
        """Should generate [tool.sine] section for pyproject.toml."""
        config = {
            "config_file": "pyproject.toml",
            "target": ["src", "tests"],
            "format": "text",
        }

        content = generate_config_content(config, Path(".sine-rules"))

        assert "[tool.sine]" in content
        assert 'rules_dir = ".sine-rules"' in content
        assert 'target = ["src", "tests"]' in content
        assert 'format = "text"' in content

    def test_generate_config_for_sine_toml(self):
        """Should generate root-level config for sine.toml."""
        config = {
            "config_file": "sine.toml",
            "target": ["."],
            "format": "json",
        }

        content = generate_config_content(config, Path(".sine-rules"))

        assert "[tool.sine]" not in content
        assert 'rules_dir = ".sine-rules"' in content
        assert 'target = ["."]' in content
        assert 'format = "json"' in content

    def test_generate_config_with_custom_rules_dir(self):
        """Should use custom rules directory path."""
        config = {
            "config_file": "sine.toml",
            "target": ["."],
            "format": "text",
        }

        content = generate_config_content(config, Path("custom/rules"))

        assert 'rules_dir = "custom/rules"' in content


class TestCopyBuiltInRulesToLocal:
    """Tests for copying built-in rules."""

    def test_copy_built_in_rules_to_local(self, tmp_path):
        """Should copy all built-in rules to local directory."""
        rules_dir = tmp_path / "test-rules"

        copy_built_in_rules_to_local(rules_dir)

        # Should create directory
        assert rules_dir.exists()
        assert rules_dir.is_dir()

        # Should copy all 7 rules
        rule_files = list(rules_dir.glob("*.yaml"))
        assert len(rule_files) == 7

        # Should include expected rules
        rule_names = {f.name for f in rule_files}
        assert "ARCH-001.yaml" in rule_names
        assert "ARCH-003.yaml" in rule_names
        assert "PATTERN-DISC-006.yaml" in rule_names

    def test_copy_built_in_rules_with_selected_ids(self, tmp_path):
        """Should copy only selected rules by ID."""
        rules_dir = tmp_path / "test-rules"
        selected_ids = ["ARCH-001", "ARCH-003"]

        copy_built_in_rules_to_local(rules_dir, selected_ids=selected_ids)

        # Should copy only selected rules
        rule_files = list(rules_dir.glob("*.yaml"))
        assert len(rule_files) == 2

        rule_names = {f.name for f in rule_files}
        assert "ARCH-001.yaml" in rule_names
        assert "ARCH-003.yaml" in rule_names

    def test_copy_built_in_rules_creates_parent_dirs(self, tmp_path):
        """Should create parent directories if needed."""
        rules_dir = tmp_path / "nested" / "path" / "rules"

        copy_built_in_rules_to_local(rules_dir)

        assert rules_dir.exists()
        assert (rules_dir / "ARCH-001.yaml").exists()


class TestRunInit:
    """Tests for run_init function (non-interactive mode only)."""

    def test_run_init_non_interactive_creates_config(self, tmp_path, monkeypatch):
        """Should create sine.toml in non-interactive mode."""
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()

        monkeypatch.chdir(project_dir)

        run_init(
            rules_dir=Path(".sine-rules"),
            copy_built_in_rules=False,
            interactive=False,
        )

        # Should create sine.toml
        config_file = project_dir / "sine.toml"
        assert config_file.exists()

        content = config_file.read_text()
        assert 'rules_dir = ".sine-rules"' in content
        assert 'target = ["."]' in content

    def test_run_init_creates_rules_directory(self, tmp_path, monkeypatch):
        """Should create .sine-rules directory."""
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()

        monkeypatch.chdir(project_dir)

        run_init(
            rules_dir=Path(".sine-rules"),
            copy_built_in_rules=False,
            interactive=False,
        )

        assert (project_dir / ".sine-rules").exists()

    def test_run_init_with_copy_built_in_rules(self, tmp_path, monkeypatch):
        """Should copy built-in rules when flag is set."""
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()

        monkeypatch.chdir(project_dir)

        run_init(
            rules_dir=Path(".sine-rules"),
            copy_built_in_rules=True,
            interactive=False,
        )

        # Should copy rules
        rules_dir = project_dir / ".sine-rules"
        rule_files = list(rules_dir.glob("*.yaml"))
        assert len(rule_files) == 7

    def test_run_init_for_python_project_uses_pyproject(self, tmp_path, monkeypatch):
        """Should use pyproject.toml for Python projects in non-interactive mode."""
        project_dir = tmp_path / "python-project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        monkeypatch.chdir(project_dir)

        run_init(
            rules_dir=Path(".sine-rules"),
            copy_built_in_rules=False,
            interactive=False,
        )

        # Should append to pyproject.toml
        content = (project_dir / "pyproject.toml").read_text()
        assert "[tool.sine]" in content
        assert 'rules_dir = ".sine-rules"' in content

    def test_run_init_fails_if_config_exists_non_interactive(self, tmp_path, monkeypatch):
        """Should exit if config exists in non-interactive mode."""
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / "sine.toml").write_text('rules_dir = "old"\n')

        monkeypatch.chdir(project_dir)

        with pytest.raises(SystemExit) as exc_info:
            run_init(
                rules_dir=Path(".sine-rules"),
                copy_built_in_rules=False,
                interactive=False,
            )

        assert exc_info.value.code == 1
