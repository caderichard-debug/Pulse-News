"""
Weekly challenge API and service tests, written against the real schema:

WeeklyChallenge (week_start_date datetime, is_published) -> ChallengeClaim
UserChallengeResponse (selected_claim_id, responded_at, status)
ChallengeArticleAssignment (user_challenge_response_id, day_number, opposition_strength)
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import (
    AgreementLevel,
    Article,
    ArticleAnalysis,
    ChallengeArticleAssignment,
    ChallengeClaim,
    ChallengeClaimType,
    ChallengeResponseStatus,
    PoliticalLean,
    ProcessingStatus,
    Source,
    User,
    UserChallengeResponse,
    WeeklyChallenge,
)
from app.services.challenge_article_matcher import ChallengeArticleMatcher
from app.services.challenge_manager import ChallengeManager
from app.utils.auth import create_access_token


def _monday(d=None):
    d = d or datetime.utcnow().date()
    return d - timedelta(days=d.weekday())


def _make_user(session, email="challenger@example.com"):
    user = User(email=email, hashed_password="x", email_verified=True,
                challenge_participation_enabled=True)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _headers(user):
    return {"Authorization": f"Bearer {create_access_token({'sub': user.email})}"}


def _make_challenge(session, monday=None, published=True):
    monday = monday or _monday()
    start = datetime.combine(monday, datetime.min.time())
    challenge = WeeklyChallenge(
        week_start_date=start,
        week_end_date=start + timedelta(days=6),
        challenge_date=start + timedelta(days=4),
        title="Test Challenge",
        description="A challenge for testing",
        is_published=published,
    )
    session.add(challenge)
    session.commit()
    session.refresh(challenge)
    claims = []
    for i, claim_type in enumerate([ChallengeClaimType.POLICY, ChallengeClaimType.ECONOMIC,
                                    ChallengeClaimType.TECHNOLOGY, ChallengeClaimType.HEALTHCARE]):
        claim = ChallengeClaim(
            weekly_challenge_id=challenge.id,
            claim_text=f"Claim {i + 1}",
            claim_type=claim_type,
            display_order=i + 1,
            controversy_score=0.5,
        )
        session.add(claim)
        claims.append(claim)
    session.commit()
    for c in claims:
        session.refresh(c)
    return challenge, claims


def _make_articles(session, n=3):
    source = Source(name="S", url="https://s.example.com", rss_feed_url="https://s.example.com/rss")
    session.add(source)
    session.commit()
    articles = []
    for i in range(n):
        a = Article(source_id=source.id, title=f"A{i}", url=f"https://s.example.com/{i}",
                    published_at=datetime.utcnow(), processing_status=ProcessingStatus.COMPLETED,
                    word_count=500, content_text="x")
        session.add(a)
        session.flush()
        session.add(ArticleAnalysis(article_id=a.id, summary="s", sentiment_score=-5,
                                    political_lean=PoliticalLean.LEFT))
        articles.append(a)
    session.commit()
    return articles


def _respond(client, user, monday, claim, level="agree"):
    return client.post(
        f"/challenge/{monday.isoformat()}/respond",
        headers=_headers(user),
        json={"selected_claim_id": claim.id, "agreement_level": level},
    )


class TestChallengeManager:
    def test_finds_challenge_by_any_day_of_week(self, session: Session):
        challenge, _ = _make_challenge(session)
        manager = ChallengeManager(session)
        wednesday = datetime.combine(_monday() + timedelta(days=2), datetime.min.time())

        assert manager.get_current_challenge().id == challenge.id
        assert manager.get_challenge_by_date(wednesday).id == challenge.id

    def test_unpublished_challenge_is_hidden(self, session: Session):
        _make_challenge(session, published=False)
        assert ChallengeManager(session).get_current_challenge() is None

    def test_cannot_respond_after_week_ends(self, session: Session):
        user = _make_user(session)
        challenge, _ = _make_challenge(session, monday=_monday() - timedelta(weeks=3))
        ok, reason = ChallengeManager(session).can_user_respond_to_challenge(user.id, challenge.id)
        assert ok is False
        assert "ended" in reason


class TestChallengeEndpoints:
    def test_current_challenge(self, client: TestClient, session: Session):
        user = _make_user(session)
        challenge, claims = _make_challenge(session)

        response = client.get("/challenge/current", headers=_headers(user))

        assert response.status_code == 200
        data = response.json()
        assert data["challenge"]["id"] == challenge.id
        assert [c["claim_text"] for c in data["challenge"]["claims"]] == [c.claim_text for c in claims]
        assert data["can_respond"] is True
        assert data["user_response"] is None

    def test_current_challenge_none(self, client: TestClient, session: Session):
        user = _make_user(session)
        response = client.get("/challenge/current", headers=_headers(user))
        assert response.status_code == 200
        assert response.json()["challenge"] is None

    def test_challenge_by_date_and_bad_date(self, client: TestClient, session: Session):
        user = _make_user(session)
        challenge, _ = _make_challenge(session)

        ok = client.get(f"/challenge/{_monday().isoformat()}", headers=_headers(user))
        assert ok.status_code == 200
        assert client.get("/challenge/not-a-date", headers=_headers(user)).status_code == 400

    def test_requires_auth(self, client: TestClient):
        assert client.get("/challenge/current").status_code == 403

    def test_respond_persists_response_without_opposing_articles(self, client: TestClient, session: Session):
        """With no matching articles the response must still be saved (it used to be rolled back)."""
        user = _make_user(session)
        challenge, claims = _make_challenge(session)

        response = _respond(client, user, _monday(), claims[1])

        assert response.status_code == 200, response.text
        assert response.json()["articles_assigned"] == 0
        saved = session.exec(select(UserChallengeResponse)).one()
        assert saved.user_id == user.id
        assert saved.selected_claim_id == claims[1].id
        assert saved.status == ChallengeResponseStatus.RESPONDED
        assert saved.agreement_level == AgreementLevel.AGREE

    def test_respond_creates_seven_daily_assignments(self, client: TestClient, session: Session):
        user = _make_user(session)
        _, claims = _make_challenge(session)
        articles = _make_articles(session, 3)

        with patch.object(ChallengeArticleMatcher, "_find_opposing_articles", return_value=articles):
            response = _respond(client, user, _monday(), claims[0])

        assert response.status_code == 200, response.text
        assert response.json()["articles_assigned"] == 7
        assignments = session.exec(
            select(ChallengeArticleAssignment).order_by(ChallengeArticleAssignment.day_number)
        ).all()
        assert [a.day_number for a in assignments] == list(range(1, 8))
        assert {a.article_id for a in assignments} == {a.id for a in articles}

    def test_cannot_respond_twice(self, client: TestClient, session: Session):
        user = _make_user(session)
        _, claims = _make_challenge(session)
        assert _respond(client, user, _monday(), claims[0]).status_code == 200

        second = _respond(client, user, _monday(), claims[1])

        assert second.status_code == 400
        assert len(session.exec(select(UserChallengeResponse)).all()) == 1

    def test_claim_must_belong_to_challenge(self, client: TestClient, session: Session):
        user = _make_user(session)
        _make_challenge(session)
        _, other_claims = _make_challenge(session, monday=_monday() + timedelta(weeks=1))

        response = _respond(client, user, _monday(), other_claims[0])

        assert response.status_code == 400

    def test_my_responses_and_statistics(self, client: TestClient, session: Session):
        user = _make_user(session)
        _, claims = _make_challenge(session)
        _respond(client, user, _monday(), claims[0], level="strongly_agree")

        mine = client.get("/challenge/my-responses", headers=_headers(user))
        assert mine.status_code == 200, mine.text
        assert len(mine.json()) == 1

        stats = client.get("/challenge/statistics", headers=_headers(user))
        assert stats.status_code == 200, stats.text
        assert stats.json()["total_participated"] == 1
        assert stats.json()["current_week_responded"] is True

    def test_assignments_are_scoped_to_caller(self, client: TestClient, session: Session):
        owner = _make_user(session, "owner@example.com")
        snoop = _make_user(session, "snoop@example.com")
        _, claims = _make_challenge(session)
        articles = _make_articles(session, 2)
        with patch.object(ChallengeArticleMatcher, "_find_opposing_articles", return_value=articles):
            response_id = _respond(client, owner, _monday(), claims[0]).json()["response_id"]

        own = client.get(f"/challenge/assignments?response_id={response_id}", headers=_headers(owner))
        other = client.get(f"/challenge/assignments?response_id={response_id}", headers=_headers(snoop))

        assert own.status_code == 200, own.text
        assert len(own.json()) == 7
        assert other.status_code == 200
        assert other.json() == []

    def test_responses_and_analytics_endpoints(self, client: TestClient, session: Session):
        user = _make_user(session)
        _, claims = _make_challenge(session)
        _respond(client, user, _monday(), claims[0])

        for path in ("/challenge/responses", "/challenge/analytics", "/challenge/analytics/trends"):
            response = client.get(path, headers=_headers(user))
            assert response.status_code == 200, f"{path}: {response.text}"

    def test_update_assignment_marks_clicked_and_enforces_ownership(self, client: TestClient, session: Session):
        owner = _make_user(session, "owner2@example.com")
        other = _make_user(session, "other2@example.com")
        _, claims = _make_challenge(session)
        articles = _make_articles(session, 1)
        with patch.object(ChallengeArticleMatcher, "_find_opposing_articles", return_value=articles):
            _respond(client, owner, _monday(), claims[0])
        assignment = session.exec(select(ChallengeArticleAssignment)).first()

        denied = client.put(f"/challenge/assignments/{assignment.id}",
                            headers=_headers(other), json={"is_completed": True})
        assert denied.status_code == 404

        ok = client.put(f"/challenge/assignments/{assignment.id}",
                        headers=_headers(owner), json={"is_completed": True})
        assert ok.status_code == 200, ok.text
        session.refresh(assignment)
        assert assignment.is_clicked is True
        assert assignment.clicked_at is not None
