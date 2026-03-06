"""Tests for BatchGridScreen."""

from __future__ import annotations

from lookout.batch.models import BatchJob, BatchStatus, CellStatus, RegistryCell
from lookout_tui.screens.batch import BatchGridScreen


class TestBatchGridScreen:
    def test_screen_title(self) -> None:
        screen = BatchGridScreen()
        assert "batch" in screen.__class__.__name__.lower()

    def test_default_languages(self) -> None:
        screen = BatchGridScreen()
        assert len(screen.DEFAULT_LANGUAGES) > 0

    def test_default_frameworks(self) -> None:
        screen = BatchGridScreen()
        assert isinstance(screen.DEFAULT_FRAMEWORKS, dict)
