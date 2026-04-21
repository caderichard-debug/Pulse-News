import pytest
import jwt

from app.utils.newsletter_token import create_newsletter_token, decode_newsletter_token


def test_newsletter_token_round_trip():
    token = create_newsletter_token(42, "unsubscribe")
    data = decode_newsletter_token(token)
    assert data["uid"] == 42
    assert data["pur"] == "unsubscribe"


def test_newsletter_token_wrong_secret():
    token = create_newsletter_token(1, "preferences")
    with pytest.raises(jwt.PyJWTError):
        jwt.decode(
            token,
            "wrong-secret-key",
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "uid", "pur"]},
        )
