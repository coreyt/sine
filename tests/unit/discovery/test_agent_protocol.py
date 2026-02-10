"""Tests for agent protocol and interface.

Test cases:
- TC-PD-020: Protocol validation
- TC-PD-021: SearchConstraints
- TC-PD-022: SearchFocus
"""

import pytest

from sine.discovery.agents.base import (
    AgentRegistry,
    SearchConstraints,
    SearchFocus,
    validate_agent,
)
from sine.discovery.models import DiscoveredPattern, PatternExamples


class TestAgentProtocol:
    """TC-PD-020: Protocol validation."""

    async def test_valid_agent_passes_validation(self) -> None:
        """Test that a valid agent implementation passes protocol validation."""

        class MockAgent:
            async def discover_patterns(
                self, focus: SearchFocus, constraints: SearchConstraints
            ) -> list[DiscoveredPattern]:
                return []

        agent = MockAgent()
        assert validate_agent(agent) is True

    async def test_invalid_agent_fails_validation(self) -> None:
        """Test that invalid agents fail validation."""

        class InvalidAgent:
            pass  # Missing discover_patterns method

        agent = InvalidAgent()
        assert validate_agent(agent) is False

    async def test_agent_discover_patterns_returns_list(self) -> None:
        """Test that agents return list of DiscoveredPattern."""

        class TestAgent:
            async def discover_patterns(
                self, focus: SearchFocus, constraints: SearchConstraints
            ) -> list[DiscoveredPattern]:
                return [
                    DiscoveredPattern(
                        pattern_id="TEST-001-001",
                        title="Test Pattern",
                        category="test",
                        description="Test description that is long enough",
                        rationale="Test rationale that is long enough",
                        confidence="high",
                        examples=PatternExamples(),
                        discovered_by="test-agent",
                    )
                ]

        agent = TestAgent()
        focus = SearchFocus(focus_type="test", description="Test focus")
        constraints = SearchConstraints()

        results = await agent.discover_patterns(focus, constraints)

        assert len(results) == 1
        assert results[0].pattern_id == "TEST-001-001"


class TestSearchConstraints:
    """TC-PD-021: SearchConstraints."""

    def test_default_constraints(self) -> None:
        """Test default constraint values."""
        constraints = SearchConstraints()

        assert constraints.languages is None
        assert constraints.frameworks is None
        assert constraints.categories is None
        assert constraints.min_confidence == "low"
        assert constraints.min_occurrences == 1
        assert constraints.max_results == 100
        assert constraints.include_framework_specific is True

    def test_custom_constraints(self) -> None:
        """Test custom constraint configuration."""
        constraints = SearchConstraints(
            languages=["python"],
            frameworks=["django"],
            categories=["security"],
            min_confidence="high",
            max_results=50,
        )

        assert constraints.languages == ["python"]
        assert constraints.frameworks == ["django"]
        assert constraints.categories == ["security"]
        assert constraints.min_confidence == "high"
        assert constraints.max_results == 50

    def test_constraints_immutable(self) -> None:
        """Test that SearchConstraints is frozen (immutable)."""
        constraints = SearchConstraints(languages=["python"])

        with pytest.raises(AttributeError):
            constraints.languages = ["javascript"]  # type: ignore


class TestSearchFocus:
    """TC-PD-022: SearchFocus."""

    def test_search_focus_creation(self) -> None:
        """Test creating a search focus."""
        focus = SearchFocus(
            focus_type="security",
            description="Find authentication patterns",
            keywords=["auth", "login", "session"],
        )

        assert focus.focus_type == "security"
        assert focus.description == "Find authentication patterns"
        assert focus.keywords == ["auth", "login", "session"]
        assert focus.codebase_path is None
        assert focus.examples is None

    def test_search_focus_with_codebase_path(self) -> None:
        """Test search focus with codebase path for analysis."""
        focus = SearchFocus(
            focus_type="architecture",
            description="Find DI patterns",
            codebase_path="/path/to/project",
        )

        assert focus.codebase_path == "/path/to/project"

    def test_search_focus_immutable(self) -> None:
        """Test that SearchFocus is frozen."""
        focus = SearchFocus(focus_type="test", description="Test")

        with pytest.raises(AttributeError):
            focus.focus_type = "other"  # type: ignore


class TestAgentRegistry:
    """Test AgentRegistry functionality."""

    async def test_register_and_get_agent(self) -> None:
        """Test registering and retrieving an agent."""

        class MockAgent:
            async def discover_patterns(
                self, focus: SearchFocus, constraints: SearchConstraints
            ) -> list[DiscoveredPattern]:
                return []

        registry = AgentRegistry()
        agent = MockAgent()

        registry.register("mock-agent", agent)
        retrieved = registry.get("mock-agent")

        assert retrieved is agent

    async def test_get_nonexistent_agent_returns_none(self) -> None:
        """Test getting a non-existent agent returns None."""
        registry = AgentRegistry()

        result = registry.get("nonexistent")

        assert result is None

    async def test_list_agents(self) -> None:
        """Test listing registered agents."""

        class MockAgent:
            async def discover_patterns(
                self, focus: SearchFocus, constraints: SearchConstraints
            ) -> list[DiscoveredPattern]:
                return []

        registry = AgentRegistry()
        agent1 = MockAgent()
        agent2 = MockAgent()

        registry.register("agent1", agent1)
        registry.register("agent2", agent2)

        agents = registry.list_agents()

        assert len(agents) == 2
        assert "agent1" in agents
        assert "agent2" in agents

    async def test_list_agents_empty_registry(self) -> None:
        """Test listing agents from empty registry."""
        registry = AgentRegistry()

        agents = registry.list_agents()

        assert agents == []
