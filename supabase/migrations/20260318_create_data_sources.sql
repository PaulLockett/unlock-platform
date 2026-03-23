-- CANVAS: Source registry for admin UI
-- Tracks data source configurations managed through the Canvas admin interface.
-- The identify_source / register_source activities query this table via PostgREST.
--
-- Note: unlock.sources (from engagement graph migration) is the internal
-- pipeline source registry with different columns. This table serves the
-- Canvas admin's source management workflow.

CREATE TABLE public.data_sources (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT UNIQUE NOT NULL,
    protocol        TEXT NOT NULL CHECK (protocol IN (
        'rest_api', 'file_upload', 'webhook', 's3', 'database', 'smtp'
    )),
    service         TEXT DEFAULT '',
    base_url        TEXT DEFAULT '',
    auth_method     TEXT DEFAULT '',
    auth_env_var    TEXT DEFAULT '',
    resource_type   TEXT DEFAULT 'posts',
    channel_key     TEXT DEFAULT '',
    config          JSONB DEFAULT '{}'::jsonb,
    status          TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'error')),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- Auto-update updated_at on modification
CREATE TRIGGER trg_data_sources_updated_at
    BEFORE UPDATE ON public.data_sources
    FOR EACH ROW EXECUTE FUNCTION unlock.set_updated_at();

-- Index for name lookups (identify_source uses ILIKE for fuzzy matching)
CREATE INDEX idx_data_sources_name ON public.data_sources(name);
CREATE INDEX idx_data_sources_protocol ON public.data_sources(protocol);
CREATE INDEX idx_data_sources_status ON public.data_sources(status);

-- Enable RLS (Supabase best practice)
ALTER TABLE public.data_sources ENABLE ROW LEVEL SECURITY;

-- Service role can do everything (used by Railway workers via service key)
CREATE POLICY "Service role full access" ON public.data_sources
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Authenticated users can read (for Canvas admin UI)
CREATE POLICY "Authenticated users can read" ON public.data_sources
    FOR SELECT
    USING (auth.role() = 'authenticated');

-- Update platform version
UPDATE unlock.platform_metadata SET value = '0.3.0' WHERE key = 'platform_version';
