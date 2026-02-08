from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


class MustWrapCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["must_wrap"]
    target: list[str]
    wrapper: list[str]


class ForbiddenCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["forbidden"]
    pattern: str


class RequiredWithCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["required_with"]
    if_present: str
    must_have: str


class RawCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["raw"]
    config: str
    engine: str = "semgrep"


class MetavariableRegex(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metavariable: str
    regex: str


class PatternDiscoveryCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["pattern_discovery"]
    patterns: list[str]
    metavariable_regex: list[MetavariableRegex] | None = None


RuleCheck = Annotated[
    Union[
        MustWrapCheck,
        ForbiddenCheck,
        RequiredWithCheck,
        RawCheck,
        PatternDiscoveryCheck,
    ],
    Field(discriminator="type"),
]


class RuleReporting(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_message: str
    confidence: Literal["low", "medium", "high"]
    documentation_url: str | None = None


class RuleExample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: str
    code: str


class RuleExamples(BaseModel):
    model_config = ConfigDict(extra="forbid")

    good: list[RuleExample]
    bad: list[RuleExample]


class RuleSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    rationale: str
    tier: int = Field(ge=1, le=3)
    category: str
    severity: Literal["error", "warning", "info"]
    languages: list[str]
    check: RuleCheck
    reporting: RuleReporting
    examples: RuleExamples
    references: list[str]


class RuleSpecFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    rule: RuleSpec


@dataclass(frozen=True)
class Finding:
    """Represents a guideline violation (enforcement mode)."""

    guideline_id: str
    title: str
    category: str
    severity: str
    file: str
    line: int
    message: str
    snippet: str
    engine: str
    tier: int


@dataclass(frozen=True)
class PatternInstance:
    """Represents a discovered pattern instance (discovery mode)."""

    pattern_id: str
    title: str
    category: str
    file: str
    line: int
    snippet: str
    confidence: str


@dataclass(frozen=True)
class RuleError:
    """Represents an error executing a rule (e.g. parse error)."""

    rule_id: str
    message: str
    level: str
    type: str