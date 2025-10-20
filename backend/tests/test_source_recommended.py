"""Tests for source is_recommended field and preferences endpoint."""

import pytest
from sqlmodel import Session, select
from app.models import User, Source
from app.utils.auth import hash_password, create_access_token


@pytest.fixture
def auth_token(session: Session):
    """Create test user and return auth token."""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("password"),
        name="Test User"
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_access_token(data={"sub": user.email})
    return token


@pytest.fixture
def test_sources(session: Session):
    """Create test sources with different is_recommended values."""
    recommended_source = Source(
        name="Recommended Source",
        url="https://recommended.com",
        rss_feed_url="https://recommended.com/rss",
        is_recommended=True,
        trust_score=0.9
    )
    community_source = Source(
        name="Community Source",
        url="https://community.com",
        rss_feed_url="https://community.com/rss",
        is_recommended=False,
        trust_score=0.7
    )
    session.add(recommended_source)
    session.add(community_source)
    session.commit()
    session.refresh(recommended_source)
    session.refresh(community_source)
    
    return {"recommended": recommended_source, "community": community_source}


def test_sources_preferences_includes_is_recommended(client, auth_token, test_sources):
    """Test that /preferences/sources includes is_recommended field."""
    response = client.get(
        "/preferences/sources",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    
    sources = response.json()
    assert len(sources) >= 2
    
    # Check that each source has is_recommended field
    for source in sources:
        assert "is_recommended" in source
        assert isinstance(source["is_recommended"], bool)
        assert "source_id" in source
        assert "name" in source
        assert "subscribed" in source


def test_recommended_sources_filtered(client, auth_token, test_sources):
    """Test that we can distinguish recommended vs community sources."""
    response = client.get(
        "/preferences/sources",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    
    sources = response.json()
    recommended = [s for s in sources if s["is_recommended"]]
    community = [s for s in sources if not s["is_recommended"]]
    
    # Should have both types from our fixtures
    assert len(recommended) >= 1
    assert len(community) >= 1
    
    # Verify the test sources are properly categorized
    recommended_names = [s["name"] for s in recommended]
    community_names = [s["name"] for s in community]
    assert "Recommended Source" in recommended_names
    assert "Community Source" in community_names
    

def test_sources_list_includes_is_recommended(client, auth_token, test_sources):
    """Test that /sources endpoint includes is_recommended."""
    response = client.get(
        "/sources",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    
    data = response.json()
    # The /sources endpoint returns a list directly
    sources = data if isinstance(data, list) else data.get("sources", [])
    
    assert len(sources) >= 2
    for source in sources:
        assert "is_recommended" in source
        assert isinstance(source["is_recommended"], bool)


def test_create_source_from_url_invalid_url(client, auth_token):
    """Test that from-url endpoint properly rejects invalid URLs."""
    response = client.post(
        "/sources/from-url",
        json={"article_url": "not-a-valid-url"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    # Should fail with 400 or 422 for invalid URL
    assert response.status_code in [400, 422]


def test_default_recommended_value_for_new_source(session: Session):
    """Test that new sources default to is_recommended=False."""
    new_source = Source(
        name="New Source",
        url="https://new.com",
        rss_feed_url="https://new.com/rss"
    )
    session.add(new_source)
    session.commit()
    session.refresh(new_source)
    
    # Default should be False for new sources
    assert new_source.is_recommended == False
