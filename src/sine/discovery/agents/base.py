"""Base interface for pattern discovery agents.

Agents are responsible for discovering coding patterns from various sources:
- Codebase analysis (AST parsing, call graph analysis)
- Web research (documentation, blog posts, StackOverflow)
- LLM synthesis (asking models about best practices)
- Manual curation (human-defined patterns)

All agents implement the PatternAgent protocol and return DiscoveredPattern objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sine.discovery.models import DiscoveredPattern


@dataclass(frozen=True)
class SearchConstraints:
    """Constraints for pattern discovery searches.

    These constraints help agents focus their search and filter results.
    """

    # Language/framework filters
    languages: list[str] | None = None  # e.g., ["python", "typescript"]
    frameworks: list[str] | None = None  # e.g., ["django", "fastapi"]

    # Category filters
    categories: list[str] | None = None  # e.g., ["security", "architecture"]

    # Quality thresholds
    min_confidence: str = "low"  # "low", "medium", "high"
    min_occurrences: int = 1  # For codebase analysis

    # Search scope
    max_results: int = 100
    include_framework_specific: bool = True


@dataclass(frozen=True)
class SearchFocus:
    """Focus area for pattern discovery.

    Agents use this to understand what patterns to prioritize.
    """

    # Primary focus
    focus_type: str  # "security", "architecture", "performance", etc.
    description: str  # Human-readable description of what to look for

    # Context
    codebase_path: str | None = None  # For codebase analysis agents
    keywords: list[str] | None = None  # For web research agents
    examples: list[str] | None = None  # Example patterns to find similar


class PatternAgent(Protocol):
    """Protocol for pattern discovery agents.

    Agents implement this interface to participate in pattern discovery.
    The protocol uses structural typing (duck typing) so agents don't
    need to inherit from a base class.

    Example:
        class CodebaseAnalyzer:
            async def discover_patterns(
                self,
                focus: SearchFocus,
                constraints: SearchConstraints,
            ) -> list[DiscoveredPattern]:
                # Analyze codebase for patterns...
                return patterns
    """

    async def discover_patterns(
        self,
        focus: SearchFocus,
        constraints: SearchConstraints,
    ) -> list[DiscoveredPattern]:
        """Discover patterns based on search focus and constraints.

        This is an async method to support agents that make network requests
        (web research, LLM API calls) or perform long-running analysis.

        Args:
            focus: What to look for
            constraints: Filters and limits

        Returns:
            List of discovered patterns

        Raises:
            AgentError: If discovery fails
        """
        ...


# ============================================================================
# Agent Registry (for Phase 2+)
# ============================================================================


class AgentRegistry:
    """Registry for pattern discovery agents.

    This will be used in Phase 2+ to manage multiple agents and
    coordinate their execution.
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._agents: dict[str, PatternAgent] = {}

    def register(self, name: str, agent: PatternAgent) -> None:
        """Register an agent.

        Args:
            name: Agent identifier (e.g., "codebase-analyzer")
            agent: Agent instance implementing PatternAgent protocol
        """
        self._agents[name] = agent

    def get(self, name: str) -> PatternAgent | None:
        """Get a registered agent by name.

        Args:
            name: Agent identifier

        Returns:
            Agent instance or None if not found
        """
        return self._agents.get(name)

    def list_agents(self) -> list[str]:
        """List all registered agent names.

        Returns:
            List of agent identifiers
        """
        return list(self._agents.keys())


# ============================================================================
# Helper Functions
# ============================================================================


def validate_agent(agent: object) -> bool:
    """Check if an object implements the PatternAgent protocol.

    Args:
        agent: Object to validate

    Returns:
        True if the object has a discover_patterns method with correct signature
    """
    return hasattr(agent, "discover_patterns") and callable(
        agent.discover_patterns
    )
