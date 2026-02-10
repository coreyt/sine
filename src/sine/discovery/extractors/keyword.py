"""Keyword-based pattern extraction.

This extractor uses rule-based templates and keyword matching to discover
patterns. It's fast, free (no API costs), and works offline, but may be
less accurate than LLM-based extraction.

Strategy:
1. Match keywords against predefined pattern templates
2. Count keyword frequency to determine confidence
3. Extract code examples based on indicators (good/bad)
4. Determine subcategory from keyword clusters
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sine.discovery.extractors.base import (
    ExtractionContext,
    ExtractionResult,
    PatternExtractor,
)
from sine.discovery.models import (
    DiscoveredPattern,
    PatternExample,
    PatternExamples,
)


@dataclass(frozen=True)
class PatternTemplate:
    """Template for a known pattern type."""

    pattern_id_prefix: str  # e.g., "ARCH-DI"
    title: str
    category: str
    subcategory: str
    description: str
    rationale: str
    severity: Literal["error", "warning", "info"]
    keywords: list[str]  # Primary keywords for matching
    languages: list[str]  # Applicable languages
    framework: str | None = None  # For tier 3 patterns


# Pattern template database
PATTERN_TEMPLATES: list[PatternTemplate] = [
    # Architecture patterns
    PatternTemplate(
        pattern_id_prefix="ARCH-DI",
        title="Use Dependency Injection",
        category="architecture",
        subcategory="dependency-injection",
        description="Services should use constructor injection for their dependencies instead of instantiating them directly.",
        rationale="Enables testing, loose coupling, and easier refactoring.",
        severity="warning",
        keywords=[
            "dependency injection",
            "di",
            "constructor injection",
            "ioc",
            "inversion of control",
        ],
        languages=["python", "typescript", "java", "csharp"],
    ),
    PatternTemplate(
        pattern_id_prefix="ARCH-SING",
        title="Avoid Singleton Pattern Abuse",
        category="architecture",
        subcategory="design-patterns",
        description="Singleton pattern should be used sparingly as it introduces global state and tight coupling.",
        rationale="Singletons make testing difficult and hide dependencies.",
        severity="warning",
        keywords=["singleton", "global state", "anti-pattern"],
        languages=["python", "typescript", "java", "csharp"],
    ),
    PatternTemplate(
        pattern_id_prefix="ARCH-FAC",
        title="Use Factory Pattern for Object Creation",
        category="architecture",
        subcategory="design-patterns",
        description="Use factory methods or abstract factories for complex object creation logic.",
        rationale="Encapsulates creation logic and enables polymorphism.",
        severity="info",
        keywords=["factory pattern", "factory method", "abstract factory", "creational pattern"],
        languages=["python", "typescript", "java", "csharp"],
    ),
    PatternTemplate(
        pattern_id_prefix="ARCH-MVC",
        title="Follow MVC Architecture",
        category="architecture",
        subcategory="architectural-patterns",
        description="Separate concerns using Model-View-Controller pattern.",
        rationale="Improves maintainability and testability through separation of concerns.",
        severity="warning",
        keywords=["mvc", "model view controller", "separation of concerns", "layered architecture"],
        languages=["python", "typescript", "java", "csharp"],
    ),
    PatternTemplate(
        pattern_id_prefix="ARCH-REP",
        title="Use Repository Pattern for Data Access",
        category="architecture",
        subcategory="data-access",
        description="Encapsulate data access logic in repository classes.",
        rationale="Abstracts data source and enables testing with mock repositories.",
        severity="info",
        keywords=["repository pattern", "data access", "dao", "data access object"],
        languages=["python", "typescript", "java", "csharp"],
    ),
    # Security patterns
    PatternTemplate(
        pattern_id_prefix="SEC-SQL",
        title="Prevent SQL Injection",
        category="security",
        subcategory="injection",
        description="Use parameterized queries or ORMs instead of string concatenation for SQL queries.",
        rationale="Prevents SQL injection attacks that can expose or modify data.",
        severity="error",
        keywords=["sql injection", "parameterized query", "prepared statement", "orm"],
        languages=["python", "typescript", "java", "csharp"],
    ),
    PatternTemplate(
        pattern_id_prefix="SEC-XSS",
        title="Prevent Cross-Site Scripting (XSS)",
        category="security",
        subcategory="injection",
        description="Sanitize and escape user input before rendering in HTML.",
        rationale="Prevents XSS attacks that can steal user credentials or session tokens.",
        severity="error",
        keywords=[
            "xss",
            "cross-site scripting",
            "sanitize input",
            "escape html",
            "content security policy",
        ],
        languages=["typescript", "python"],
    ),
    PatternTemplate(
        pattern_id_prefix="SEC-AUTH",
        title="Implement Proper Authentication",
        category="security",
        subcategory="authentication",
        description="Use industry-standard authentication mechanisms (OAuth, JWT, etc.).",
        rationale="Ensures user identity is properly verified.",
        severity="error",
        keywords=["authentication", "oauth", "jwt", "session management", "password hashing"],
        languages=["python", "typescript", "java", "csharp"],
    ),
    PatternTemplate(
        pattern_id_prefix="SEC-CSRF",
        title="Prevent CSRF Attacks",
        category="security",
        subcategory="csrf",
        description="Use CSRF tokens for state-changing operations.",
        rationale="Prevents cross-site request forgery attacks.",
        severity="error",
        keywords=["csrf", "cross-site request forgery", "csrf token", "same-site cookie"],
        languages=["typescript", "python"],
    ),
    PatternTemplate(
        pattern_id_prefix="SEC-VAL",
        title="Validate All User Input",
        category="security",
        subcategory="input-validation",
        description="Validate and sanitize all user input at system boundaries.",
        rationale="Prevents injection attacks and data corruption.",
        severity="error",
        keywords=["input validation", "sanitize", "whitelist", "validate input"],
        languages=["python", "typescript", "java", "csharp"],
    ),
    # Performance patterns
    PatternTemplate(
        pattern_id_prefix="PERF-CACHE",
        title="Use Caching Appropriately",
        category="performance",
        subcategory="caching",
        description="Cache expensive computations and frequently accessed data.",
        rationale="Reduces latency and computational load.",
        severity="info",
        keywords=["caching", "cache", "memoization", "redis", "in-memory cache"],
        languages=["python", "typescript", "java", "csharp"],
    ),
    PatternTemplate(
        pattern_id_prefix="PERF-LAZY",
        title="Use Lazy Loading",
        category="performance",
        subcategory="loading",
        description="Load resources only when needed, not eagerly.",
        rationale="Reduces initial load time and memory usage.",
        severity="info",
        keywords=["lazy loading", "deferred loading", "on-demand loading"],
        languages=["python", "typescript", "java", "csharp"],
    ),
    PatternTemplate(
        pattern_id_prefix="PERF-POOL",
        title="Use Connection Pooling",
        category="performance",
        subcategory="resource-management",
        description="Reuse database connections via connection pools.",
        rationale="Reduces overhead of creating new connections.",
        severity="warning",
        keywords=["connection pool", "connection pooling", "database pool"],
        languages=["python", "typescript", "java", "csharp"],
    ),
]


class KeywordExtractor(PatternExtractor):
    """Keyword-based pattern extractor.

    Uses predefined templates and keyword frequency analysis to discover
    patterns. Fast and free, but may miss nuanced patterns that require
    deeper semantic understanding.

    Example:
        async with KeywordExtractor() as extractor:
            context = ExtractionContext(...)
            result = await extractor.extract_patterns(context)
    """

    def __init__(self) -> None:
        """Initialize the keyword extractor."""
        self.templates = PATTERN_TEMPLATES

    async def extract_patterns(self, context: ExtractionContext) -> ExtractionResult:
        """Extract patterns using keyword matching.

        Strategy:
        1. Match keywords against templates
        2. Count keyword frequency
        3. Extract code examples
        4. Determine confidence from frequency

        Args:
            context: Extraction context with source text

        Returns:
            ExtractionResult with discovered patterns
        """
        patterns: list[DiscoveredPattern] = []
        text_lower = context.source_text.lower()

        for template in self.templates:
            # Filter by category if specified in focus
            if context.focus.focus_type not in (template.category, "all"):
                continue

            # Count keyword occurrences
            keyword_counts = self._count_keywords(text_lower, template.keywords)
            total_mentions = sum(keyword_counts.values())

            # Skip if no matches
            if total_mentions == 0:
                continue

            # Determine confidence from frequency
            if total_mentions >= 3:
                confidence = "high"
            elif total_mentions >= 2:
                confidence = "medium"
            else:
                confidence = "low"

            # Extract code examples
            examples = self._extract_examples(context.source_text)

            # Create pattern (use template + sequential ID)
            pattern_id = f"{template.pattern_id_prefix}-{len(patterns) + 1:03d}"

            pattern = DiscoveredPattern(
                pattern_id=pattern_id,
                title=template.title,
                category=template.category,
                subcategory=template.subcategory,
                description=template.description,
                rationale=template.rationale,
                confidence=confidence,  # type: ignore
                severity=template.severity,
                languages=template.languages,
                framework=template.framework,
                examples=examples,
                discovered_by="keyword-extractor",
                discovered_at=datetime.now(),
                source_files=[],
                evidence={
                    "keyword_counts": dict(keyword_counts),
                    "total_mentions": total_mentions,
                    "source_url": context.source_url,
                },
                tags=template.keywords[:3],  # Use first 3 keywords as tags
                references=[context.source_url],
            )

            patterns.append(pattern)

        # Overall confidence is average of pattern confidences
        if patterns:
            confidence_map = {"high": 1.0, "medium": 0.66, "low": 0.33}
            avg_confidence = sum(confidence_map[p.confidence] for p in patterns) / len(patterns)
        else:
            avg_confidence = 0.0

        return ExtractionResult(
            patterns=patterns,
            confidence=avg_confidence,
            method="keyword",
            metadata={
                "template_count": len(self.templates),
                "matches_found": len(patterns),
            },
        )

    def _count_keywords(self, text_lower: str, keywords: list[str]) -> Counter[str]:
        """Count occurrences of each keyword in text.

        Args:
            text_lower: Lowercase text to search
            keywords: List of keywords to count

        Returns:
            Counter with keyword frequencies
        """
        counts: Counter[str] = Counter()
        for keyword in keywords:
            # Use word boundaries for accurate matching
            pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
            matches = re.findall(pattern, text_lower)
            if matches:
                counts[keyword] = len(matches)
        return counts

    def _extract_examples(self, text: str) -> PatternExamples:
        """Extract code examples from text.

        Looks for code blocks and classifies them as good/bad based on
        indicators in surrounding text.

        Args:
            text: Source text

        Returns:
            PatternExamples with good/bad examples
        """
        good_examples: list[PatternExample] = []
        bad_examples: list[PatternExample] = []

        # Find code blocks (markdown fenced code blocks)
        # More flexible pattern: ``` with optional language, then content, then closing ```
        code_block_pattern = r"```(\w+)?\s*\n(.*?)```"
        matches = re.finditer(code_block_pattern, text, re.DOTALL)

        for match in matches:
            language = match.group(1) or "text"
            code = match.group(2).strip()

            # Skip empty code blocks
            if not code:
                continue

            # Look for context around code block (up to 200 chars before)
            start_pos = max(0, match.start() - 200)
            context_before = text[start_pos : match.start()].lower()

            # Classify based on indicators
            if any(
                indicator in context_before
                for indicator in ["good", "correct", "right", "✓", "✅", "do this", "recommended"]
            ):
                good_examples.append(
                    PatternExample(
                        language=language,
                        code=code,
                        description="Recommended approach",
                    )
                )
            elif any(
                indicator in context_before
                for indicator in [
                    "bad",
                    "wrong",
                    "incorrect",
                    "✗",
                    "❌",
                    "don't",
                    "avoid",
                    "anti-pattern",
                ]
            ):
                bad_examples.append(
                    PatternExample(
                        language=language,
                        code=code,
                        description="Approach to avoid",
                    )
                )

        return PatternExamples(good=good_examples, bad=bad_examples)

    def estimate_cost(self, context: ExtractionContext) -> float:
        """Estimate extraction cost (always 0 for keyword-based).

        Args:
            context: Extraction context

        Returns:
            0.0 (keyword extraction is free)
        """
        return 0.0
