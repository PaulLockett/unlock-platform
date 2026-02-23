"""Tests for Supabase JWT verification."""

from __future__ import annotations

import time

import jwt as pyjwt
import pytest
from unlock_auth.jwt import get_user_id, verify_token
from unlock_shared.auth_models import AuthUser

SECRET = "super-secret-jwt-token-for-testing-only"


def _make_token(
    sub: str = "user-123",
    email: str = "test@example.com",
    role: str = "authenticated",
    exp: int | None = None,
    secret: str = SECRET,
    **extra: object,
) -> str:
    """Helper — build a signed JWT with Supabase-shaped claims."""
    payload: dict[str, object] = {
        "sub": sub,
        "email": email,
        "role": role,
        "exp": exp or int(time.time()) + 3600,
        "aud": "authenticated",
        **extra,
    }
    return pyjwt.encode(payload, secret, algorithm="HS256")


class TestVerifyToken:
    def test_valid_token(self) -> None:
        token = _make_token()
        user = verify_token(token, SECRET)

        assert isinstance(user, AuthUser)
        assert user.user_id == "user-123"
        assert user.email == "test@example.com"
        assert user.role == "authenticated"
        assert user.exp > time.time()

    def test_extracts_custom_role(self) -> None:
        token = _make_token(role="service_role")
        user = verify_token(token, SECRET)
        assert user.role == "service_role"

    def test_expired_token_raises(self) -> None:
        token = _make_token(exp=int(time.time()) - 60)
        with pytest.raises(pyjwt.ExpiredSignatureError):
            verify_token(token, SECRET)

    def test_invalid_signature_raises(self) -> None:
        token = _make_token(secret="wrong-secret")
        with pytest.raises(pyjwt.InvalidSignatureError):
            verify_token(token, SECRET)

    def test_missing_sub_raises(self) -> None:
        payload = {
            "email": "test@example.com",
            "role": "authenticated",
            "exp": int(time.time()) + 3600,
        }
        token = pyjwt.encode(payload, SECRET, algorithm="HS256")
        with pytest.raises(pyjwt.MissingRequiredClaimError):
            verify_token(token, SECRET)

    def test_missing_email_defaults_empty(self) -> None:
        payload = {
            "sub": "user-456",
            "aud": "authenticated",
            "role": "authenticated",
            "exp": int(time.time()) + 3600,
        }
        token = pyjwt.encode(payload, SECRET, algorithm="HS256")
        user = verify_token(token, SECRET)
        assert user.user_id == "user-456"
        assert user.email == ""

    def test_malformed_token_raises(self) -> None:
        with pytest.raises(pyjwt.DecodeError):
            verify_token("not.a.jwt", SECRET)


class TestGetUserId:
    def test_returns_user_id_string(self) -> None:
        token = _make_token(sub="abc-def-ghi")
        assert get_user_id(token, SECRET) == "abc-def-ghi"
