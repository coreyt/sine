"""Tests for the sine research CLI command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from click.testing import CliRunner

from sine.cli import cli
from sine.discovery.models import DiscoveredPattern, PatternExamples


def _sample_pattern(pattern_id: str = "ARCH-DI-001") -> DiscoveredPattern:
    return DiscoveredPattern(
        pattern_id=pattern_id,
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


class TestResearchCommand:
    def test_research_command_saves_patterns(self, monkeypatch) -> None:
        """research command saves discovered patterns to storage."""
        patterns = [_sample_pattern("ARCH-DI-001"), _sample_pattern("ARCH-DI-002")]

        async def mock_discover(*args, **kwargs):  # type: ignore[no-untyped-def]
            return patterns

        mock_agent = MagicMock()
        mock_agent.discover_patterns = mock_discover
        mock_agent_cls = MagicMock(return_value=mock_agent)
        monkeypatch.setattr(
            "sine.discovery.agents.architecture.ArchitectureAgent", mock_agent_cls
        )

        mock_storage = MagicMock()
        mock_storage_cls = MagicMock(return_value=mock_storage)
        monkeypatch.setattr("sine.discovery.storage.PatternStorage", mock_storage_cls)

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "research",
                    "--focus",
                    "dependency injection patterns",
                    "--no-llm",
                ],
            )

        assert result.exit_code == 0, result.output
        assert mock_storage.save_pattern.call_count == 2
        # Verify stage is "raw"
        for call_args in mock_storage.save_pattern.call_args_list:
            assert call_args[0][1] == "raw"

    def test_research_command_no_results(self, monkeypatch) -> None:
        """research command prints informational message when no patterns found."""

        async def mock_discover(*args, **kwargs):  # type: ignore[no-untyped-def]
            return []

        mock_agent = MagicMock()
        mock_agent.discover_patterns = mock_discover
        mock_agent_cls = MagicMock(return_value=mock_agent)
        monkeypatch.setattr(
            "sine.discovery.agents.architecture.ArchitectureAgent", mock_agent_cls
        )

        mock_storage = MagicMock()
        mock_storage_cls = MagicMock(return_value=mock_storage)
        monkeypatch.setattr("sine.discovery.storage.PatternStorage", mock_storage_cls)

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                ["research", "--focus", "some obscure topic", "--no-llm"],
            )

        assert result.exit_code == 0
        assert "No patterns" in result.output or "0" in result.output
        mock_storage.save_pattern.assert_not_called()

    def test_research_command_missing_focus(self) -> None:
        """research command exits non-zero when --focus is not provided."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["research"])

        assert result.exit_code != 0
        assert "focus" in result.output.lower() or "focus" in (result.stderr or "").lower()
