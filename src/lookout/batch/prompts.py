"""Prompt builder for batch generation requests."""

from __future__ import annotations

import yaml

from lookout.batch.models import RegistryCell
from lookout.models import PatternSpecFile
from lookout.prompts import PromptTemplateLoader


def build_batch_prompts(
    cell: RegistryCell,
    spec: PatternSpecFile,
    loader: PromptTemplateLoader,
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for a batch cell.

    Generic variants use the language-generic template.
    Framework variants use the language-framework template with
    the generic check injected as context.
    """
    system_prompt = loader.load("system-prompt-pattern-research.md")
    pat = spec.pattern
    pattern_id_lower = pat.id.lower().replace("-", "_")

    # Build top-level spec summary for injection
    top_level_spec = _build_top_level_summary(spec)

    if cell.framework is None:
        # Generic variant
        user_prompt = loader.render(
            "user-prompt-language-generic.md",
            TOP_LEVEL_SPEC=top_level_spec,
            LANGUAGE=cell.language,
            VERSION_CONSTRAINT_OR_SKIP="[SKIP]",
            PATTERN_ID_LOWER=pattern_id_lower,
        )
    else:
        # Framework variant — inject generic check as context
        generic_spec = _get_generic_check_yaml(spec, cell.language)
        user_prompt = loader.render(
            "user-prompt-language-framework.md",
            TOP_LEVEL_SPEC=top_level_spec,
            LANGUAGE_GENERIC_SPEC=generic_spec,
            LANGUAGE=cell.language,
            FRAMEWORK=cell.framework,
            FRAMEWORK_VERSION_CONSTRAINT_OR_SKIP="[SKIP]",
            PATTERN_ID_LOWER=pattern_id_lower,
        )

    return system_prompt, user_prompt


def _build_top_level_summary(spec: PatternSpecFile) -> str:
    """Build a text summary of the pattern's top-level spec for prompt injection."""
    pat = spec.pattern
    lines = [
        f"**ID**: {pat.id}",
        f"**Title**: {pat.title}",
        f"**Category**: {pat.category}",
        f"**Tier**: {pat.tier}",
        f"**Severity**: {pat.severity}",
        f"**Description**: {pat.description}",
        f"**Rationale**: {pat.rationale}",
        f"**Default message**: {pat.reporting.default_message}",
        f"**Confidence**: {pat.reporting.confidence}",
    ]
    return "\n".join(lines)


def _get_generic_check_yaml(spec: PatternSpecFile, language: str) -> str:
    """Get the generic variant's check as YAML string for framework prompt context."""
    for variant in spec.pattern.variants:
        if variant.language == language and variant.generic is not None:
            check_data = variant.generic.check.model_dump(mode="json")
            return yaml.dump(check_data, default_flow_style=False)
    return "(No generic variant available yet — generate one from the top-level spec)"
