"""Source credibility scoring for web search results.

This module scores web sources by their trustworthiness and authority
for coding best practices and pattern discovery.

Scoring tiers:
- High (0.9-1.0): Official documentation, standards bodies
- Medium-High (0.8-0.9): Recognized authorities and experts
- Medium (0.6-0.8): Quality tutorials and reputable blogs
- Low (0.4-0.6): User-generated content and forums
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

# High credibility domains (0.9-1.0)
HIGH_CREDIBILITY_DOMAINS = {
    # Official language documentation
    "docs.python.org": 1.0,
    "peps.python.org": 1.0,
    "typescriptlang.org": 1.0,
    "developer.mozilla.org": 0.95,  # MDN
    "docs.oracle.com": 0.95,  # Java docs
    "learn.microsoft.com": 0.95,  # Microsoft docs
    "go.dev": 0.95,  # Go documentation
    "doc.rust-lang.org": 0.95,  # Rust documentation
    # Security authorities
    "owasp.org": 0.98,
    "cheatsheetseries.owasp.org": 0.98,
    "cwe.mitre.org": 0.95,
    "csrc.nist.gov": 0.95,  # NIST
    "nvd.nist.gov": 0.95,  # National Vulnerability Database
    # Standards and best practices
    "w3.org": 0.95,  # W3C
    "ietf.org": 0.95,  # IETF RFCs
    "iso.org": 0.95,
    # Cloud providers (architectural patterns)
    "aws.amazon.com": 0.90,
    "cloud.google.com": 0.90,
    "azure.microsoft.com": 0.90,
}

# Medium-high credibility domains (0.8-0.9)
MEDIUM_HIGH_CREDIBILITY_DOMAINS = {
    # Recognized experts and authorities
    "martinfowler.com": 0.95,  # Martin Fowler
    "refactoring.guru": 0.90,  # Design patterns
    "reactjs.org": 0.90,  # React official
    "vuejs.org": 0.90,  # Vue official
    "angular.io": 0.90,  # Angular official
    "spring.io": 0.90,  # Spring framework
    "djangoproject.com": 0.90,  # Django
    "fastapi.tiangolo.com": 0.85,  # FastAPI
    "nodejs.org": 0.90,  # Node.js official
    # Reputable technology blogs
    "github.blog": 0.85,
    "stackoverflow.blog": 0.85,
    "engineering.fb.com": 0.85,  # Meta engineering
    "netflixtechblog.com": 0.85,
    "eng.uber.com": 0.85,
}

# Medium credibility domains (0.6-0.8)
MEDIUM_CREDIBILITY_DOMAINS = {
    # Quality tutorials and educational sites
    "realpython.com": 0.75,
    "freecodecamp.org": 0.70,
    "codecademy.com": 0.70,
    "pluralsight.com": 0.70,
    "udemy.com": 0.65,
    "coursera.org": 0.70,
    # Tech news and reputable blogs
    "smashingmagazine.com": 0.75,
    "css-tricks.com": 0.75,
    "sitepoint.com": 0.70,
    # Company engineering blogs
    "airbnb.io": 0.75,
    "stripe.com": 0.75,
    "shopify.engineering": 0.75,
}

# Low credibility domains (0.4-0.6)
# User-generated content - not inherently bad, but needs more scrutiny
LOW_CREDIBILITY_DOMAINS = {
    "medium.com": 0.55,  # Varies widely by author
    "dev.to": 0.55,
    "hashnode.com": 0.55,
    "reddit.com": 0.50,
    "quora.com": 0.50,
    "stackoverflow.com": 0.60,  # Good for specific questions, not patterns
}

# Default score for unknown domains
DEFAULT_CREDIBILITY_SCORE = 0.5


class SourceCredibilityScorer:
    """Scores web sources by credibility for coding best practices.

    Uses a tiered domain classification system to assign credibility scores.
    Scores range from 0.0 (untrustworthy) to 1.0 (authoritative).

    Example:
        scorer = SourceCredibilityScorer()
        score = scorer.score_url("https://docs.python.org/3/tutorial/")
        print(f"Credibility: {score}")  # 1.0
    """

    def __init__(self):
        """Initialize the credibility scorer."""
        # Combine all domain mappings
        self.domain_scores = {
            **HIGH_CREDIBILITY_DOMAINS,
            **MEDIUM_HIGH_CREDIBILITY_DOMAINS,
            **MEDIUM_CREDIBILITY_DOMAINS,
            **LOW_CREDIBILITY_DOMAINS,
        }

    def score_url(self, url: str) -> float:
        """Score a URL's credibility.

        Args:
            url: URL to score

        Returns:
            Credibility score (0.0 - 1.0)
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix
            domain = re.sub(r"^www\.", "", domain)

            # Check exact domain match
            if domain in self.domain_scores:
                return self.domain_scores[domain]

            # Check subdomain matches (e.g., blog.example.com → example.com)
            base_domain = self._extract_base_domain(domain)
            if base_domain in self.domain_scores:
                # Slightly reduce score for subdomains
                return self.domain_scores[base_domain] * 0.95

            # Check for known patterns
            if self._is_github_repo(domain, parsed.path):
                return 0.70  # GitHub repositories (community code)

            if self._is_official_blog(domain):
                return 0.75  # Company blogs

            # Default score for unknown domains
            return DEFAULT_CREDIBILITY_SCORE

        except Exception:
            # If URL parsing fails, return default
            return DEFAULT_CREDIBILITY_SCORE

    def _extract_base_domain(self, domain: str) -> str:
        """Extract base domain from subdomain.

        Args:
            domain: Full domain (e.g., blog.example.com)

        Returns:
            Base domain (e.g., example.com)
        """
        parts = domain.split(".")
        if len(parts) >= 2:
            # Return last two parts (example.com)
            return ".".join(parts[-2:])
        return domain

    def _is_github_repo(self, domain: str, path: str) -> bool:
        """Check if URL is a GitHub repository.

        Args:
            domain: Domain name
            path: URL path

        Returns:
            True if GitHub repository
        """
        if domain == "github.com":
            # GitHub repos have format: /owner/repo
            path_parts = [p for p in path.split("/") if p]
            return len(path_parts) >= 2
        return False

    def _is_official_blog(self, domain: str) -> bool:
        """Check if domain appears to be an official company blog.

        Args:
            domain: Domain name

        Returns:
            True if likely an official blog
        """
        # Common engineering blog patterns
        blog_patterns = [
            r"engineering\.",
            r"tech\.",
            r"blog\.",
            r"developers\.",
        ]

        # You could expand this with a list of tech companies
        return any(re.search(pattern, domain) for pattern in blog_patterns)

    def get_domain_tier(self, url: str) -> str:
        """Get the credibility tier for a URL.

        Args:
            url: URL to categorize

        Returns:
            Tier name: "high", "medium-high", "medium", "low", or "unknown"
        """
        score = self.score_url(url)

        if score >= 0.9:
            return "high"
        elif score >= 0.8:
            return "medium-high"
        elif score >= 0.6:
            return "medium"
        elif score >= 0.4:
            return "low"
        else:
            return "unknown"

    def list_high_credibility_domains(self) -> list[str]:
        """Get list of high credibility domains.

        Returns:
            List of high credibility domain names
        """
        return sorted(HIGH_CREDIBILITY_DOMAINS.keys())

    def get_domain_count(self) -> dict[str, int]:
        """Get count of domains in each tier.

        Returns:
            Dictionary with tier counts
        """
        return {
            "high": len(HIGH_CREDIBILITY_DOMAINS),
            "medium-high": len(MEDIUM_HIGH_CREDIBILITY_DOMAINS),
            "medium": len(MEDIUM_CREDIBILITY_DOMAINS),
            "low": len(LOW_CREDIBILITY_DOMAINS),
            "total": len(self.domain_scores),
        }
