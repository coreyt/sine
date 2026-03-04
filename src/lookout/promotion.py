"""Promotion logic for converting discovered patterns into enforcement rules."""

from __future__ import annotations

from pathlib import Path

import yaml

from lookout.discovery.models import ValidatedPattern
from lookout.models import (
    RuleCheck,
    RuleExample,
    RuleExamples,
    RuleReporting,
    RuleSpec,
    RuleSpecFile,
)


def promote_to_spec(
    pattern: ValidatedPattern,
    check_override: RuleCheck | None = None,
) -> RuleSpecFile:
    """Convert a validated pattern into a Lookout rule specification.

    Args:
        pattern: The validated pattern to promote
        check_override: Optional check to use instead of the pattern's proposed_check

    Returns:
        A RuleSpecFile instance
    """
    discovered = pattern.discovered

    # Use override first, then proposed_check, then fallback placeholder
    check = check_override or discovered.proposed_check
    if not check:
        from lookout.models import PatternDiscoveryCheck

        check = PatternDiscoveryCheck(
            type="pattern_discovery",
            patterns=["..."],  # wildcard placeholder — replace with specific patterns
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


def save_spec(
    spec: RuleSpecFile,
    output_dir: Path,
    scaffolding: str | None = None,
) -> Path:
    """Save a RuleSpecFile to a YAML file.

    If scaffolding text is provided (Requirement/Constraints/Design from the
    LLM rule generator), it is prepended as YAML comments above the rule body.

    Args:
        spec: The specification to save
        output_dir: Directory to save the YAML file in
        scaffolding: Optional scaffolding text to include as YAML comments

    Returns:
        Path to the saved file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{spec.rule.id}.yaml"

    # Convert to dict for YAML serialization
    # We use model_dump(mode="json") to handle Pydantic objects/enums
    data = spec.model_dump(mode="json")

    with file_path.open("w", encoding="utf-8") as f:
        if scaffolding:
            for line in scaffolding.splitlines():
                f.write(f"# {line}\n")
            f.write("#\n")
        yaml.safe_dump(data, f, sort_keys=False, indent=2)

    return file_path
