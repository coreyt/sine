"""Unit tests for documentation pattern discovery agent."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from lookout.discovery.agents.base import SearchConstraints, SearchFocus, validate_agent
from lookout.discovery.extractors.base import ExtractionResult
from lookout.discovery.models import DiscoveredPattern, PatternExamples


def _make_pattern(
    pattern_id: str = "ARCH-DI-001",
    title: str = "Use Dependency Injection for Loose Coupling",
    confidence: str = "high",
    languages: list[str] | None = None,
    framework: str | None = None,
    evidence: dict[str, str] | None = None,
) -> DiscoveredPattern:
    """Helper to build a DiscoveredPattern with minimal boilerplate."""
    return DiscoveredPattern(
        pattern_id=pattern_id,
        title=title,
        category="architecture",
        subcategory="dependency-injection",
        description="Inject dependencies rather than creating them directly for loose coupling.",
        rationale="Improves testability, maintainability, and flexibility by decoupling implementations.",
        severity="info",
        confidence=confidence,
        discovered_by="docs-agent",
        languages=languages or [],
        framework=framework,
        examples=PatternExamples(),
        evidence=evidence or {},
    )


# ============================================================================
# DocSection parsing
# ============================================================================


class TestParseSections:
    """Tests for DocsAgent._parse_sections."""

    def _parse(self, text: str, path: Path | None = None) -> list:
        from lookout.discovery.agents.docs import DocsAgent

        agent = DocsAgent(extractor=Mock())
        return agent._parse_sections(path or Path("test.md"), text)

    def test_splits_on_headings(self) -> None:
        """Splits markdown on ## headings correctly."""
        text = (
            "# Top\nThis is the introduction text and it is long enough to pass the filter.\n"
            "## Section A\nContent for section A is also long enough to pass the fifty char filter.\n"
            "## Section B\nContent for section B is also long enough to pass the fifty char filter."
        )
        sections = self._parse(text)
        headings = [s.heading for s in sections]
        assert "Top" in headings
        assert "Section A" in headings
        assert "Section B" in headings

    def test_preserves_code_blocks(self) -> None:
        """Code blocks within sections are preserved intact."""
        text = "## Example\nSome text\n```python\ndef foo():\n    pass\n```\nMore text"
        sections = self._parse(text)
        code_section = [s for s in sections if s.heading == "Example"][0]
        assert "```python" in code_section.content
        assert "def foo():" in code_section.content

    def test_single_section_document(self) -> None:
        """Handles a document with only a single top-level heading."""
        text = "# Architecture\nThis document describes our architecture in great detail."
        sections = self._parse(text)
        assert len(sections) == 1
        assert sections[0].heading == "Architecture"

    def test_nested_headings(self) -> None:
        """### headings under ## are captured with correct level."""
        text = (
            "## Parent\nParent text that is long enough to pass the fifty character minimum length filter.\n"
            "### Child\nChild text that is also long enough to pass the fifty character minimum length filter."
        )
        sections = self._parse(text)
        levels = {s.heading: s.level for s in sections}
        assert levels["Parent"] == 2
        assert levels["Child"] == 3

    def test_skips_short_sections(self) -> None:
        """Sections shorter than 50 characters are skipped."""
        text = "## Short\nToo short\n## Long Enough\nThis section has more than fifty characters of content to pass the filter."
        sections = self._parse(text)
        headings = [s.heading for s in sections]
        assert "Short" not in headings
        assert "Long Enough" in headings

    def test_empty_file(self) -> None:
        """Empty files return no sections."""
        assert self._parse("") == []

    def test_file_path_preserved(self, tmp_path: Path) -> None:
        """DocSection.file_path matches the input path."""
        text = "## Section\nContent that is long enough to pass the fifty character minimum filter."
        sections = self._parse(text, path=tmp_path / "ARCHITECTURE.md")
        assert sections[0].file_path == tmp_path / "ARCHITECTURE.md"


# ============================================================================
# File discovery
# ============================================================================


class TestFindDocFiles:
    """Tests for DocsAgent._find_doc_files."""

    def _find(self, root: Path) -> list[Path]:
        from lookout.discovery.agents.docs import DocsAgent

        agent = DocsAgent(extractor=Mock())
        return agent._find_doc_files(root)

    def test_finds_architecture_md_at_root(self, tmp_path: Path) -> None:
        """Finds ARCHITECTURE.md at the project root."""
        (tmp_path / "ARCHITECTURE.md").write_text("# Arch\nContent")
        files = self._find(tmp_path)
        assert tmp_path / "ARCHITECTURE.md" in files

    def test_finds_docs_architecture_subdir(self, tmp_path: Path) -> None:
        """Finds docs/architecture/**/*.md recursively."""
        arch_dir = tmp_path / "docs" / "architecture"
        arch_dir.mkdir(parents=True)
        (arch_dir / "overview.md").write_text("# Overview\nContent")
        files = self._find(tmp_path)
        assert arch_dir / "overview.md" in files

    def test_finds_adr_files(self, tmp_path: Path) -> None:
        """Finds ADR files in docs/adr/ directory."""
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True)
        (adr_dir / "001-use-di.md").write_text("# ADR-001\nContent")
        files = self._find(tmp_path)
        assert adr_dir / "001-use-di.md" in files

    def test_skips_excluded_dirs(self, tmp_path: Path) -> None:
        """Skips node_modules, .git, venv, __pycache__."""
        for dirname in ["node_modules", ".git", "venv", "__pycache__"]:
            excluded = tmp_path / dirname
            excluded.mkdir()
            (excluded / "ARCHITECTURE.md").write_text("# Arch\nContent")
        files = self._find(tmp_path)
        assert files == []

    def test_returns_empty_when_no_docs(self, tmp_path: Path) -> None:
        """Returns empty list when no documentation files exist."""
        (tmp_path / "main.py").write_text("print('hello')")
        files = self._find(tmp_path)
        assert files == []

    def test_handles_explicit_file_path(self, tmp_path: Path) -> None:
        """When given a file path (not dir), returns just that file."""
        f = tmp_path / "MY_DOCS.md"
        f.write_text("# Custom\nContent")
        files = self._find(f)
        assert files == [f]

    def test_priority_order(self, tmp_path: Path) -> None:
        """Architecture docs come before design docs, which come before ADRs."""
        (tmp_path / "ARCHITECTURE.md").write_text("# Arch\nContent")
        (tmp_path / "DESIGN.md").write_text("# Design\nContent")
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True)
        (adr_dir / "001.md").write_text("# ADR\nContent")
        (tmp_path / "CONTRIBUTING.md").write_text("# Contributing\nContent")
        files = self._find(tmp_path)
        names = [f.name for f in files]
        arch_idx = names.index("ARCHITECTURE.md")
        design_idx = names.index("DESIGN.md")
        adr_idx = names.index("001.md")
        contrib_idx = names.index("CONTRIBUTING.md")
        assert arch_idx < design_idx < adr_idx < contrib_idx


# ============================================================================
# Pattern discovery (integration with mocked extractor)
# ============================================================================


class TestDiscoverPatterns:
    """Tests for DocsAgent.discover_patterns."""

    @pytest.fixture
    def mock_extractor(self) -> Mock:
        return Mock()

    @pytest.fixture
    def arch_doc(self, tmp_path: Path) -> Path:
        """Create an ARCHITECTURE.md with realistic content."""
        doc = tmp_path / "ARCHITECTURE.md"
        doc.write_text(
            "# Architecture\n\n"
            "## Dependency Injection\n\n"
            "All services use constructor injection. Never instantiate dependencies "
            "directly. This ensures testability and allows swapping implementations.\n\n"
            "```python\n"
            "class UserService:\n"
            "    def __init__(self, repo: UserRepository):\n"
            "        self.repo = repo\n"
            "```\n\n"
            "## Error Handling\n\n"
            "All errors must be caught at the boundary layer. Internal code should "
            "raise domain exceptions. Never swallow exceptions silently.\n"
        )
        return tmp_path

    @pytest.mark.asyncio
    async def test_extracts_patterns_from_doc(self, mock_extractor: Mock, arch_doc: Path) -> None:
        """Extracts patterns from architecture documentation."""
        from lookout.discovery.agents.docs import DocsAgent

        pattern = _make_pattern()
        mock_extractor.extract_patterns = AsyncMock(
            return_value=ExtractionResult(patterns=[pattern], confidence=0.9, method="keyword")
        )

        agent = DocsAgent(extractor=mock_extractor)
        focus = SearchFocus(
            focus_type="architecture",
            description="Find patterns",
            codebase_path=str(arch_doc),
        )
        constraints = SearchConstraints(max_results=10)

        patterns = await agent.discover_patterns(focus, constraints)
        assert len(patterns) >= 1
        mock_extractor.extract_patterns.assert_called()

    @pytest.mark.asyncio
    async def test_respects_language_filter(self, mock_extractor: Mock, arch_doc: Path) -> None:
        """Only returns patterns matching the language constraint."""
        from lookout.discovery.agents.docs import DocsAgent

        py_pattern = _make_pattern(pattern_id="ARCH-DI-001", languages=["python"])
        java_pattern = _make_pattern(pattern_id="ARCH-DI-002", languages=["java"])

        mock_extractor.extract_patterns = AsyncMock(
            return_value=ExtractionResult(
                patterns=[py_pattern, java_pattern], confidence=0.9, method="keyword"
            )
        )

        agent = DocsAgent(extractor=mock_extractor)
        focus = SearchFocus(
            focus_type="architecture",
            description="Find patterns",
            codebase_path=str(arch_doc),
        )
        constraints = SearchConstraints(languages=["python"], max_results=10)

        patterns = await agent.discover_patterns(focus, constraints)
        ids = {p.pattern_id for p in patterns}
        assert "ARCH-DI-001" in ids
        assert "ARCH-DI-002" not in ids

    @pytest.mark.asyncio
    async def test_deduplicates_across_files(self, mock_extractor: Mock, tmp_path: Path) -> None:
        """Duplicate pattern_ids across files are deduplicated."""
        from lookout.discovery.agents.docs import DocsAgent

        (tmp_path / "ARCHITECTURE.md").write_text(
            "## DI Pattern\nAll services use constructor injection for all dependencies in the system.\n"
        )
        (tmp_path / "DESIGN.md").write_text(
            "## DI Pattern\nDependency injection is used everywhere for all services in the system.\n"
        )

        pattern = _make_pattern(pattern_id="ARCH-DI-001", confidence="high")
        mock_extractor.extract_patterns = AsyncMock(
            return_value=ExtractionResult(patterns=[pattern], confidence=0.9, method="keyword")
        )

        agent = DocsAgent(extractor=mock_extractor)
        focus = SearchFocus(
            focus_type="architecture",
            description="Find patterns",
            codebase_path=str(tmp_path),
        )
        constraints = SearchConstraints(max_results=10)

        patterns = await agent.discover_patterns(focus, constraints)
        ids = [p.pattern_id for p in patterns]
        assert ids.count("ARCH-DI-001") == 1

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_docs(self, mock_extractor: Mock, tmp_path: Path) -> None:
        """Returns empty list when no documentation files are found."""
        from lookout.discovery.agents.docs import DocsAgent

        agent = DocsAgent(extractor=mock_extractor)
        focus = SearchFocus(
            focus_type="architecture",
            description="Find patterns",
            codebase_path=str(tmp_path),
        )
        constraints = SearchConstraints(max_results=10)

        patterns = await agent.discover_patterns(focus, constraints)
        assert patterns == []

    @pytest.mark.asyncio
    async def test_respects_max_results(self, mock_extractor: Mock, arch_doc: Path) -> None:
        """Respects max_results constraint."""
        from lookout.discovery.agents.docs import DocsAgent

        many_patterns = [_make_pattern(pattern_id=f"ARCH-DI-{i:03d}") for i in range(10)]
        mock_extractor.extract_patterns = AsyncMock(
            return_value=ExtractionResult(patterns=many_patterns, confidence=0.9, method="keyword")
        )

        agent = DocsAgent(extractor=mock_extractor)
        focus = SearchFocus(
            focus_type="architecture",
            description="Find patterns",
            codebase_path=str(arch_doc),
        )
        constraints = SearchConstraints(max_results=3)

        patterns = await agent.discover_patterns(focus, constraints)
        assert len(patterns) <= 3

    @pytest.mark.asyncio
    async def test_extraction_context_metadata(self, mock_extractor: Mock, arch_doc: Path) -> None:
        """ExtractionContext has correct source_type and credibility metadata."""
        from lookout.discovery.agents.docs import DocsAgent
        from lookout.discovery.extractors.base import ExtractionContext

        captured: list[ExtractionContext] = []

        async def capture_extract(ctx: ExtractionContext) -> ExtractionResult:
            captured.append(ctx)
            return ExtractionResult(patterns=[], confidence=0.0, method="keyword")

        mock_extractor.extract_patterns = AsyncMock(side_effect=capture_extract)

        agent = DocsAgent(extractor=mock_extractor)
        focus = SearchFocus(
            focus_type="architecture",
            description="Find patterns",
            codebase_path=str(arch_doc),
        )
        constraints = SearchConstraints(max_results=10)

        await agent.discover_patterns(focus, constraints)

        assert len(captured) > 0
        ctx = captured[0]
        assert ctx.metadata["source_type"] == "project_documentation"
        assert ctx.metadata["credibility"] == "0.95"
        assert ctx.source_url.startswith("file://")

    @pytest.mark.asyncio
    async def test_defaults_to_cwd(self, tmp_path: Path) -> None:
        """When codebase_path is None, defaults to current directory."""
        import os

        from lookout.discovery.agents.docs import DocsAgent

        mock_ext = Mock()
        mock_ext.extract_patterns = AsyncMock(
            return_value=ExtractionResult(patterns=[], confidence=0.0, method="keyword")
        )
        agent = DocsAgent(extractor=mock_ext)

        # Use an empty tmp dir so no docs are found
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            focus = SearchFocus(
                focus_type="architecture",
                description="Find patterns",
                codebase_path=None,
            )
            constraints = SearchConstraints(max_results=10)
            patterns = await agent.discover_patterns(focus, constraints)
            assert isinstance(patterns, list)
        finally:
            os.chdir(old_cwd)


# ============================================================================
# Protocol conformance
# ============================================================================


class TestDocsAgentProtocol:
    """Tests for DocsAgent conformance to PatternAgent protocol."""

    def test_passes_validate_agent(self) -> None:
        """DocsAgent passes the validate_agent check."""
        from lookout.discovery.agents.docs import DocsAgent

        agent = DocsAgent(extractor=Mock())
        assert validate_agent(agent)

    def test_works_with_search_focus_codebase_path(self) -> None:
        """SearchFocus.codebase_path is accepted by DocsAgent."""
        from lookout.discovery.agents.docs import DocsAgent

        agent = DocsAgent(extractor=Mock())
        focus = SearchFocus(
            focus_type="architecture",
            description="Find patterns",
            codebase_path="/some/path",
        )
        # Should be accepted without error
        assert focus.codebase_path == "/some/path"
        assert validate_agent(agent)
