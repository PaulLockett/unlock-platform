"""Typed models for X.com (Twitter) API v2 responses.

The X API v2 uses a flat data + includes structure. These models map the
tweet object and its public_metrics directly. Note the pay-per-use pricing:
$0.005/read tweet, $0.01/profile lookup — the connector should track usage.
"""

from datetime import datetime

from pydantic import BaseModel


class XTweetMetrics(BaseModel):
    """Public engagement metrics for a tweet."""

    retweet_count: int = 0
    reply_count: int = 0
    like_count: int = 0
    quote_count: int = 0
    bookmark_count: int = 0
    impression_count: int = 0


class XTweet(BaseModel):
    """A tweet from the X API v2."""

    id: str
    text: str = ""
    created_at: datetime | None = None
    author_id: str = ""
    conversation_id: str = ""
    public_metrics: XTweetMetrics = XTweetMetrics()
    lang: str = ""
    edit_history_tweet_ids: list[str] = []


class XUser(BaseModel):
    """A user profile from the X API v2."""

    id: str
    name: str = ""
    username: str = ""
    description: str = ""
    created_at: datetime | None = None
    public_metrics: dict[str, int] = {}
    profile_image_url: str = ""
    verified: bool = False


class XPaginationMeta(BaseModel):
    """Pagination metadata from X API v2 responses."""

    result_count: int = 0
    next_token: str | None = None
    previous_token: str | None = None
    newest_id: str | None = None
    oldest_id: str | None = None
