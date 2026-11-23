"""
Tests for GET /articles/{id}/opposing-viewpoints and POST /articles/{id}/analyze-viewpoints.

The endpoint serves stored ViewpointRelationship rows; when none exist (or they lack
the enhanced how/why fields) it runs the enhanced ViewpointAnalyzer on demand.
"""

from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import (
    Article,
    ArticleAnalysis,
    OrganizationalBias,
    PoliticalLean,
    ProcessingStatus,
    Source,
    User,
    ViewpointRelationship,
)
from app.services.viewpoint_analyzer_enhanced import ViewpointAnalyzer
from app.utils.auth import create_access_token

ENDPOINT = "/articles/{}/opposing-viewpoints"


@pytest.fixture
def headers(session: Session):
    session.add(User(email="reader@example.com", hashed_password="x", email_verified=True))
    session.commit()
    return {"Authorization": f"Bearer {create_access_token({'sub': 'reader@example.com'})}"}


@pytest.fixture
def articles(session: Session):
    left = Source(name="Left Daily", url="https://left.example.com",
                  rss_feed_url="https://left.example.com/rss",
                  organizational_bias=OrganizationalBias.LEFT)
    right = Source(name="Right Times", url="https://right.example.com",
                   rss_feed_url="https://right.example.com/rss",
                   organizational_bias=OrganizationalBias.RIGHT)
    session.add_all([left, right])
    session.commit()

    def make(source, title, lean, sentiment):
        a = Article(source_id=source.id, title=title, url=f"https://x.example.com/{title}",
                    published_at=datetime(2025, 1, 1), processing_status=ProcessingStatus.COMPLETED)
        session.add(a)
        session.flush()
        session.add(ArticleAnalysis(article_id=a.id, summary=f"Summary of {title}",
                                    sentiment_score=sentiment, political_lean=lean))
        return a

    primary = make(left, "primary", PoliticalLean.LEFT, 3)
    opposing = [make(right, f"opp{i}", PoliticalLean.RIGHT, -2) for i in range(3)]
    session.commit()
    return primary, opposing


def _relationship(session, primary, opposing, strength=0.8, complete=True):
    rel = ViewpointRelationship(
        primary_article_id=primary.id,
        opposing_article_id=opposing.id,
        relationship_type="framework_opposition",
        opposition_strength=strength,
        framework_name="Liberty vs Welfare",
        primary_position=6,
        opposing_position=-5,
        how_this_opposes="How text" if complete else None,
        why_this_opposes="Why text" if complete else None,
        ai_explanation="Explanation",
        quality_score=0.7,
    )
    session.add(rel)
    session.commit()
    return rel


class TestOpposingViewpoints:
    def test_requires_auth(self, client: TestClient, articles):
        assert client.get(ENDPOINT.format(articles[0].id)).status_code == 403

    def test_missing_article_is_404(self, client: TestClient, headers):
        assert client.get(ENDPOINT.format(99999), headers=headers).status_code == 404

    def test_serves_stored_relationships_without_reanalysis(self, client, session, headers, articles):
        primary, opposing = articles
        _relationship(session, primary, opposing[0], strength=0.6)
        _relationship(session, primary, opposing[1], strength=0.9)

        with patch.object(ViewpointAnalyzer, "save_opposing_viewpoints") as analyze:
            response = client.get(ENDPOINT.format(primary.id), headers=headers)

        assert response.status_code == 200, response.text
        analyze.assert_not_called()
        data = response.json()
        assert data["primary_article_id"] == primary.id
        assert data["total_found"] == 2
        first = data["opposing_viewpoints"][0]
        # Ordered by opposition strength, enriched with article/source/analysis data
        assert first["article_id"] == opposing[1].id
        assert first["title"] == "opp1"
        assert first["source_name"] == "Right Times"
        assert first["source_bias"] == "right"
        assert first["political_lean"] == "right"
        assert first["how_this_opposes"] == "How text"
        assert first["framework_name"] == "Liberty vs Welfare"

    def test_max_results(self, client, session, headers, articles):
        primary, opposing = articles
        for o in opposing:
            _relationship(session, primary, o)

        response = client.get(ENDPOINT.format(primary.id) + "?max_results=2", headers=headers)

        assert response.json()["total_found"] == 2

    def test_runs_analysis_when_none_stored(self, client, session, headers, articles):
        primary, opposing = articles

        def fake_save(self, article, session=None, max_results=10):
            return [_relationship(session, article, opposing[2])]

        with patch.object(ViewpointAnalyzer, "save_opposing_viewpoints", fake_save):
            response = client.get(ENDPOINT.format(primary.id), headers=headers)

        assert response.status_code == 200, response.text
        assert [v["article_id"] for v in response.json()["opposing_viewpoints"]] == [opposing[2].id]

    def test_reanalyzes_when_enhanced_fields_missing(self, client, session, headers, articles):
        primary, opposing = articles
        _relationship(session, primary, opposing[0], complete=False)

        with patch.object(ViewpointAnalyzer, "save_opposing_viewpoints", return_value=[]) as analyze:
            client.get(ENDPOINT.format(primary.id), headers=headers)

        analyze.assert_called_once()

    def test_no_results_and_openai_unavailable_is_503(self, client, headers, articles):
        with patch.object(ViewpointAnalyzer, "save_opposing_viewpoints", return_value=[]), \
             patch("app.utils.openai_client.openai_client.is_available", return_value=False):
            response = client.get(ENDPOINT.format(articles[0].id), headers=headers)

        assert response.status_code == 503

    def test_no_results_is_empty_list(self, client, headers, articles):
        with patch.object(ViewpointAnalyzer, "save_opposing_viewpoints", return_value=[]), \
             patch("app.utils.openai_client.openai_client.is_available", return_value=True):
            response = client.get(ENDPOINT.format(articles[0].id), headers=headers)

        assert response.status_code == 200
        assert response.json()["opposing_viewpoints"] == []

    def test_openai_rate_limit_is_429(self, client, headers, articles):
        with patch.object(ViewpointAnalyzer, "save_opposing_viewpoints",
                          side_effect=Exception("Rate limit reached for requests")):
            response = client.get(ENDPOINT.format(articles[0].id), headers=headers)

        assert response.status_code == 429


class TestTriggerAnalysis:
    def test_triggers_background_job(self, client, headers, articles):
        with patch("app.routes.articles.analyze_single_article_viewpoints_job") as job:
            response = client.post(f"/articles/{articles[0].id}/analyze-viewpoints", headers=headers)

        assert response.status_code == 200, response.text
        assert response.json()["status"] == "triggered"
        job.assert_called_once()

    def test_missing_article_is_404(self, client, headers):
        assert client.post("/articles/99999/analyze-viewpoints", headers=headers).status_code == 404
