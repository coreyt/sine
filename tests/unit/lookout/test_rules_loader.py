"""Tests for rules_loader module (hierarchical rule loading)."""

from __future__ import annotations

from pathlib import Path

from lookout.rules_loader import (
    get_built_in_patterns_path,
    load_all_rules,
    load_built_in_patterns,
)
from lookout.semgrep import get_spec_id


class TestGetBuiltInPatternsPath:
    """Tests for get_built_in_patterns_path function."""

    def test_returns_path_object(self):
        """Should return a Path object."""
        path = get_built_in_patterns_path()
        assert isinstance(path, Path)

    def test_points_to_patterns_directory(self):
        """Should point to src/lookout/patterns directory."""
        path = get_built_in_patterns_path()
        assert path.name == "patterns"
        assert path.parent.name == "lookout"


class TestLoadBuiltInPatterns:
    """Tests for load_built_in_patterns function."""

    def test_returns_ten_specs(self):
        """Should load exactly 10 built-in specs (7 v1 + 3 v2)."""
        specs = load_built_in_patterns()
        assert len(specs) == 10

    def test_includes_expected_ids(self):
        """Should include all expected spec IDs."""
        specs = load_built_in_patterns()
        spec_ids = {get_spec_id(s) for s in specs}
        expected_ids = {
            "ARCH-001",
            "ARCH-003",
            "DI-001",
            "LAYER-001",
            "PATTERN-DISC-006",
            "PATTERN-DISC-010",
            "PATTERN-DISC-011",
            "PATTERN-DISC-012",
            "PATTERN-DISC-015",
            "REPO-001",
        }
        assert spec_ids == expected_ids

    def test_handles_missing_directory(self, monkeypatch):
        """Should return empty list if patterns directory doesn't exist."""
        fake_path = Path("/nonexistent/path")
        monkeypatch.setattr("lookout.rules_loader.get_built_in_patterns_path", lambda: fake_path)
        specs = load_built_in_patterns()
        assert specs == []


class TestLoadAllRules:
    """Tests for load_all_rules function."""

    def test_with_no_user_rules_returns_only_builtin(self):
        """Should return only built-in rules when user_rules_dir is None."""
        specs = load_all_rules(user_rules_dir=None)
        assert len(specs) == 10
        spec_ids = {get_spec_id(s) for s in specs}
        assert "ARCH-001" in spec_ids
        assert "ARCH-003" in spec_ids

    def test_with_nonexistent_user_dir_returns_only_builtin(self, tmp_path):
        """Should return only built-in rules when user directory doesn't exist."""
        nonexistent_dir = tmp_path / "nonexistent"
        specs = load_all_rules(user_rules_dir=nonexistent_dir)
        assert len(specs) == 10

    def test_merges_builtin_and_user_rules(self, tmp_path):
        """Should merge built-in and user rules."""
        user_rules_dir = tmp_path / "user-rules"
        user_rules_dir.mkdir()

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

        specs = load_all_rules(user_rules_dir=user_rules_dir)

        assert len(specs) == 11
        spec_ids = {get_spec_id(s) for s in specs}
        assert "ARCH-001" in spec_ids
        assert "CUSTOM-001" in spec_ids

    def test_user_rules_override_builtin_by_id(self, tmp_path):
        """Should allow user rules to override built-in rules by ID."""
        user_rules_dir = tmp_path / "user-rules"
        user_rules_dir.mkdir()

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

        specs = load_all_rules(user_rules_dir=user_rules_dir)

        assert len(specs) == 10

        from lookout.models import RuleSpecFile

        arch_001 = next(s for s in specs if isinstance(s, RuleSpecFile) and s.rule.id == "ARCH-001")
        assert arch_001.rule.title == "Modified HTTP rule"
        assert arch_001.rule.severity == "info"
