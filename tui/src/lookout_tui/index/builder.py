"""Build pattern index from YAML spec files."""

from __future__ import annotations

import json
from pathlib import Path

from lookout.models import PatternSpecFile, RuleSpecFile
from lookout.rules_loader import get_built_in_patterns_path
from lookout.specs import SpecUnion, load_specs

from lookout_tui.index.models import PatternIndex, PatternIndexEntry


def _entry_from_rule_spec(spec: RuleSpecFile, source_file: str) -> PatternIndexEntry:
    """Build index entry from a v1 RuleSpecFile."""
    rule = spec.rule
    return PatternIndexEntry(
        id=rule.id,
        title=rule.title,
        schema_version=1,
        category=rule.category,
        severity=rule.severity,
        tier=rule.tier,
        languages=list(rule.languages),
        framework_count=0,
        variant_count=0,
        source_file=source_file,
    )


def _entry_from_pattern_spec(spec: PatternSpecFile, source_file: str) -> PatternIndexEntry:
    """Build index entry from a v2 PatternSpecFile."""
    pattern = spec.pattern
    languages: list[str] = []
    framework_count = 0
    for variant in pattern.variants:
        languages.append(variant.language)
        framework_count += len(variant.frameworks)

    return PatternIndexEntry(
        id=pattern.id,
        title=pattern.title,
        schema_version=2,
        category=pattern.category,
        subcategory=pattern.subcategory,
        severity=pattern.severity,
        tier=pattern.tier,
        tags=list(pattern.tags),
        languages=languages,
        framework_count=framework_count,
        variant_count=len(pattern.variants),
        source_file=source_file,
    )


def _build_entry(spec: SpecUnion, source_file: str) -> PatternIndexEntry:
    """Build an index entry from any spec type."""
    if isinstance(spec, PatternSpecFile):
        return _entry_from_pattern_spec(spec, source_file)
    return _entry_from_rule_spec(spec, source_file)


def _get_spec_id(spec: SpecUnion) -> str:
    if isinstance(spec, PatternSpecFile):
        return str(spec.pattern.id)
    return str(spec.rule.id)


def build_index(
    patterns_dirs: list[Path] | None = None,
    include_built_in: bool = True,
    output_path: Path | None = None,
) -> PatternIndex:
    """Build a pattern index from YAML spec files.

    Args:
        patterns_dirs: Additional directories to scan for patterns.
        include_built_in: Whether to include built-in patterns.
        output_path: If provided, write JSON index to this path.

    Returns:
        PatternIndex with all discovered entries.
    """
    entries: list[PatternIndexEntry] = []
    built_in_count = 0

    if include_built_in:
        built_in_path = get_built_in_patterns_path()
        if built_in_path.exists():
            specs = load_specs(built_in_path)
            for spec in specs:
                spec_id = _get_spec_id(spec)
                # Find the source file by matching ID
                source = ""
                for yaml_file in sorted(built_in_path.glob("*.yaml")):
                    if yaml_file.stem.upper() == spec_id or yaml_file.stem == spec_id:
                        source = str(yaml_file)
                        break
                if not source:
                    source = str(built_in_path / f"{spec_id}.yaml")
                entries.append(_build_entry(spec, source))
            built_in_count = len(entries)

    user_count = 0
    for patterns_dir in patterns_dirs or []:
        if patterns_dir.exists():
            specs = load_specs(patterns_dir)
            for spec in specs:
                spec_id = _get_spec_id(spec)
                source = ""
                for yaml_file in sorted(patterns_dir.glob("*.yaml")):
                    if yaml_file.stem.upper() == spec_id or yaml_file.stem == spec_id:
                        source = str(yaml_file)
                        break
                if not source:
                    source = str(patterns_dir / f"{spec_id}.yaml")
                entries.append(_build_entry(spec, source))
                user_count += 1

    index = PatternIndex(
        entries=entries,
        total=len(entries),
        built_in_count=built_in_count,
        user_count=user_count,
    )

    if output_path:
        output_path.write_text(json.dumps(index.model_dump(), indent=2))

    return index
