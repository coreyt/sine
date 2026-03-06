"""Tests for keyboard binding helpers."""

from __future__ import annotations

from lookout_tui.keys import ci


class TestCiHelper:
    def test_returns_two_bindings(self) -> None:
        result = ci("r", "refresh", "Refresh")
        assert len(result) == 2

    def test_first_binding_is_lowercase(self) -> None:
        result = ci("r", "refresh", "Refresh")
        assert result[0].key == "r"

    def test_second_binding_is_uppercase(self) -> None:
        result = ci("r", "refresh", "Refresh")
        assert result[1].key == "R"

    def test_lowercase_shown_uppercase_hidden(self) -> None:
        result = ci("r", "refresh", "Refresh")
        assert result[0].show is True
        assert result[1].show is False

    def test_both_have_same_action(self) -> None:
        result = ci("d", "delete", "Delete")
        assert result[0].action == "delete"
        assert result[1].action == "delete"

    def test_priority_passed_to_both(self) -> None:
        result = ci("q", "quit", "Quit", priority=True)
        assert result[0].priority is True
        assert result[1].priority is True

    def test_show_false_hides_both(self) -> None:
        result = ci("x", "action", "Action", show=False)
        assert result[0].show is False
        assert result[1].show is False

    def test_key_display_passed_through(self) -> None:
        result = ci("s", "sort", "Sort", key_display="/")
        assert result[0].key_display == "/"
        assert result[1].key_display == "/"
