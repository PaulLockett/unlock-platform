"""Supabase JWT verification for Python services.

Temporal workers and API endpoints use this to extract the authenticated user
from a Supabase access token. This is a library function — Auth has no task
queue and no worker process.
"""

from __future__ import annotations

import jwt as pyjwt
from unlock_shared.auth_models import AuthUser


def verify_token(token: str, jwt_secret: str) -> AuthUser:
    """Decode and validate a Supabase JWT.

    Args:
        token: The raw JWT string (from the Authorization header or cookie).
        jwt_secret: The Supabase JWT secret (Settings → API → JWT Secret).

    Returns:
        AuthUser with user_id, email, role, and expiry.

    Raises:
        pyjwt.ExpiredSignatureError: Token has expired.
        pyjwt.InvalidSignatureError: Signature doesn't match the secret.
        pyjwt.DecodeError: Malformed token.
        KeyError: Required claims (sub, email) missing from payload.
    """
    payload = pyjwt.decode(
        token,
        jwt_secret,
        algorithms=["HS256"],
        audience="authenticated",
        options={"require": ["exp", "sub"]},
    )

    return AuthUser(
        user_id=payload["sub"],
        email=payload.get("email", ""),
        role=payload.get("role", "authenticated"),
        exp=payload["exp"],
    )


def get_user_id(token: str, jwt_secret: str) -> str:
    """Convenience wrapper — returns just the user_id string."""
    return verify_token(token, jwt_secret).user_id
