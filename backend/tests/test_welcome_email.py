"""
Tests for welcome email functionality.
Run with: pytest backend/tests/test_welcome_email.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from app.main import app
from app.database import get_session
from app.models import User, Topic


@pytest.fixture(name="session")
def session_fixture():
    """Create test database session"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Add default topics
        topics = [
            Topic(name="Politics", slug="politics"),
            Topic(name="Technology", slug="technology"),
            Topic(name="Science", slug="science"),
        ]
        for topic in topics:
            session.add(topic)
        session.commit()
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create test client with overridden database dependency"""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestWelcomeEmail:
    """Test suite for welcome email functionality"""

    @patch('app.services.email_service.resend.Emails.send')
    def test_welcome_email_sent_on_registration(self, mock_send, client: TestClient):
        """Test that welcome email is sent when a new user registers"""
        # Mock the email service
        mock_send.return_value = {"id": "test-email-id"}

        # Register a new user
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "name": "Test User"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == "newuser@example.com"

        # Verify that send was called twice (verification + welcome email)
        assert mock_send.call_count == 2

        # Get the two email calls
        calls = mock_send.call_args_list

        # First call should be verification email
        verification_call = calls[0][0][0]
        assert verification_call["subject"] == "Verify Your Pulse Email Address"
        assert verification_call["to"] == ["newuser@example.com"]

        # Second call should be welcome email
        welcome_call = calls[1][0][0]
        assert welcome_call["subject"] == "Welcome to Pulse - Your AI-Powered News Companion"
        assert welcome_call["to"] == ["newuser@example.com"]
        assert "Test User" in welcome_call["html"]

    @patch('app.services.email_service.resend.Emails.send')
    def test_welcome_email_contains_personalization(self, mock_send, client: TestClient):
        """Test that welcome email contains personalized content"""
        mock_send.return_value = {"id": "test-email-id"}

        # Register a new user
        response = client.post(
            "/auth/register",
            json={
                "email": "john.doe@example.com",
                "password": "securepass123",
                "name": "John Doe"
            }
        )

        assert response.status_code == 201

        # Get welcome email call (second call)
        welcome_call = mock_send.call_args_list[1][0][0]

        # Verify personalization
        html_content = welcome_call["html"]
        assert "John Doe" in html_content  # User's name
        assert "dashboard" in html_content.lower()  # Dashboard link
        assert "preferences" in html_content.lower()  # Preferences link
        assert "how-it-works" in html_content.lower()  # How it works link

    @patch('app.services.email_service.resend.Emails.send')
    def test_welcome_email_fallback_to_email_as_name(self, mock_send, client: TestClient):
        """Test that welcome email uses email as name if name not provided"""
        mock_send.return_value = {"id": "test-email-id"}

        # Register without providing name
        response = client.post(
            "/auth/register",
            json={
                "email": "noname@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 201

        # Get welcome email call (second call)
        welcome_call = mock_send.call_args_list[1][0][0]

        # Verify email is used as fallback name
        html_content = welcome_call["html"]
        assert "noname@example.com" in html_content

    @patch('app.services.email_service.resend.Emails.send')
    def test_registration_succeeds_even_if_welcome_email_fails(self, mock_send, client: TestClient):
        """Test that user registration completes even if welcome email fails"""
        # Make welcome email fail (second call)
        mock_send.side_effect = [
            {"id": "verification-email-id"},  # Verification email succeeds
            Exception("Email service error")  # Welcome email fails
        ]

        # Register a new user
        response = client.post(
            "/auth/register",
            json={
                "email": "resilient@example.com",
                "password": "password123",
                "name": "Resilient User"
            }
        )

        # Registration should still succeed
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == "resilient@example.com"
        assert "access_token" in data

    @patch('app.services.email_service.resend.Emails.send')
    def test_welcome_email_includes_key_features(self, mock_send, client: TestClient):
        """Test that welcome email highlights key product features"""
        mock_send.return_value = {"id": "test-email-id"}

        response = client.post(
            "/auth/register",
            json={
                "email": "features@example.com",
                "password": "password123",
                "name": "Feature Test"
            }
        )

        assert response.status_code == 201

        # Get welcome email call
        welcome_call = mock_send.call_args_list[1][0][0]
        html_content = welcome_call["html"]

        # Check for key feature mentions
        assert "sentiment" in html_content.lower() or "bias" in html_content.lower()
        assert "statistics" in html_content.lower() or "verification" in html_content.lower()
        assert "framework" in html_content.lower() or "ethical" in html_content.lower()
        assert "newsletter" in html_content.lower() or "digest" in html_content.lower()

    @patch('app.services.email_service.settings')
    @patch('app.services.email_service.resend.Emails.send')
    def test_welcome_email_not_sent_without_api_key(self, mock_send, mock_settings, client: TestClient):
        """Test that welcome email is gracefully skipped if API key is not configured"""
        # Simulate missing API key
        mock_settings.resend_api_key = None

        response = client.post(
            "/auth/register",
            json={
                "email": "noapi@example.com",
                "password": "password123",
                "name": "No API User"
            }
        )

        # Registration should still succeed
        assert response.status_code == 201

        # Email service should not have been called
        mock_send.assert_not_called()


class TestWelcomeEmailService:
    """Direct tests for the welcome email service function"""

    @patch('app.services.email_service.resend.Emails.send')
    @patch('app.services.email_service.settings')
    def test_send_welcome_email_success(self, mock_settings, mock_send):
        """Test send_welcome_email function directly"""
        from app.services.email_service import send_welcome_email

        mock_settings.resend_api_key = "test-key"
        mock_settings.from_name = "Pulse News"
        mock_settings.from_email = "test@pulse.com"
        mock_settings.frontend_url = "http://localhost:3000"
        mock_send.return_value = {"id": "email-123"}

        result = send_welcome_email("user@example.com", "Test User")

        assert result is True
        mock_send.assert_called_once()

        # Verify email parameters
        call_args = mock_send.call_args[0][0]
        assert call_args["to"] == ["user@example.com"]
        assert call_args["subject"] == "Welcome to Pulse - Your AI-Powered News Companion"
        assert "Test User" in call_args["html"]

    @patch('app.services.email_service.settings')
    def test_send_welcome_email_no_api_key(self, mock_settings):
        """Test send_welcome_email returns False when no API key"""
        from app.services.email_service import send_welcome_email

        mock_settings.resend_api_key = None

        result = send_welcome_email("user@example.com", "Test User")

        assert result is False

    @patch('app.services.email_service.resend.Emails.send')
    @patch('app.services.email_service.settings')
    def test_send_welcome_email_handles_exception(self, mock_settings, mock_send):
        """Test send_welcome_email handles exceptions gracefully"""
        from app.services.email_service import send_welcome_email

        mock_settings.resend_api_key = "test-key"
        mock_settings.from_name = "Pulse News"
        mock_settings.from_email = "test@pulse.com"
        mock_settings.frontend_url = "http://localhost:3000"
        mock_send.side_effect = Exception("Network error")

        result = send_welcome_email("user@example.com", "Test User")

        assert result is False
