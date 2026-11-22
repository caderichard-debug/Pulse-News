"""
Pytest configuration and fixtures.
"""

import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from app.database import get_session
from app.main import app
from app.utils.rate_limit import reset_rate_limits


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Rate-limit buckets are module-global; isolate them between tests."""
    reset_rate_limits()
    yield
    reset_rate_limits()


@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client with database session override"""
    from fastapi.testclient import TestClient

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


TEST_ADMIN_TOKEN = "test-admin-token"


@pytest.fixture
def admin_token_headers(monkeypatch):
    """Headers that satisfy require_admin_access via the X-Admin-Token path."""
    from app.config import settings
    monkeypatch.setattr(settings, "admin_token", TEST_ADMIN_TOKEN)
    return {"X-Admin-Token": TEST_ADMIN_TOKEN}
