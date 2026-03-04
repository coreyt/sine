"""Configuration management for Lookout.

Supports loading configuration from:
1. pyproject.toml ([tool.lookout])
2. lookout.toml
3. CLI overrides
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from pydantic import BaseModel, ConfigDict, Field


class LookoutConfig(BaseModel):
    """Global configuration for Lookout."""

    model_config = ConfigDict(extra="ignore")

    # Core settings
    rules_dir: Path = Field(default=Path(".lookout-rules"))
    target: list[Path] = Field(default_factory=lambda: [Path(".")])

    # Output settings
    format: str = Field(default="text")
    fail_on_rule_error: bool = Field(default=False)

    # Discovery settings
    patterns_dir: Path = Field(default=Path(".lookout-patterns"))

    # Integration settings
    repo: str | None = None

    @classmethod
    def load(cls) -> LookoutConfig:
        """Load configuration from standard locations."""
        # 1. Try lookout.toml
        toml_path = Path("lookout.toml")
        if toml_path.exists():
            return cls._load_from_toml(toml_path, section=None)

        # 2. Try pyproject.toml
        pyproject_path = Path("pyproject.toml")
        if pyproject_path.exists():
            return cls._load_from_toml(pyproject_path, section="tool.lookout")

        # 3. Default
        return cls()

    @classmethod
    def _load_from_toml(cls, path: Path, section: str | None) -> LookoutConfig:
        try:
            with path.open("rb") as f:
                data = tomllib.load(f)

            if section:
                # Traverse "tool.lookout"
                for key in section.split("."):
                    data = data.get(key, {})

            # Handle Path conversion for specific fields if they exist as strings
            if "rules_dir" in data:
                data["rules_dir"] = Path(data["rules_dir"])
            if "patterns_dir" in data:
                data["patterns_dir"] = Path(data["patterns_dir"])
            if "target" in data and isinstance(data["target"], list):
                data["target"] = [Path(t) for t in data["target"]]

            return cls.model_validate(data)
        except Exception as e:
            logging.warning(f"Failed to load config from {path}: {e}")
            return cls()
