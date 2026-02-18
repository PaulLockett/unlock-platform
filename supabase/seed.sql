-- Seed data for local development and Supabase preview branches.
-- Applied after migrations when running `supabase db reset`.

INSERT INTO unlock.platform_metadata (key, value)
VALUES ('environment', 'local')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
