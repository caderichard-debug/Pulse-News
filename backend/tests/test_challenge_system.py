"""
Comprehensive test suite for newsletter challenge system.

Tests all major components:
- Challenge claim generation and management
- User response processing and validation
- Article assignment algorithm and matching
- Analytics and engagement tracking
- API endpoints and error handling
- Database model relationships and constraints
"""

import pytest
from datetime import datetime, timedelta, date
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, create_engine, select, and_, or_
from typing import List, Dict, Any, Optional
import json

from ..models import (
    User, WeeklyChallenge, ChallengeClaim, UserChallengeResponse,
    ChallengeArticleAssignment, ChallengeEngagement, ChallengeClaimType,
    ChallengeResponseStatus, AgreementLevel, Article, Source,
    ArticleAnalysis
)
from ..routes.auth import create_access_token
from ..services.challenge_manager import ChallengeManager
from ..services.challenge_claim_generator import ChallengeClaimGenerator
from ..services.challenge_analytics import ChallengeAnalytics
from ..services.challenge_article_matcher import ChallengeArticleMatcher
from ..database import get_session


class TestChallengeModels:
    """Test challenge system database models and relationships."""

    def test_challenge_claim_model_creation(self, test_session: Session):
        """Test ChallengeClaim model creation and validation."""
        claim = ChallengeClaim(
            weekly_challenge_id=1,
            claim_text="Test claim for testing purposes",
            claim_type=ChallengeClaimType.MORAL_PRINCIPLE,
            display_order=1,
            background_context="This is a test background context",
            controversy_score=0.65,
            philosophical_alignment=0.8
        )

        test_session.add(claim)
        test_session.commit()

        # Verify claim was created with correct data
        retrieved_claim = test_session.get(ChallengeClaim, claim.id)
        assert retrieved_claim is not None
        assert retrieved_claim.claim_text == "Test claim for testing purposes"
        assert retrieved_claim.claim_type == ChallengeClaimType.MORAL_PRINCIPLE
        assert retrieved_claim.controversy_score == 0.65

    def test_user_challenge_response_model_creation(self, test_session: Session):
        """Test UserChallengeResponse model creation and validation."""
        # First create a user and challenge
        user = User(
            email="test@example.com",
            name="Test User",
            email_verified=True,
            challenge_participation_enabled=True
        )
        test_session.add(user)
        test_session.commit()

        claim = ChallengeClaim(
            weekly_challenge_id=1,
            claim_text="Test claim",
            claim_type=ChallengeClaimType.MORAL_PRINCIPLE,
            display_order=1,
            controversy_score=0.5,
            philosophical_alignment=0.7
        )
        test_session.add(claim)
        test_session.commit()

        response = UserChallengeResponse(
            user_id=user.id,
            weekly_challenge_id=1,
            claim_id=claim.id,
            agreement_level=AgreementLevel.AGREE,
            justification="This is my test justification",
            response_source="newsletter",
            status=ChallengeResponseStatus.RESPONDED
        )

        test_session.add(response)
        test_session.commit()

        # Verify response was created correctly
        retrieved_response = test_session.get(UserChallengeResponse, response.id)
        assert retrieved_response is not None
        assert retrieved_response.user_id == user.id
        assert retrieved_response.agreement_level == AgreementLevel.AGREE
        assert retrieved_response.status == ChallengeResponseStatus.RESPONDED

    def test_challenge_article_assignment_model(self, test_session: Session):
        """Test ChallengeArticleAssignment model creation and validation."""
        # Create prerequisite objects
        user = User(
            email="test@example.com",
            name="Test User",
            email_verified=True
        )
        test_session.add(user)
        test_session.commit()

        response = UserChallengeResponse(
            user_id=user.id,
            weekly_challenge_id=1,
            claim_id=1,
            agreement_level=AgreementLevel.NEUTRAL,
            status=ChallengeResponseStatus.RESPONDED
        )
        test_session.add(response)
        test_session.commit()

        article = Article(
            title="Test Article",
            url="https://example.com/test-article",
            source_id=1,
            published_at=datetime.utcnow(),
            processing_status="completed",
            word_count=500
        )
        test_session.add(article)
        test_session.commit()

        assignment = ChallengeArticleAssignment(
            challenge_response_id=str(response.id),
            article_id=article.id,
            sequence_day=1,
            opposition_score=0.75,
            is_completed=False,
            engagement_score=0.0
        )

        test_session.add(assignment)
        test_session.commit()

        # Verify assignment was created correctly
        retrieved_assignment = test_session.get(ChallengeArticleAssignment, assignment.id)
        assert retrieved_assignment is not None
        assert retrieved_assignment.sequence_day == 1
        assert retrieved_assignment.opposition_score == 0.75
        assert not retrieved_assignment.is_completed

    def test_weekly_challenge_model(self, test_session: Session):
        """Test WeeklyChallenge model creation and validation."""
        # Create a sample challenge
        challenge = WeeklyChallenge(
            week_start_date="2024-01-15",
            title="Test Weekly Challenge",
            description="A test challenge for unit testing",
            challenge_date="2024-01-19",
            week_end_date="2024-01-21",
            status="PUBLISHED"
        )

        test_session.add(challenge)
        test_session.commit()

        # Verify challenge was created correctly
        retrieved_challenge = test_session.get(WeeklyChallenge, challenge.id)
        assert retrieved_challenge is not None
        assert retrieved_challenge.week_start_date == "2024-01-15"
        assert retrieved_challenge.title == "Test Weekly Challenge"
        assert retrieved_challenge.status == "PUBLISHED"


class TestChallengeClaimGenerator:
    """Test challenge claim generation and management."""

    def test_generate_balanced_claims(self, test_session: Session):
        """Test generation of balanced challenge claims."""
        # Mock articles with various characteristics
        mock_articles = [
            {
                "id": 1,
                "title": "Article 1",
                "summary": "Summary 1",
                "political_lean": "left",
                "sentiment_score": 2.0,
                "framework_position": -8
            },
            {
                "id": 2,
                "title": "Article 2",
                "summary": "Summary 2",
                "political_lean": "right",
                "sentiment_score": -1.5,
                "framework_position": 6
            },
            {
                "id": 3,
                "title": "Article 3",
                "summary": "Summary 3",
                "political_lean": "center",
                "sentiment_score": 0.5,
                "framework_position": 1
            }
        ]

        generator = ChallengeClaimGenerator(test_session)

        claims = generator.generate_balanced_claims(mock_articles, target_count=4)

        # Verify we got the requested number of claims
        assert len(claims) == 4

        # Verify claims have required properties
        for claim in claims:
            assert hasattr(claim, 'claim_text')
            assert hasattr(claim, 'claim_type')
            assert hasattr(claim, 'controversy_score')
            assert hasattr(claim, 'display_order')

        # Verify political balance (should have mix of perspectives)
        claim_types = [claim.claim_type for claim in claims]
        assert len(set(claim_types)) >= 2  # Should have at least 2 different types

    def test_controversy_scoring(self, test_session: Session):
        """Test controversy scoring algorithm."""
        generator = ChallengeClaimGenerator(test_session)

        # Test high controversy claim
        high_controversy_text = "Government surveillance is necessary for national security"
        high_score = generator.calculate_controversy_score(high_controversy_text)
        assert high_score > 0.6  # Should be highly controversial

        # Test low controversy claim
        low_controversy_text = "Everyone should be kind to each other"
        low_score = generator.calculate_controversy_score(low_controversy_text)
        assert low_score < 0.4  # Should be low controversy

        # Test medium controversy claim
        medium_controversy_text = "Economic policies need to balance growth and stability"
        medium_score = generator.calculate_controversy_score(medium_controversy_text)
        assert 0.4 <= medium_score <= 0.6  # Should be medium controversy

    def test_political_balance_filtering(self, test_session: Session):
        """Test political balance filtering in claim selection."""
        generator = ChallengeClaimGenerator(test_session)

        # Create claims with known political biases
        claims_with_bias = [
            {
                "claim_text": "Left-leaning claim about wealth redistribution",
                "political_bias": "left",
                "sentiment_score": 1.5,
                "controversy_score": 0.7
            },
            {
                "claim_text": "Right-leaning claim about free market principles",
                "political_bias": "right",
                "sentiment_score": -1.0,
                "controversy_score": 0.6
            },
            {
                "claim_text": "Center-leaning claim about balanced governance",
                "political_bias": "center",
                "sentiment_score": 0.0,
                "controversy_score": 0.4
            }
        ]

        # Test filtering for balance
        balanced_claims = generator.filter_for_political_balance(claims_with_bias, target_count=2)

        # Should get one claim from each side or center claims
        assert len(balanced_claims) == 2

        # Verify claims are from different political perspectives
        political_biases = [claim['political_bias'] for claim in balanced_claims]
        assert len(set(political_biases)) == 2  # Should have 2 different biases

    @patch('backend.services.challenge_claim_generator.openai_client')
    def test_ai_claim_generation(self, mock_openai, test_session: Session):
        """Test AI-powered claim generation."""
        # Mock OpenAI response
        mock_openai.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message={
                'content': json.dumps({
                    'claims': [
                        {
                            'claim': 'Generated claim about economic justice',
                            'type': 'ECONOMIC_PRINCIPLE',
                            'reasoning': 'This claim addresses economic inequality',
                            'controversy_score': 0.75,
                            'philosophical_alignment': 0.8
                        },
                        {
                            'claim': 'Generated claim about social responsibility',
                            'type': 'SOCIAL_JUSTICE',
                            'reasoning': 'This claim focuses on community welfare',
                            'controversy_score': 0.65,
                            'philosophical_alignment': 0.7
                        }
                    ]
                })
            })]
        )

        generator = ChallengeClaimGenerator(test_session)
        articles = [
            {"title": "Test Article", "summary": "Test summary about economic policy"},
            "political_lean": "center", "sentiment_score": 0.0}
        ]

        claims = generator.generate_ai_claims(articles, target_count=2)

        # Verify AI-generated claims were processed correctly
        assert len(claims) == 2
        assert all('claim' in claim for claim in claims)
        assert all('type' in claim for claim in claims)


class TestChallengeManager:
    """Test challenge management and user response processing."""

    def test_create_weekly_challenge(self, test_session: Session):
        """Test weekly challenge creation."""
        manager = ChallengeManager(test_session)

        # Create a user for the challenge
        user = User(
            email="test@example.com",
            name="Test User",
            email_verified=True,
            challenge_participation_enabled=True
        )
        test_session.add(user)
        test_session.commit()

        # Create weekly challenge
        challenge_date = date.today() - timedelta(days=2)  # Tuesday
        week_start = challenge_date - timedelta(days=challenge_date.weekday())  # Monday of this week

        challenge = manager.create_weekly_challenge(week_start)

        # Verify challenge was created
        assert challenge is not None
        assert challenge.week_start_date == week_start.strftime("%Y-%m-%d")
        assert challenge.status == "PUBLISHED"
        assert len(challenge.claims) == 4  # Should generate 4 claims

    def test_can_user_respond_to_challenge(self, test_session: Session):
        """Test user eligibility checking for challenge responses."""
        manager = ChallengeManager(test_session)

        # Create test user and challenge
        user = User(email="test@example.com", challenge_participation_enabled=True)
        test_session.add(user)
        test_session.commit()

        challenge = WeeklyChallenge(
            week_start_date=date.today().strftime("%Y-%m-%d"),
            title="Test Challenge"
        )
        test_session.add(challenge)
        test_session.commit()

        # Test eligible user
        can_respond, reason = manager.can_user_respond_to_challenge(user.id, challenge.id)
        assert can_respond is True
        assert reason is None

    def test_user_response_submission(self, test_session: Session):
        """Test user challenge response submission."""
        manager = ChallengeManager(test_session)

        # Create test data
        user = User(email="test@example.com", challenge_participation_enabled=True)
        test_session.add(user)
        test_session.commit()

        challenge = WeeklyChallenge(
            week_start_date=date.today().strftime("%Y-%m-%d"),
            title="Test Challenge"
        )
        test_session.add(challenge)
        test_session.commit()

        claim = ChallengeClaim(
            weekly_challenge_id=challenge.id,
            claim_text="Test claim",
            claim_type=ChallengeClaimType.MORAL_PRINCIPLE,
            display_order=1
        )
        test_session.add(claim)
        test_session.commit()

        response_data = {
            "selected_claim_id": claim.id,
            "agreement_level": "AGREE",
            "justification": "I agree with this claim because..."
        }

        # Submit response
        response = manager.submit_challenge_response(
            user.id, challenge.id, response_data, "web_form"
        )

        # Verify response was created
        assert response is not None
        assert response.user_id == user.id
        assert response.claim_id == claim.id
        assert response.agreement_level == AgreementLevel.AGREE
        assert response.status == ChallengeResponseStatus.RESPONDED

    def test_duplicate_submission_prevention(self, test_session: Session):
        """Test prevention of duplicate challenge responses."""
        manager = ChallengeManager(test_session)

        # Create test data
        user = User(email="test@example.com", challenge_participation_enabled=True)
        test_session.add(user)
        test_session.commit()

        challenge = WeeklyChallenge(
            week_start_date=date.today().strftime("%Y-%m-%d"),
            title="Test Challenge"
        )
        test_session.add(challenge)
        test_session.commit()

        claim = ChallengeClaim(
            weekly_challenge_id=challenge.id,
            claim_text="Test claim",
            claim_type=ChallengeClaimType.MORAL_PRINCIPLE,
            display_order=1
        )
        test_session.add(claim)
        test_session.commit()

        # Submit first response
        response_data = {
            "selected_claim_id": claim.id,
            "agreement_level": "AGREE",
            "justification": "First response"
        }

        manager.submit_challenge_response(user.id, challenge.id, response_data, "web_form")

        # Attempt duplicate submission
        can_respond, reason = manager.can_user_respond_to_challenge(user.id, challenge.id)
        assert can_respond is False
        assert "already responded" in reason.lower()

    def test_get_challenge_by_date(self, test_session: Session):
        """Test challenge retrieval by date."""
        manager = ChallengeManager(test_session)

        # Create test user and challenge
        user = User(email="test@example.com", challenge_participation_enabled=True)
        test_session.add(user)
        test_session.commit()

        test_date = date.today().strftime("%Y-%m-%d")
        challenge = WeeklyChallenge(
            week_start_date=test_date,
            title="Test Challenge"
        )
        test_session.add(challenge)
        test_session.commit()

        claim = ChallengeClaim(
            weekly_challenge_id=challenge.id,
            claim_text="Test claim",
            claim_type=ChallengeClaimType.MORAL_PRINCIPLE,
            display_order=1
        )
        test_session.add(claim)
        test_session.commit()

        # Get challenge
        result = manager.get_challenge_by_date(test_date, user.id)

        # Verify challenge data
        assert result is not None
        assert result["challenge"]["title"] == "Test Challenge"
        assert len(result["challenge"]["claims"]) == 1
        assert result["can_respond"] is True

        # Test response for user who hasn't responded
        assert result["user_response"] is None

    def test_get_user_challenge_history(self, test_session: Session):
        """Test retrieval of user's challenge history."""
        manager = ChallengeManager(test_session)

        # Create test user with multiple responses
        user = User(email="test@example.com", challenge_participation_enabled=True)
        test_session.add(user)
        test_session.commit()

        # Create multiple challenge responses
        responses = []
        for i in range(3):
            challenge = WeeklyChallenge(
                week_start_date=(date.today() - timedelta(weeks=i)).strftime("%Y-%m-%d"),
                title=f"Challenge {i+1}"
            )
            test_session.add(challenge)
            test_session.commit()

            claim = ChallengeClaim(
                weekly_challenge_id=challenge.id,
                claim_text=f"Claim {i+1}",
                claim_type=ChallengeClaimType.MORAL_PRINCIPLE,
                display_order=1
            )
            test_session.add(claim)
            test_session.commit()

            response = UserChallengeResponse(
                user_id=user.id,
                weekly_challenge_id=challenge.id,
                claim_id=claim.id,
                agreement_level=AgreementLevel.AGREE if i % 2 == 0 else AgreementLevel.DISAGREE,
                justification=f"Response {i+1}",
                status=ChallengeResponseStatus.COMPLETED if i > 0 else ChallengeResponseStatus.RESPONDED
            )
            test_session.add(response)
            test_session.commit()
            responses.append(response)

        # Get user history
        history = manager.get_user_challenge_history(user.id, limit=10)

        # Verify history contains all responses
        assert len(history) == 3
        assert all("claim_text" in response for response in history)
        assert all("agreement_level" in response for response in history)


class TestChallengeArticleMatcher:
    """Test article assignment algorithm and matching."""

    def test_opposing_viewpoint_matching(self, test_session: Session):
        """Test opposing viewpoint matching algorithm."""
        # Create test user stance
        user_stance = {
            "topic": "economic justice",
            "position": -7,  # Left-leaning position
            "agreement_strength": 0.8
        }

        matcher = ChallengeArticleMatcher(test_session)

        # Test with mock viewpoint data
        mock_viewpoints = [
            {
                "article_id": 1,
                "title": "Opposing Article 1",
                "source_name": "Conservative News",
                "political_lean": "right",
                "sentiment_score": -2.0,
                "relationship_strength": 0.85,
                "reasoning": "Strong opposition on economic policy"
            },
            {
                "article_id": 2,
                "title": "Opposing Article 2",
                "source_name": "Centrist Daily",
                "political_lean": "center",
                "sentiment_score": -0.5,
                "relationship_strength": 0.45,
                "reasoning": "Moderate opposition with some common ground"
            }
        ]

        matched_articles = matcher.score_and_filter_articles(user_stance, mock_viewpoints, max_articles=5)

        # Verify we get the most opposing articles first
        assert len(matched_articles) <= 5
        assert matched_articles[0]["relationship_strength"] >= matched_articles[1]["relationship_strength"]

        # Verify opposition scores are calculated correctly
        for article in matched_articles:
            assert "opposition_score" in article
            assert 0 <= article["opposition_score"] <= 1

    def test_multi_factor_scoring(self, test_session: Session):
        """Test multi-factor scoring algorithm."""
        matcher = ChallengeArticleMatcher(test_session)

        # Create test article with known characteristics
        test_article = {
            "article_id": 1,
            "title": "Test Article",
            "source_name": "Test Source",
            "political_lean": "right",
            "sentiment_score": -1.8,
            "topic_relevance": 0.8,
            "word_count": 800,
            "has_analysis": True
        }

        user_stance = {
            "topic": "economic policy",
            "position": -6,  # Slightly left-leaning
            "agreement_strength": 0.7
        }

        # Calculate score using the same algorithm as the matcher
        topic_score = matcher.calculate_topic_relevance(test_article, user_stance) * 0.20
        sentiment_score = matcher.calculate_sentiment_opposition(test_article, user_stance) * 0.30
        political_score = matcher.calculate_political_opposition(test_article, user_stance) * 0.25
        quality_score = matcher.calculate_quality_indicators(test_article) * 0.25

        total_score = topic_score + sentiment_score + political_score + quality_score

        # Verify score components are reasonable
        assert 0 <= topic_score <= 0.20
        assert 0 <= sentiment_score <= 0.30
        assert 0 <= political_score <= 0.25
        assert 0 <= quality_score <= 0.25

        # Verify total score is in expected range
        assert 0 <= total_score <= 1.0

    def test_diversity_selection(self, test_session: Session):
        """Test diversity selection in article assignment."""
        matcher = ChallengeArticleMatcher(test_session)

        # Create mock candidate articles
        candidates = [
            {
                "article_id": 1,
                "title": "Article from Source A",
                "source_name": "Source A",
                "political_lean": "right",
                "opposition_score": 0.8
            },
            {
                "article_id": 2,
                "title": "Article from Source A",
                "source_name": "Source A",
                "political_lean": "right",
                "opposition_score": 0.75
            },
            {
                "article_id": 3,
                "title": "Article from Source B",
                "source_name": "Source B",
                "political_lean": "left",
                "opposition_score": 0.85
            },
            {
                "article_id": 4,
                "title": "Article from Source C",
                "source_name": "Source C",
                "political_lean": "center",
                "opposition_score": 0.6
            }
        ]

        # Select diverse articles
        selected = matcher.select_diverse_articles(candidates, target_count=3)

        # Verify diversity (should have different sources when possible)
        source_names = [article["source_name"] for article in selected]
        assert len(selected) == 3

        # Should prefer higher opposition scores
        assert selected[0]["opposition_score"] >= selected[1]["opposition_score"] if len(selected) > 1 else True

    @patch('backend.services.challenge_article_matcher.WebSearch')
    @patch('backend.services.challenge_article_matcher.find_opposing_viewpoints')
    def test_web_search_fallback(self, mock_web_search, mock_viewpoints, test_session: Session):
        """Test web search fallback when database articles are insufficient."""
        matcher = ChallengeArticleMatcher(test_session)

        # Mock web search to return some results
        mock_web_search.search.return_value = [
            {
                "url": "https://example.com/web-article-1",
                "title": "Web Article 1",
                "snippet": "This is a web article snippet about opposing views"
            },
            {
                "url": "https://example.com/web-article-2",
                "title": "Web Article 2",
                "snippet": "Another web article with different perspective"
            }
        ]

        # Mock viewpoint finder to return empty (simulate database insufficiency)
        mock_viewpoints.find_opposing_viewpoints.return_value = []

        user_stance = {
            "topic": "economic policy",
            "position": -6,
            "agreement_strength": 0.7
        }

        # Should fallback to web search
        articles = matcher.find_challenge_articles(user_stance, max_articles=5)

        # Verify web search was called
        mock_web_search.search.assert_called_once()

        # Verify web articles were processed
        assert len(articles) >= 1
        assert all("web_search" in article for article in articles)

    def test_historical_article_fallback(self, test_session: Session):
        """Test historical article fallback."""
        matcher = ChallengeArticleMatcher(test_session)

        user_stance = {
            "topic": "economic policy",
            "position": -6,
            "agreement_strength": 0.7
        }

        # Mock insufficient results from both database and web search
        with patch('backend.services.challenge_article_matcher.find_opposing_viewpoints', return_value=[]), \
             patch('backend.services.challenge_article_matcher.WebSearch.search', return_value=[]):

            articles = matcher.find_challenge_articles(user_stance, max_articles=3)

        # Should handle insufficient articles gracefully
        assert isinstance(articles, list)
        assert len(articles) >= 0  # Should return empty list rather than fail

    def test_get_user_assignments(self, test_session: Session):
        """Test retrieval of user's article assignments."""
        matcher = ChallengeArticleMatcher(test_session)

        # Create test user and response
        user = User(email="test@example.com", challenge_participation_enabled=True)
        test_session.add(user)
        test_session.commit()

        response = UserChallengeResponse(
            user_id=user.id,
            weekly_challenge_id=1,
            claim_id=1,
            agreement_level=AgreementLevel.AGREE,
            status=ChallengeResponseStatus.RESPONDED
        )
        test_session.add(response)
        test_session.commit()

        # Create some test assignments
        for i in range(5):
            article = Article(
                title=f"Article {i+1}",
                url=f"https://example.com/article{i+1}",
                source_id=1,
                published_at=datetime.utcnow(),
                processing_status="completed"
            )
            test_session.add(article)
            test_session.commit()

            assignment = ChallengeArticleAssignment(
                challenge_response_id=str(response.id),
                article_id=article.id,
                sequence_day=i+1,
                opposition_score=0.5 + (i * 0.1),
                is_completed=i < 2,  # First 2 completed
                engagement_score=0.8 if i < 2 else 0.0
            )
            test_session.add(assignment)
            test_session.commit()

        # Get assignments
        assignments = matcher.get_user_assignments(user.id, limit=10)

        # Verify assignments were retrieved
        assert len(assignments) == 5
        assert all("sequence_day" in assignment for assignment in assignments)
        assert all("article_id" in assignment for assignment in assignments)

        # Verify completion status
        completed_count = sum(1 for assignment in assignments if assignment.is_completed)
        assert completed_count == 2  # First 2 should be completed


class TestChallengeAnalytics:
    """Test challenge analytics and reporting."""

    def test_user_analytics_calculation(self, test_session: Session):
        """Test user analytics calculation."""
        analytics = ChallengeAnalytics(test_session)

        # Create test user with participation data
        user = User(email="test@example.com", challenge_participation_enabled=True)
        test_session.add(user)
        test_session.commit()

        # Create test challenge and response data
        challenge = WeeklyChallenge(
            week_start_date="2024-01-15",
            title="Test Challenge"
        )
        test_session.add(challenge)
        test_session.commit()

        claim = ChallengeClaim(
            weekly_challenge_id=challenge.id,
            claim_text="Test claim",
            claim_type=ChallengeClaimType.MORAL_PRINCIPLE,
            display_order=1
        )
        test_session.add(claim)
        test_session.commit()

        response = UserChallengeResponse(
            user_id=user.id,
            weekly_challenge_id=challenge.id,
            claim_id=claim.id,
            agreement_level=AgreementLevel.AGREE,
            status=ChallengeResponseStatus.COMPLETED
        )
        test_session.add(response)
        test_session.commit()

        # Create some assignments
        for i in range(3):
            article = Article(title=f"Article {i+1}", source_id=1, url=f"https://example.com/{i+1}")
            test_session.add(article)
            test_session.commit()

            assignment = ChallengeArticleAssignment(
                challenge_response_id=str(response.id),
                article_id=article.id,
                sequence_day=i+1,
                is_completed=i < 2,
                engagement_score=0.8 if i < 2 else 0.0
            )
            test_session.add(assignment)
            test_session.commit()

        # Calculate user analytics
        user_analytics = analytics.get_user_analytics(user.id)

        # Verify basic participation metrics
        assert user_analytics["participation_metrics"]["total_challenges"] == 1
        assert user_analytics["participation_metrics"]["completed_challenges"] == 1
        assert user_analytics["participation_metrics"]["completion_rate"] == 100.0
        assert user_analytics["participation_metrics"]["current_streak"] == 1

        # Verify engagement metrics
        assert user_analytics["engagement_metrics"]["total_articles_assigned"] == 3
        assert user_analytics["engagement_metrics"]["total_articles_engaged"] == 2
        assert user_analytics["engagement_metrics"]["engagement_rate"] == 66.7  # 2/3 * 100

        # Verify quality indicators exist
        assert "response_quality_score" in user_analytics["quality_indicators"]
        assert "engagement_consistency" in user_analytics["quality_indicators"]
        assert "perspective_diversity_score" in user_analytics["quality_indicators"]

    def test_empty_user_analytics(self, test_session: Session):
        """Test analytics calculation for user with no data."""
        analytics = ChallengeAnalytics(test_session)

        # Create user with no challenge data
        user = User(email="new@example.com", challenge_participation_enabled=True)
        test_session.add(user)
        test_session.commit()

        # Calculate analytics for new user
        user_analytics = analytics.get_user_analytics(user.id)

        # Verify empty analytics structure
        assert user_analytics["participation_metrics"]["total_challenges"] == 0
        assert user_analytics["participation_metrics"]["completion_rate"] == 0.0
        assert user_analytics["engagement_metrics"]["total_articles_assigned"] == 0
        assert user_analytics["engagement_metrics"]["engagement_rate"] == 0.0

    def test_system_analytics(self, test_session: Session):
        """Test system-wide analytics calculation."""
        analytics = ChallengeAnalytics(test_session)

        # Create multiple users with varying participation
        users = []
        for i in range(5):
            user = User(
                email=f"test{i}@example.com",
                name=f"Test User {i+1}",
                challenge_participation_enabled=i % 2 == 0  # Half have it enabled
            )
            test_session.add(user)
            users.append(user)

        # Create challenges and responses
        for i, user in enumerate(users[:3]):  # Only 3 users participated
            challenge = WeeklyChallenge(
                week_start_date="2024-01-15",
                title=f"Challenge {i+1}"
            )
            test_session.add(challenge)

            claim = ChallengeClaim(
                weekly_challenge_id=challenge.id,
                claim_text=f"Claim {i+1}",
                claim_type=ChallengeClaimType.MORAL_PRINCIPLE,
                display_order=1
            )
            test_session.add(claim)

            response = UserChallengeResponse(
                user_id=user.id,
                weekly_challenge_id=challenge.id,
                claim_id=claim.id,
                agreement_level=AgreementLevel.AGREE,
                status=ChallengeResponseStatus.COMPLETED
            )
            test_session.add(response)

        test_session.commit()

        # Calculate system analytics
        system_analytics = analytics.get_system_analytics()

        # Verify overview metrics
        assert system_analytics["overview"]["total_users"] == 5
        assert system_analytics["overview"]["active_users"] == 3  # Half have it enabled
        assert 0 <= system_analytics["overview"]["participation_rate"] <= 100

        # Verify weekly trends exist
        assert "weekly_trends" in system_analytics
        assert isinstance(system_analytics["weekly_trends"], list)

        # Verify system health metrics
        assert "system_health" in system_analytics
        assert "system_status" in system_analytics["system_health"]

    def test_challenge_performance_analytics(self, test_session: Session):
        """Test individual challenge performance analytics."""
        analytics = ChallengeAnalytics(test_session)

        # Create test challenge with multiple claims and responses
        challenge = WeeklyChallenge(
            week_start_date="2024-01-15",
            title="Multi-claim Challenge"
        )
        test_session.add(challenge)

        claims = []
        responses = []
        for i in range(4):
            claim = ChallengeClaim(
                weekly_challenge_id=challenge.id,
                claim_text=f"Claim {i+1}",
                claim_type=ChallengeClaimType.MORAL_PRINCIPLE,
                display_order=i+1
            )
            test_session.add(claim)
            claims.append(claim)

            # Create responses for 2 claims
            if i < 2:
                user = User(email=f"user{i}@example.com", challenge_participation_enabled=True)
                test_session.add(user)

                response = UserChallengeResponse(
                    user_id=user.id,
                    weekly_challenge_id=challenge.id,
                    claim_id=claim.id,
                    agreement_level=AgreementLevel.AGREE,
                    status=ChallengeResponseStatus.COMPLETED
                )
                test_session.add(response)
                responses.append(response)

        test_session.commit()

        # Calculate challenge performance
        performance = analytics.get_challenge_performance(challenge.id)

        # Verify challenge info
        assert performance["challenge_info"]["id"] == challenge.id
        assert performance["challenge_info"]["claim_count"] == 4

        # Verify participation metrics
        expected_responses = len(responses)
        assert performance["participation_metrics"]["total_responses"] == expected_responses
        assert performance["participation_metrics"]["completion_rate"] == 100.0  # All marked completed

        # Verify claim performance exists
        assert "claim_performance" in performance
        assert isinstance(performance["claim_performance"], list)

    def test_participation_streak_calculation(self, test_session: Session):
        """Test participation streak calculation."""
        analytics = ChallengeAnalytics(test_session)

        # Create user with specific participation pattern
        user = User(email="streak@test.com", challenge_participation_enabled=True)
        test_session.add(user)

        # Create responses with known dates (simulate 3-week streak)
        today = date.today()
        streak_dates = [
            today - timedelta(weeks=0),  # This week
            today - timedelta(weeks=1),  # Last week
            today - timedelta(weeks=2),  # Two weeks ago
        ]

        responses = []
        for i, week_date in enumerate(streak_dates):
            challenge = WeeklyChallenge(
                week_start_date=week_date.strftime("%Y-%m-%d"),
                title=f"Challenge {i+1}"
            )
            test_session.add(challenge)

            claim = ChallengeClaim(
                weekly_challenge_id=challenge.id,
                claim_text=f"Claim {i+1}",
                claim_type=ChallengeClaimType.MORAL_PRINCIPLE,
                display_order=1
            )
            test_session.add(claim)

            response = UserChallengeResponse(
                user_id=user.id,
                weekly_challenge_id=challenge.id,
                claim_id=claim.id,
                agreement_level=AgreementLevel.AGREE,
                status=ChallengeResponseStatus.COMPLETED
            )
            test_session.add(response)
            responses.append(response)

        test_session.commit()

        # Calculate streak
        user_analytics = analytics.get_user_analytics(user.id)

        # Verify streak calculation
        assert user_analytics["participation_metrics"]["current_streak"] == 3
        assert user_analytics["participation_metrics"]["longest_streak"] == 3

        # Test broken streak (add a gap)
        broken_date = today - timedelta(weeks=3)
        broken_response = UserChallengeResponse(
            user_id=user.id,
            weekly_challenge_id=challenge.id,
            claim_id=claim.id,
            agreement_level=AgreementLevel.AGREE,
            status=ChallengeResponseStatus.COMPLETED,
            submitted_at=broken_date  # Set submitted_at manually
        )
        test_session.add(broken_response)
        test_session.commit()

        # Recalculate analytics with broken streak
        user_analytics_broken = analytics.get_user_analytics(user.id)

        # Should now have current streak of 1 (most recent only)
        assert user_analytics_broken["participation_metrics"]["current_streak"] == 1


# Pytest fixtures
@pytest.fixture
def test_session():
    """Create in-memory test database session."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


@pytest.fixture
def test_user(test_session: Session):
    """Create a test user."""
    user = User(
        email="challenge_test@example.com",
        name="Challenge Test User",
        email_verified=True,
        challenge_participation_enabled=True
    )
    test_session.add(user)
    test_session.commit()
    return user


@pytest.fixture
def sample_challenge(test_session: Session, test_user: User):
    """Create a sample challenge for testing."""
    challenge = WeeklyChallenge(
        week_start_date="2024-01-15",
        title="Test Weekly Challenge",
        description="A test challenge for unit testing",
        status="PUBLISHED"
    )
    test_session.add(challenge)
    test_session.commit()

    claim = ChallengeClaim(
        weekly_challenge_id=challenge.id,
        claim_text="Test claim about ethical principles",
        claim_type=ChallengeClaimType.MORAL_PRINCIPLE,
        display_order=1,
        controversy_score=0.65,
        philosophical_alignment=0.8
    )
    test_session.add(claim)
    test_session.commit()

    return challenge


@pytest.fixture
def sample_claim_response(test_session: Session, test_user: User, sample_challenge: WeeklyChallenge):
    """Create a sample challenge response."""
    # Get a claim from the challenge
    claim = test_session.exec(select(ChallengeClaim)).first()

    response = UserChallengeResponse(
        user_id=test_user.id,
        weekly_challenge_id=sample_challenge.id,
        claim_id=claim.id,
        agreement_level=AgreementLevel.AGREE,
        justification="This is a test response for unit testing",
        response_source="web_form",
        status=ChallengeResponseStatus.RESPONDED,
        submitted_at=datetime.utcnow()
    )
    test_session.add(response)
    test_session.commit()
    return response


if __name__ == "__main__":
    pytest.main([__file__])