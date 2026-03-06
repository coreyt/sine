from __future__ import annotations

from pathlib import Path

import yaml

from lookout.models import PatternSpecFile, RuleSpecFile

SpecUnion = RuleSpecFile | PatternSpecFile


def is_discovery_spec(spec: SpecUnion) -> bool:
    """Check if a spec contains only discovery (non-enforcement) checks."""
    if isinstance(spec, PatternSpecFile):
        check_types: list[str] = []
        for v in spec.pattern.variants:
            if v.generic:
                check_types.append(v.generic.check.type)
            for fw in v.frameworks:
                check_types.append(fw.check.type)
        return bool(check_types) and all(t == "pattern_discovery" for t in check_types)
    return spec.rule.check.type == "pattern_discovery"


def load_specs(directory: Path) -> list[SpecUnion]:
    """Load both v1 (flat) and v2 (hierarchical) spec files from a directory."""
    if not directory.exists():
        raise FileNotFoundError(f"Spec directory not found: {directory}")
    specs: list[SpecUnion] = []
    for path in sorted(directory.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        version = data.get("schema_version", 1)
        if version == 1:
            specs.append(RuleSpecFile.model_validate(data))
        elif version == 2:
            specs.append(PatternSpecFile.model_validate(data))
        else:
            raise ValueError(f"Unknown schema_version {version} in {path}")
    return specs


def load_rule_specs(directory: Path) -> list[RuleSpecFile]:
    """Load v1 rule specs only (backward compatibility)."""
    return [s for s in load_specs(directory) if isinstance(s, RuleSpecFile)]
