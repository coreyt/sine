"""Tests for sine init interactive paths."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import call

import pytest

from sine.init import generate_config_content, prompt_user_config, run_init


class TestPromptUserConfig:
    def test_python_project_with_pyproject_choice(self, monkeypatch) -> None:
        monkeypatch.setattr("sine.init.click.confirm", lambda *args, **kwargs: True)
        monkeypatch.setattr("sine.init.click.prompt", lambda *args, **kwargs: "src")

        config = prompt_user_config({"python": True, "javascript": False, "typescript": False, "git": False})

        assert config["config_file"] == "pyproject.toml"
        assert config["target"] == ["src"]

    def test_python_project_declines_pyproject(self, monkeypatch) -> None:
        monkeypatch.setattr("sine.init.click.confirm", lambda *args, **kwargs: False)
        monkeypatch.setattr("sine.init.click.prompt", lambda *args, **kwargs: ".")

        config = prompt_user_config({"python": True, "javascript": False, "typescript": False, "git": False})

        assert config["config_file"] == "sine.toml"

    def test_non_python_project_uses_sine_toml(self, monkeypatch) -> None:
        monkeypatch.setattr("sine.init.click.prompt", lambda *args, **kwargs: ".")

        config = prompt_user_config({"python": False, "javascript": True, "typescript": False, "git": False})

        assert config["config_file"] == "sine.toml"

    def test_target_is_split_on_comma(self, monkeypatch) -> None:
        monkeypatch.setattr("sine.init.click.confirm", lambda *args, **kwargs: False)
        prompts = iter(["src, lib", "text"])
        monkeypatch.setattr("sine.init.click.prompt", lambda *args, **kwargs: next(prompts))

        config = prompt_user_config({"python": False, "javascript": False, "typescript": False, "git": False})

        assert config["target"] == ["src", "lib"]

    def test_format_is_included_in_config(self, monkeypatch) -> None:
        formats = iter(["src", "json"])
        monkeypatch.setattr("sine.init.click.confirm", lambda *args, **kwargs: False)
        monkeypatch.setattr("sine.init.click.prompt", lambda *args, **kwargs: next(formats))

        config = prompt_user_config({"python": False, "javascript": False, "typescript": False, "git": False})

        assert config["format"] == "json"


class TestRunInitInteractive:
    def test_interactive_mode_echos_project_characteristics(self, tmp_path, monkeypatch, capsys) -> None:
        project_dir = tmp_path / "proj"
        project_dir.mkdir()
        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            "sine.init.prompt_user_config",
            lambda info: {"config_file": "sine.toml", "target": ["."], "format": "text"},
        )

        run_init(rules_dir=Path(".sine-rules"), copy_built_in_rules=False, interactive=True)

        captured = capsys.readouterr()
        assert "python" in captured.out
        assert "git" in captured.out

    def test_interactive_mode_creates_config_file(self, tmp_path, monkeypatch) -> None:
        project_dir = tmp_path / "proj"
        project_dir.mkdir()
        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            "sine.init.prompt_user_config",
            lambda info: {"config_file": "sine.toml", "target": ["."], "format": "text"},
        )

        run_init(rules_dir=Path(".sine-rules"), copy_built_in_rules=False, interactive=True)

        assert (project_dir / "sine.toml").exists()

    def test_interactive_mode_confirms_overwrite_of_existing_config(self, tmp_path, monkeypatch) -> None:
        project_dir = tmp_path / "proj"
        project_dir.mkdir()
        (project_dir / "sine.toml").write_text('rules_dir = "old"\n')
        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            "sine.init.prompt_user_config",
            lambda info: {"config_file": "sine.toml", "target": ["."], "format": "text"},
        )
        # Confirm overwrite = True
        monkeypatch.setattr("sine.init.click.confirm", lambda *args, **kwargs: True)

        run_init(rules_dir=Path(".sine-rules"), copy_built_in_rules=False, interactive=True)

        content = (project_dir / "sine.toml").read_text()
        assert 'rules_dir = ".sine-rules"' in content

    def test_interactive_mode_cancels_if_overwrite_declined(self, tmp_path, monkeypatch) -> None:
        project_dir = tmp_path / "proj"
        project_dir.mkdir()
        (project_dir / "sine.toml").write_text('rules_dir = "old"\n')
        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            "sine.init.prompt_user_config",
            lambda info: {"config_file": "sine.toml", "target": ["."], "format": "text"},
        )
        monkeypatch.setattr("sine.init.click.confirm", lambda *args, **kwargs: False)

        with pytest.raises(SystemExit) as exc_info:
            run_init(rules_dir=Path(".sine-rules"), copy_built_in_rules=False, interactive=True)

        assert exc_info.value.code == 0

    def test_interactive_mode_with_copy_all_built_in_rules(self, tmp_path, monkeypatch) -> None:
        project_dir = tmp_path / "proj"
        project_dir.mkdir()
        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            "sine.init.prompt_user_config",
            lambda info: {"config_file": "sine.toml", "target": ["."], "format": "text"},
        )
        # First confirm = copy all rules (True)
        monkeypatch.setattr("sine.init.click.confirm", lambda *args, **kwargs: True)

        run_init(rules_dir=Path(".sine-rules"), copy_built_in_rules=True, interactive=True)

        rules = list((project_dir / ".sine-rules").glob("*.yaml"))
        assert len(rules) == 7

    def test_interactive_mode_copies_all_when_selective_not_chosen(self, tmp_path, monkeypatch) -> None:
        project_dir = tmp_path / "proj"
        project_dir.mkdir()
        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            "sine.init.prompt_user_config",
            lambda info: {"config_file": "sine.toml", "target": ["."], "format": "text"},
        )
        # Declining "copy all" triggers ID prompt; empty input falls back to all
        monkeypatch.setattr("sine.init.click.confirm", lambda *args, **kwargs: False)
        monkeypatch.setattr("sine.init.click.prompt", lambda *args, **kwargs: "")

        run_init(rules_dir=Path(".sine-rules"), copy_built_in_rules=True, interactive=True)

        rules = list((project_dir / ".sine-rules").glob("*.yaml"))
        assert len(rules) == 7

    def test_interactive_mode_selective_copy_by_id(self, tmp_path, monkeypatch) -> None:
        project_dir = tmp_path / "proj"
        project_dir.mkdir()
        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            "sine.init.prompt_user_config",
            lambda info: {"config_file": "sine.toml", "target": ["."], "format": "text"},
        )
        monkeypatch.setattr("sine.init.click.confirm", lambda *args, **kwargs: False)
        monkeypatch.setattr("sine.init.click.prompt", lambda *args, **kwargs: "ARCH-001,ARCH-003")

        run_init(rules_dir=Path(".sine-rules"), copy_built_in_rules=True, interactive=True)

        rules = list((project_dir / ".sine-rules").glob("*.yaml"))
        assert len(rules) == 2
        rule_stems = {r.stem for r in rules}
        assert "ARCH-001" in rule_stems
        assert "ARCH-003" in rule_stems

    def test_interactive_mode_selective_copy_empty_falls_back_to_all(self, tmp_path, monkeypatch) -> None:
        project_dir = tmp_path / "proj"
        project_dir.mkdir()
        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            "sine.init.prompt_user_config",
            lambda info: {"config_file": "sine.toml", "target": ["."], "format": "text"},
        )
        monkeypatch.setattr("sine.init.click.confirm", lambda *args, **kwargs: False)
        monkeypatch.setattr("sine.init.click.prompt", lambda *args, **kwargs: "")

        run_init(rules_dir=Path(".sine-rules"), copy_built_in_rules=True, interactive=True)

        rules = list((project_dir / ".sine-rules").glob("*.yaml"))
        assert len(rules) == 7
