"""Parse LLM markdown output into structured check data."""

from __future__ import annotations

import re

import yaml

from lookout.models import (
    ForbiddenCheck,
    MustWrapCheck,
    RawCheck,
    RequiredWithCheck,
    RuleCheck,
    RuleExample,
    VariantExamples,
)


def parse_language_generic_output(output: str) -> tuple[RuleCheck, VariantExamples]:
    """Parse markdown from language-generic template into RuleCheck + examples."""
    check_type = _extract_check_type(output)
    yaml_block = _extract_yaml_block(output)
    check = _build_check(check_type, yaml_block)
    examples = _extract_examples(output)
    return check, examples


def parse_framework_output(
    output: str,
) -> tuple[RuleCheck, VariantExamples] | None:
    """Parse framework output. Returns None if output contains SKIP."""
    if re.search(r"^\s*SKIP:", output, re.MULTILINE):
        return None
    return parse_language_generic_output(output)


def _extract_check_type(output: str) -> str:
    """Extract check type from **Check type**: `xxx` pattern."""
    m = re.search(r"\*\*Check type\*\*:\s*[`_]*(\w+)[`_]*", output)
    if not m:
        raise ValueError("Could not find check type in output")
    return m.group(1)


def _extract_yaml_block(output: str) -> str:
    """Extract the first YAML code block after 'Semgrep pattern'."""
    # Find content between ```yaml and ``` after the pattern section
    pattern = r"```yaml\s*\n(.*?)```"
    m = re.search(pattern, output, re.DOTALL)
    if m:
        return m.group(1).strip()
    return ""


def _build_check(check_type: str, yaml_content: str) -> RuleCheck:
    """Build the appropriate check model from type and YAML content."""
    if check_type == "forbidden":
        return ForbiddenCheck(type="forbidden", pattern=yaml_content)

    if check_type == "raw":
        return RawCheck(type="raw", config=yaml_content)

    if check_type == "must_wrap":
        data = yaml.safe_load(yaml_content)
        return MustWrapCheck(
            type="must_wrap",
            target=data.get("target", []),
            wrapper=data.get("wrapper", []),
        )

    if check_type == "required_with":
        data = yaml.safe_load(yaml_content)
        return RequiredWithCheck(
            type="required_with",
            if_present=data.get("if_present", ""),
            must_have=data.get("must_have", ""),
        )

    raise ValueError(f"Unknown check type: {check_type}")


def _extract_examples(output: str) -> VariantExamples:
    """Extract good and bad code examples from the output."""
    good = _extract_example_block(output, "good")
    bad = _extract_example_block(output, "bad")
    return VariantExamples(good=good, bad=bad)


def _extract_example_block(output: str, kind: str) -> list[RuleExample]:
    """Extract code examples marked as good or bad."""
    # Look for **Good example** or **Bad example** followed by a code block
    if kind == "good":
        pattern = r"\*\*Good example\*\*.*?```(\w+)\s*\n(.*?)```"
    else:
        pattern = r"\*\*Bad example\*\*.*?```(\w+)\s*\n(.*?)```"

    matches = re.findall(pattern, output, re.DOTALL)
    examples: list[RuleExample] = []
    for lang, code in matches:
        examples.append(RuleExample(language=lang, code=code.strip()))
    return examples
