"""
Signed newsletter links (preferences / unsubscribe). Uses SECRET_KEY from settings.
"""

from __future__ import annotations

import time
from typing import Any, Dict

import jwt

from ..config import settings

_PURPOSES = frozenset({"preferences", "unsubscribe"})
_DEFAULT_TTL_SECONDS = 90 * 24 * 3600


def create_newsletter_token(user_id: int, purpose: str, ttl_seconds: int = _DEFAULT_TTL_SECONDS) -> str:
    if purpose not in _PURPOSES:
        raise ValueError(f"Invalid newsletter token purpose: {purpose}")
    now = int(time.time())
    payload: Dict[str, Any] = {
        "uid": user_id,
        "pur": purpose,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_newsletter_token(token: str) -> Dict[str, Any]:
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=["HS256"],
        options={"require": ["exp", "iat", "uid", "pur"]},
    )
