-- DATA_ACC: Civic Engagement Graph schema
-- 23 tables: 6 core + 4 person history + 1 org history + 9 junction + 3 infrastructure
-- All tables in the "unlock" schema (created by the initial migration)

-- ============================================================================
-- Utility: updated_at trigger function
-- ============================================================================

CREATE OR REPLACE FUNCTION unlock.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Infrastructure Tables (3)
-- ============================================================================

-- sources: Registered data sources
CREATE TABLE unlock.sources (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_key      TEXT UNIQUE NOT NULL,
    source_type     TEXT NOT NULL,
    display_name    TEXT NOT NULL,
    base_url        TEXT,
    auth_env_var    TEXT,
    account_id      TEXT,
    project_id      TEXT,
    rate_limit_per_second FLOAT DEFAULT 5.0,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_sources_updated_at
    BEFORE UPDATE ON unlock.sources
    FOR EACH ROW EXECUTE FUNCTION unlock.set_updated_at();

-- pipeline_runs: Tracks each ingestion execution for audit/lineage
CREATE TABLE unlock.pipeline_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id       UUID NOT NULL REFERENCES unlock.sources(id),
    workflow_run_id TEXT,
    status          TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    resource_type   TEXT,
    record_count    INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    error_message   TEXT,
    duration_seconds FLOAT,
    pages_fetched   INTEGER,
    started_at      TIMESTAMPTZ DEFAULT now(),
    completed_at    TIMESTAMPTZ
);

-- source_mappings: External ID → internal ID dedup table
CREATE TABLE unlock.source_mappings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id       UUID NOT NULL REFERENCES unlock.sources(id),
    external_id     TEXT NOT NULL,
    entity_type     TEXT NOT NULL,
    internal_id     UUID NOT NULL,
    confidence      FLOAT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE (source_id, external_id, entity_type)
);

-- ============================================================================
-- Core Entity Tables (6)
-- ============================================================================

-- people: Central identity node
CREATE TABLE unlock.people (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name        TEXT,
    primary_email       TEXT,
    title               TEXT,
    company_name        TEXT,
    industry            TEXT,
    bio                 TEXT,
    avatar_url          TEXT,
    website_url         TEXT,
    timezone            TEXT,
    preferred_language  TEXT,
    referral_source     TEXT,
    tags                TEXT[],
    first_seen_at       TIMESTAMPTZ,
    last_seen_at        TIMESTAMPTZ,
    is_active           BOOLEAN DEFAULT true,
    merged_into_id      UUID REFERENCES unlock.people(id),
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_people_updated_at
    BEFORE UPDATE ON unlock.people
    FOR EACH ROW EXECUTE FUNCTION unlock.set_updated_at();

-- organizations: Companies, nonprofits, communities, government agencies
CREATE TABLE unlock.organizations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                TEXT NOT NULL,
    organization_type   TEXT NOT NULL,
    domain              TEXT,
    industry            TEXT,
    description         TEXT,
    mission_statement   TEXT,
    employee_count      INTEGER,
    revenue_range       TEXT,
    phone               TEXT,
    email               TEXT,
    website_url         TEXT,
    linkedin_url        TEXT,
    founded_year        INTEGER,
    tags                TEXT[],
    is_active           BOOLEAN DEFAULT true,
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_organizations_updated_at
    BEFORE UPDATE ON unlock.organizations
    FOR EACH ROW EXECUTE FUNCTION unlock.set_updated_at();

-- channels: Communication/platform channels
CREATE TABLE unlock.channels (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_key     TEXT UNIQUE NOT NULL,
    display_name    TEXT NOT NULL,
    channel_type    TEXT NOT NULL,
    base_url        TEXT,
    icon_url        TEXT,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- content: Any created content
CREATE TABLE unlock.content (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id              UUID NOT NULL REFERENCES unlock.channels(id),
    creator_id              UUID REFERENCES unlock.people(id),
    source_id               UUID REFERENCES unlock.sources(id),
    pipeline_run_id         UUID REFERENCES unlock.pipeline_runs(id),
    content_type            TEXT NOT NULL,
    title                   TEXT,
    body                    TEXT,
    url                     TEXT,
    published_at            TIMESTAMPTZ,
    language                TEXT,
    is_public               BOOLEAN DEFAULT true,
    media_type              TEXT,
    thumbnail_url           TEXT,
    word_count              INTEGER,
    conversation_thread_id  TEXT,
    in_reply_to_id          UUID REFERENCES unlock.content(id),
    like_count              INTEGER DEFAULT 0,
    comment_count           INTEGER DEFAULT 0,
    share_count             INTEGER DEFAULT 0,
    view_count              INTEGER DEFAULT 0,
    impression_count        INTEGER DEFAULT 0,
    reach_count             INTEGER DEFAULT 0,
    bookmark_count          INTEGER DEFAULT 0,
    retweet_count           INTEGER DEFAULT 0,
    reply_count             INTEGER DEFAULT 0,
    quote_count             INTEGER DEFAULT 0,
    tags                    TEXT[],
    created_at              TIMESTAMPTZ DEFAULT now(),
    updated_at              TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_content_updated_at
    BEFORE UPDATE ON unlock.content
    FOR EACH ROW EXECUTE FUNCTION unlock.set_updated_at();

-- events: Meetings, courses, workshops, rallies, webinars
CREATE TABLE unlock.events (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organizer_id        UUID REFERENCES unlock.organizations(id),
    event_type          TEXT NOT NULL,
    title               TEXT NOT NULL,
    description         TEXT,
    venue_name          TEXT,
    city                TEXT,
    state               TEXT,
    country             TEXT,
    zip_code            TEXT,
    event_format        TEXT,
    url                 TEXT,
    registration_url    TEXT,
    recording_url       TEXT,
    starts_at           TIMESTAMPTZ,
    ends_at             TIMESTAMPTZ,
    max_capacity        INTEGER,
    actual_attendance   INTEGER,
    is_free             BOOLEAN DEFAULT true,
    cost_amount         DECIMAL(10,2),
    cost_currency       TEXT DEFAULT 'USD',
    is_external         BOOLEAN DEFAULT false,
    tags                TEXT[],
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_events_updated_at
    BEFORE UPDATE ON unlock.events
    FOR EACH ROW EXECUTE FUNCTION unlock.set_updated_at();

-- campaigns: Organized efforts with goals and timelines
CREATE TABLE unlock.campaigns (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                TEXT NOT NULL,
    description         TEXT,
    goal                TEXT,
    campaign_type       TEXT,
    status              TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('draft', 'active', 'paused', 'completed', 'archived')),
    target_audience     TEXT,
    budget_amount       DECIMAL(10,2),
    budget_currency     TEXT DEFAULT 'USD',
    outcome_summary     TEXT,
    starts_at           TIMESTAMPTZ,
    ends_at             TIMESTAMPTZ,
    tags                TEXT[],
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_campaigns_updated_at
    BEFORE UPDATE ON unlock.campaigns
    FOR EACH ROW EXECUTE FUNCTION unlock.set_updated_at();

-- ============================================================================
-- Person History Tables (4)
-- ============================================================================

-- person_names: Full name history across platforms and time
CREATE TABLE unlock.person_names (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id       UUID NOT NULL REFERENCES unlock.people(id),
    first_name      TEXT,
    last_name       TEXT,
    display_name    TEXT,
    name_type       TEXT,
    source_id       UUID REFERENCES unlock.sources(id),
    channel_id      UUID REFERENCES unlock.channels(id),
    is_current      BOOLEAN DEFAULT true,
    observed_at     TIMESTAMPTZ DEFAULT now(),
    superseded_at   TIMESTAMPTZ
);

-- person_emails: Full email history
CREATE TABLE unlock.person_emails (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id       UUID NOT NULL REFERENCES unlock.people(id),
    email           TEXT NOT NULL,
    email_type      TEXT,
    is_primary      BOOLEAN DEFAULT false,
    is_verified     BOOLEAN DEFAULT false,
    source_id       UUID REFERENCES unlock.sources(id),
    channel_id      UUID REFERENCES unlock.channels(id),
    observed_at     TIMESTAMPTZ DEFAULT now(),
    superseded_at   TIMESTAMPTZ
);

-- person_phones: Full phone number history
CREATE TABLE unlock.person_phones (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id       UUID NOT NULL REFERENCES unlock.people(id),
    phone           TEXT NOT NULL,
    phone_type      TEXT,
    is_primary      BOOLEAN DEFAULT false,
    source_id       UUID REFERENCES unlock.sources(id),
    observed_at     TIMESTAMPTZ DEFAULT now(),
    superseded_at   TIMESTAMPTZ
);

-- person_locations: Full location history
CREATE TABLE unlock.person_locations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id       UUID NOT NULL REFERENCES unlock.people(id),
    city            TEXT,
    state           TEXT,
    country         TEXT,
    zip_code        TEXT,
    location_type   TEXT,
    is_current      BOOLEAN DEFAULT true,
    source_id       UUID REFERENCES unlock.sources(id),
    observed_at     TIMESTAMPTZ DEFAULT now(),
    superseded_at   TIMESTAMPTZ
);

-- ============================================================================
-- Organization History Tables (1)
-- ============================================================================

-- organization_locations: Full location history for organizations
CREATE TABLE unlock.organization_locations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES unlock.organizations(id),
    city                TEXT,
    state               TEXT,
    country             TEXT,
    zip_code            TEXT,
    location_type       TEXT,
    is_current          BOOLEAN DEFAULT true,
    source_id           UUID REFERENCES unlock.sources(id),
    observed_at         TIMESTAMPTZ DEFAULT now(),
    superseded_at       TIMESTAMPTZ
);

-- ============================================================================
-- Junction / Activity Tables (9)
-- ============================================================================

-- engagements: Person + content interaction (highest volume table)
CREATE TABLE unlock.engagements (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id           UUID NOT NULL REFERENCES unlock.people(id),
    content_id          UUID NOT NULL REFERENCES unlock.content(id),
    channel_id          UUID NOT NULL REFERENCES unlock.channels(id),
    source_id           UUID REFERENCES unlock.sources(id),
    pipeline_run_id     UUID REFERENCES unlock.pipeline_runs(id),
    engagement_type     TEXT NOT NULL,
    occurred_at         TIMESTAMPTZ NOT NULL,
    comment_text        TEXT,
    media_url           TEXT,
    media_type          TEXT,
    reaction_type       TEXT,
    referrer_url        TEXT,
    target_url          TEXT,
    duration_seconds    INTEGER,
    device_type         TEXT,
    browser             TEXT,
    os                  TEXT,
    utm_source          TEXT,
    utm_medium          TEXT,
    utm_campaign        TEXT,
    ip_address_hash     TEXT,
    created_at          TIMESTAMPTZ DEFAULT now()
);

-- messages: Person-to-person communications (emails, DMs)
CREATE TABLE unlock.messages (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id           UUID NOT NULL REFERENCES unlock.people(id),
    channel_id          UUID NOT NULL REFERENCES unlock.channels(id),
    content_id          UUID REFERENCES unlock.content(id),
    source_id           UUID REFERENCES unlock.sources(id),
    pipeline_run_id     UUID REFERENCES unlock.pipeline_runs(id),
    subject             TEXT,
    body_plain          TEXT,
    body_html           TEXT,
    sent_at             TIMESTAMPTZ NOT NULL,
    is_read             BOOLEAN,
    thread_id           TEXT,
    in_reply_to_id      UUID REFERENCES unlock.messages(id),
    folder              TEXT,
    labels              TEXT[],
    is_automated        BOOLEAN DEFAULT false,
    created_at          TIMESTAMPTZ DEFAULT now()
);

-- message_recipients: Many-to-many for messages
CREATE TABLE unlock.message_recipients (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id          UUID NOT NULL REFERENCES unlock.messages(id) ON DELETE CASCADE,
    person_id           UUID NOT NULL REFERENCES unlock.people(id),
    recipient_type      TEXT NOT NULL DEFAULT 'to' CHECK (recipient_type IN ('to', 'cc', 'bcc')),
    UNIQUE (message_id, person_id, recipient_type)
);

-- event_participations: Person + event with participation semantics
CREATE TABLE unlock.event_participations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id           UUID NOT NULL REFERENCES unlock.people(id),
    event_id            UUID NOT NULL REFERENCES unlock.events(id),
    source_id           UUID REFERENCES unlock.sources(id),
    participation_type  TEXT NOT NULL,
    registered_at       TIMESTAMPTZ,
    attended_at         TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    feedback_score      INTEGER,
    feedback_text       TEXT,
    certificate_url     TEXT,
    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT now(),
    UNIQUE (person_id, event_id, participation_type)
);

-- memberships: Person + organization affiliation
CREATE TABLE unlock.memberships (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id           UUID NOT NULL REFERENCES unlock.people(id),
    organization_id     UUID NOT NULL REFERENCES unlock.organizations(id),
    source_id           UUID REFERENCES unlock.sources(id),
    role                TEXT,
    department          TEXT,
    started_at          TIMESTAMPTZ,
    ended_at            TIMESTAMPTZ,
    is_active           BOOLEAN DEFAULT true,
    notes               TEXT,
    tags                TEXT[],
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER trg_memberships_updated_at
    BEFORE UPDATE ON unlock.memberships
    FOR EACH ROW EXECUTE FUNCTION unlock.set_updated_at();

-- channel_identities: Platform identities for a person
CREATE TABLE unlock.channel_identities (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id           UUID NOT NULL REFERENCES unlock.people(id),
    channel_id          UUID NOT NULL REFERENCES unlock.channels(id),
    platform_user_id    TEXT,
    username            TEXT,
    profile_url         TEXT,
    display_name        TEXT,
    is_verified         BOOLEAN DEFAULT false,
    is_connected        BOOLEAN DEFAULT false,
    followers_count     INTEGER,
    following_count     INTEGER,
    post_count          INTEGER,
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now(),
    UNIQUE (channel_id, platform_user_id)
);

CREATE TRIGGER trg_channel_identities_updated_at
    BEFORE UPDATE ON unlock.channel_identities
    FOR EACH ROW EXECUTE FUNCTION unlock.set_updated_at();

-- campaign_content: Which content belongs to which campaign
CREATE TABLE unlock.campaign_content (
    campaign_id     UUID NOT NULL REFERENCES unlock.campaigns(id),
    content_id      UUID NOT NULL REFERENCES unlock.content(id),
    created_at      TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (campaign_id, content_id)
);

-- campaign_events: Which events are part of which campaign
CREATE TABLE unlock.campaign_events (
    campaign_id     UUID NOT NULL REFERENCES unlock.campaigns(id),
    event_id        UUID NOT NULL REFERENCES unlock.events(id),
    created_at      TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (campaign_id, event_id)
);

-- content_attachments: Normalized attachment storage
CREATE TABLE unlock.content_attachments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id          UUID NOT NULL REFERENCES unlock.content(id),
    attachment_type     TEXT NOT NULL,
    filename            TEXT,
    mime_type           TEXT,
    size_bytes          BIGINT,
    url                 TEXT NOT NULL,
    storage_path        TEXT,
    thumbnail_url       TEXT,
    alt_text            TEXT,
    duration_seconds    INTEGER,
    width               INTEGER,
    height              INTEGER,
    created_at          TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- Indexes
-- ============================================================================

-- Contact Journey (person timeline across all tables)
CREATE INDEX idx_engagements_person_time ON unlock.engagements(person_id, occurred_at);
CREATE INDEX idx_messages_sender_time ON unlock.messages(sender_id, sent_at);
CREATE INDEX idx_message_recipients_person ON unlock.message_recipients(person_id);
CREATE INDEX idx_participations_person_time ON unlock.event_participations(person_id, registered_at);
CREATE INDEX idx_memberships_person_time ON unlock.memberships(person_id, started_at);
CREATE INDEX idx_content_creator_time ON unlock.content(creator_id, published_at);

-- Person History (temporal profile reconstruction)
CREATE INDEX idx_person_names_lookup ON unlock.person_names(person_id, is_current);
CREATE INDEX idx_person_names_temporal ON unlock.person_names(person_id, observed_at);
CREATE INDEX idx_person_emails_lookup ON unlock.person_emails(person_id, is_primary);
CREATE INDEX idx_person_emails_temporal ON unlock.person_emails(person_id, observed_at);
CREATE INDEX idx_person_emails_address ON unlock.person_emails(email);
CREATE INDEX idx_person_phones_lookup ON unlock.person_phones(person_id, is_primary);
CREATE INDEX idx_person_locations_lookup ON unlock.person_locations(person_id, is_current);
CREATE INDEX idx_person_locations_temporal ON unlock.person_locations(person_id, observed_at);

-- Correlation Analysis (org changes → participation impact)
CREATE INDEX idx_org_locations_lookup ON unlock.organization_locations(organization_id, is_current);
CREATE INDEX idx_org_locations_temporal ON unlock.organization_locations(organization_id, observed_at);
CREATE INDEX idx_events_organizer_time ON unlock.events(organizer_id, starts_at);
CREATE INDEX idx_participations_event ON unlock.event_participations(event_id);

-- Content & Engagement Performance
CREATE INDEX idx_engagements_content ON unlock.engagements(content_id, engagement_type);
CREATE INDEX idx_engagements_channel_time ON unlock.engagements(channel_id, occurred_at);
CREATE INDEX idx_engagements_type_time ON unlock.engagements(engagement_type, occurred_at);
CREATE INDEX idx_content_channel_time ON unlock.content(channel_id, published_at);
CREATE INDEX idx_content_type_time ON unlock.content(content_type, published_at);

-- Identity Resolution
CREATE INDEX idx_channel_identities_person ON unlock.channel_identities(person_id);
CREATE INDEX idx_people_email ON unlock.people(primary_email) WHERE primary_email IS NOT NULL;

-- Tag-Based Filtering (GIN)
CREATE INDEX idx_people_tags_gin ON unlock.people USING GIN(tags);
CREATE INDEX idx_organizations_tags_gin ON unlock.organizations USING GIN(tags);
CREATE INDEX idx_events_tags_gin ON unlock.events USING GIN(tags);
CREATE INDEX idx_content_tags_gin ON unlock.content USING GIN(tags);
CREATE INDEX idx_campaigns_tags_gin ON unlock.campaigns USING GIN(tags);

-- High-Volume Partial Index
CREATE INDEX idx_engagements_views ON unlock.engagements(occurred_at) WHERE engagement_type = 'view';

-- ============================================================================
-- Seed Data
-- ============================================================================

-- 12 channels (including community platforms)
INSERT INTO unlock.channels (channel_key, display_name, channel_type) VALUES
    ('linkedin', 'LinkedIn', 'social'),
    ('x', 'X (Twitter)', 'social'),
    ('instagram', 'Instagram', 'social'),
    ('facebook', 'Facebook', 'social'),
    ('tiktok', 'TikTok', 'social'),
    ('email', 'Email', 'email'),
    ('website', 'Website', 'web'),
    ('youtube', 'YouTube', 'video'),
    ('discord', 'Discord', 'community'),
    ('skool', 'Skool', 'community'),
    ('slack', 'Slack', 'community'),
    ('whatsapp', 'WhatsApp', 'messaging');

-- 4 data sources
INSERT INTO unlock.sources (source_key, source_type, display_name) VALUES
    ('unipile', 'api', 'Unipile'),
    ('x', 'api', 'X.com API'),
    ('posthog', 'api', 'PostHog'),
    ('rb2b', 'api', 'RB2B');

-- Update platform version
UPDATE unlock.platform_metadata SET value = '0.2.0' WHERE key = 'platform_version';
