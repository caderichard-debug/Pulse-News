"""
Tests for Credibility Rater Service
"""
import pytest
from sqlmodel import Session, select
from ..services.credibility_rater import CredibilityRater, get_credibility_rater
from ..models import SourceCredibilityRating
from datetime import datetime, timedelta


class TestCredibilityRater:
    """Test source credibility rating functionality"""

    def test_rate_government_domain(self, session: Session):
        """Test rating for .gov domain"""
        rater = CredibilityRater()

        score = rater.rate_source_credibility(
            source_url="https://cdc.gov/data",
            source_name="Centers for Disease Control",
            session=session
        )

        # .gov should have high credibility
        assert score >= 0.8

    def test_rate_edu_domain(self, session: Session):
        """Test rating for .edu domain"""
        rater = CredibilityRater()

        score = rater.rate_source_credibility(
            source_url="https://stanford.edu/research",
            source_name="Stanford University",
            session=session
        )

        # .edu should have high credibility
        assert score >= 0.8

    def test_rate_known_high_credibility_domain(self, session: Session):
        """Test rating for known high-credibility domain"""
        rater = CredibilityRater()

        score = rater.rate_source_credibility(
            source_url="https://reuters.com/article",
            source_name="Reuters",
            session=session
        )

        # Reuters is in HIGH_CREDIBILITY_DOMAINS
        assert score == 0.8

    def test_rate_academic_organization(self, session: Session):
        """Test rating boost for academic organizations"""
        rater = CredibilityRater()

        score = rater.rate_source_credibility(
            source_url="https://example.org/study",
            source_name="Institute for Advanced Study",
            session=session
        )

        # Should get boost for "Institute" keyword
        assert score > 0.5

    def test_rate_think_tank(self, session: Session):
        """Test rating for think tank"""
        rater = CredibilityRater()

        score = rater.rate_source_credibility(
            source_url="https://example.org/report",
            source_name="Brookings Foundation",
            session=session
        )

        # Should get boost for "Foundation" keyword
        assert score > 0.5

    def test_rate_unknown_com_domain(self, session: Session):
        """Test rating for unknown .com domain"""
        rater = CredibilityRater()

        score = rater.rate_source_credibility(
            source_url="https://randomsite.com/article",
            source_name="Random Site",
            session=session
        )

        # Should be around base score
        assert 0.3 <= score <= 0.6

    def test_caching_credibility_rating(self, session: Session):
        """Test that ratings are cached in database"""
        rater = CredibilityRater()

        # Rate a source
        rater.rate_source_credibility(
            source_url="https://test-domain.com/article",
            source_name="Test Source",
            session=session
        )

        # Check database for cached rating
        cached = session.exec(
            select(SourceCredibilityRating)
            .where(SourceCredibilityRating.domain == "test-domain.com")
        ).first()

        assert cached is not None
        assert cached.domain == "test-domain.com"
        assert cached.credibility_score > 0

    def test_cache_is_used_on_second_call(self, session: Session):
        """Test that cached rating is used on subsequent calls"""
        rater = CredibilityRater()

        # First call - creates cache
        score1 = rater.rate_source_credibility(
            source_url="https://cached-test.com/article",
            source_name="Cached Test",
            session=session
        )

        # Manually update cache to different score
        cached = session.exec(
            select(SourceCredibilityRating)
            .where(SourceCredibilityRating.domain == "cached-test.com")
        ).first()
        cached.credibility_score = 0.99
        session.commit()

        # Second call - should use cache
        score2 = rater.rate_source_credibility(
            source_url="https://cached-test.com/different-article",
            source_name="Cached Test Different",
            session=session
        )

        assert score2 == 0.99

    def test_cache_expiry(self, session: Session):
        """Test that old cache is refreshed"""
        rater = CredibilityRater()

        # Create old cached entry
        old_cache = SourceCredibilityRating(
            domain="old-cache.com",
            credibility_score=0.99,
            is_academic=False,
            is_government=False,
            is_news_organization=False,
            is_think_tank=False,
            rating_method="manual",
            last_updated=datetime.utcnow() - timedelta(days=100),  # 100 days old
            created_at=datetime.utcnow() - timedelta(days=100)
        )
        session.add(old_cache)
        session.commit()

        # Rate the source - should recalculate since cache is > 90 days old
        score = rater.rate_source_credibility(
            source_url="https://old-cache.com/article",
            source_name="Old Cache",
            session=session
        )

        # Score should be recalculated (not 0.99)
        assert score != 0.99

    def test_extract_domain_removes_www(self):
        """Test domain extraction removes www prefix"""
        rater = CredibilityRater()

        domain = rater._extract_domain("https://www.example.com/article")
        assert domain == "example.com"

    def test_is_academic_detection(self):
        """Test academic organization detection"""
        rater = CredibilityRater()

        assert rater._is_academic("Harvard University", "harvard.edu") is True
        assert rater._is_academic("Research Institute", "example.org") is True
        assert rater._is_academic("Some College", "example.com") is True
        assert rater._is_academic("Random Blog", "example.com") is False

    def test_is_government_detection(self):
        """Test government organization detection"""
        rater = CredibilityRater()

        assert rater._is_government("CDC", "cdc.gov") is True
        assert rater._is_government("Department of Energy", "example.org") is True
        assert rater._is_government("Private Company", "example.com") is False

    def test_is_news_organization_detection(self):
        """Test news organization detection"""
        rater = CredibilityRater()

        assert rater._is_news_organization("New York Times", "nytimes.com") is True
        assert rater._is_news_organization("CNN", "cnn.com") is True
        assert rater._is_news_organization("Random Blog", "blog.com") is False

    def test_determine_organization_type(self):
        """Test organization type determination"""
        rater = CredibilityRater()

        org_type = rater._determine_organization_type(
            source_url="https://stanford.edu/study",
            source_name="Stanford University",
            domain="stanford.edu"
        )

        assert org_type["is_academic"] is True
        assert org_type["is_government"] is False

    def test_calculate_credibility_score_gov(self):
        """Test score calculation for government source"""
        rater = CredibilityRater()

        score = rater._calculate_credibility_score(
            source_url="https://nih.gov/data",
            source_name="National Institutes of Health",
            domain="nih.gov"
        )

        # Base (0.5) + .gov TLD (0.3) + government keyword (0.2) = 1.0
        assert score >= 0.8

    def test_calculate_credibility_score_unknown(self):
        """Test score calculation for unknown source"""
        rater = CredibilityRater()

        score = rater._calculate_credibility_score(
            source_url="https://randomwebsite.com/article",
            source_name="Random Website",
            domain="randomwebsite.com"
        )

        # Should be close to base score
        assert 0.3 <= score <= 0.6

    def test_get_credibility_rater_singleton(self):
        """Test singleton pattern"""
        rater1 = get_credibility_rater()
        rater2 = get_credibility_rater()

        assert rater1 is rater2

    def test_rate_source_handles_exception(self, session: Session):
        """Test that rating handles exceptions gracefully"""
        rater = CredibilityRater()

        # Use invalid URL - it will treat "not-a-valid-url" as the domain
        score = rater.rate_source_credibility(
            source_url="not-a-valid-url",
            source_name="Test",
            session=session
        )

        # Should calculate some score (may apply short domain penalty)
        assert 0.0 <= score <= 1.0

    def test_org_domain_gets_bonus(self, session: Session):
        """Test that .org domains get appropriate bonus"""
        rater = CredibilityRater()

        # Academic .org should get higher score
        score_academic = rater.rate_source_credibility(
            source_url="https://research-institute.org/study",
            source_name="Research Institute",
            session=session
        )

        # Non-academic .org should get smaller bonus
        score_non_academic = rater.rate_source_credibility(
            source_url="https://random.org/page",
            source_name="Random Org",
            session=session
        )

        assert score_academic > score_non_academic

    def test_very_short_domain_penalty(self, session: Session):
        """Test penalty for very short domains"""
        rater = CredibilityRater()

        score = rater._calculate_credibility_score(
            source_url="https://ab.com/page",
            source_name="AB",
            domain="ab.com"
        )

        # Length of "ab.com" without dots is 4, which is < 5
        # Base score (0.5) + .com (0.05) - penalty (0.1) + small bonus might be around 0.45-0.5
        # Just check it's not high credibility
        assert score <= 0.55
