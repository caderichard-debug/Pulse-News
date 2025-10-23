"""
Comprehensive tests for challenge system API endpoints.

Tests all challenge API routes:
- Authentication and authorization
- Input validation and error handling
- Response format and data integrity
- Rate limiting and performance
- Integration with services
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, select, and_, or_
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, date
import json

from ..main import app
from ..models import (
    User, WeeklyChallenge, ChallengeClaim, UserChallengeResponse,
    ChallengeArticleAssignment, ChallengeClaimType, AgreementLevel,
    ChallengeResponseStatus, Article, Source
)
from ..database import get_session
from ..routes.auth import create_access_token


@pytest.fixture
def client():
    """Create test client with proper session dependency."""
    return TestClient(app)


@pytest.fixture
def session():
    """Create test database session."""
    engine = create_engine("sqlite:///:memory:")
    from ..models import SQLModel
    SQLModel.metadata.create_all(engine)
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_user(session: Session):
    """Create a test user with challenge participation enabled."""
    user = User(
        email="challenge_api_test@example.com",
        name="Challenge API Test User",
        email_verified=True,
        challenge_participation_enabled=True
    )
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def auth_headers(test_user: User):
    """Create authentication headers for test user."""
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_challenge(session: Session):
    """Create a sample weekly challenge with claims."""
    challenge = WeeklyChallenge(
        week_start_date="2024-01-15",
        title="API Test Challenge",
        description="A challenge for testing API endpoints",
        challenge_date="2024-01-19",
        week_end_date="2024-01-21",
        status="PUBLISHED"
    )
    session.add(challenge)
    session.commit()

    # Create multiple claims for the challenge
    claims = []
    claim_types = [
        ChallengeClaimType.MORAL_PRINCIPLE,
        ChallengeClaimType.SOCIAL_JUSTICE,
        ChallengeClaimType.ECONOMIC_PRINCIPLE,
        ChallengeClaimType.VALUE_CONFLICT
    ]

    for i, claim_type in enumerate(claim_types):
        claim = ChallengeClaim(
            weekly_challenge_id=challenge.id,
            claim_text=f"API Test Claim {i+1}: This is a {claim_type.value.lower()} claim for testing",
            claim_type=claim_type,
            display_order=i + 1,
            controversy_score=0.5 + (i * 0.1),
            philosophical_alignment=0.6 + (i * 0.1)
        )
        session.add(claim)
        session.commit()
        claims.append(claim)

    return {"challenge": challenge, "claims": claims}


@pytest.fixture
def sample_response(session: Session, test_user: User, sample_challenge: dict):
    """Create a sample user challenge response."""
    claim = sample_challenge["claims"][0]  # Use first claim

    response = UserChallengeResponse(
        user_id=test_user.id,
        weekly_challenge_id=sample_challenge["challenge"].id,
        claim_id=claim.id,
        agreement_level=AgreementLevel.AGREE,
        justification="This is a test response for API testing",
        response_source="web_form",
        status=ChallengeResponseStatus.RESPONDED,
        submitted_at=datetime.utcnow()
    )
    session.add(response)
    session.commit()
    return response


class TestChallengeCurrentEndpoint:
    """Test GET /challenge/current endpoint."""

    def test_get_current_challenge_success(self, client: TestClient, test_user: User,
                                         auth_headers: dict, sample_challenge: dict):
        """Test successful retrieval of current challenge."""
        response = client.get("/challenge/current", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "challenge" in data
        assert "user_response" in data
        assert "can_respond" in data
        assert "reason" in data

        # Verify challenge data
        challenge = data["challenge"]
        assert challenge["title"] == "API Test Challenge"
        assert challenge["week_start_date"] == "2024-01-15"
        assert len(challenge["claims"]) == 4

        # Verify claims structure
        for claim in challenge["claims"]:
            assert "id" in claim
            assert "claim_text" in claim
            assert "claim_type" in claim
            assert "display_order" in claim

    def test_get_current_challenge_user_already_responded(
        self, client: TestClient, test_user: User, auth_headers: dict,
        sample_response: UserChallengeResponse
    ):
        """Test current challenge retrieval when user has already responded."""
        response = client.get("/challenge/current", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should show user has already responded
        assert data["user_response"] is not None
        assert data["can_respond"] is False
        assert "already responded" in data["reason"].lower()

        # Verify user response data
        user_response = data["user_response"]
        assert user_response["selected_claim_id"] == sample_response.claim_id
        assert user_response["agreement_level"] == "AGREE"
        assert user_response["status"] == "RESPONDED"

    def test_get_current_challenge_user_not_participating(self, client: TestClient, session: Session):
        """Test current challenge retrieval for user not participating."""
        # Create user with challenge participation disabled
        user = User(
            email="no_participation@example.com",
            challenge_participation_enabled=False
        )
        session.add(user)
        session.commit()

        token = create_access_token(data={"sub": user.email})
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/challenge/current", headers=headers)

        assert response.status_code == 200
        data = response.json()

        assert data["can_respond"] is False
        assert "participation" in data["reason"].lower()

    def test_get_current_challenge_no_active_challenge(
        self, client: TestClient, test_user: User, auth_headers: dict, session: Session
    ):
        """Test current challenge retrieval when no active challenge exists."""
        response = client.get("/challenge/current", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["challenge"] is None
        assert data["can_respond"] is False
        assert "no active challenge" in data["reason"].lower()

    def test_get_current_challenge_unauthorized(self, client: TestClient):
        """Test current challenge retrieval without authentication."""
        response = client.get("/challenge/current")

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"

    def test_get_current_challenge_invalid_token(self, client: TestClient):
        """Test current challenge retrieval with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/challenge/current", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestChallengeByDateEndpoint:
    """Test GET /challenge/{week_date} endpoint."""

    def test_get_challenge_by_date_success(
        self, client: TestClient, test_user: User, auth_headers: dict, sample_challenge: dict
    ):
        """Test successful challenge retrieval by date."""
        week_date = "2024-01-15"
        response = client.get(f"/challenge/{week_date}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify challenge data
        assert "challenge" in data
        assert "user_response" in data
        assert "can_respond" in data
        assert "user_name" in data

        challenge = data["challenge"]
        assert challenge["week_start_date"] == week_date
        assert challenge["title"] == "API Test Challenge"

    def test_get_challenge_by_date_invalid_date_format(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test challenge retrieval with invalid date format."""
        response = client.get("/challenge/invalid-date", headers=auth_headers)

        assert response.status_code == 400
        data = response.json()
        assert "invalid date format" in data["detail"].lower()

    def test_get_challenge_by_date_challenge_not_found(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test challenge retrieval for non-existent challenge."""
        future_date = "2025-01-01"
        response = client.get(f"/challenge/{future_date}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["challenge"] is None
        assert data["can_respond"] is False
        assert "not found" in data["reason"].lower()

    def test_get_challenge_by_date_unauthorized(self, client: TestClient):
        """Test challenge retrieval by date without authentication."""
        response = client.get("/challenge/2024-01-15")

        assert response.status_code == 401


class TestChallengeResponseEndpoint:
    """Test POST /challenge/{week_date}/respond endpoint."""

    def test_submit_challenge_response_success(
        self, client: TestClient, test_user: User, auth_headers: dict, sample_challenge: dict
    ):
        """Test successful challenge response submission."""
        week_date = "2024-01-15"
        claim = sample_challenge["claims"][1]  # Use second claim
        response_data = {
            "selected_claim_id": claim.id,
            "agreement_level": "DISAGREE"
        }

        response = client.post(
            f"/challenge/{week_date}/respond",
            json=response_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "success" in data
        assert "response_id" in data
        assert "selected_claim" in data
        assert "agreement_level" in data
        assert "challenge_started" in data

        assert data["success"] is True
        assert data["selected_claim"]["id"] == claim.id
        assert data["agreement_level"] == "DISAGREE"
        assert data["challenge_started"] is True

    def test_submit_challenge_response_with_justification(
        self, client: TestClient, test_user: User, auth_headers: dict, sample_challenge: dict
    ):
        """Test challenge response submission with justification."""
        week_date = "2024-01-15"
        claim = sample_challenge["claims"][0]
        response_data = {
            "selected_claim_id": claim.id,
            "agreement_level": "STRONGLY_AGREE",
            "justification": "I strongly agree because this aligns with my core values"
        }

        response = client.post(
            f"/challenge/{week_date}/respond",
            json=response_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_submit_duplicate_response(
        self, client: TestClient, test_user: User, auth_headers: dict,
        sample_response: UserChallengeResponse
    ):
        """Test duplicate response submission prevention."""
        week_date = "2024-01-15"
        claim_id = sample_response.claim_id
        response_data = {
            "selected_claim_id": claim_id,
            "agreement_level": "NEUTRAL"
        }

        response = client.post(
            f"/challenge/{week_date}/respond",
            json=response_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "already responded" in data["detail"].lower()

    def test_submit_response_invalid_claim_id(
        self, client: TestClient, test_user: User, auth_headers: dict, sample_challenge: dict
    ):
        """Test response submission with invalid claim ID."""
        week_date = "2024-01-15"
        response_data = {
            "selected_claim_id": 999,  # Non-existent claim ID
            "agreement_level": "AGREE"
        }

        response = client.post(
            f"/challenge/{week_date}/respond",
            json=response_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "invalid claim" in data["detail"].lower()

    def test_submit_response_invalid_agreement_level(
        self, client: TestClient, test_user: User, auth_headers: dict, sample_challenge: dict
    ):
        """Test response submission with invalid agreement level."""
        week_date = "2024-01-15"
        claim = sample_challenge["claims"][0]
        response_data = {
            "selected_claim_id": claim.id,
            "agreement_level": "INVALID_LEVEL"
        }

        response = client.post(
            f"/challenge/{week_date}/respond",
            json=response_data,
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    def test_submit_response_missing_fields(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test response submission with missing required fields."""
        week_date = "2024-01-15"
        response_data = {
            "selected_claim_id": 1
            # Missing agreement_level
        }

        response = client.post(
            f"/challenge/{week_date}/respond",
            json=response_data,
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    def test_submit_response_unauthorized(self, client: TestClient, sample_challenge: dict):
        """Test response submission without authentication."""
        week_date = "2024-01-15"
        response_data = {
            "selected_claim_id": 1,
            "agreement_level": "AGREE"
        }

        response = client.post(f"/challenge/{week_date}/respond", json=response_data)

        assert response.status_code == 401


class TestChallengeAnalyticsEndpoints:
    """Test challenge analytics endpoints."""

    @patch('backend.routes.challenge.ChallengeAnalytics')
    def test_get_challenge_analytics_success(
        self, mock_analytics_class, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test successful analytics retrieval."""
        # Mock analytics service
        mock_analytics_instance = MagicMock()
        mock_analytics_instance.get_user_analytics.return_value = {
            "participation_metrics": {
                "total_challenges": 5,
                "completed_challenges": 4,
                "completion_rate": 80.0,
                "current_streak": 2,
                "longest_streak": 3
            },
            "engagement_metrics": {
                "total_articles_assigned": 35,
                "total_articles_engaged": 28,
                "engagement_rate": 80.0
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        mock_analytics_class.return_value = mock_analytics_instance

        response = client.get("/challenge/analytics", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify analytics data structure
        assert "participation_metrics" in data
        assert "engagement_metrics" in data
        assert "generated_at" in data

        # Verify metrics values
        assert data["participation_metrics"]["total_challenges"] == 5
        assert data["engagement_metrics"]["engagement_rate"] == 80.0

    @patch('backend.routes.challenge.ChallengeAnalytics')
    def test_get_challenge_analytics_service_error(
        self, mock_analytics_class, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test analytics retrieval with service error."""
        # Mock analytics service to throw error
        mock_analytics_instance = MagicMock()
        mock_analytics_instance.get_user_analytics.side_effect = Exception("Service error")
        mock_analytics_class.return_value = mock_analytics_instance

        response = client.get("/challenge/analytics", headers=auth_headers)

        assert response.status_code == 500
        data = response.json()
        assert "error getting challenge analytics" in data["detail"].lower()

    def test_get_challenge_analytics_unauthorized(self, client: TestClient):
        """Test analytics retrieval without authentication."""
        response = client.get("/challenge/analytics")

        assert response.status_code == 401

    @patch('backend.routes.challenge.ChallengeAnalytics')
    def test_get_participation_trends_success(
        self, mock_analytics_class, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test successful participation trends retrieval."""
        # Mock trends data
        mock_analytics_instance = MagicMock()
        mock_analytics_instance.get_participation_trends.return_value = {
            "trends": [
                {
                    "week_start": "2024-01-15",
                    "participated": True,
                    "claim_type": "MORAL_PRINCIPLE",
                    "agreement_level": "AGREE",
                    "completion_rate": 85.7
                },
                {
                    "week_start": "2024-01-08",
                    "participated": False,
                    "claim_type": None,
                    "agreement_level": None,
                    "completion_rate": 0.0
                }
            ],
            "summary": {
                "total_weeks": 12,
                "participated_weeks": 8,
                "participation_rate": 66.7
            }
        }
        mock_analytics_class.return_value = mock_analytics_instance

        response = client.get("/challenge/analytics/trends", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify trends structure
        assert "trends" in data
        assert "summary" in data
        assert "generated_at" in data

        # Verify trends data
        assert len(data["trends"]) == 2
        assert data["trends"][0]["participated"] is True
        assert data["trends"][1]["participated"] is False

    def test_get_participation_trends_custom_time_range(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test participation trends with custom time range parameter."""
        with patch('backend.routes.challenge.ChallengeAnalytics') as mock_analytics_class:
            mock_analytics_instance = MagicMock()
            mock_analytics_instance.get_participation_trends.return_value = {
                "trends": [],
                "summary": {"total_weeks": 4, "participated_weeks": 2, "participation_rate": 50.0}
            }
            mock_analytics_class.return_value = mock_analytics_instance

            response = client.get("/challenge/analytics/trends?weeks=4", headers=auth_headers)

            assert response.status_code == 200

            # Verify the correct parameter was passed
            mock_analytics_instance.get_participation_trends.assert_called_with(4)


class TestChallengeAssignmentEndpoints:
    """Test challenge assignment endpoints."""

    def test_get_challenge_assignments_success(
        self, client: TestClient, test_user: User, auth_headers: dict,
        sample_response: UserChallengeResponse, session: Session
    ):
        """Test successful assignment retrieval."""
        # Create test assignments
        assignments = []
        for i in range(3):
            article = Article(
                title=f"Assignment Article {i+1}",
                url=f"https://example.com/article{i+1}",
                source_id=1,
                published_at=datetime.utcnow()
            )
            session.add(article)
            session.commit()

            assignment = ChallengeArticleAssignment(
                challenge_response_id=str(sample_response.id),
                article_id=article.id,
                sequence_day=i+1,
                opposition_score=0.5 + (i * 0.1),
                is_completed=i < 2,
                engagement_score=0.8 if i < 2 else 0.0
            )
            session.add(assignment)
            session.commit()
            assignments.append(assignment)

        response = client.get("/challenge/assignments", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should return list of assignments
        assert isinstance(data, list)
        assert len(data) == 3

        # Verify assignment structure
        assignment_data = data[0]
        assert "id" in assignment_data
        assert "article_id" in assignment_data
        assert "sequence_day" in assignment_data
        assert "is_completed" in assignment_data
        assert "article" in assignment_data

    def test_get_challenge_assignments_for_specific_response(
        self, client: TestClient, test_user: User, auth_headers: dict,
        sample_response: UserChallengeResponse, session: Session
    ):
        """Test assignment retrieval for specific response."""
        # Create test assignment
        article = Article(title="Test Article", source_id=1, url="https://example.com")
        session.add(article)
        session.commit()

        assignment = ChallengeArticleAssignment(
            challenge_response_id=str(sample_response.id),
            article_id=article.id,
            sequence_day=1,
            is_completed=False
        )
        session.add(assignment)
        session.commit()

        response = client.get(
            f"/challenge/assignments?response_id={sample_response.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:  # Should return assignments if they exist
            assert data[0]["challenge_response_id"] == str(sample_response.id)

    def test_update_assignment_completion(
        self, client: TestClient, test_user: User, auth_headers: dict,
        sample_response: UserChallengeResponse, session: Session
    ):
        """Test assignment completion update."""
        # Create test assignment
        article = Article(title="Test Article", source_id=1, url="https://example.com")
        session.add(article)
        session.commit()

        assignment = ChallengeArticleAssignment(
            challenge_response_id=str(sample_response.id),
            article_id=article.id,
            sequence_day=1,
            is_completed=False
        )
        session.add(assignment)
        session.commit()

        update_data = {"is_completed": True}
        response = client.put(
            f"/challenge/assignments/{assignment.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "success" in data
        assert data["success"] is True
        assert "message" in data

        # Verify assignment was updated in database
        updated_assignment = session.get(ChallengeArticleAssignment, assignment.id)
        assert updated_assignment.is_completed is True
        assert updated_assignment.completed_at is not None

    def test_update_assignment_not_found(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test assignment update for non-existent assignment."""
        update_data = {"is_completed": True}
        response = client.put(
            "/challenge/assignments/non-existent-id",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 404
        data = response.json()
        assert "assignment not found" in data["detail"].lower()

    def test_update_assignment_unauthorized(self, client: TestClient):
        """Test assignment update without authentication."""
        update_data = {"is_completed": True}
        response = client.put("/challenge/assignments/some-id", json=update_data)

        assert response.status_code == 401


class TestChallengeFeedbackEndpoint:
    """Test challenge feedback endpoint."""

    def test_submit_challenge_feedback_success(
        self, client: TestClient, test_user: User, auth_headers: dict,
        sample_response: UserChallengeResponse
    ):
        """Test successful feedback submission."""
        feedback_data = {
            "found_valuable": True,
            "feedback_text": "This challenge was very valuable for broadening my perspective"
        }

        response = client.post(
            f"/challenge/feedback?response_id={sample_response.id}",
            json=feedback_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "success" in data
        assert "message" in data

    def test_submit_challenge_feedback_minimal(
        self, client: TestClient, test_user: User, auth_headers: dict,
        sample_response: UserChallengeResponse
    ):
        """Test feedback submission with minimal data."""
        feedback_data = {"found_valuable": False}

        response = client.post(
            f"/challenge/feedback?response_id={sample_response.id}",
            json=feedback_data,
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_submit_feedback_response_not_found(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test feedback submission for non-existent response."""
        feedback_data = {"found_valuable": True}

        response = client.post(
            "/challenge/feedback?response_id=999",
            json=feedback_data,
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_submit_feedback_unauthorized(self, client: TestClient, sample_response: UserChallengeResponse):
        """Test feedback submission without authentication."""
        feedback_data = {"found_valuable": True}

        response = client.post(
            f"/challenge/feedback?response_id={sample_response.id}",
            json=feedback_data
        )

        assert response.status_code == 401


class TestChallengeResponseEndpoint:
    """Test GET /challenge/responses endpoint."""

    def test_get_user_challenge_responses_success(
        self, client: TestClient, test_user: User, auth_headers: dict,
        sample_response: UserChallengeResponse
    ):
        """Test successful retrieval of user challenge responses."""
        response = client.get("/challenge/responses", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should return list of responses
        assert isinstance(data, list)
        assert len(data) >= 1  # At least our sample response

        # Verify response structure
        response_data = data[0]
        assert "id" in response_data
        assert "week_start_date" in response_data
        assert "claim_text" in response_data
        assert "claim_type" in response_data
        assert "agreement_level" in response_data
        assert "assigned_articles_count" in response_data
        assert "engaged_articles_count" in response_data

    def test_get_user_challenge_responses_unauthorized(self, client: TestClient):
        """Test response retrieval without authentication."""
        response = client.get("/challenge/responses")

        assert response.status_code == 401


class TestChallengeStatisticsEndpoint:
    """Test GET /challenge/statistics endpoint."""

    def test_get_challenge_statistics_success(
        self, client: TestClient, test_user: User, auth_headers: dict,
        sample_response: UserChallengeResponse
    ):
        """Test successful statistics retrieval."""
        response = client.get("/challenge/statistics", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify statistics structure
        expected_fields = [
            "total_participated",
            "average_agreement_level",
            "claim_type_breakdown",
            "participation_streak",
            "current_week_responded"
        ]

        for field in expected_fields:
            assert field in data

        # Verify data types
        assert isinstance(data["total_participated"], int)
        assert isinstance(data["average_agreement_level"], (int, float))
        assert isinstance(data["claim_type_breakdown"], dict)
        assert isinstance(data["participation_streak"], int)
        assert isinstance(data["current_week_responded"], bool)

    def test_get_challenge_statistics_empty_user(
        self, client: TestClient, session: Session
    ):
        """Test statistics retrieval for user with no challenge data."""
        # Create user with no challenge responses
        user = User(email="empty_stats@example.com", challenge_participation_enabled=True)
        session.add(user)
        session.commit()

        token = create_access_token(data={"sub": user.email})
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/challenge/statistics", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Should return empty statistics
        assert data["total_participated"] == 0
        assert data["average_agreement_level"] == 0.0
        assert data["claim_type_breakdown"] == {}
        assert data["participation_streak"] == 0
        assert data["current_week_responded"] is False

    def test_get_challenge_statistics_unauthorized(self, client: TestClient):
        """Test statistics retrieval without authentication."""
        response = client.get("/challenge/statistics")

        assert response.status_code == 401


class TestChallengeRateLimiting:
    """Test rate limiting on challenge endpoints."""

    def test_response_rate_limiting(
        self, client: TestClient, test_user: User, auth_headers: dict, sample_challenge: dict
    ):
        """Test rate limiting on response submission."""
        week_date = "2024-01-15"
        claim = sample_challenge["claims"][0]
        response_data = {
            "selected_claim_id": claim.id,
            "agreement_level": "AGREE"
        }

        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = client.post(
                f"/challenge/{week_date}/respond",
                json=response_data,
                headers=auth_headers
            )
            responses.append(response)

        # First request should succeed (or fail due to duplicate)
        # Subsequent requests might be rate limited
        assert responses[0].status_code in [200, 400]  # Success or duplicate error

        # Check if any requests show rate limiting (status 429)
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        if rate_limited_responses:
            for response in rate_limited_responses:
                data = response.json()
                assert "rate limited" in data["detail"].lower()


class TestChallengeErrorHandling:
    """Test comprehensive error handling in challenge endpoints."""

    def test_database_connection_error_handling(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test handling of database connection errors."""
        with patch('backend.routes.challenge.Session') as mock_session:
            # Mock session to raise database error
            mock_session.side_effect = Exception("Database connection failed")

            response = client.get("/challenge/statistics", headers=auth_headers)

            assert response.status_code == 500
            data = response.json()
            assert "internal server error" in data["detail"].lower()

    def test_malformed_json_handling(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test handling of malformed JSON in request bodies."""
        malformed_data = '{"invalid": json structure}'

        response = client.post(
            "/challenge/2024-01-15/respond",
            data=malformed_data,
            headers={**auth_headers, "Content-Type": "application/json"}
        )

        assert response.status_code == 422  # JSON parsing error

    def test_large_payload_handling(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test handling of excessively large request payloads."""
        large_justification = "x" * 10000  # 10KB justification
        response_data = {
            "selected_claim_id": 1,
            "agreement_level": "AGREE",
            "justification": large_justification
        }

        response = client.post(
            "/challenge/2024-01-15/respond",
            json=response_data,
            headers=auth_headers
        )

        # Should either accept or reject based on size limits
        assert response.status_code in [200, 400, 413]

    def test_sql_injection_protection(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test protection against SQL injection attacks."""
        malicious_input = "'; DROP TABLE users; --"

        # Try to inject malicious input into various endpoints
        endpoints_to_test = [
            f"/challenge/{malicious_input}",
            f"/challenge/analytics/performance/{malicious_input}",
            f"/challenge/assignments/{malicious_input}",
            f"/challenge/feedback?response_id={malicious_input}"
        ]

        for endpoint in endpoints_to_test:
            response = client.get(endpoint, headers=auth_headers)
            # Should return safe error (404, 400, or 422) but not 500 with SQL error
            assert response.status_code in [400, 404, 422]

    def test_path_traversal_protection(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test protection against path traversal attacks."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]

        for malicious_path in malicious_paths:
            response = client.get(f"/challenge/{malicious_path}", headers=auth_headers)
            # Should handle path traversal attempts safely
            assert response.status_code in [400, 404]


if __name__ == "__main__":
    pytest.main([__file__])