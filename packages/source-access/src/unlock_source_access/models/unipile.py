"""Typed models for Unipile API responses.

Unipile provides a unified API for LinkedIn, Instagram, and Gmail. These
models capture the raw analytics data points — engagement rate and other
derived metrics are calculated downstream by the Transform Engine.
"""

from datetime import datetime

from pydantic import BaseModel


class UnipileAttachment(BaseModel):
    """File or media attachment on a post or email."""

    id: str = ""
    filename: str = ""
    mime_type: str = ""
    size: int = 0
    url: str = ""


class UnipilePost(BaseModel):
    """A LinkedIn or Instagram post with raw engagement metrics.

    The provider field distinguishes platform ("LINKEDIN" or "INSTAGRAM").
    Metrics are raw counts — engagement rate is derived downstream.
    """

    id: str
    provider: str = ""
    account_id: str = ""
    text: str = ""
    created_at: datetime | None = None
    url: str = ""
    likes: int = 0
    comments: int = 0
    shares: int = 0
    impressions: int = 0
    reach: int = 0
    attachments: list[UnipileAttachment] = []


class UnipileEmail(BaseModel):
    """An email message from the Gmail connector."""

    id: str
    account_id: str = ""
    subject: str = ""
    from_address: str = ""
    to_addresses: list[str] = []
    cc_addresses: list[str] = []
    date: datetime | None = None
    body_plain: str = ""
    body_html: str = ""
    is_read: bool = False
    folder: str = ""
    attachments: list[UnipileAttachment] = []
