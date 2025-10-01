"""
Test database models and validation.
"""

from app.models import User, Article, Framework, ProcessingStatus, PoliticalLean
from datetime import datetime
import pytest


def test_user_model():
    """Test User model creation"""
    user = User(
        name="Test User",
        email="test@example.com",
        password_hash="hashed_password_here",
        is_active=True,
        email_verified=False,
        created_at=datetime.utcnow()
    )
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.is_active is True


def test_article_model():
    """Test Article model creation"""
    article = Article(
        source_id=1,
        title="Test Article",
        url="https://example.com/article",
        processing_status=ProcessingStatus.PENDING,
        scraped_at=datetime.utcnow()
    )
    assert article.title == "Test Article"
    assert article.processing_status == ProcessingStatus.PENDING


def test_framework_model():
    """Test Framework model creation"""
    framework = Framework(
        name="Test Framework",
        description="A test ethical framework",
        axis_description="left vs right",
        left_position="Position A",
        right_position="Position B",
        article_count=0,
        is_seed=True,
        created_at=datetime.utcnow()
    )
    assert framework.name == "Test Framework"
    assert framework.is_seed is True


def test_processing_status_enum():
    """Test ProcessingStatus enum values"""
    assert ProcessingStatus.PENDING == "pending"
    assert ProcessingStatus.COMPLETED == "completed"
    assert ProcessingStatus.FAILED == "failed"


def test_political_lean_enum():
    """Test PoliticalLean enum values"""
    assert PoliticalLean.LEFT == "LEFT"
    assert PoliticalLean.CENTER == "CENTER"
    assert PoliticalLean.RIGHT == "RIGHT"
