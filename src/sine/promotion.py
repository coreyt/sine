"""Promotion logic for converting discovered patterns into enforcement rules."""

from __future__ import annotations

from pathlib import Path

import yaml

from sine.discovery.models import ValidatedPattern
from sine.models import (
    RuleExample,
    RuleExamples,
    RuleReporting,
    RuleSpec,
    RuleSpecFile,
)


def promote_to_spec(pattern: ValidatedPattern) -> RuleSpecFile:
    """Convert a validated pattern into a Sine rule specification.

    Args:
        pattern: The validated pattern to promote

    Returns:
        A RuleSpecFile instance
    """
    discovered = pattern.discovered

    # If the agent didn't propose a check, we default to raw (placeholder)
    # or forbidden if there's a pattern string
    check = discovered.proposed_check
    if not check:
        from sine.models import RawCheck

        check = RawCheck(
            type="raw",
            config="# TODO: Implement Semgrep patterns for this rule\nrules: []",
            engine="semgrep",
        )

    rule = RuleSpec(
        id=discovered.pattern_id,
        title=discovered.title,
        description=discovered.description,
        rationale=discovered.rationale,
        tier=pattern.effective_tier,
        category=discovered.category,
        severity=discovered.severity,
        languages=discovered.languages,
        check=check,
        reporting=RuleReporting(
            default_message=f"{discovered.title} ({discovered.pattern_id})",
            confidence=discovered.confidence,
            documentation_url=discovered.references[0] if discovered.references else None,
        ),
        examples=RuleExamples(
            good=[
                RuleExample(language=ex.language, code=ex.code) for ex in discovered.examples.good
            ],
            bad=[RuleExample(language=ex.language, code=ex.code) for ex in discovered.examples.bad],
        ),
        references=discovered.references,
    )

    return RuleSpecFile(schema_version=1, rule=rule)


def save_spec(spec: RuleSpecFile, output_dir: Path) -> Path:
    """Save a RuleSpecFile to a YAML file.

    Args:
        spec: The specification to save
        output_dir: Directory to save the YAML file in

    Returns:
        Path to the saved file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{spec.rule.id}.yaml"

    # Convert to dict for YAML serialization
    # We use model_dump(mode="json") to handle Pydantic objects/enums
    data = spec.model_dump(mode="json")

    with file_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, indent=2)

    return file_path
