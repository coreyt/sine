"""Pattern index data models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PatternIndexEntry(BaseModel):
    """A single pattern in the index."""

    id: str
    title: str
    schema_version: int
    category: str
    subcategory: str | None = None
    severity: str
    tier: int
    tags: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    framework_count: int = 0
    variant_count: int = 0
    source_file: str = ""
    status: str = "active"


class PatternIndex(BaseModel):
    """Collection of pattern index entries."""

    entries: list[PatternIndexEntry] = Field(default_factory=list)
    total: int = 0
    built_in_count: int = 0
    user_count: int = 0
