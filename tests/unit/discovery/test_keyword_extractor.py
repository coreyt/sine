"""Unit tests for keyword-based pattern extraction."""

import pytest

from sine.discovery.agents.base import SearchFocus
from sine.discovery.extractors.base import ExtractionContext
from sine.discovery.extractors.keyword import KeywordExtractor


class TestKeywordExtractor:
    """Tests for KeywordExtractor."""

    @pytest.mark.asyncio
    async def test_basic_extraction(self):
        """Test basic keyword matching and pattern extraction."""
        async with KeywordExtractor() as extractor:
            focus = SearchFocus(
                focus_type="security",
                description="Find security patterns",
            )
            context = ExtractionContext(
                source_url="https://example.com/security",
                source_text="""
                SQL injection is a critical security vulnerability.
                Always use parameterized queries to prevent SQL injection attacks.
                Never concatenate user input directly into SQL queries.
                """,
                focus=focus,
            )

            result = await extractor.extract_patterns(context)

            assert result.method == "keyword"
            assert result.confidence > 0.0
            assert len(result.patterns) >= 1

            # Should find SQL injection pattern
            sql_pattern = next(
                (p for p in result.patterns if "SQL" in p.title), None
            )
            assert sql_pattern is not None
            assert sql_pattern.category == "security"
            assert sql_pattern.subcategory == "injection"
            assert sql_pattern.confidence in ["low", "medium", "high"]

    @pytest.mark.asyncio
    async def test_confidence_from_frequency(self):
        """Test that confidence is determined by keyword frequency."""
        async with KeywordExtractor() as extractor:
            focus = SearchFocus(
                focus_type="security",
                description="Test",
            )

            # Low confidence (1 mention)
            context_low = ExtractionContext(
                source_url="https://example.com",
                source_text="Use parameterized queries for database access.",
                focus=focus,
            )
            result_low = await extractor.extract_patterns(context_low)
            if result_low.patterns:
                assert result_low.patterns[0].confidence == "low"

            # Medium confidence (2 mentions)
            context_med = ExtractionContext(
                source_url="https://example.com",
                source_text="""
                SQL injection is dangerous. Use parameterized queries
                to prevent SQL injection.
                """,
                focus=focus,
            )
            result_med = await extractor.extract_patterns(context_med)
            if result_med.patterns:
                assert result_med.patterns[0].confidence == "medium"

            # High confidence (3+ mentions)
            context_high = ExtractionContext(
                source_url="https://example.com",
                source_text="""
                SQL injection is a critical vulnerability. Always use
                parameterized queries to prevent SQL injection. Never
                concatenate strings. SQL injection can expose data.
                """,
                focus=focus,
            )
            result_high = await extractor.extract_patterns(context_high)
            if result_high.patterns:
                assert result_high.patterns[0].confidence == "high"

    @pytest.mark.asyncio
    async def test_code_example_extraction_good(self):
        """Test extraction of good code examples."""
        async with KeywordExtractor() as extractor:
            focus = SearchFocus(
                focus_type="security",
                description="Test",
            )
            context = ExtractionContext(
                source_url="https://example.com",
                source_text="""
                Use parameterized queries for SQL injection prevention.

                Good approach:
                ```python
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                ```
                """,
                focus=focus,
            )

            result = await extractor.extract_patterns(context)

            if result.patterns:
                pattern = result.patterns[0]
                assert len(pattern.examples.good) >= 1
                assert pattern.examples.good[0].language == "python"
                assert "SELECT" in pattern.examples.good[0].code

    @pytest.mark.asyncio
    async def test_code_example_extraction_bad(self):
        """Test extraction of bad code examples."""
        async with KeywordExtractor() as extractor:
            focus = SearchFocus(
                focus_type="security",
                description="Test",
            )
            context = ExtractionContext(
                source_url="https://example.com",
                source_text="""
                Never concatenate user input into SQL queries.

                Bad approach (SQL injection vulnerable):
                ```python
                query = "SELECT * FROM users WHERE id = " + user_id
                cursor.execute(query)
                ```
                """,
                focus=focus,
            )

            result = await extractor.extract_patterns(context)

            if result.patterns:
                pattern = result.patterns[0]
                assert len(pattern.examples.bad) >= 1
                assert pattern.examples.bad[0].language == "python"
                assert "SELECT" in pattern.examples.bad[0].code

    @pytest.mark.asyncio
    async def test_focus_type_filtering(self):
        """Test that patterns are filtered by focus type."""
        async with KeywordExtractor() as extractor:
            # Security focus should only find security patterns
            focus_security = SearchFocus(
                focus_type="security",
                description="Test",
            )
            context = ExtractionContext(
                source_url="https://example.com",
                source_text="""
                Prevent SQL injection with parameterized queries.
                Use dependency injection for better testability.
                Implement proper authentication mechanisms.
                Cache frequently accessed data for performance.
                """,
                focus=focus_security,
            )

            result = await extractor.extract_patterns(context)

            # Should only find security patterns
            for pattern in result.patterns:
                assert pattern.category == "security"

            # Architecture focus should only find architecture patterns
            focus_arch = SearchFocus(
                focus_type="architecture",
                description="Test",
            )
            context_arch = ExtractionContext(
                source_url="https://example.com",
                source_text=context.source_text,
                focus=focus_arch,
            )

            result_arch = await extractor.extract_patterns(context_arch)

            # Should only find architecture patterns
            for pattern in result_arch.patterns:
                assert pattern.category == "architecture"

    @pytest.mark.asyncio
    async def test_no_matches(self):
        """Test extraction when no patterns match."""
        async with KeywordExtractor() as extractor:
            focus = SearchFocus(
                focus_type="security",
                description="Test",
            )
            context = ExtractionContext(
                source_url="https://example.com",
                source_text="This text has no security-related keywords at all.",
                focus=focus,
            )

            result = await extractor.extract_patterns(context)

            assert result.patterns == []
            assert result.confidence == 0.0
            assert result.method == "keyword"

    @pytest.mark.asyncio
    async def test_cost_estimation(self):
        """Test that keyword extraction has zero cost."""
        async with KeywordExtractor() as extractor:
            focus = SearchFocus(
                focus_type="security",
                description="Test",
            )
            context = ExtractionContext(
                source_url="https://example.com",
                source_text="Any text content",
                focus=focus,
            )

            cost = extractor.estimate_cost(context)
            assert cost == 0.0

    @pytest.mark.asyncio
    async def test_pattern_metadata(self):
        """Test that patterns have proper metadata."""
        async with KeywordExtractor() as extractor:
            focus = SearchFocus(
                focus_type="security",
                description="Test",
            )
            context = ExtractionContext(
                source_url="https://example.com/security-guide",
                source_text="""
                SQL injection prevention requires parameterized queries.
                Always validate and sanitize user input.
                Use prepared statements to prevent SQL injection.
                """,
                focus=focus,
            )

            result = await extractor.extract_patterns(context)

            assert len(result.patterns) >= 1
            pattern = result.patterns[0]

            # Check required fields
            assert pattern.pattern_id.startswith("SEC-")
            assert pattern.discovered_by == "keyword-extractor"
            assert pattern.discovered_at is not None
            assert "keyword_counts" in pattern.evidence
            assert "total_mentions" in pattern.evidence
            assert pattern.evidence["source_url"] == "https://example.com/security-guide"
            assert len(pattern.references) == 1
            assert pattern.references[0] == "https://example.com/security-guide"

    @pytest.mark.asyncio
    async def test_multiple_pattern_discovery(self):
        """Test discovering multiple patterns from rich text."""
        async with KeywordExtractor() as extractor:
            focus = SearchFocus(
                focus_type="security",
                description="Test",
            )
            context = ExtractionContext(
                source_url="https://example.com",
                source_text="""
                # Security Best Practices

                ## SQL Injection
                Use parameterized queries and prepared statements to prevent
                SQL injection attacks. Never concatenate user input.

                ## XSS Prevention
                Sanitize user input and escape HTML to prevent cross-site
                scripting (XSS) attacks. Use Content Security Policy.

                ## Authentication
                Implement strong authentication using OAuth or JWT tokens.
                Never store passwords in plain text. Use bcrypt for hashing.
                """,
                focus=focus,
            )

            result = await extractor.extract_patterns(context)

            # Should find multiple security patterns
            assert len(result.patterns) >= 2

            pattern_titles = {p.title for p in result.patterns}
            # Should have SQL injection and possibly XSS/auth patterns
            assert any("SQL" in title for title in pattern_titles)

    @pytest.mark.asyncio
    async def test_result_metadata(self):
        """Test that result metadata is populated correctly."""
        async with KeywordExtractor() as extractor:
            focus = SearchFocus(
                focus_type="architecture",
                description="Test",
            )
            context = ExtractionContext(
                source_url="https://example.com",
                source_text="""
                Use dependency injection for better testability.
                The factory pattern helps with object creation.
                Repository pattern abstracts data access.
                """,
                focus=focus,
            )

            result = await extractor.extract_patterns(context)

            assert "template_count" in result.metadata
            assert "matches_found" in result.metadata
            assert result.metadata["template_count"] > 0
            assert result.metadata["matches_found"] == len(result.patterns)

    @pytest.mark.asyncio
    async def test_pattern_id_uniqueness(self):
        """Test that pattern IDs are unique within a result."""
        async with KeywordExtractor() as extractor:
            focus = SearchFocus(
                focus_type="security",
                description="Test",
            )
            context = ExtractionContext(
                source_url="https://example.com",
                source_text="""
                SQL injection, XSS, CSRF, and authentication are all critical.
                Use parameterized queries, sanitize input, use CSRF tokens,
                and implement OAuth for security.
                """,
                focus=focus,
            )

            result = await extractor.extract_patterns(context)

            if len(result.patterns) > 1:
                pattern_ids = [p.pattern_id for p in result.patterns]
                assert len(pattern_ids) == len(set(pattern_ids)), "Pattern IDs should be unique"
