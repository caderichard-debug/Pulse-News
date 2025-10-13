"""
Tests for sources management endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from datetime import datetime

from app.main import app
from app.models import Source, Article, OrganizationalBias, User
from app.database import get_session
from app.utils.auth import hash_password, create_access_token


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
        # Create test user
        user = User(
            id=1,
            email="testuser@example.com",
            hashed_password=hash_password("testpass123"),
            email_verified=False,
            is_active=True
        )
        session.add(user)

        # Create test sources with bias
        sources = [
            Source(
                id=1,
                name="Test Center Source",
                url="https://center.com",
                rss_feed_url="https://center.com/rss",
                organizational_bias=OrganizationalBias.CENTER,
                trust_score=0.9
            ),
            Source(
                id=2,
                name="Test Left Source",
                url="https://left.com",
                rss_feed_url="https://left.com/rss",
                organizational_bias=OrganizationalBias.CENTER_LEFT,
                trust_score=0.8
            ),
        ]
        for source in sources:
            session.add(source)

        session.commit()
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client with database session override"""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="auth_headers")
def auth_headers_fixture():
    """Create authentication headers"""
    token = create_access_token(data={"sub": "testuser@example.com"})
    return {"Authorization": f"Bearer {token}"}


def test_list_sources_success(client: TestClient, auth_headers: dict, session: Session):
    """Test listing all sources with default filters."""
    response = client.get("/sources", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "sources" in data
    assert "total_count" in data
    assert isinstance(data["sources"], list)
    assert data["total_count"] > 0


def test_list_sources_filter_by_bias(client: TestClient, auth_headers: dict, session: Session):
    """Test filtering sources by organizational bias."""
    response = client.get("/sources?bias=center", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    sources = data["sources"]

    # All returned sources should have center bias
    for source in sources:
        if source["organizational_bias"]:
            assert source["organizational_bias"] == "center"


def test_list_sources_filter_active_only(client: TestClient, auth_headers: dict, session: Session):
    """Test filtering only active sources."""
    # Create an inactive source
    inactive_source = Source(
        name="Inactive Test Source",
        url="https://inactive.test.com",
        rss_feed_url="https://inactive.test.com/rss_unique_123",
        is_active=False
    )
    session.add(inactive_source)
    session.commit()

    # Get active sources only
    response = client.get("/sources?active_only=true", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    sources = data["sources"]

    # All returned sources should be active
    for source in sources:
        assert source["is_active"] == True

    # Inactive source should not be in results
    source_names = [s["name"] for s in sources]
    assert "Inactive Test Source" not in source_names


def test_list_sources_sort_by_name(client: TestClient, auth_headers: dict):
    """Test sorting sources alphabetically."""
    response = client.get("/sources?sort_by=name", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    sources = data["sources"]

    # Verify alphabetical order
    names = [s["name"] for s in sources]
    assert names == sorted(names)


def test_list_sources_sort_by_trust_score(client: TestClient, auth_headers: dict):
    """Test sorting sources by trust score descending."""
    response = client.get("/sources?sort_by=trust_score", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    sources = data["sources"]

    # Verify descending order
    trust_scores = [s["trust_score"] for s in sources]
    assert trust_scores == sorted(trust_scores, reverse=True)


def test_list_sources_sort_by_article_count(client: TestClient, auth_headers: dict):
    """Test sorting sources by article count descending."""
    response = client.get("/sources?sort_by=article_count", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    sources = data["sources"]

    # Verify descending order
    article_counts = [s["article_count"] for s in sources]
    assert article_counts == sorted(article_counts, reverse=True)


def test_list_sources_requires_auth(client: TestClient):
    """Test that listing sources requires authentication."""
    response = client.get("/sources")
    assert response.status_code in [401, 403]


def test_list_sources_includes_article_count(client: TestClient, auth_headers: dict):
    """Test that source responses include article counts."""
    response = client.get("/sources", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    sources = data["sources"]

    # All sources should have article_count field
    for source in sources:
        assert "article_count" in source
        assert isinstance(source["article_count"], int)
        assert source["article_count"] >= 0


def test_get_source_by_id_success(client: TestClient, auth_headers: dict, session: Session):
    """Test getting source details by ID."""
    # Get first source
    source = session.exec(select(Source)).first()
    assert source is not None

    response = client.get(f"/sources/{source.id}", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == source.id
    assert data["name"] == source.name
    assert "article_count" in data


def test_get_source_not_found(client: TestClient, auth_headers: dict):
    """Test 404 for non-existent source."""
    response = client.get("/sources/999999", headers=auth_headers)
    assert response.status_code == 404


def test_get_source_requires_auth(client: TestClient):
    """Test that getting source requires authentication."""
    response = client.get("/sources/1")
    assert response.status_code in [401, 403]


def test_create_source_success(client: TestClient, auth_headers: dict, session: Session):
    """Test creating new source with valid data."""
    source_data = {
        "name": "Test News Source",
        "url": "https://testnews.com",
        "rss_feed_url": "https://testnews.com/rss_unique_456",
        "description": "A test news source",
        "trust_score": 0.85,
        "fetch_bias": False
    }

    response = client.post("/sources", headers=auth_headers, params=source_data)
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Source created successfully"
    assert data["source"]["name"] == "Test News Source"
    assert data["source"]["trust_score"] == 0.85

    # Verify in database
    source = session.exec(
        select(Source).where(Source.rss_feed_url == "https://testnews.com/rss_unique_456")
    ).first()
    assert source is not None
    assert source.name == "Test News Source"


def test_create_source_with_bias_fetch(client: TestClient, auth_headers: dict, session: Session):
    """Test creating source with automatic bias fetching."""
    source_data = {
        "name": "NPR Test",
        "url": "https://npr.org",
        "rss_feed_url": "https://npr.org/rss_unique_789",
        "fetch_bias": True
    }

    response = client.post("/sources", headers=auth_headers, params=source_data)
    assert response.status_code == 200

    data = response.json()
    # Should have bias_auto_fetched field
    assert "bias_auto_fetched" in data

    # Verify bias was fetched (NPR is in our lookup table)
    source = session.exec(
        select(Source).where(Source.rss_feed_url == "https://npr.org/rss_unique_789")
    ).first()
    assert source is not None
    # NPR should have center-left bias from our lookup table
    if data["bias_auto_fetched"]:
        assert source.organizational_bias == OrganizationalBias.CENTER_LEFT


def test_create_source_duplicate_rss_url(client: TestClient, auth_headers: dict, session: Session):
    """Test that duplicate RSS feed URLs are prevented."""
    # Get existing source
    source = session.exec(select(Source)).first()
    assert source is not None

    source_data = {
        "name": "Duplicate Source",
        "url": "https://duplicate.com",
        "rss_feed_url": source.rss_feed_url,  # Use existing RSS URL
    }

    response = client.post("/sources", headers=auth_headers, params=source_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_source_invalid_trust_score(client: TestClient, auth_headers: dict):
    """Test that trust_score is validated to be between 0.0 and 1.0."""
    source_data = {
        "name": "Invalid Trust Source",
        "url": "https://invalid.com",
        "rss_feed_url": "https://invalid.com/rss_unique_999",
        "trust_score": 1.5  # Invalid - too high
    }

    response = client.post("/sources", headers=auth_headers, params=source_data)
    assert response.status_code == 400


def test_create_source_requires_auth(client: TestClient):
    """Test that creating source requires authentication."""
    source_data = {
        "name": "Unauth Source",
        "url": "https://unauth.com",
        "rss_feed_url": "https://unauth.com/rss",
    }

    response = client.post("/sources", params=source_data)
    assert response.status_code in [401, 403]


def test_update_source_success(client: TestClient, auth_headers: dict, session: Session):
    """Test updating source fields."""
    # Create a source to update
    source = Source(
        name="Original Name",
        url="https://original.com",
        rss_feed_url="https://original.com/rss_unique_111",
        trust_score=0.7
    )
    session.add(source)
    session.commit()
    session.refresh(source)

    # Update the source
    update_data = {
        "name": "Updated Name",
        "trust_score": 0.9
    }

    response = client.put(f"/sources/{source.id}", headers=auth_headers, params=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Source updated successfully"
    assert data["source"]["name"] == "Updated Name"
    assert data["source"]["trust_score"] == 0.9


def test_update_source_bias(client: TestClient, auth_headers: dict, session: Session):
    """Test updating organizational bias."""
    source = Source(
        name="Bias Update Test",
        url="https://biasupdate.com",
        rss_feed_url="https://biasupdate.com/rss_unique_222"
    )
    session.add(source)
    session.commit()
    session.refresh(source)

    update_data = {
        "organizational_bias": "center-left",
        "bias_description": "Center-left news source"
    }

    response = client.put(f"/sources/{source.id}", headers=auth_headers, params=update_data)
    assert response.status_code == 200

    # Verify update
    session.refresh(source)
    assert source.organizational_bias == OrganizationalBias.CENTER_LEFT
    assert source.bias_description == "Center-left news source"


def test_update_source_not_found(client: TestClient, auth_headers: dict):
    """Test 404 for updating non-existent source."""
    response = client.put("/sources/999999", headers=auth_headers, params={"name": "New Name"})
    assert response.status_code == 404


def test_update_source_duplicate_rss_url(client: TestClient, auth_headers: dict, session: Session):
    """Test that updating to duplicate RSS URL is prevented."""
    # Create two sources
    source1 = Source(
        name="Source 1",
        url="https://source1.com",
        rss_feed_url="https://source1.com/rss_unique_333"
    )
    source2 = Source(
        name="Source 2",
        url="https://source2.com",
        rss_feed_url="https://source2.com/rss_unique_444"
    )
    session.add(source1)
    session.add(source2)
    session.commit()
    session.refresh(source1)
    session.refresh(source2)

    # Try to update source2 to use source1's RSS URL
    response = client.put(
        f"/sources/{source2.id}",
        headers=auth_headers,
        params={"rss_feed_url": source1.rss_feed_url}
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_update_source_requires_auth(client: TestClient):
    """Test that updating source requires authentication."""
    response = client.put("/sources/1", params={"name": "New Name"})
    assert response.status_code in [401, 403]


def test_delete_source_soft(client: TestClient, auth_headers: dict, session: Session):
    """Test soft delete (set is_active=False)."""
    source = Source(
        name="To Be Deleted",
        url="https://tobedeleted.com",
        rss_feed_url="https://tobedeleted.com/rss_unique_555",
        is_active=True
    )
    session.add(source)
    session.commit()
    session.refresh(source)

    response = client.delete(f"/sources/{source.id}", headers=auth_headers)
    assert response.status_code == 200
    assert "deactivated" in response.json()["message"]

    # Verify soft delete
    session.refresh(source)
    assert source.is_active == False


def test_delete_source_hard_with_articles(client: TestClient, auth_headers: dict, session: Session):
    """Test that hard delete is prevented when articles exist."""
    # Create source with an article
    source = Source(
        name="Source With Articles",
        url="https://witharticles.com",
        rss_feed_url="https://witharticles.com/rss_unique_666"
    )
    session.add(source)
    session.commit()
    session.refresh(source)

    # Add an article
    from datetime import datetime
    article = Article(
        source_id=source.id,
        title="Test Article",
        url="https://witharticles.com/article1",
        published_at=datetime.utcnow()
    )
    session.add(article)
    session.commit()

    # Try hard delete
    response = client.delete(f"/sources/{source.id}?hard_delete=true", headers=auth_headers)
    assert response.status_code == 400
    assert "Cannot hard delete" in response.json()["detail"]


def test_delete_source_not_found(client: TestClient, auth_headers: dict):
    """Test 404 for deleting non-existent source."""
    response = client.delete("/sources/999999", headers=auth_headers)
    assert response.status_code == 404


def test_delete_source_requires_auth(client: TestClient):
    """Test that deleting source requires authentication."""
    response = client.delete("/sources/1")
    assert response.status_code in [401, 403]
