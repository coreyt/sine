"""Pattern discovery module for Lookout.

This module provides infrastructure for discovering, validating, and compiling
coding patterns into automated guidelines.

Public API:
    Models:
        - DiscoveredPattern: Raw agent output
        - ValidatedPattern: Post-quality-gate
        - CompiledPattern: With Semgrep rules
        - PatternSearchResult: Lightweight listing metadata

    Storage:
        - PatternStorage: File-based pattern storage

    Agents:
        - PatternAgent: Protocol for discovery agents
        - SearchFocus: Search focus definition
        - SearchConstraints: Search filters
"""

from lookout.discovery.agents.base import (
    PatternAgent,
    SearchConstraints,
    SearchFocus,
)
from lookout.discovery.models import (
    CompiledPattern,
    DiscoveredPattern,
    PatternExample,
    PatternExamples,
    PatternSearchResult,
    ValidatedPattern,
)
from lookout.discovery.storage import PatternStorage

__all__ = [
    # Models
    "DiscoveredPattern",
    "ValidatedPattern",
    "CompiledPattern",
    "PatternSearchResult",
    "PatternExample",
    "PatternExamples",
    # Storage
    "PatternStorage",
    # Agents
    "PatternAgent",
    "SearchFocus",
    "SearchConstraints",
]
