"""Data Access boundary models — the contract between Data Manager and Data Access.

These types cross the Temporal activity boundary. Workflows in the Data Manager
create them as arguments; activities in Data Access receive and return them.

Design choices:
  - Every field is explicitly typed — no dict/Any placeholders. The schema has
    23 tables with concrete columns, so the boundary models mirror that precision.
  - Person history records (names, emails, phones, locations) are separate models
    to support the temporal history pattern (observed_at/superseded_at).
  - Request/Result pairs follow the same pattern as source_models.py.
  - All Results extend PlatformResult for consistent success/failure handling.
"""

from datetime import datetime

from pydantic import BaseModel

from unlock_shared.models import PlatformResult

# ============================================================================
# Person History Records
# ============================================================================


class PersonName(BaseModel):
    """A name observation for a person — one entry per platform/time."""

    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None
    name_type: str | None = None  # legal, preferred, nickname, maiden, platform_specific
    source_key: str | None = None
    channel_key: str | None = None
    is_current: bool = True
    observed_at: datetime | None = None


class PersonEmail(BaseModel):
    """An email observation for a person."""

    email: str
    email_type: str | None = None  # personal, work, school, alias
    is_primary: bool = False
    is_verified: bool = False
    source_key: str | None = None
    channel_key: str | None = None
    observed_at: datetime | None = None


class PersonPhone(BaseModel):
    """A phone number observation for a person."""

    phone: str
    phone_type: str | None = None  # mobile, work, home, fax
    is_primary: bool = False
    source_key: str | None = None
    observed_at: datetime | None = None


class PersonLocation(BaseModel):
    """A location observation for a person."""

    city: str | None = None
    state: str | None = None
    country: str | None = None
    zip_code: str | None = None
    location_type: str | None = None  # home, work, mailing
    is_current: bool = True
    source_key: str | None = None
    observed_at: datetime | None = None


# ============================================================================
# Contact Identity
# ============================================================================


class ContactIdentity(BaseModel):
    """External platform identity for a person — bridges platform user IDs to people."""

    channel_key: str
    platform_user_id: str | None = None
    username: str | None = None
    profile_url: str | None = None
    display_name: str | None = None
    is_verified: bool = False
    is_connected: bool = False
    followers_count: int | None = None
    following_count: int | None = None
    post_count: int | None = None


# ============================================================================
# Activity Input Records
# ============================================================================


class ContentRecord(BaseModel):
    """A content item to catalog: post, tweet, email, video, etc."""

    channel_key: str
    content_type: str
    source_key: str | None = None
    pipeline_run_id: str | None = None
    external_id: str | None = None  # For dedup via source_mappings
    creator_platform_user_id: str | None = None  # Resolved to person internally
    title: str | None = None
    body: str | None = None
    url: str | None = None
    published_at: datetime | None = None
    language: str | None = None
    is_public: bool = True
    media_type: str | None = None
    thumbnail_url: str | None = None
    conversation_thread_id: str | None = None
    in_reply_to_external_id: str | None = None
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    view_count: int = 0
    impression_count: int = 0
    reach_count: int = 0
    bookmark_count: int = 0
    retweet_count: int = 0
    reply_count: int = 0
    quote_count: int = 0
    tags: list[str] | None = None
    attachments: list[dict[str, str | int | None]] | None = None


class EngagementRecord(BaseModel):
    """A person + content interaction to record."""

    person_external_id: str  # Resolved to person_id via source_mappings
    content_external_id: str  # Resolved to content_id via source_mappings
    channel_key: str
    source_key: str | None = None
    pipeline_run_id: str | None = None
    engagement_type: str  # like, comment, share, view, click, retweet, etc.
    occurred_at: datetime
    comment_text: str | None = None
    media_url: str | None = None
    media_type: str | None = None
    reaction_type: str | None = None
    referrer_url: str | None = None
    target_url: str | None = None
    duration_seconds: int | None = None
    device_type: str | None = None
    browser: str | None = None
    os: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    ip_address_hash: str | None = None


class CommunicationRecord(BaseModel):
    """A person-to-person message to log: email, DM."""

    sender_external_id: str  # Resolved to person_id
    channel_key: str
    source_key: str | None = None
    pipeline_run_id: str | None = None
    subject: str | None = None
    body_plain: str | None = None
    body_html: str | None = None
    sent_at: datetime
    is_read: bool | None = None
    thread_id: str | None = None
    folder: str | None = None
    labels: list[str] | None = None
    is_automated: bool = False
    recipient_ids: list[str] | None = None  # External IDs for 'to' recipients
    cc_ids: list[str] | None = None
    bcc_ids: list[str] | None = None


class ParticipationRecord(BaseModel):
    """A person + event participation to register."""

    person_external_id: str
    event_title: str  # Matched to event by title (or event_external_id)
    event_external_id: str | None = None
    source_key: str | None = None
    participation_type: str  # registered, attended, completed, cancelled, no_show, waitlisted
    registered_at: datetime | None = None
    attended_at: datetime | None = None
    completed_at: datetime | None = None
    feedback_score: int | None = None
    feedback_text: str | None = None
    certificate_url: str | None = None
    notes: str | None = None


class MembershipRecord(BaseModel):
    """A person + organization affiliation to enroll."""

    person_external_id: str
    organization_name: str
    organization_type: str = "company"
    source_key: str | None = None
    role: str | None = None  # staff, volunteer, board_member, supporter, donor, member
    department: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    is_active: bool = True
    notes: str | None = None
    tags: list[str] | None = None


# ============================================================================
# Activity Request/Result Pairs (10)
# ============================================================================


class IdentifyContactRequest(BaseModel):
    """Input for identify_contact: resolve external identity to internal person."""

    source_key: str
    external_id: str
    channel_key: str | None = None
    platform_user_id: str | None = None
    username: str | None = None
    profile_url: str | None = None
    display_name: str | None = None
    names: list[PersonName] | None = None
    emails: list[PersonEmail] | None = None
    phones: list[PersonPhone] | None = None
    locations: list[PersonLocation] | None = None
    title: str | None = None
    company_name: str | None = None
    industry: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    website_url: str | None = None
    tags: list[str] | None = None


class IdentifyContactResult(PlatformResult):
    """Result of identify_contact."""

    person_id: str = ""
    is_new: bool = False
    source_key: str = ""


class CatalogContentRequest(BaseModel):
    """Input for catalog_content: register content in the engagement graph."""

    records: list[ContentRecord]
    source_key: str


class CatalogContentResult(PlatformResult):
    """Result of catalog_content."""

    created: int = 0
    updated: int = 0
    skipped: int = 0


class RecordEngagementRequest(BaseModel):
    """Input for record_engagement: capture person+content interactions."""

    records: list[EngagementRecord]
    source_key: str


class RecordEngagementResult(PlatformResult):
    """Result of record_engagement."""

    recorded: int = 0
    skipped: int = 0


class LogCommunicationRequest(BaseModel):
    """Input for log_communication: capture person-to-person messages."""

    records: list[CommunicationRecord]
    source_key: str


class LogCommunicationResult(PlatformResult):
    """Result of log_communication."""

    logged: int = 0
    skipped: int = 0


class RegisterParticipationRequest(BaseModel):
    """Input for register_participation: record event attendance."""

    records: list[ParticipationRecord]
    source_key: str


class RegisterParticipationResult(PlatformResult):
    """Result of register_participation."""

    registered: int = 0
    updated: int = 0
    skipped: int = 0


class EnrollMemberRequest(BaseModel):
    """Input for enroll_member: record organizational affiliation."""

    records: list[MembershipRecord]
    source_key: str


class EnrollMemberResult(PlatformResult):
    """Result of enroll_member."""

    enrolled: int = 0
    updated: int = 0
    skipped: int = 0


class ProfileContactRequest(BaseModel):
    """Input for profile_contact: assemble unified contact view."""

    person_id: str | None = None
    external_id: str | None = None
    source_key: str | None = None
    email: str | None = None


class ProfileContactResult(PlatformResult):
    """Result of profile_contact: full person picture across all channels."""

    person_id: str = ""
    display_name: str | None = None
    primary_email: str | None = None
    title: str | None = None
    company_name: str | None = None
    bio: str | None = None
    names: list[dict[str, str | bool | None]] | None = None
    emails: list[dict[str, str | bool | None]] | None = None
    phones: list[dict[str, str | bool | None]] | None = None
    locations: list[dict[str, str | bool | None]] | None = None
    identities: list[dict[str, str | bool | int | None]] | None = None
    engagement_summary: dict[str, int] | None = None
    membership_summary: list[dict[str, str | bool | None]] | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    tags: list[str] | None = None


class SurveyEngagementRequest(BaseModel):
    """Input for survey_engagement: broad view of engagement data."""

    channel_key: str | None = None
    source_key: str | None = None
    engagement_type: str | None = None
    person_id: str | None = None
    content_type: str | None = None
    since: datetime | None = None
    until: datetime | None = None
    limit: int = 100
    offset: int = 0


class SurveyEngagementResult(PlatformResult):
    """Result of survey_engagement."""

    records: list[dict[str, str | int | float | bool | None]] = []
    total_count: int = 0
    has_more: bool = False


class OpenPipelineRunRequest(BaseModel):
    """Input for open_pipeline_run: start tracking ingestion execution."""

    source_key: str
    workflow_run_id: str | None = None
    resource_type: str | None = None


class OpenPipelineRunResult(PlatformResult):
    """Result of open_pipeline_run."""

    pipeline_run_id: str = ""


class ClosePipelineRunRequest(BaseModel):
    """Input for close_pipeline_run: complete ingestion tracking."""

    pipeline_run_id: str
    status: str = "completed"  # completed, failed, cancelled
    record_count: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    error_message: str | None = None
    pages_fetched: int | None = None


class ClosePipelineRunResult(PlatformResult):
    """Result of close_pipeline_run."""

    pipeline_run_id: str = ""
    duration_seconds: float | None = None
