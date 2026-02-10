from __future__ import annotations

from pathlib import Path

import yaml

from sine.models import RuleSpecFile


def load_rule_specs(directory: Path) -> list[RuleSpecFile]:
    if not directory.exists():
        raise FileNotFoundError(f"Rule spec directory not found: {directory}")
    specs: list[RuleSpecFile] = []
    for path in sorted(directory.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        specs.append(RuleSpecFile.model_validate(data))
    return specs
