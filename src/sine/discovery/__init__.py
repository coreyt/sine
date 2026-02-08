"""Pattern discovery module for ling.

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

from sine.discovery.agents.base import (
    PatternAgent,
    SearchConstraints,
    SearchFocus,
)
from sine.discovery.models import (
    CompiledPattern,
    DiscoveredPattern,
    PatternExample,
    PatternExamples,
    PatternSearchResult,
    ValidatedPattern,
)
from sine.discovery.storage import PatternStorage

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
