"""Hierarchical rule loading for Lookout.

Supports loading built-in patterns (shipped with package) and user-defined
patterns, with user specs taking precedence by ID (ESLint-style).
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from lookout.semgrep import get_spec_id
from lookout.specs import SpecUnion, load_specs


def get_built_in_patterns_path() -> Path:
    """Get path to built-in patterns directory.

    Uses importlib.resources to locate the patterns directory
    within the lookout package.

    Returns:
        Path to patterns directory
    """
    import lookout

    return Path(str(files(lookout) / "patterns"))


def load_built_in_patterns() -> list[SpecUnion]:
    """Load all built-in pattern specifications.

    Built-in specs are shipped with the Lookout package and are always available.

    Returns:
        List of spec objects. Returns empty list if directory doesn't exist.
    """
    built_in_path = get_built_in_patterns_path()

    if not built_in_path.exists():
        return []

    return load_specs(built_in_path)


def load_all_rules(user_rules_dir: Path | None) -> list[SpecUnion]:
    """Load built-in and user patterns with user patterns taking precedence.

    Implements ESLint-style loading where:
    1. Built-in patterns are always loaded from the package
    2. User patterns are loaded from the specified directory (if it exists)
    3. If a user pattern has the same ID as a built-in, the user pattern wins

    Args:
        user_rules_dir: Directory containing user-defined patterns.
                       Can be None or a non-existent path (built-in only).

    Returns:
        Combined list of spec objects with user patterns overriding
        built-in patterns by ID.
    """
    built_in = load_built_in_patterns()
    built_in_by_id = {get_spec_id(spec): spec for spec in built_in}

    user_specs: list[SpecUnion] = []
    if user_rules_dir and user_rules_dir.exists():
        user_specs = load_specs(user_rules_dir)

    user_by_id = {get_spec_id(spec): spec for spec in user_specs}

    merged: dict[str, SpecUnion] = {}
    merged.update(built_in_by_id)
    merged.update(user_by_id)

    return list(merged.values())
