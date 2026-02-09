"""Hierarchical rule loading for Sine.

Supports loading built-in rules (shipped with package) and user-defined rules,
with user rules taking precedence by rule ID (ESLint-style).
"""

from __future__ import annotations

import sys
from pathlib import Path

from sine.models import RuleSpecFile
from sine.specs import load_rule_specs

if sys.version_info >= (3, 9):
    from importlib.resources import files
else:
    # Fallback for Python 3.8 (though Sine requires 3.10+)
    from importlib.resources import path as resources_path


def get_built_in_rules_path() -> Path:
    """Get path to built-in rules directory.

    Uses importlib.resources to locate the built_in_rules directory
    within the sine package.

    Returns:
        Path to built_in_rules directory
    """
    if sys.version_info >= (3, 9):
        # Python 3.9+: Use importlib.resources.files()
        import sine

        return Path(str(files(sine) / "built_in_rules"))
    else:
        # Fallback: Use __file__ based path resolution
        import sine

        return Path(sine.__file__).parent / "built_in_rules"


def load_built_in_rules() -> list[RuleSpecFile]:
    """Load all built-in rule specifications.

    Built-in rules are shipped with the Sine package in the
    src/sine/built_in_rules/ directory and are always available.

    Returns:
        List of built-in RuleSpecFile objects. Returns empty list
        if built-in rules directory doesn't exist.
    """
    built_in_path = get_built_in_rules_path()

    if not built_in_path.exists():
        return []

    return load_rule_specs(built_in_path)


def load_all_rules(user_rules_dir: Path | None) -> list[RuleSpecFile]:
    """Load built-in rules and user rules with user rules taking precedence.

    This function implements ESLint-style rule loading where:
    1. Built-in rules are always loaded from the package
    2. User rules are loaded from the specified directory (if it exists)
    3. If a user rule has the same ID as a built-in rule, the user rule wins

    Args:
        user_rules_dir: Directory containing user-defined rules.
                       Can be None or a non-existent path (built-in rules only).

    Returns:
        Combined list of RuleSpecFile objects with user rules overriding
        built-in rules by ID.

    Example:
        # Load only built-in rules
        rules = load_all_rules(user_rules_dir=None)

        # Load built-in + user rules from .sine-rules/
        rules = load_all_rules(user_rules_dir=Path(".sine-rules"))
    """
    # Load built-in rules
    built_in_rules = load_built_in_rules()
    built_in_by_id = {spec.rule.id: spec for spec in built_in_rules}

    # Load user rules if directory exists
    user_rules: list[RuleSpecFile] = []
    if user_rules_dir and user_rules_dir.exists():
        user_rules = load_rule_specs(user_rules_dir)

    # Build user rules lookup
    user_by_id = {spec.rule.id: spec for spec in user_rules}

    # Merge: start with built-in, override with user rules
    merged = {}
    merged.update(built_in_by_id)
    merged.update(user_by_id)  # User rules take precedence

    # Return as list (dict values)
    return list(merged.values())
