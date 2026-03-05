"""TUI configuration settings."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class TUIConfig(BaseModel):
    """Configuration for the Lookout TUI."""

    llm_model: str = Field(
        default="gemini/gemini-3.1-pro-tools",
        description="LLM model string (provider/model format for litellm)",
    )
    llm_temperature: float = Field(
        default=0.3,
        description="Temperature for LLM generation",
    )
    llm_max_tokens: int = Field(
        default=4096,
        description="Max tokens for LLM responses",
    )
    llm_timeout: float = Field(
        default=120.0,
        description="Timeout in seconds for LLM calls",
    )
    llm_max_retries: int = Field(
        default=3,
        description="Max retry attempts for transient LLM errors",
    )
    prompts_dir: Path = Field(
        default=Path("docs/prompts"),
        description="Directory containing prompt template files",
    )
    index_path: Path = Field(
        default=Path(".lookout-index.json"),
        description="Path to write the pattern index JSON",
    )
    patterns_dir: Path = Field(
        default=Path(".lookout-patterns"),
        description="User patterns directory",
    )
