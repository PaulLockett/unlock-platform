-- Initial migration: creates the unlock schema and platform_metadata table.
-- This proves the migration pipeline works end-to-end (local + cloud).

-- All platform tables live in the "unlock" schema to keep them separate
-- from Supabase's built-in schemas (auth, storage, etc.).
CREATE SCHEMA IF NOT EXISTS unlock;

-- Platform metadata table: tracks infrastructure state, version info,
-- and deployment markers. Serves as the "hello world" for the DB layer.
CREATE TABLE unlock.platform_metadata (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    key         TEXT NOT NULL UNIQUE,
    value       TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed with a version marker so we can verify the migration applied.
INSERT INTO unlock.platform_metadata (key, value)
VALUES ('platform_version', '0.1.0');
