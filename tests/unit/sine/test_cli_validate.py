"""Tests for the sine validate CLI command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from sine.cli import cli
from sine.discovery.models import DiscoveredPattern, PatternExamples, ValidatedPattern


def _sample_raw() -> DiscoveredPattern:
    return DiscoveredPattern(
        pattern_id="ARCH-DI-001",
        title="Use Dependency Injection",
        category="architecture",
        subcategory="dependency-injection",
        description="Services should use constructor injection for dependencies.",
        rationale="Improves testability and enables loose coupling between components.",
        severity="warning",
        confidence="high",
        examples=PatternExamples(),
        discovered_by="architecture-agent",
    )


class TestValidateCommand:
    def test_validate_command_promotes_raw_to_validated(self, monkeypatch) -> None:
        """validate command loads raw pattern and saves as validated."""
        raw = _sample_raw()

        mock_storage = MagicMock()
        mock_storage.load_pattern.return_value = raw
        mock_storage_cls = MagicMock(return_value=mock_storage)
        monkeypatch.setattr("sine.discovery.storage.PatternStorage", mock_storage_cls)

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path(".sine-patterns").mkdir()
            result = runner.invoke(
                cli,
                ["validate", "ARCH-DI-001", "--patterns-dir", ".sine-patterns"],
            )

        assert result.exit_code == 0, result.output
        mock_storage.save_pattern.assert_called_once()
        saved_pattern, saved_stage = mock_storage.save_pattern.call_args[0]
        assert saved_stage == "validated"
        assert isinstance(saved_pattern, ValidatedPattern)

    def test_validate_command_pattern_not_found(self, monkeypatch) -> None:
        """validate command exits 1 when pattern is not found."""
        mock_storage = MagicMock()
        mock_storage.load_pattern.return_value = None
        mock_storage_cls = MagicMock(return_value=mock_storage)
        monkeypatch.setattr("sine.discovery.storage.PatternStorage", mock_storage_cls)

        runner = CliRunner(mix_stderr=False)
        with runner.isolated_filesystem():
            Path(".sine-patterns").mkdir()
            result = runner.invoke(
                cli,
                ["validate", "ARCH-DI-999", "--patterns-dir", ".sine-patterns"],
            )

        assert result.exit_code == 1
        assert "not found" in result.stderr.lower() or "not found" in result.output.lower()

    def test_validate_command_with_tier_override(self, monkeypatch) -> None:
        """validate command respects --tier override."""
        raw = _sample_raw()

        saved: list[ValidatedPattern] = []

        mock_storage = MagicMock()
        mock_storage.load_pattern.return_value = raw
        mock_storage.save_pattern.side_effect = lambda p, stage: saved.append(p)
        mock_storage_cls = MagicMock(return_value=mock_storage)
        monkeypatch.setattr("sine.discovery.storage.PatternStorage", mock_storage_cls)

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path(".sine-patterns").mkdir()
            result = runner.invoke(
                cli,
                [
                    "validate",
                    "ARCH-DI-001",
                    "--patterns-dir",
                    ".sine-patterns",
                    "--tier",
                    "1",
                ],
            )

        assert result.exit_code == 0, result.output
        assert len(saved) == 1
        assert saved[0].effective_tier == 1
