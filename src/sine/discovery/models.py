"""Data models for pattern discovery.

This module defines the progression of pattern data through the discovery pipeline:
1. DiscoveredPattern - Raw agent output
2. ValidatedPattern - Post-quality-gate (with human review metadata)
3. CompiledPattern - With generated Semgrep rules

All models use Pydantic for validation with extra="forbid" to catch typos.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sine.models import RuleCheck

# ============================================================================
# Pattern Examples
# ============================================================================


class PatternExample(BaseModel):
    """A code example demonstrating a pattern."""

    model_config = ConfigDict(extra="forbid")

    language: str = Field(..., description="Programming language (e.g., 'python', 'typescript')")
    code: str = Field(..., description="Code snippet")
    description: str | None = Field(default=None, description="Optional explanation of the example")


class PatternExamples(BaseModel):
    """Good and bad examples for a pattern."""

    model_config = ConfigDict(extra="forbid")

    good: list[PatternExample] = Field(
        default_factory=list,
        description="Examples demonstrating correct pattern usage",
    )
    bad: list[PatternExample] = Field(
        default_factory=list,
        description="Examples demonstrating pattern violations",
    )


# ============================================================================
# Tier 1: Agent Output (Raw Discovery)
# ============================================================================


class DiscoveredPattern(BaseModel):
    """Pattern as discovered by an agent (Tier 1).

    This is the raw output from pattern discovery agents. It contains
    everything needed to evaluate whether the pattern should be promoted
    to a validated guideline.

    Tier mapping (from best practices config):
    - confidence "high" + severity "error" → Tier 1 (Non-Negotiables)
    - confidence "medium-high" + severity "warning" → Tier 2 (Strong Recommendations)
    - confidence "low-medium" + framework-specific → Tier 3 (Contextual)
    """

    model_config = ConfigDict(extra="forbid")

    # Identity
    pattern_id: str = Field(
        ...,
        description="Unique identifier (e.g., 'ARCH-DI-001', 'SEC-AUTH-042')",
        pattern=r"^[A-Z]+-[A-Z0-9]+-\d{3}$",
    )
    title: str = Field(..., min_length=5, max_length=120)
    category: str = Field(
        ..., description="Primary category (architecture, security, performance, etc.)"
    )
    subcategory: str | None = Field(
        default=None, description="Subcategory for finer-grained organization"
    )

    # Content
    description: str = Field(
        ..., min_length=20, description="Detailed description of what the pattern requires"
    )
    rationale: str = Field(
        ...,
        min_length=20,
        description="Why this pattern exists and what problems it prevents",
    )

    # Context
    languages: list[str] = Field(
        default_factory=list,
        description="Applicable languages (empty = language-agnostic)",
    )
    framework: str | None = Field(
        default=None, description="Specific framework if tier 3 contextual pattern"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for filtering (e.g., ['solid', 'testability', 'concurrency'])",
    )

    # Severity and confidence
    severity: Literal["error", "warning", "info"] = Field(
        default="warning", description="How critical is this pattern (maps to tier)"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        ..., description="Agent's confidence in the pattern validity"
    )

    # Proposed enforcement
    proposed_check: RuleCheck | None = Field(
        default=None,
        description="Proposed automated check (RuleCheck) for this pattern",
    )

    # Examples and references
    examples: PatternExamples
    references: list[str] = Field(
        default_factory=list, description="URLs or document references for further reading"
    )

    # Provenance (for auditing)
    discovered_by: str = Field(
        ...,
        description='Agent that discovered this pattern (e.g., "codebase-analyzer", "web-research")',
    )
    discovered_at: datetime = Field(
        default_factory=datetime.now, description="When the pattern was discovered (ISO 8601)"
    )
    source_files: list[str] = Field(
        default_factory=list,
        description="Source files analyzed (for codebase-derived patterns)",
    )
    evidence: dict[str, Any] = Field(
        default_factory=dict,
        description="Agent-specific evidence (e.g., occurrence_count, web_sources)",
    )

    @field_validator("pattern_id")
    @classmethod
    def validate_pattern_id_format(cls, v: str) -> str:
        """Ensure pattern ID follows CATEGORY-SUBCATEGORY-NNN format."""
        parts = v.split("-")
        if len(parts) != 3:
            raise ValueError(f"Pattern ID must have 3 parts: {v}")
        if not parts[2].isdigit() or len(parts[2]) != 3:
            raise ValueError(f"Third part must be 3-digit number: {v}")
        return v

    def infer_tier(self) -> int:
        """Infer tier based on severity and confidence.

        Returns:
            1 for non-negotiables, 2 for strong recommendations, 3 for contextual
        """
        if self.severity == "error" and self.confidence == "high":
            return 1
        elif self.framework is not None:
            return 3
        else:
            return 2


# ============================================================================
# Tier 2: Validated Pattern (Post-Quality-Gate)
# ============================================================================


class ValidationMetadata(BaseModel):
    """Metadata from the validation process."""

    model_config = ConfigDict(extra="forbid")

    validated_by: str = Field(..., description="Reviewer username/identifier")
    validated_at: datetime = Field(
        default_factory=datetime.now, description="When validation occurred"
    )
    review_notes: str = Field(default="", description="Notes from validation review")
    tier_override: int | None = Field(
        default=None, ge=1, le=3, description="Manual tier override (if different from inferred)"
    )


class ValidatedPattern(BaseModel):
    """Pattern that has passed quality gate (Tier 2).

    This represents a pattern that has been reviewed by a human and
    approved for inclusion in coding guidelines. It extends the
    discovered pattern with validation metadata.
    """

    model_config = ConfigDict(extra="forbid")

    # Original discovery data (denormalized for easier loading)
    discovered: DiscoveredPattern

    # Validation metadata
    validation: ValidationMetadata

    # Effective tier (either inferred or override)
    effective_tier: int = Field(..., ge=1, le=3)

    @classmethod
    def from_discovered(
        cls,
        pattern: DiscoveredPattern,
        validated_by: str,
        review_notes: str = "",
        tier_override: int | None = None,
    ) -> ValidatedPattern:
        """Create a validated pattern from a discovered pattern.

        Args:
            pattern: The discovered pattern
            validated_by: Reviewer identifier
            review_notes: Optional review notes
            tier_override: Optional tier override

        Returns:
            ValidatedPattern instance
        """
        validation = ValidationMetadata(
            validated_by=validated_by,
            review_notes=review_notes,
            tier_override=tier_override,
        )
        effective_tier = tier_override if tier_override is not None else pattern.infer_tier()

        return cls(
            discovered=pattern,
            validation=validation,
            effective_tier=effective_tier,
        )


# ============================================================================
# Tier 3: Compiled Pattern (With Semgrep Rules)
# ============================================================================


class SemgrepRule(BaseModel):
    """A compiled Semgrep rule for pattern detection."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(..., description="Semgrep rule ID (derived from pattern_id)")
    language: str = Field(..., description="Target language")
    pattern: str | None = Field(default=None, description="Semgrep pattern")
    patterns: list[dict[str, Any]] | None = Field(default=None, description="Complex pattern logic")
    message: str = Field(..., description="Message shown on violation")
    severity: Literal["ERROR", "WARNING", "INFO"]
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata (guideline_id, tier, category, etc.)"
    )


class CompilationMetadata(BaseModel):
    """Metadata from Semgrep rule compilation."""

    model_config = ConfigDict(extra="forbid")

    compiled_at: datetime = Field(
        default_factory=datetime.now, description="When compilation occurred"
    )
    compiler_version: str = Field(default="1.0.0", description="Version of the compilation logic")
    compilation_notes: str = Field(default="", description="Notes about the compilation process")


class CompiledPattern(BaseModel):
    """Pattern with generated Semgrep rules (Tier 3).

    This represents a validated pattern that has been compiled into
    executable Semgrep rules for automated enforcement.
    """

    model_config = ConfigDict(extra="forbid")

    # Original validation data (denormalized)
    validated: ValidatedPattern

    # Generated Semgrep rules (one per language)
    semgrep_rules: list[SemgrepRule] = Field(
        default_factory=list, description="Compiled Semgrep rules"
    )

    # Compilation metadata
    compilation: CompilationMetadata

    @classmethod
    def from_validated(
        cls,
        pattern: ValidatedPattern,
        semgrep_rules: list[SemgrepRule],
        compilation_notes: str = "",
    ) -> CompiledPattern:
        """Create a compiled pattern from a validated pattern.

        Args:
            pattern: The validated pattern
            semgrep_rules: Generated Semgrep rules
            compilation_notes: Optional compilation notes

        Returns:
            CompiledPattern instance
        """
        compilation = CompilationMetadata(compilation_notes=compilation_notes)

        return cls(
            validated=pattern,
            semgrep_rules=semgrep_rules,
            compilation=compilation,
        )


# ============================================================================
# Frozen Result Dataclasses (Immutable)
# ============================================================================


@dataclass(frozen=True)
class PatternSearchResult:
    """Result from searching/listing patterns.

    Lightweight representation for listings and indexes.
    """

    pattern_id: str
    title: str
    category: str
    subcategory: str | None
    tier: int
    confidence: str
    stage: Literal["raw", "validated", "compiled"]


@dataclass(frozen=True)
class PatternLoadError:
    """Error encountered while loading a pattern file."""

    file_path: str
    error_type: str  # e.g., "ValidationError", "JSONDecodeError"
    error_message: str
