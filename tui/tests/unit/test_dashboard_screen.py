"""Tests for the Dashboard home screen."""

from __future__ import annotations

from lookout_tui.screens.dashboard import DashboardScreen, DashboardStats


class TestDashboardStats:
    """Tests for DashboardStats data model."""

    def test_defaults(self) -> None:
        stats = DashboardStats()
        assert stats.total_patterns == 0
        assert stats.built_in_count == 0
        assert stats.user_count == 0
        assert stats.enforcement_count == 0
        assert stats.discovery_count == 0
        assert stats.languages == []
        assert stats.categories == []
        assert stats.llm_configured is False
        assert stats.llm_model == ""

    def test_from_index_empty(self) -> None:
        from lookout_tui.index.models import PatternIndex

        index = PatternIndex()
        stats = DashboardStats.from_index(index)
        assert stats.total_patterns == 0

    def test_from_index_with_entries(self) -> None:
        from lookout_tui.index.models import PatternIndex, PatternIndexEntry

        entries = [
            PatternIndexEntry(
                id="ARCH-001",
                title="HTTP resilience",
                schema_version=1,
                category="resilience",
                severity="error",
                tier=1,
                languages=["python"],
            ),
            PatternIndexEntry(
                id="DI-001",
                title="Dependency Injection",
                schema_version=2,
                category="architecture",
                severity="warning",
                tier=2,
                languages=["python", "typescript"],
            ),
        ]
        index = PatternIndex(
            entries=entries, total=2, built_in_count=2, user_count=0
        )
        stats = DashboardStats.from_index(index)
        assert stats.total_patterns == 2
        assert stats.built_in_count == 2
        assert stats.user_count == 0
        assert sorted(stats.languages) == ["python", "typescript"]
        assert sorted(stats.categories) == ["architecture", "resilience"]

    def test_from_index_deduplicates_languages(self) -> None:
        from lookout_tui.index.models import PatternIndex, PatternIndexEntry

        entries = [
            PatternIndexEntry(
                id="A-001",
                title="A",
                schema_version=1,
                category="cat",
                severity="error",
                tier=1,
                languages=["python"],
            ),
            PatternIndexEntry(
                id="B-001",
                title="B",
                schema_version=1,
                category="cat",
                severity="error",
                tier=1,
                languages=["python"],
            ),
        ]
        index = PatternIndex(entries=entries, total=2, built_in_count=2, user_count=0)
        stats = DashboardStats.from_index(index)
        assert stats.languages == ["python"]

    def test_from_index_splits_enforcement_and_discovery(self) -> None:
        from lookout_tui.index.models import PatternIndex, PatternIndexEntry

        entries = [
            PatternIndexEntry(
                id="A-001", title="Enforce", schema_version=1,
                category="arch", severity="error", tier=1,
            ),
            PatternIndexEntry(
                id="B-001", title="Discover", schema_version=1,
                category="arch", severity="info", tier=1,
            ),
        ]
        index = PatternIndex(entries=entries, total=2, built_in_count=2, user_count=0)
        stats = DashboardStats.from_index(index)
        assert stats.enforcement_count == 1
        assert stats.discovery_count == 1


class TestDashboardScreen:
    """Tests for DashboardScreen."""

    def test_screen_has_bindings(self) -> None:
        """Dashboard should have r/Refresh."""
        screen = DashboardScreen()
        binding_keys = {b.key for b in screen.BINDINGS}
        assert "r" in binding_keys

    def test_stats_initialized(self) -> None:
        """Screen should initialize with empty stats."""
        screen = DashboardScreen()
        assert screen._stats.total_patterns == 0

    def test_stats_zero_patterns(self) -> None:
        """Default stats should have zero patterns."""
        stats = DashboardStats()
        assert stats.total_patterns == 0

    def test_stats_with_counts(self) -> None:
        """Stats should reflect pattern counts."""
        stats = DashboardStats(
            total_patterns=10,
            built_in_count=7,
            user_count=3,
            enforcement_count=5,
            discovery_count=5,
        )
        assert stats.total_patterns == 10
        assert stats.built_in_count == 7
        assert stats.user_count == 3
