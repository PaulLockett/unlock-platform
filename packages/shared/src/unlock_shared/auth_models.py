"""Auth domain models — shared between Canvas (via JWT) and Python services."""

from pydantic import BaseModel


class AuthUser(BaseModel):
    """Decoded Supabase JWT claims."""

    user_id: str
    email: str
    role: str = "authenticated"
    exp: int
