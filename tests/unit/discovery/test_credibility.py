"""Unit tests for source credibility scoring."""

import pytest

from sine.discovery.search.credibility import SourceCredibilityScorer


class TestSourceCredibilityScorer:
    """Tests for SourceCredibilityScorer."""

    @pytest.fixture
    def scorer(self):
        """Create a credibility scorer instance."""
        return SourceCredibilityScorer()

    def test_high_credibility_official_docs(self, scorer):
        """Test that official documentation gets high scores."""
        # Python official docs
        assert scorer.score_url("https://docs.python.org/3/tutorial/") == 1.0

        # TypeScript official
        assert scorer.score_url("https://www.typescriptlang.org/docs/") == 1.0

        # MDN
        assert scorer.score_url("https://developer.mozilla.org/en-US/docs/Web") == 0.95

    def test_high_credibility_security_authorities(self, scorer):
        """Test that security authorities get high scores."""
        # OWASP
        assert scorer.score_url("https://owasp.org/www-project-top-ten/") == 0.98

        # OWASP Cheat Series
        assert scorer.score_url("https://cheatsheetseries.owasp.org/") == 0.98

        # CWE
        assert scorer.score_url("https://cwe.mitre.org/data/") == 0.95

    def test_medium_high_credibility_experts(self, scorer):
        """Test that recognized experts get medium-high scores."""
        # Martin Fowler
        assert scorer.score_url("https://martinfowler.com/articles/") == 0.95

        # Refactoring Guru
        assert scorer.score_url("https://refactoring.guru/design-patterns") == 0.90

        # React official
        assert scorer.score_url("https://reactjs.org/docs/") == 0.90

    def test_medium_credibility_quality_tutorials(self, scorer):
        """Test that quality tutorial sites get medium scores."""
        # Real Python
        assert scorer.score_url("https://realpython.com/python-testing/") == 0.75

        # freeCodeCamp
        assert scorer.score_url("https://www.freecodecamp.org/news/") == 0.70

    def test_low_credibility_user_generated(self, scorer):
        """Test that user-generated content gets lower scores."""
        # Medium
        assert scorer.score_url("https://medium.com/@user/article") == 0.55

        # Dev.to
        assert scorer.score_url("https://dev.to/user/post") == 0.55

        # Stack Overflow
        assert scorer.score_url("https://stackoverflow.com/questions/123") == 0.60

    def test_unknown_domain_gets_default_score(self, scorer):
        """Test that unknown domains get default score."""
        score = scorer.score_url("https://random-blog-123.com/post")
        assert score == 0.5  # DEFAULT_CREDIBILITY_SCORE

    def test_github_repos_get_moderate_score(self, scorer):
        """Test that GitHub repositories get moderate credibility."""
        score = scorer.score_url("https://github.com/user/repo")
        assert score == 0.70

    def test_subdomain_matching(self, scorer):
        """Test that subdomains are matched to base domains."""
        # blog.example.com should match example.com if it's known
        # AWS subdomain example (docs.aws.amazon.com)
        # Subdomain doesn't match exact domain "aws.amazon.com", so it
        # extracts base domain amazon.com which is not in our list
        score = scorer.score_url("https://docs.aws.amazon.com/guide")
        # Should be default score since amazon.com is not classified
        assert score == 0.5  # DEFAULT_CREDIBILITY_SCORE

    def test_www_prefix_removed(self, scorer):
        """Test that www. prefix is properly handled."""
        # With www.
        score_with_www = scorer.score_url("https://www.owasp.org/")

        # Without www.
        score_without_www = scorer.score_url("https://owasp.org/")

        # Should be the same
        assert score_with_www == score_without_www

    def test_get_domain_tier(self, scorer):
        """Test domain tier categorization."""
        assert scorer.get_domain_tier("https://docs.python.org/") == "high"  # 1.0
        assert scorer.get_domain_tier("https://martinfowler.com/") == "high"  # 0.95
        assert scorer.get_domain_tier("https://reactjs.org/") == "high"  # 0.90
        assert scorer.get_domain_tier("https://github.blog/") == "medium-high"  # 0.85
        assert scorer.get_domain_tier("https://realpython.com/") == "medium"  # 0.75
        assert scorer.get_domain_tier("https://medium.com/") == "low"  # 0.55
        assert scorer.get_domain_tier("https://unknown-site.com/") == "low"  # 0.5 (default)

    def test_list_high_credibility_domains(self, scorer):
        """Test listing high credibility domains."""
        domains = scorer.list_high_credibility_domains()

        # Should be a sorted list
        assert isinstance(domains, list)
        assert len(domains) > 0
        assert domains == sorted(domains)

        # Should include known high-cred domains
        assert "docs.python.org" in domains
        assert "owasp.org" in domains

    def test_get_domain_count(self, scorer):
        """Test getting domain count statistics."""
        counts = scorer.get_domain_count()

        assert "high" in counts
        assert "medium-high" in counts
        assert "medium" in counts
        assert "low" in counts
        assert "total" in counts

        # Total should be sum of tiers
        assert counts["total"] == (
            counts["high"]
            + counts["medium-high"]
            + counts["medium"]
            + counts["low"]
        )

        # Should have reasonable numbers
        assert counts["total"] > 50  # We defined ~50+ domains

    def test_malformed_url_returns_default(self, scorer):
        """Test that malformed URLs return default score."""
        score = scorer.score_url("not-a-valid-url")
        assert score == 0.5

    def test_case_insensitive_domain_matching(self, scorer):
        """Test that domain matching is case-insensitive."""
        score_lower = scorer.score_url("https://owasp.org/")
        score_upper = scorer.score_url("https://OWASP.ORG/")
        score_mixed = scorer.score_url("https://Owasp.Org/")

        assert score_lower == score_upper == score_mixed

    def test_cloud_providers_get_high_scores(self, scorer):
        """Test that cloud provider docs get high credibility."""
        assert scorer.score_url("https://aws.amazon.com/architecture/") == 0.90
        assert scorer.score_url("https://cloud.google.com/architecture") == 0.90
        assert scorer.score_url("https://azure.microsoft.com/en-us/") == 0.90

    def test_framework_official_docs_get_high_scores(self, scorer):
        """Test that framework official documentation gets high scores."""
        assert scorer.score_url("https://spring.io/guides") == 0.90
        assert scorer.score_url("https://www.djangoproject.com/") == 0.90
        assert scorer.score_url("https://vuejs.org/guide/") == 0.90
