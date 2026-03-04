"""Documentation pattern discovery agent.

This agent discovers architectural patterns from a project's own documentation
(ARCHITECTURE.md, DESIGN.md, ADR files, etc.). It reads markdown files, splits
them into sections, and feeds each section through the configured pattern
extractor.

Unlike the ArchitectureAgent which searches the web for best practices, the
DocsAgent answers "what does *this project* intend?" by reading the project's
own design documentation.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from lookout.discovery.agents.base import SearchConstraints, SearchFocus
from lookout.discovery.models import DiscoveredPattern

if TYPE_CHECKING:
    from lookout.discovery.extractors.base import PatternExtractor

logger = logging.getLogger(__name__)

# Directories to skip when searching for documentation
_EXCLUDED_DIRS = frozenset(
    ["node_modules", ".git", "venv", "__pycache__", "build", "dist", ".venv", ".tox"]
)


@dataclass(frozen=True)
class DocSection:
    """A section extracted from a markdown document."""

    heading: str
    content: str
    level: int
    file_path: Path


class DocsAgent:
    """Agent for discovering patterns from project documentation.

    Reads a project's own markdown documentation, extracts architectural
    patterns and design decisions, and feeds them into the existing
    discovery pipeline.

    Example:
        agent = DocsAgent(extractor=keyword_extractor)

        focus = SearchFocus(
            focus_type="architecture",
            description="Find architectural patterns",
            codebase_path="/path/to/project",
        )

        constraints = SearchConstraints(max_results=10)
        patterns = await agent.discover_patterns(focus, constraints)
    """

    # File patterns grouped by priority (lower index = higher priority)
    _FILE_PATTERNS: list[list[str]] = [
        # Priority 0: Architecture docs
        ["ARCHITECTURE.md", "architecture.md"],
        # Priority 1: Design docs
        ["DESIGN.md", "design.md"],
        # Priority 2: Architecture/design subdirs (handled via glob)
        # Priority 3: ADR files (handled via glob)
        # Priority 4: Contributing
        ["CONTRIBUTING.md", "contributing.md"],
    ]

    _MIN_SECTION_LENGTH = 50

    def __init__(self, extractor: PatternExtractor) -> None:
        self.extractor = extractor

    async def discover_patterns(
        self,
        focus: SearchFocus,
        constraints: SearchConstraints,
    ) -> list[DiscoveredPattern]:
        """Discover patterns from project documentation.

        Args:
            focus: What patterns to look for (codebase_path points to docs)
            constraints: Filters and limits

        Returns:
            List of discovered patterns
        """
        root = Path(focus.codebase_path) if focus.codebase_path else Path(".")
        logger.info(f"Discovering patterns from documentation at {root}")

        doc_files = self._find_doc_files(root)
        if not doc_files:
            logger.warning(f"No documentation files found at {root}")
            return []

        logger.info(f"Found {len(doc_files)} documentation file(s)")

        all_patterns: list[DiscoveredPattern] = []

        for doc_file in doc_files:
            try:
                text = doc_file.read_text(encoding="utf-8")
            except OSError as exc:
                logger.warning(f"Failed to read {doc_file}: {exc}")
                continue

            sections = self._parse_sections(doc_file, text)

            for section in sections:
                from lookout.discovery.extractors.base import ExtractionContext

                heading_slug = re.sub(r"\W+", "-", section.heading.lower()).strip("-")
                context = ExtractionContext(
                    source_url=f"file://{section.file_path}#{heading_slug}",
                    source_text=f"{section.heading}\n\n{section.content}",
                    focus=focus,
                    metadata={
                        "credibility": "0.95",
                        "source_type": "project_documentation",
                    },
                )

                result = await self.extractor.extract_patterns(context)
                filtered = self._filter_patterns(result.patterns, constraints)
                all_patterns.extend(filtered)

        deduplicated = self._deduplicate_patterns(all_patterns)
        logger.info(f"Discovered {len(deduplicated)} unique patterns from documentation")
        return deduplicated[: constraints.max_results]

    def _find_doc_files(self, root: Path) -> list[Path]:
        """Find documentation files in the project.

        Searches for architecture/design documentation using priority-ordered
        patterns. Excludes common non-documentation directories.

        Args:
            root: Project root or explicit file path

        Returns:
            List of documentation file paths, sorted by priority
        """
        # If root is a file, return it directly
        if root.is_file():
            return [root]

        if not root.is_dir():
            return []

        # Priority buckets: each bucket collects files at that priority level
        buckets: list[list[Path]] = [[] for _ in range(5)]

        # Priority 0 & 1: Root-level files (architecture, design)
        for priority, patterns in enumerate(self._FILE_PATTERNS):
            if priority > 1:
                continue
            for name in patterns:
                candidate = root / name
                if candidate.is_file():
                    buckets[priority].append(candidate)

        # Priority 2: docs/architecture/ and docs/design/ subdirs
        for subdir in ["architecture", "design"]:
            docs_dir = root / "docs" / subdir
            if docs_dir.is_dir():
                for md_file in sorted(docs_dir.rglob("*.md")):
                    if not self._is_excluded(md_file, root):
                        buckets[2].append(md_file)

        # Priority 3: ADR files
        for adr_prefix in [root / "docs" / "adr", root / "adr"]:
            if adr_prefix.is_dir():
                for md_file in sorted(adr_prefix.rglob("*.md")):
                    if not self._is_excluded(md_file, root):
                        buckets[3].append(md_file)

        # Priority 4: Contributing
        for name in self._FILE_PATTERNS[2]:  # CONTRIBUTING.md, contributing.md
            candidate = root / name
            if candidate.is_file():
                buckets[4].append(candidate)

        # Flatten in priority order
        result: list[Path] = []
        for bucket in buckets:
            result.extend(bucket)
        return result

    def _is_excluded(self, path: Path, root: Path) -> bool:
        """Check if a path falls under an excluded directory."""
        try:
            relative = path.relative_to(root)
        except ValueError:
            return False
        return any(part in _EXCLUDED_DIRS for part in relative.parts)

    def _parse_sections(self, path: Path, text: str) -> list[DocSection]:
        """Parse markdown text into sections.

        Splits on heading markers (#, ##, ###), preserving code blocks
        intact within sections. Filters out sections shorter than
        _MIN_SECTION_LENGTH characters.

        Args:
            path: Source file path (for metadata)
            text: Raw markdown text

        Returns:
            List of DocSection objects
        """
        if not text.strip():
            return []

        sections: list[DocSection] = []
        current_heading: str | None = None
        current_level: int = 0
        current_lines: list[str] = []

        for line in text.split("\n"):
            heading_match = re.match(r"^(#{1,3})\s+(.+)$", line)
            if heading_match:
                # Flush previous section
                if current_heading is not None:
                    content = "\n".join(current_lines).strip()
                    if len(content) >= self._MIN_SECTION_LENGTH:
                        sections.append(
                            DocSection(
                                heading=current_heading,
                                content=content,
                                level=current_level,
                                file_path=path,
                            )
                        )
                current_heading = heading_match.group(2).strip()
                current_level = len(heading_match.group(1))
                current_lines = []
            else:
                current_lines.append(line)

        # Flush last section
        if current_heading is not None:
            content = "\n".join(current_lines).strip()
            if len(content) >= self._MIN_SECTION_LENGTH:
                sections.append(
                    DocSection(
                        heading=current_heading,
                        content=content,
                        level=current_level,
                        file_path=path,
                    )
                )

        return sections

    def _filter_patterns(
        self,
        patterns: list[DiscoveredPattern],
        constraints: SearchConstraints,
    ) -> list[DiscoveredPattern]:
        """Filter patterns by constraints.

        Same logic as ArchitectureAgent._filter_patterns.
        """
        filtered = []
        for pattern in patterns:
            if (
                constraints.languages
                and pattern.languages
                and not any(lang in constraints.languages for lang in pattern.languages)
            ):
                continue
            if (
                constraints.frameworks
                and pattern.framework
                and pattern.framework not in constraints.frameworks
            ):
                continue
            confidence_levels = {"low": 1, "medium": 2, "high": 3}
            min_level = confidence_levels.get(constraints.min_confidence, 1)
            pattern_level = confidence_levels.get(pattern.confidence, 1)
            if pattern_level < min_level:
                continue
            filtered.append(pattern)
        return filtered

    def _deduplicate_patterns(
        self,
        patterns: list[DiscoveredPattern],
    ) -> list[DiscoveredPattern]:
        """Remove duplicate patterns, keeping highest confidence.

        Same logic as ArchitectureAgent._deduplicate_patterns.
        """
        seen: dict[str, DiscoveredPattern] = {}
        for pattern in patterns:
            if pattern.pattern_id not in seen:
                seen[pattern.pattern_id] = pattern
            else:
                existing = seen[pattern.pattern_id]
                confidence_levels = {"low": 1, "medium": 2, "high": 3}
                existing_level = confidence_levels.get(existing.confidence, 1)
                new_level = confidence_levels.get(pattern.confidence, 1)
                if new_level > existing_level:
                    seen[pattern.pattern_id] = pattern
                elif new_level == existing_level:
                    existing_cred = float(existing.evidence.get("credibility", "0.5"))
                    new_cred = float(pattern.evidence.get("credibility", "0.5"))
                    if new_cred > existing_cred:
                        seen[pattern.pattern_id] = pattern
        return list(seen.values())
