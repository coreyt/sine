"""Tests for rules_loader module (hierarchical rule loading)."""

from __future__ import annotations

from pathlib import Path

import pytest

from sine.models import RuleSpecFile
from sine.rules_loader import get_built_in_rules_path, load_all_rules, load_built_in_rules


class TestGetBuiltInRulesPath:
    """Tests for get_built_in_rules_path function."""

    def test_returns_path_object(self):
        """Should return a Path object."""
        path = get_built_in_rules_path()
        assert isinstance(path, Path)

    def test_points_to_built_in_rules_directory(self):
        """Should point to src/sine/built_in_rules directory."""
        path = get_built_in_rules_path()
        assert path.name == "built_in_rules"
        assert path.parent.name == "sine"


class TestLoadBuiltInRules:
    """Tests for load_built_in_rules function."""

    def test_load_built_in_rules_returns_seven_rules(self):
        """Should load exactly 7 built-in rules."""
        rules = load_built_in_rules()
        assert len(rules) == 7
        assert all(isinstance(rule, RuleSpecFile) for rule in rules)

    def test_load_built_in_rules_includes_expected_rule_ids(self):
        """Should include the 7 expected rule IDs."""
        rules = load_built_in_rules()
        rule_ids = {rule.rule.id for rule in rules}
        expected_ids = {
            "ARCH-001",
            "ARCH-003",
            "PATTERN-DISC-006",
            "PATTERN-DISC-010",
            "PATTERN-DISC-011",
            "PATTERN-DISC-012",
            "PATTERN-DISC-015",
        }
        assert rule_ids == expected_ids

    def test_load_built_in_rules_handles_missing_directory(self, monkeypatch):
        """Should return empty list if built-in rules directory doesn't exist."""
        # Mock get_built_in_rules_path to return non-existent path
        fake_path = Path("/nonexistent/path")
        monkeypatch.setattr(
            "sine.rules_loader.get_built_in_rules_path", lambda: fake_path
        )
        rules = load_built_in_rules()
        assert rules == []


class TestLoadAllRules:
    """Tests for load_all_rules function."""

    def test_load_all_rules_with_no_user_rules_returns_only_builtin(self):
        """Should return only built-in rules when user_rules_dir is None."""
        rules = load_all_rules(user_rules_dir=None)
        assert len(rules) == 7
        rule_ids = {rule.rule.id for rule in rules}
        assert "ARCH-001" in rule_ids
        assert "ARCH-003" in rule_ids

    def test_load_all_rules_with_nonexistent_user_dir_returns_only_builtin(self, tmp_path):
        """Should return only built-in rules when user directory doesn't exist."""
        nonexistent_dir = tmp_path / "nonexistent"
        rules = load_all_rules(user_rules_dir=nonexistent_dir)
        assert len(rules) == 7

    def test_load_all_rules_merges_builtin_and_user_rules(self, tmp_path):
        """Should merge built-in and user rules."""
        # Create a user rules directory with a custom rule
        user_rules_dir = tmp_path / "user-rules"
        user_rules_dir.mkdir()

        # Write a custom rule (not in built-in set)
        custom_rule_content = """schema_version: 1
rule:
  id: "CUSTOM-001"
  title: "Custom rule"
  description: "A custom rule for testing"
  rationale: "Testing purposes"
  tier: 1
  category: "testing"
  severity: "warning"
  languages: [python]
  check:
    type: "forbidden"
    pattern: "test(...)"
  reporting:
    default_message: "Custom rule violation"
    confidence: "high"
    documentation_url: null
  examples:
    good:
      - language: python
        code: "pass"
    bad:
      - language: python
        code: "test()"
  references: []
"""
        (user_rules_dir / "CUSTOM-001.yaml").write_text(custom_rule_content)

        rules = load_all_rules(user_rules_dir=user_rules_dir)

        # Should have 7 built-in + 1 custom = 8 total
        assert len(rules) == 8
        rule_ids = {rule.rule.id for rule in rules}
        assert "ARCH-001" in rule_ids  # Built-in
        assert "CUSTOM-001" in rule_ids  # User rule

    def test_user_rules_override_builtin_rules_by_id(self, tmp_path):
        """Should allow user rules to override built-in rules by ID."""
        # Create a user rules directory with a modified version of ARCH-001
        user_rules_dir = tmp_path / "user-rules"
        user_rules_dir.mkdir()

        # Write a modified ARCH-001 rule with different severity
        modified_rule_content = """schema_version: 1
rule:
  id: "ARCH-001"
  title: "Modified HTTP rule"
  description: "User-customized version"
  rationale: "Custom rationale"
  tier: 1
  category: "resilience"
  severity: "info"
  languages: [python]
  check:
    type: "forbidden"
    pattern: "requests.get(...)"
  reporting:
    default_message: "Modified message"
    confidence: "high"
    documentation_url: null
  examples:
    good:
      - language: python
        code: "pass"
    bad:
      - language: python
        code: "requests.get()"
  references: []
"""
        (user_rules_dir / "ARCH-001.yaml").write_text(modified_rule_content)

        rules = load_all_rules(user_rules_dir=user_rules_dir)

        # Should still have 7 rules (user ARCH-001 replaced built-in ARCH-001)
        assert len(rules) == 7

        # Find the ARCH-001 rule
        arch_001 = next(rule for rule in rules if rule.rule.id == "ARCH-001")

        # Should have user's modifications
        assert arch_001.rule.title == "Modified HTTP rule"
        assert arch_001.rule.severity == "info"
        assert arch_001.rule.reporting.default_message == "Modified message"
