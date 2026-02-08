"""Configuration management for Sine."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class DiscoveryConfig(BaseModel):
    """Configuration for pattern discovery features."""

    engine: str = Field(
        default="llm-claude",
        description="Pattern extraction engine (llm-claude, llm-openai, llm-gemini, keyword, hybrid)",
    )
    trusted_domains: list[str] = Field(
        default_factory=lambda: ["martinfowler.com", "refactoring.guru"],
        description="Trusted domains for pattern discovery",
    )


class SineConfig(BaseModel):
    """Main configuration for Sine."""

    enabled: bool = Field(
        default=True,
        description="Enable Sine checks",
    )
    specs_dir: Path = Field(
        default=Path("guidelines"),
        description="Directory containing rule specifications",
    )
    baseline_path: Path = Field(
        default=Path(".sine-baseline.json"),
        description="Path to the baseline file",
    )
    discovery: DiscoveryConfig = Field(
        default_factory=DiscoveryConfig,
        description="Pattern discovery configuration",
    )
