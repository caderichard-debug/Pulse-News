"""
Credibility Rater Service

Rates the credibility of sources based on domain reputation and organization type.
Caches ratings in the database for performance.
"""

import logging
from typing import Optional
from urllib.parse import urlparse
from datetime import datetime, timedelta
from sqlmodel import Session, select

from ..models import SourceCredibilityRating

logger = logging.getLogger(__name__)

# Credibility tiers
CREDIBILITY_TIERS = {
    "very_high": (0.8, 1.0),    # Government, academic, peer-reviewed
    "high": (0.6, 0.8),          # Established news, research institutions
    "medium": (0.4, 0.6),        # Trade publications, specialized press
    "low": (0.2, 0.4),           # Blogs, opinion sites
    "very_low": (0.0, 0.2)       # Unverified, personal sites
}

# Known high-credibility domains
HIGH_CREDIBILITY_DOMAINS = {
    # Government (.gov)
    "cdc.gov": 0.95,
    "fda.gov": 0.95,
    "nih.gov": 0.95,
    "nasa.gov": 0.95,
    "census.gov": 0.95,

    # Academic institutions
    "harvard.edu": 0.9,
    "stanford.edu": 0.9,
    "mit.edu": 0.9,
    "princeton.edu": 0.9,
    "yale.edu": 0.9,
    "oxford.ac.uk": 0.9,
    "cambridge.ac.uk": 0.9,

    # Research institutions
    "who.int": 0.9,
    "nature.com": 0.85,
    "science.org": 0.85,
    "thelancet.com": 0.85,
    "nejm.org": 0.85,

    # Established news organizations
    "apnews.com": 0.8,
    "reuters.com": 0.8,
    "bbc.com": 0.8,
    "npr.org": 0.75,
    "pbs.org": 0.75,
    "economist.com": 0.75,
}

# Organization type keywords
ACADEMIC_KEYWORDS = ["university", "college", "institute", "laboratory", "research"]
GOVERNMENT_KEYWORDS = ["department of", "ministry of", "bureau", "agency", "administration"]
THINK_TANK_KEYWORDS = ["foundation", "institute", "center for", "council", "institute for"]


class CredibilityRater:
    """Service for rating source credibility."""

    def __init__(self):
        pass

    def rate_source_credibility(
        self,
        source_url: str,
        source_name: str,
        session: Session
    ) -> float:
        """
        Rate source credibility (0.0 to 1.0).

        Uses:
        1. Cached ratings from database
        2. Known domain list
        3. Domain TLD heuristics (.gov, .edu, etc.)
        4. Organization name analysis

        Args:
            source_url: URL of the source
            source_name: Name of the source organization
            session: Database session

        Returns:
            Credibility score (0.0 to 1.0)
        """
        try:
            domain = self._extract_domain(source_url)

            # Check cache first
            cached = session.exec(
                select(SourceCredibilityRating)
                .where(SourceCredibilityRating.domain == domain)
            ).first()

            if cached and self._is_cache_fresh(cached):
                logger.debug(f"Using cached credibility for {domain}: {cached.credibility_score}")
                return cached.credibility_score

            # Calculate new score
            score = self._calculate_credibility_score(source_url, source_name, domain)

            # Determine organization type
            org_type = self._determine_organization_type(source_url, source_name, domain)

            # Cache it
            self._cache_credibility_rating(
                domain=domain,
                score=score,
                org_type=org_type,
                session=session
            )

            logger.info(f"Rated {domain} credibility: {score:.2f}")
            return score

        except Exception as e:
            logger.error(f"Error rating credibility for {source_url}: {e}")
            return 0.5  # Default to medium credibility on error

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]

            return domain
        except Exception:
            return url.lower()

    def _is_cache_fresh(self, cached: SourceCredibilityRating, max_age_days: int = 90) -> bool:
        """Check if cached rating is still fresh."""
        age = datetime.utcnow() - cached.last_updated
        return age < timedelta(days=max_age_days)

    def _calculate_credibility_score(self, source_url: str, source_name: str, domain: str) -> float:
        """
        Calculate credibility score using heuristics.

        Scoring rubric:
        - Base score: 0.5
        - Known high-credibility domain: use predefined score
        - Domain TLD: +0.3 for .gov, +0.3 for .edu, +0.2 for .org (if academic)
        - Organization type: +0.2 for university/institute, +0.2 for government
        - Unknown domains: -0.1

        Max: 1.0, Min: 0.0
        """
        # Check if it's a known high-credibility domain
        if domain in HIGH_CREDIBILITY_DOMAINS:
            return HIGH_CREDIBILITY_DOMAINS[domain]

        # Start with base score
        score = 0.5

        # Domain TLD analysis
        tld = domain.split(".")[-1] if "." in domain else ""

        if tld == "gov":
            score += 0.3
        elif tld == "edu":
            score += 0.3
        elif tld == "org":
            # .org gets bonus if it's academic/research
            if self._is_academic(source_name, domain):
                score += 0.2
            else:
                score += 0.1
        elif tld in ["ac", "edu.au", "edu.uk"]:  # International academic
            score += 0.3
        elif tld == "int":  # International organizations
            score += 0.2
        elif tld == "com":
            # Established .com news/research gets smaller bonus
            if any(keyword in domain for keyword in ["research", "journal", "news"]):
                score += 0.05
        else:
            # Unknown TLD
            score -= 0.05

        # Organization type analysis
        source_name_lower = source_name.lower() if source_name else ""

        if self._is_academic(source_name, domain):
            score += 0.2

        if self._is_government(source_name, domain):
            score += 0.2

        if self._is_think_tank(source_name, domain):
            score += 0.1

        # Penalty for very short domains (often spam/personal sites)
        if len(domain.replace(".", "")) < 5:
            score -= 0.1

        # Ensure score is within bounds
        return max(0.0, min(1.0, score))

    def _determine_organization_type(self, source_url: str, source_name: str, domain: str) -> dict:
        """Determine organization type flags."""
        return {
            "is_academic": self._is_academic(source_name, domain),
            "is_government": self._is_government(source_name, domain),
            "is_think_tank": self._is_think_tank(source_name, domain),
            "is_news_organization": self._is_news_organization(source_name, domain)
        }

    def _is_academic(self, source_name: str, domain: str) -> bool:
        """Check if source is academic."""
        if not source_name:
            return False

        name_lower = source_name.lower()
        tld = domain.split(".")[-1] if "." in domain else ""

        # Check TLD
        if tld in ["edu", "ac"] or ".edu." in domain or ".ac." in domain:
            return True

        # Check keywords
        return any(keyword in name_lower for keyword in ACADEMIC_KEYWORDS)

    def _is_government(self, source_name: str, domain: str) -> bool:
        """Check if source is government."""
        tld = domain.split(".")[-1] if "." in domain else ""

        # Check TLD
        if tld == "gov" or ".gov." in domain:
            return True

        # Check keywords
        if source_name:
            name_lower = source_name.lower()
            return any(keyword in name_lower for keyword in GOVERNMENT_KEYWORDS)

        return False

    def _is_think_tank(self, source_name: str, domain: str) -> bool:
        """Check if source is a think tank/research institution."""
        if not source_name:
            return False

        name_lower = source_name.lower()
        return any(keyword in name_lower for keyword in THINK_TANK_KEYWORDS)

    def _is_news_organization(self, source_name: str, domain: str) -> bool:
        """Check if source is a news organization."""
        news_keywords = ["news", "times", "post", "tribune", "herald", "gazette",
                        "journal", "press", "daily", "bbc", "cnn", "npr", "reuters"]

        if source_name:
            name_lower = source_name.lower()
            if any(keyword in name_lower for keyword in news_keywords):
                return True

        # Check domain
        return any(keyword in domain for keyword in news_keywords)

    def _cache_credibility_rating(
        self,
        domain: str,
        score: float,
        org_type: dict,
        session: Session
    ) -> None:
        """Cache credibility rating in database."""
        try:
            # Check if exists
            existing = session.exec(
                select(SourceCredibilityRating)
                .where(SourceCredibilityRating.domain == domain)
            ).first()

            if existing:
                # Update existing
                existing.credibility_score = score
                existing.is_academic = org_type["is_academic"]
                existing.is_government = org_type["is_government"]
                existing.is_news_organization = org_type["is_news_organization"]
                existing.is_think_tank = org_type["is_think_tank"]
                existing.last_updated = datetime.utcnow()
                existing.rating_method = "heuristic"
            else:
                # Create new
                new_rating = SourceCredibilityRating(
                    domain=domain,
                    credibility_score=score,
                    is_academic=org_type["is_academic"],
                    is_government=org_type["is_government"],
                    is_news_organization=org_type["is_news_organization"],
                    is_think_tank=org_type["is_think_tank"],
                    rating_method="heuristic",
                    last_updated=datetime.utcnow(),
                    created_at=datetime.utcnow()
                )
                session.add(new_rating)

            session.commit()
            logger.debug(f"Cached credibility rating for {domain}")

        except Exception as e:
            logger.error(f"Error caching credibility rating for {domain}: {e}")
            session.rollback()


# Singleton instance
_credibility_rater = None


def get_credibility_rater() -> CredibilityRater:
    """Get singleton instance of CredibilityRater."""
    global _credibility_rater
    if _credibility_rater is None:
        _credibility_rater = CredibilityRater()
    return _credibility_rater
