"""SQLAlchemy Core table definitions — Python-side mirror of the Supabase migration.

These Table objects are used by the query builder to construct typed, parameterized
SQL. They are NOT an ORM — there's no object mapping, identity map, or lazy loading.
Just typed column references that catch typos at import time instead of at query execution.

If the Supabase migration and these definitions drift, tests will catch it immediately.
"""

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

metadata = MetaData(schema="unlock")

# ============================================================================
# Infrastructure Tables
# ============================================================================

sources = Table(
    "sources",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("source_key", Text, unique=True, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("display_name", Text, nullable=False),
    Column("base_url", Text),
    Column("auth_env_var", Text),
    Column("account_id", Text),
    Column("project_id", Text),
    Column("rate_limit_per_second", Float, server_default="5.0"),
    Column("is_active", Boolean, server_default="true"),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
    Column("updated_at", DateTime(timezone=True), server_default="now()"),
)

pipeline_runs = Table(
    "pipeline_runs",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("source_id", UUID, ForeignKey("unlock.sources.id"), nullable=False),
    Column("workflow_run_id", Text),
    Column("status", Text, nullable=False),
    Column("resource_type", Text),
    Column("record_count", Integer, server_default="0"),
    Column("records_created", Integer, server_default="0"),
    Column("records_updated", Integer, server_default="0"),
    Column("records_skipped", Integer, server_default="0"),
    Column("error_message", Text),
    Column("duration_seconds", Float),
    Column("pages_fetched", Integer),
    Column("started_at", DateTime(timezone=True), server_default="now()"),
    Column("completed_at", DateTime(timezone=True)),
)

source_mappings = Table(
    "source_mappings",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("source_id", UUID, ForeignKey("unlock.sources.id"), nullable=False),
    Column("external_id", Text, nullable=False),
    Column("entity_type", Text, nullable=False),
    Column("internal_id", UUID, nullable=False),
    Column("confidence", Float),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
    UniqueConstraint("source_id", "external_id", "entity_type"),
)

# ============================================================================
# Core Entity Tables
# ============================================================================

people = Table(
    "people",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("display_name", Text),
    Column("primary_email", Text),
    Column("title", Text),
    Column("company_name", Text),
    Column("industry", Text),
    Column("bio", Text),
    Column("avatar_url", Text),
    Column("website_url", Text),
    Column("timezone", Text),
    Column("preferred_language", Text),
    Column("referral_source", Text),
    Column("tags", ARRAY(Text)),
    Column("first_seen_at", DateTime(timezone=True)),
    Column("last_seen_at", DateTime(timezone=True)),
    Column("is_active", Boolean, server_default="true"),
    Column("merged_into_id", UUID, ForeignKey("unlock.people.id")),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
    Column("updated_at", DateTime(timezone=True), server_default="now()"),
)

organizations = Table(
    "organizations",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("name", Text, nullable=False),
    Column("organization_type", Text, nullable=False),
    Column("domain", Text),
    Column("industry", Text),
    Column("description", Text),
    Column("mission_statement", Text),
    Column("employee_count", Integer),
    Column("revenue_range", Text),
    Column("phone", Text),
    Column("email", Text),
    Column("website_url", Text),
    Column("linkedin_url", Text),
    Column("founded_year", Integer),
    Column("tags", ARRAY(Text)),
    Column("is_active", Boolean, server_default="true"),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
    Column("updated_at", DateTime(timezone=True), server_default="now()"),
)

channels = Table(
    "channels",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("channel_key", Text, unique=True, nullable=False),
    Column("display_name", Text, nullable=False),
    Column("channel_type", Text, nullable=False),
    Column("base_url", Text),
    Column("icon_url", Text),
    Column("is_active", Boolean, server_default="true"),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
)

content = Table(
    "content",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("channel_id", UUID, ForeignKey("unlock.channels.id"), nullable=False),
    Column("creator_id", UUID, ForeignKey("unlock.people.id")),
    Column("source_id", UUID, ForeignKey("unlock.sources.id")),
    Column("pipeline_run_id", UUID, ForeignKey("unlock.pipeline_runs.id")),
    Column("content_type", Text, nullable=False),
    Column("title", Text),
    Column("body", Text),
    Column("url", Text),
    Column("published_at", DateTime(timezone=True)),
    Column("language", Text),
    Column("is_public", Boolean, server_default="true"),
    Column("media_type", Text),
    Column("thumbnail_url", Text),
    Column("word_count", Integer),
    Column("conversation_thread_id", Text),
    Column("in_reply_to_id", UUID, ForeignKey("unlock.content.id")),
    Column("like_count", Integer, server_default="0"),
    Column("comment_count", Integer, server_default="0"),
    Column("share_count", Integer, server_default="0"),
    Column("view_count", Integer, server_default="0"),
    Column("impression_count", Integer, server_default="0"),
    Column("reach_count", Integer, server_default="0"),
    Column("bookmark_count", Integer, server_default="0"),
    Column("retweet_count", Integer, server_default="0"),
    Column("reply_count", Integer, server_default="0"),
    Column("quote_count", Integer, server_default="0"),
    Column("tags", ARRAY(Text)),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
    Column("updated_at", DateTime(timezone=True), server_default="now()"),
)

events = Table(
    "events",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("organizer_id", UUID, ForeignKey("unlock.organizations.id")),
    Column("event_type", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text),
    Column("venue_name", Text),
    Column("city", Text),
    Column("state", Text),
    Column("country", Text),
    Column("zip_code", Text),
    Column("event_format", Text),
    Column("url", Text),
    Column("registration_url", Text),
    Column("recording_url", Text),
    Column("starts_at", DateTime(timezone=True)),
    Column("ends_at", DateTime(timezone=True)),
    Column("max_capacity", Integer),
    Column("actual_attendance", Integer),
    Column("is_free", Boolean, server_default="true"),
    Column("cost_amount", Numeric(10, 2)),
    Column("cost_currency", Text, server_default="'USD'"),
    Column("is_external", Boolean, server_default="false"),
    Column("tags", ARRAY(Text)),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
    Column("updated_at", DateTime(timezone=True), server_default="now()"),
)

campaigns = Table(
    "campaigns",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("name", Text, nullable=False),
    Column("description", Text),
    Column("goal", Text),
    Column("campaign_type", Text),
    Column("status", Text, nullable=False, server_default="'active'"),
    Column("target_audience", Text),
    Column("budget_amount", Numeric(10, 2)),
    Column("budget_currency", Text, server_default="'USD'"),
    Column("outcome_summary", Text),
    Column("starts_at", DateTime(timezone=True)),
    Column("ends_at", DateTime(timezone=True)),
    Column("tags", ARRAY(Text)),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
    Column("updated_at", DateTime(timezone=True), server_default="now()"),
)

# ============================================================================
# Person History Tables
# ============================================================================

person_names = Table(
    "person_names",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("person_id", UUID, ForeignKey("unlock.people.id"), nullable=False),
    Column("first_name", Text),
    Column("last_name", Text),
    Column("display_name", Text),
    Column("name_type", Text),
    Column("source_id", UUID, ForeignKey("unlock.sources.id")),
    Column("channel_id", UUID, ForeignKey("unlock.channels.id")),
    Column("is_current", Boolean, server_default="true"),
    Column("observed_at", DateTime(timezone=True), server_default="now()"),
    Column("superseded_at", DateTime(timezone=True)),
)

person_emails = Table(
    "person_emails",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("person_id", UUID, ForeignKey("unlock.people.id"), nullable=False),
    Column("email", Text, nullable=False),
    Column("email_type", Text),
    Column("is_primary", Boolean, server_default="false"),
    Column("is_verified", Boolean, server_default="false"),
    Column("source_id", UUID, ForeignKey("unlock.sources.id")),
    Column("channel_id", UUID, ForeignKey("unlock.channels.id")),
    Column("observed_at", DateTime(timezone=True), server_default="now()"),
    Column("superseded_at", DateTime(timezone=True)),
)

person_phones = Table(
    "person_phones",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("person_id", UUID, ForeignKey("unlock.people.id"), nullable=False),
    Column("phone", Text, nullable=False),
    Column("phone_type", Text),
    Column("is_primary", Boolean, server_default="false"),
    Column("source_id", UUID, ForeignKey("unlock.sources.id")),
    Column("observed_at", DateTime(timezone=True), server_default="now()"),
    Column("superseded_at", DateTime(timezone=True)),
)

person_locations = Table(
    "person_locations",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("person_id", UUID, ForeignKey("unlock.people.id"), nullable=False),
    Column("city", Text),
    Column("state", Text),
    Column("country", Text),
    Column("zip_code", Text),
    Column("location_type", Text),
    Column("is_current", Boolean, server_default="true"),
    Column("source_id", UUID, ForeignKey("unlock.sources.id")),
    Column("observed_at", DateTime(timezone=True), server_default="now()"),
    Column("superseded_at", DateTime(timezone=True)),
)

# ============================================================================
# Organization History Tables
# ============================================================================

organization_locations = Table(
    "organization_locations",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("organization_id", UUID, ForeignKey("unlock.organizations.id"), nullable=False),
    Column("city", Text),
    Column("state", Text),
    Column("country", Text),
    Column("zip_code", Text),
    Column("location_type", Text),
    Column("is_current", Boolean, server_default="true"),
    Column("source_id", UUID, ForeignKey("unlock.sources.id")),
    Column("observed_at", DateTime(timezone=True), server_default="now()"),
    Column("superseded_at", DateTime(timezone=True)),
)

# ============================================================================
# Junction / Activity Tables
# ============================================================================

engagements = Table(
    "engagements",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("person_id", UUID, ForeignKey("unlock.people.id"), nullable=False),
    Column("content_id", UUID, ForeignKey("unlock.content.id"), nullable=False),
    Column("channel_id", UUID, ForeignKey("unlock.channels.id"), nullable=False),
    Column("source_id", UUID, ForeignKey("unlock.sources.id")),
    Column("pipeline_run_id", UUID, ForeignKey("unlock.pipeline_runs.id")),
    Column("engagement_type", Text, nullable=False),
    Column("occurred_at", DateTime(timezone=True), nullable=False),
    Column("comment_text", Text),
    Column("media_url", Text),
    Column("media_type", Text),
    Column("reaction_type", Text),
    Column("referrer_url", Text),
    Column("target_url", Text),
    Column("duration_seconds", Integer),
    Column("device_type", Text),
    Column("browser", Text),
    Column("os", Text),
    Column("utm_source", Text),
    Column("utm_medium", Text),
    Column("utm_campaign", Text),
    Column("ip_address_hash", Text),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
)

messages = Table(
    "messages",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("sender_id", UUID, ForeignKey("unlock.people.id"), nullable=False),
    Column("channel_id", UUID, ForeignKey("unlock.channels.id"), nullable=False),
    Column("content_id", UUID, ForeignKey("unlock.content.id")),
    Column("source_id", UUID, ForeignKey("unlock.sources.id")),
    Column("pipeline_run_id", UUID, ForeignKey("unlock.pipeline_runs.id")),
    Column("subject", Text),
    Column("body_plain", Text),
    Column("body_html", Text),
    Column("sent_at", DateTime(timezone=True), nullable=False),
    Column("is_read", Boolean),
    Column("thread_id", Text),
    Column("in_reply_to_id", UUID, ForeignKey("unlock.messages.id")),
    Column("folder", Text),
    Column("labels", ARRAY(Text)),
    Column("is_automated", Boolean, server_default="false"),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
)

message_recipients = Table(
    "message_recipients",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column(
        "message_id", UUID,
        ForeignKey("unlock.messages.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("person_id", UUID, ForeignKey("unlock.people.id"), nullable=False),
    Column("recipient_type", Text, nullable=False, server_default="'to'"),
    UniqueConstraint("message_id", "person_id", "recipient_type"),
)

event_participations = Table(
    "event_participations",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("person_id", UUID, ForeignKey("unlock.people.id"), nullable=False),
    Column("event_id", UUID, ForeignKey("unlock.events.id"), nullable=False),
    Column("source_id", UUID, ForeignKey("unlock.sources.id")),
    Column("participation_type", Text, nullable=False),
    Column("registered_at", DateTime(timezone=True)),
    Column("attended_at", DateTime(timezone=True)),
    Column("completed_at", DateTime(timezone=True)),
    Column("feedback_score", Integer),
    Column("feedback_text", Text),
    Column("certificate_url", Text),
    Column("notes", Text),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
    UniqueConstraint("person_id", "event_id", "participation_type"),
)

memberships = Table(
    "memberships",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("person_id", UUID, ForeignKey("unlock.people.id"), nullable=False),
    Column("organization_id", UUID, ForeignKey("unlock.organizations.id"), nullable=False),
    Column("source_id", UUID, ForeignKey("unlock.sources.id")),
    Column("role", Text),
    Column("department", Text),
    Column("started_at", DateTime(timezone=True)),
    Column("ended_at", DateTime(timezone=True)),
    Column("is_active", Boolean, server_default="true"),
    Column("notes", Text),
    Column("tags", ARRAY(Text)),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
    Column("updated_at", DateTime(timezone=True), server_default="now()"),
)

channel_identities = Table(
    "channel_identities",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("person_id", UUID, ForeignKey("unlock.people.id"), nullable=False),
    Column("channel_id", UUID, ForeignKey("unlock.channels.id"), nullable=False),
    Column("platform_user_id", Text),
    Column("username", Text),
    Column("profile_url", Text),
    Column("display_name", Text),
    Column("is_verified", Boolean, server_default="false"),
    Column("is_connected", Boolean, server_default="false"),
    Column("followers_count", Integer),
    Column("following_count", Integer),
    Column("post_count", Integer),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
    Column("updated_at", DateTime(timezone=True), server_default="now()"),
    UniqueConstraint("channel_id", "platform_user_id"),
)

campaign_content = Table(
    "campaign_content",
    metadata,
    Column(
        "campaign_id", UUID,
        ForeignKey("unlock.campaigns.id"),
        nullable=False, primary_key=True,
    ),
    Column("content_id", UUID, ForeignKey("unlock.content.id"), nullable=False, primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
)

campaign_events = Table(
    "campaign_events",
    metadata,
    Column(
        "campaign_id", UUID,
        ForeignKey("unlock.campaigns.id"),
        nullable=False, primary_key=True,
    ),
    Column("event_id", UUID, ForeignKey("unlock.events.id"), nullable=False, primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
)

content_attachments = Table(
    "content_attachments",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("content_id", UUID, ForeignKey("unlock.content.id"), nullable=False),
    Column("attachment_type", Text, nullable=False),
    Column("filename", Text),
    Column("mime_type", Text),
    Column("size_bytes", BigInteger),
    Column("url", Text, nullable=False),
    Column("storage_path", Text),
    Column("thumbnail_url", Text),
    Column("alt_text", Text),
    Column("duration_seconds", Integer),
    Column("width", Integer),
    Column("height", Integer),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
)
