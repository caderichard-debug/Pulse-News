"""
Public newsletter action links (signed tokens from email).
"""

from __future__ import annotations

import logging

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session

from ..config import settings
from ..database import get_session
from ..models import User
from ..utils.newsletter_token import decode_newsletter_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/newsletter", tags=["newsletter"])


def _invalid_token_response() -> HTMLResponse:
    return HTMLResponse(
        content=(
            "<html><body><p>This link is invalid or has expired.</p>"
            "<p>You can still change email settings in the Pulse app.</p></body></html>"
        ),
        status_code=400,
    )


@router.get("/unsubscribe", response_class=HTMLResponse)
def newsletter_unsubscribe(
    token: str = Query(..., description="Signed token from newsletter email"),
    session: Session = Depends(get_session),
):
    try:
        data = decode_newsletter_token(token)
    except jwt.PyJWTError as e:
        logger.info("Newsletter unsubscribe: bad token: %s", e)
        return _invalid_token_response()

    if data.get("pur") != "unsubscribe":
        return _invalid_token_response()

    user = session.get(User, int(data["uid"]))
    if not user:
        return HTMLResponse(
            "<html><body><p>Account not found.</p></body></html>",
            status_code=404,
        )

    user.newsletter_enabled = False
    session.add(user)
    session.commit()

    return HTMLResponse(
        content=(
            "<html><body><p>You have been unsubscribed from Pulse newsletters.</p>"
            "<p>You can re-enable them anytime in your account preferences.</p></body></html>"
        ),
        status_code=200,
    )


@router.get("/preferences")
def newsletter_preferences_redirect(
    token: str = Query(..., description="Signed token from newsletter email"),
):
    try:
        data = decode_newsletter_token(token)
    except jwt.PyJWTError as e:
        logger.info("Newsletter preferences: bad token: %s", e)
        raise HTTPException(status_code=400, detail="Invalid or expired link") from e

    if data.get("pur") != "preferences":
        raise HTTPException(status_code=400, detail="Invalid link")

    base = settings.frontend_url.rstrip("/")
    url = f"{base}/preferences?newsletter_token={token}"
    return RedirectResponse(url=url, status_code=302)
