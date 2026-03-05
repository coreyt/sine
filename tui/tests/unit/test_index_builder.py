"""Tests for pattern index builder."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from lookout_tui.index.builder import build_index


@pytest.fixture
def v1_pattern_dir(tmp_path: Path) -> Path:
    """Create a temp dir with a v1 RuleSpecFile YAML."""
    d = tmp_path / "patterns"
    d.mkdir()
    spec = {
        "schema_version": 1,
        "rule": {
            "id": "ARCH-001",
            "title": "HTTP Resilience",
            "description": "Wrap HTTP calls",
            "rationale": "Prevent cascading failures",
            "tier": 1,
            "category": "resilience",
            "severity": "error",
            "languages": ["python", "typescript"],
            "check": {"type": "must_wrap", "target": ["requests.get"], "wrapper": ["retry"]},
            "reporting": {"default_message": "Wrap HTTP calls", "confidence": "high"},
            "examples": {
                "good": [{"language": "python", "code": "retry(requests.get(url))"}],
                "bad": [{"language": "python", "code": "requests.get(url)"}],
            },
            "references": ["https://example.com"],
        },
    }
    (d / "ARCH-001.yaml").write_text(yaml.dump(spec))
    return d


@pytest.fixture
def v2_pattern_dir(tmp_path: Path) -> Path:
    """Create a temp dir with a v2 PatternSpecFile YAML."""
    d = tmp_path / "patterns_v2"
    d.mkdir()
    spec = {
        "schema_version": 2,
        "pattern": {
            "id": "DI-001",
            "title": "Dependency Injection",
            "description": "Use DI for dependencies",
            "rationale": "Testability",
            "version": "1.0.0",
            "tier": 2,
            "category": "architecture",
            "subcategory": "dependency-injection",
            "severity": "warning",
            "tags": ["solid", "testability"],
            "reporting": {"default_message": "Use DI", "confidence": "medium"},
            "references": [],
            "variants": [
                {
                    "language": "python",
                    "generic": {
                        "check": {"type": "pattern_discovery", "patterns": ["class $C: ..."]},
                        "examples": {"good": [], "bad": []},
                    },
                    "frameworks": [
                        {
                            "name": "django",
                            "check": {
                                "type": "pattern_discovery",
                                "patterns": ["from django.db import ..."],
                            },
                            "examples": {"good": [], "bad": []},
                        }
                    ],
                },
                {
                    "language": "typescript",
                    "generic": {
                        "check": {"type": "pattern_discovery", "patterns": ["class $C { }"]},
                        "examples": {"good": [], "bad": []},
                    },
                    "frameworks": [],
                },
            ],
        },
    }
    (d / "DI-001.yaml").write_text(yaml.dump(spec))
    return d


class TestV1Indexing:
    def test_v1_entry_fields(self, v1_pattern_dir: Path) -> None:
        index = build_index(patterns_dirs=[v1_pattern_dir], include_built_in=False)
        assert index.total == 1
        entry = index.entries[0]
        assert entry.id == "ARCH-001"
        assert entry.title == "HTTP Resilience"
        assert entry.schema_version == 1
        assert entry.category == "resilience"
        assert entry.severity == "error"
        assert entry.tier == 1
        assert entry.languages == ["python", "typescript"]
        assert entry.framework_count == 0
        assert entry.variant_count == 0


class TestV2Indexing:
    def test_v2_entry_fields(self, v2_pattern_dir: Path) -> None:
        index = build_index(patterns_dirs=[v2_pattern_dir], include_built_in=False)
        assert index.total == 1
        entry = index.entries[0]
        assert entry.id == "DI-001"
        assert entry.title == "Dependency Injection"
        assert entry.schema_version == 2
        assert entry.category == "architecture"
        assert entry.subcategory == "dependency-injection"
        assert entry.tags == ["solid", "testability"]
        assert entry.languages == ["python", "typescript"]
        assert entry.framework_count == 1
        assert entry.variant_count == 2


class TestBuiltInPatterns:
    def test_includes_built_in(self) -> None:
        index = build_index(include_built_in=True)
        # Built-in patterns should exist
        assert index.total > 0
        assert index.built_in_count > 0

    def test_excludes_built_in(self) -> None:
        index = build_index(include_built_in=False)
        assert index.total == 0
        assert index.built_in_count == 0


class TestJsonOutput:
    def test_writes_json(self, v1_pattern_dir: Path, tmp_path: Path) -> None:
        output = tmp_path / "index.json"
        build_index(
            patterns_dirs=[v1_pattern_dir],
            include_built_in=False,
            output_path=output,
        )
        assert output.exists()
        data = json.loads(output.read_text())
        assert data["total"] == 1
        assert data["entries"][0]["id"] == "ARCH-001"


class TestMixedVersions:
    def test_v1_and_v2_together(self, v1_pattern_dir: Path, v2_pattern_dir: Path) -> None:
        index = build_index(
            patterns_dirs=[v1_pattern_dir, v2_pattern_dir],
            include_built_in=False,
        )
        assert index.total == 2
        ids = {e.id for e in index.entries}
        assert ids == {"ARCH-001", "DI-001"}
        assert index.user_count == 2


class TestEmptyDir:
    def test_empty_dir(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        index = build_index(patterns_dirs=[empty], include_built_in=False)
        assert index.total == 0

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing"
        index = build_index(patterns_dirs=[missing], include_built_in=False)
        assert index.total == 0
