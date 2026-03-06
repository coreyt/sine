"""Tests for loading PatternSpecFile (schema_version 2) specs."""

from __future__ import annotations

from pathlib import Path

import yaml

from lookout.models import (
    ForbiddenCheck,
    PatternSpecFile,
    RuleSpecFile,
)
from lookout.specs import load_specs


def _write_v1_rule(directory: Path, rule_id: str = "ARCH-100") -> Path:
    path = directory / f"{rule_id}.yaml"
    path.write_text(
        f"""
schema_version: 1
rule:
  id: "{rule_id}"
  title: "Test Rule"
  description: "Desc"
  rationale: "Because"
  tier: 1
  category: "security"
  severity: "error"
  languages: [python]
  check:
    type: "forbidden"
    pattern: "eval($X)"
  reporting:
    default_message: "Forbidden ({rule_id})"
    confidence: "high"
  examples:
    good:
      - language: python
        code: "safe()"
    bad:
      - language: python
        code: "eval(x)"
  references: []
""",
        encoding="utf-8",
    )
    return path


def _write_v2_pattern(directory: Path, pattern_id: str = "DI-001") -> Path:
    path = directory / f"{pattern_id}.yaml"
    data = {
        "schema_version": 2,
        "pattern": {
            "id": pattern_id,
            "title": "Dependency Injection",
            "description": "Use DI",
            "rationale": "Testability",
            "tier": 2,
            "category": "architecture",
            "severity": "warning",
            "reporting": {
                "default_message": f"DI violation ({pattern_id})",
                "confidence": "high",
            },
            "variants": [
                {
                    "language": "python",
                    "version_constraint": ">=3.10",
                    "generic": {
                        "check": {
                            "type": "forbidden",
                            "pattern": "self.$X = $Y()",
                        },
                        "examples": {
                            "good": [{"language": "python", "code": "self.x = dep"}],
                            "bad": [{"language": "python", "code": "self.x = Dep()"}],
                        },
                    },
                    "frameworks": [
                        {
                            "name": "django",
                            "version_constraint": ">=4.0",
                            "check": {
                                "type": "forbidden",
                                "pattern": "self.$X = $Y()",
                            },
                            "examples": {"good": [], "bad": []},
                        },
                    ],
                },
            ],
            "references": [],
        },
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


class TestLoadSpecs:
    def test_loads_v1_rule_spec(self, tmp_path: Path) -> None:
        _write_v1_rule(tmp_path)
        specs = load_specs(tmp_path)
        assert len(specs) == 1
        assert isinstance(specs[0], RuleSpecFile)
        assert specs[0].rule.id == "ARCH-100"

    def test_loads_v2_pattern_spec(self, tmp_path: Path) -> None:
        _write_v2_pattern(tmp_path)
        specs = load_specs(tmp_path)
        assert len(specs) == 1
        assert isinstance(specs[0], PatternSpecFile)
        assert specs[0].pattern.id == "DI-001"

    def test_loads_mixed_v1_and_v2(self, tmp_path: Path) -> None:
        _write_v1_rule(tmp_path, "ARCH-100")
        _write_v2_pattern(tmp_path, "DI-001")
        specs = load_specs(tmp_path)
        assert len(specs) == 2
        types = {type(s) for s in specs}
        assert RuleSpecFile in types
        assert PatternSpecFile in types

    def test_v2_pattern_has_correct_variant_structure(self, tmp_path: Path) -> None:
        _write_v2_pattern(tmp_path)
        specs = load_specs(tmp_path)
        pattern = specs[0]
        assert isinstance(pattern, PatternSpecFile)
        assert len(pattern.pattern.variants) == 1
        variant = pattern.pattern.variants[0]
        assert variant.language == "python"
        assert variant.version_constraint == ">=3.10"
        assert variant.generic is not None
        assert isinstance(variant.generic.check, ForbiddenCheck)
        assert len(variant.frameworks) == 1
        assert variant.frameworks[0].name == "django"
        assert variant.frameworks[0].version_constraint == ">=4.0"

    def test_load_specs_backwards_compat_with_load_rule_specs(self, tmp_path: Path) -> None:
        """load_rule_specs still works for v1-only directories."""
        from lookout.specs import load_rule_specs

        _write_v1_rule(tmp_path)
        specs = load_rule_specs(tmp_path)
        assert len(specs) == 1
        assert isinstance(specs[0], RuleSpecFile)
