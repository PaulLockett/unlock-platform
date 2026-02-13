"""Typed Pydantic models for each connector's API responses.

These models are internal to source-access but importable by the Transform
Engine for validation. At the Temporal activity boundary we use list[dict],
but these models let downstream code parse and validate records with full
type safety.
"""

from unlock_source_access.models.posthog import (
    PostHogEvent,
    PostHogPerson,
    PostHogQueryResult,
)
from unlock_source_access.models.rb2b import (
    RB2BCompany,
    RB2BPerson,
    RB2BWebhookPayload,
)
from unlock_source_access.models.unipile import (
    UnipileAttachment,
    UnipileEmail,
    UnipilePost,
)
from unlock_source_access.models.x import (
    XPaginationMeta,
    XTweet,
    XTweetMetrics,
    XUser,
)

__all__ = [
    "PostHogEvent",
    "PostHogPerson",
    "PostHogQueryResult",
    "RB2BCompany",
    "RB2BPerson",
    "RB2BWebhookPayload",
    "UnipileAttachment",
    "UnipileEmail",
    "UnipilePost",
    "XPaginationMeta",
    "XTweet",
    "XTweetMetrics",
    "XUser",
]
