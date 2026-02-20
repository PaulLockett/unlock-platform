# Lessons Learned

Corrections and patterns captured during development.

## 2026-02-11: Temporal Cloud API key auth — do NOT use rpc_metadata

**Problem:** Temporal Cloud connection succeeded but every operation (list_workflows,
execute_workflow, worker heartbeats) returned `PermissionDenied: Request unauthorized`.

**Root cause:** Our `Client.connect()` call included `rpc_metadata={"temporal-namespace": namespace}`.
This extra gRPC metadata header interferes with API key authentication on Temporal Cloud.

**Fix:** Remove `rpc_metadata` entirely. The SDK routes to the correct namespace using just the
`namespace=` parameter when combined with `api_key=` and `tls=True`. The Temporal Cloud "Connect"
dialog's sample code confirms this — it only uses `address`, `namespace`, `api_key`, and `tls`.

**Rule:** When connecting to Temporal Cloud with API key auth, use ONLY:
```python
await Client.connect(address, namespace=ns, api_key=key, tls=True)
```
No `rpc_metadata`. The `rpc_metadata` approach is for mTLS certificate-based auth, not API keys.

## 2026-02-11: Temporal Cloud regional endpoint is region-specific

**Problem:** Initially assumed us-east-1 as default region, but the namespace was created in
ap-northeast-1 (Tokyo). Using the wrong regional endpoint gives connection errors.

**Rule:** Never hardcode a default region. Require `TEMPORAL_REGIONAL_ENDPOINT` explicitly — the
region depends on where the namespace was created and there's no API to discover it. The value
comes from the Temporal Cloud namespace "Connect" dialog.

## 2026-02-11: Commit uv.lock (not in .gitignore)

**Problem:** Docker build failed with `uv sync --frozen` because `uv.lock` was in `.gitignore`.
Railway's `railway up` respects `.gitignore`, so the lockfile was never uploaded. The Dockerfile
`COPY pyproject.toml uv.lock* ./` silently matched nothing (glob), then `--frozen` failed.

**Fix:** Remove `uv.lock` from `.gitignore` and commit it. Like `package-lock.json`, the lockfile
ensures reproducible builds across environments.

**Rule:** Always commit `uv.lock`. Use explicit `COPY pyproject.toml uv.lock ./` (no glob) in
Dockerfiles so a missing lockfile fails loudly at build time.

## 2026-02-11: Temporal activity.heartbeat() fails outside activity context

**Problem:** Connector tests called `fetch_data()` which invokes `activity.heartbeat()` inside the
pagination loop. Outside a Temporal worker, this raises "Not in activity context" and the catch-all
`except Exception` in `fetch_data` returns `success=False` even though records were fetched.

**Fix:** Wrap heartbeat in `contextlib.suppress(Exception)` — heartbeat is best-effort progress
reporting, not a correctness requirement. The pagination loop works identically with or without it.

**Rule:** Always use `contextlib.suppress` for Temporal activity context methods (heartbeat, info)
when the code may run outside a worker context (tests, scripts). Never let infrastructure-level
calls break business logic.

## 2026-02-11: pytest collects imported functions named test_*

**Problem:** `from activities import test_connection` in a test file causes pytest to collect
`test_connection` as a module-level test function and fail because it expects fixture parameters.

**Fix:** Alias the import: `from activities import test_connection as activity_test_connection`.
The alias must NOT start with `test_` or pytest will still collect it.

**Rule:** When importing production functions named `test_*` into test files, always alias them
with a non-`test_` prefix to prevent pytest collection.

## 2026-02-12: Railway GitHub integration is per-service, not per-project

**Problem:** Created 9 Railway services via `railway up` (CLI push) but assumed GitHub auto-deploy
would "just work." PR environments never triggered because Railway had no connection to GitHub.

**Root cause:** Railway connects to GitHub repos at the **service** level, not the project level.
Each service must be individually connected via `serviceConnect` GraphQL mutation or the dashboard.
The `railway up` command uploads code directly — it bypasses GitHub entirely.

**Fix:** Used Railway's GraphQL API to connect all 9 services to the GitHub repo:
```graphql
mutation { serviceConnect(id: $serviceId, input: { repo: "owner/repo", branch: "main" }) { id } }
```

**Rule:** After creating Railway services, always connect them to GitHub via `serviceConnect`. The
CLI's `railway up` is for bootstrapping/testing — production should deploy from GitHub pushes.

## 2026-02-12: Railway PR environments require PRs targeting the connected branch

**Problem:** PR #1 targeted `staging`, but services were connected to `main`. Railway only creates
PR environments for PRs against the branch a service is connected to.

**Fix:** Set up two Railway environments:
- **production** → services connected to `main` branch
- **staging** → services connected to `staging` branch (via separate deployment triggers)

PR environments are ephemeral copies created when PRs target either branch.

**Rule:** Railway's branch model maps 1:1 with environments. If you have a `feat → staging → main`
workflow, you need separate Railway environments for staging and production, each watching its branch.

## 2026-02-12: Railway deployment triggers control branch, checkSuites, and repo per environment

**Problem:** After creating a staging environment by duplicating production, all triggers pointed to
`main`. Staging services deployed from the wrong branch.

**Fix:** Use `deploymentTriggerUpdate` mutation to update each trigger's branch and enable checkSuites:
```graphql
mutation { deploymentTriggerUpdate(id: $triggerId, input: { branch: "staging", checkSuites: true }) { id } }
```

**Rule:** When duplicating a Railway environment, always update the deployment triggers on the new
environment — they inherit the source environment's branch, not the new environment's intended branch.

## 2026-02-13: Never swallow HTTP errors to fake a successful connection

**Problem:** RB2B connector's `_check_connection` caught `httpx.HTTPStatusError` and returned
`ConnectionResult(success=True, message="...status endpoint unavailable")`. This caused live API
tests to falsely pass even when the API key had no activated endpoints — the dashboard showed zero
requests with data, confirming no real work was done.

**Root cause:** A well-intentioned "fallback" for accounts without the status endpoint. But this
silently hid real failures (404 = no endpoints activated, 401 = bad auth). The base class `connect()`
already catches all exceptions and returns `success=False` — the subclass exception handler was
redundant and harmful.

**Fix:** Removed the `except httpx.HTTPStatusError` block from `_check_connection`. HTTP errors now
propagate to the base class, which properly returns `success=False` with the actual error message.

**Rule:** Connector `_check_connection` implementations must NEVER catch HTTP errors. The base class
`connect()` handles all exception-to-result conversion. If a subclass catches exceptions, it creates
a false positive that defeats the entire purpose of connection verification.

## 2026-02-13: Cost estimates for live API tests must be based on measured data

**Problem:** Initial ESVT cost estimate was "~$0.02 per full run" based on theoretical API pricing.
Actual X.com spend was $0.51 for 8 requests across development iterations — 25x higher than quoted.

**Fix:** Added `request_count` to `BaseConnector`, incremented in `_request_with_retry`. Every live
test now reports its actual request count via `_report_requests()`. Run with `pytest -s` to see.

**Rule:** Never quote cost estimates without measurement. Always track and surface actual request
counts. Cost-per-request varies by API tier, endpoint, and account plan — the only reliable number
is the one you measure.

## 2026-02-13: Distinguish external failures from code bugs in live tests

**Problem:** Paul identified that disconnected accounts (Instagram on Unipile), lack of API credits,
and non-activated endpoints should not cause test failures. But they also shouldn't be silently
ignored — tests must verify the failure is external before passing.

**Fix:** Added `EXTERNAL_FAILURE_PATTERNS` dict that maps known external failure signals (disconnected,
rate limited, 404 not found, insufficient credits) to categories. `_assert_success_or_external_failure`
either passes, skips with reason (external), or fails (internal bug).

**Rule:** Live API tests must handle three outcomes: (1) success → pass, (2) external failure →
skip with reason, (3) internal failure → fail. Never let external issues mask code bugs, and never
let code bugs be excused as external issues.

## 2026-02-12: Temporal Worker requires at least one activity or workflow

**Problem:** Registered a scheduler stub in the component registry with zero workflows and zero
activities. Temporal's `Worker.__init__` raises `ValueError: At least one activity, Nexus service,
or workflow must be specified`, causing the Railway service to crash-loop.

**Fix:** Added an early exit in the runner: if a component has no workflows and no activities, log
a clean message and return instead of constructing a Worker.

**Rule:** Stub components in the registry should be handled gracefully at runtime. Never pass empty
workflow/activity lists to `Worker()` — guard against it in the runner.

## 2026-02-13: RB2B API Partner Program is a separate product from RB2B pixel

**Problem:** Built the RB2B connector against invented endpoints (`/v1/account/status`, `/v1/visitors`)
that don't exist. Every URL at `api.rb2b.com/v1/` returns a 404 HTML page. Live tests "passed" only
because the external failure detector treated 404 as "endpoint not activated."

**Root cause:** The standard RB2B product is a website pixel (JavaScript snippet) that tracks visitors.
The RB2B **API Partner Program** is a completely separate enrichment/identity resolution API. It has:
  - Different base URL: `https://api.rb2b.com/api/v1/` (note the `/api/` prefix)
  - Different auth header: `Api-Key` (not `X-API-Key`)
  - No `/visitors` or `/account/status` endpoints
  - `GET /credits` for credit balance
  - 13 enrichment endpoints: `ip_to_hem`, `ip_to_maid`, `ip_to_company`, `hem_to_best_linkedin`,
    `hem_to_business_profile`, `hem_to_linkedin`, `hem_to_maid`, `linkedin_to_best_personal_email`,
    `linkedin_to_hashed_emails`, `linkedin_to_mobile_phone`, `linkedin_to_personal_email`,
    `linkedin_to_business_profile`, `linkedin_slug_search`
  - All enrichment endpoints are POST with specific input (IP, email/MD5, LinkedIn slug)

**Fix:** Rewrote connector with correct base URL, auth header, `/credits` connection check, and
enrichment dispatch via `resource_type` matching endpoint name. Kept file dump mode for CSV/JSON
exports from the RB2B dashboard (pixel data).

**Rule:** Never build a connector against assumed API endpoints. Always verify endpoint paths against
actual API documentation (Postman collection, OpenAPI spec, or manual probing). When an API returns
HTML on 404 instead of JSON error responses, that's a signal the endpoint doesn't exist.

## 2026-02-13: RB2B API returns score as string, not float

**Problem:** Postman docs show `"score": 0.95` (number), but the real `ip_to_hem` response returns
`"score": "0.844"` (string). Contract test caught this immediately.

**Fix:** Changed assertion from `isinstance(record["score"], (int, float))` to `float(record["score"])`
to handle both string and numeric representations.

**Rule:** Never trust example responses in API documentation for type assertions. Contract tests should
be resilient to string↔number coercion since many APIs are inconsistent about JSON types.

## 2026-02-13: Railway auto-deploys on push regardless of CI status

**Problem:** After merging staging→main, Railway immediately deploys the new code — it doesn't wait
for GitHub Actions CI to pass. If CI fails (or the code has a runtime bug CI doesn't catch), Railway
serves broken code until someone manually rolls back.

**Root cause:** Railway deployment triggers have a `checkSuites` flag that defaults to `false`. When
false, Railway deploys on any push to the connected branch. When true, Railway waits for all GitHub
check suites to pass before deploying.

**Fix:** Created `scripts/enable_check_suites.py` to query and update deployment triggers via Railway's
GraphQL API. Run once per environment: `python scripts/enable_check_suites.py --env production`.

**Rule:** After connecting Railway services to GitHub, always enable `checkSuites: true` on deployment
triggers. Without it, CI is advisory — Railway deploys regardless of test results.

## 2026-02-13: Post-deploy verification requires polling Railway's deployment status

**Problem:** GitHub Actions doesn't know when Railway finishes deploying. A smoke test that runs
immediately after the merge commit would test the *old* deployment, not the new one.

**Fix:** Created `scripts/poll_railway_deploy.py` that polls Railway's GraphQL API every 30s until
all services reach a terminal state (SUCCESS, FAILED, CRASHED). The post-deploy smoke test workflow
gates on this poller before running acceptance tests.

**Rule:** When building post-deploy verification for async deployment platforms (Railway, Vercel, etc.),
always poll for deployment completion before running health checks. Don't assume "push = deployed."

## 2026-02-14: Resource Access must NOT modify Manager workflows

**Problem:** Initial DATA_ACC plan included changes to `ingest.py` and `query.py` (Manager workflows)
to wire the new business verb activities directly.

**Root cause:** Misunderstanding of Righting Software's encapsulation of volatility. Resource Access
components encapsulate WHERE data lives. Manager components encapsulate WHAT workflows orchestrate.
If Resource Access changes force Manager changes, the volatility isn't properly encapsulated.

**Fix:** DATA_ACC exposes 10 new activities on `DATA_ACCESS_QUEUE` alongside the existing `hello_store_data`
shim. Manager workflows are untouched. When DATA_MGR is implemented (its turn on the critical path),
it will wire workflows to the new activities.

**Rule:** Resource Access components must be independently deployable. Adding new data operations should
never require modifying Manager workflow code — that's a layer boundary violation.

## 2026-02-14: Business verbs must survive storage technology change

**Problem:** Early designs used CRUD-like names (`insert_person`, `update_engagement`, `query_content`)
for Resource Access activities.

**Root cause:** Naming by implementation (SQL operations) instead of by domain intent. If we switched
from PostgreSQL to a graph database, "insert_person" stops making sense.

**Fix:** Applied the Righting Software test: "If I switched from PostgreSQL to a graph database,
would this operation name still make sense?" Final verbs: `identify_contact`, `catalog_content`,
`record_engagement`, `log_communication`, `register_participation`, `enroll_member`, `profile_contact`,
`survey_engagement`, `open_pipeline_run`, `close_pipeline_run`.

**Rule:** Resource Access activity names should be technology-agnostic business verbs. If the name
includes a storage operation (insert, update, query, select), it belongs in the implementation, not
the interface.

## 2026-02-14: SQLAlchemy Core over supabase-py for Temporal workers

**Problem:** Needed to choose between raw asyncpg, supabase-py, SQLAlchemy Core, or full ORM for
23-table schema interactions from Temporal activity workers.

**Decision:** SQLAlchemy Core + asyncpg. Typed table definitions catch column typos at import time.
Query builder prevents SQL injection. Full SQL control (ON CONFLICT, CTEs, window functions). True
async (no event loop blocking in Temporal workers). No ORM overhead (no identity map, no lazy loading).

**Rejected alternatives:**
- `supabase-py`: No async support, HTTP hop through PostgREST, limited upsert control
- Raw `asyncpg`: No column-level type safety, string-based SQL
- Full ORM: Two sources of truth with Supabase migrations, awkward for complex upserts/temporal joins

**Rule:** For Temporal workers with complex schema interactions, SQLAlchemy Core + asyncpg is the
sweet spot. Types without ORM overhead. Use Supabase migrations as the schema source of truth;
SQLAlchemy Table objects mirror it in Python.

## 2026-02-14: No JSONB placeholders — enumerate all columns explicitly

**Problem:** Temptation to use JSONB columns for "flexible" data like PostHog custom properties or
RB2B enrichment fields.

**Root cause:** JSONB hides schema — queries can't be validated at write time, no foreign keys,
no type checking, difficult to index. "Flexible" really means "I haven't designed the schema yet."

**Fix:** 23 tables with every column explicitly typed. Source-specific fields from Unipile, X,
PostHog, and RB2B mapped to normalized columns. The one case where JSONB would be unavoidable
(PostHog's arbitrary custom event properties) is handled by TRANS_ENG at transformation time.

**Rule:** DATA_ACC never stores raw JSONB blobs. If a field seems like it needs JSONB, either
(a) design explicit columns for the known variants, or (b) delegate the dynamic handling to
TRANS_ENG which extracts known properties into explicit columns.

## 2026-02-14: Temporal history tables for past state simulation

**Problem:** People's names, emails, phones, and locations change over time and differ across
platforms. A single scalar column (e.g., `people.email`) loses all history.

**Fix:** Dedicated one-to-many history tables (`person_names`, `person_emails`, `person_phones`,
`person_locations`, `organization_locations`) with `observed_at` / `superseded_at` temporal fields.
The `people` table keeps `display_name` and `primary_email` as denormalized caches to avoid JOINs
on every contact list query.

**Pattern:**
```sql
-- What was this person's email on 2026-01-15?
SELECT * FROM person_emails
WHERE person_id = ? AND observed_at <= '2026-01-15'
  AND (superseded_at IS NULL OR superseded_at > '2026-01-15')
```

**Rule:** For contact data that changes over time, model as one-to-many history tables with
temporal fields — not scalar columns, not change-summary audit logs. This enables full temporal
profiles, past state simulation, and cross-platform identity resolution.

## 2026-02-14: Always validate migrations locally before pushing to production

**Problem:** Risk of applying broken SQL to production Supabase, which could corrupt schema or
leave the database in an inconsistent state.

**Fix:** Local-first validation workflow: `supabase start` → write migration → `supabase db reset`
(drops and recreates local DB from scratch) → verify tables/seeds via psql → then `supabase db push`
to production.

**Rule:** Never run `supabase db push` without first validating the migration locally via
`supabase db reset`. Local reset tests the full migration chain from scratch — if it succeeds
locally, it will succeed in production.

## 2026-02-18: Supabase CLI config.toml version drift breaks CI

**Problem:** `supabase link` and `supabase db push` failed in CI with config parsing errors.
Local Supabase CLI (newer) auto-generates config keys (`oauth_server`, `web3`, `storage.vector`,
`major_version: 17`) that the CI CLI version doesn't recognize.

**Root cause:** `supabase/setup-cli@v1` installs a CLI version that lags behind the local
version. The CLI validates the entire `config.toml` on every command, even when config values
are irrelevant to the operation (e.g., `major_version` doesn't matter for `db push --db-url`).

**Fix (three-part):**
1. Removed unsupported auto-generated keys (web3, oauth_server, storage.analytics/vector, etc.)
2. Set `major_version = 15` (only affects local Docker image, not remote db push)
3. Replaced `supabase link` + `supabase db push` with `supabase db push --db-url` — bypasses
   config.toml dependency on project linking entirely

**Rule:** For CI/CD migrations, use `supabase db push --db-url "$SUPABASE_DB_URL"` instead of
`supabase link` + `supabase db push`. It's simpler (one secret instead of three), avoids
config.toml parsing issues, and doesn't require `SUPABASE_ACCESS_TOKEN` or `SUPABASE_DB_PASSWORD`.
Keep `config.toml` conservative — remove auto-generated keys for features you don't use.

## 2026-02-18: Supabase branching gives free PR-level migration validation

**Setup:** Enable branching in Supabase dashboard (Project Settings → Branching → Enable).
Connect to GitHub repo. Supabase auto-creates an isolated preview database for every PR,
runs all migrations from `supabase/migrations/`, seeds data, and reports via a "Supabase Preview"
GitHub check. Preview branches auto-delete on PR close/merge.

**Important:** Disable "Deploy to production" in branching settings if you handle production
migrations separately (we do, via `supabase db push --db-url` in `deploy.yml`). Having both
enabled would run migrations twice on every merge to main.

**No CI changes required.** The GitHub integration handles everything — no workflow steps to
add, no secrets to configure for preview branches. The "Supabase Preview" check appears
automatically on PRs.

**Branch protection:** On GitHub Pro (or public repos), add "Supabase Preview" as a required
status check to prevent merging PRs with broken migrations. On free private repos, the check
still appears but can't be enforced as a gate.

**Rule:** Supabase branching is the PR-level database validation layer. `deploy.yml` is the
production deployment layer. Keep them separate — branching validates, deploy.yml applies.

## 2026-02-20: pytest import-mode=importlib required for multi-package monorepos

**Problem:** When running `pytest packages/ workers/` across multiple workspace packages that
each have `tests/test_activities.py`, `tests/test_models.py`, etc., pytest fails with
`ImportPathMismatchError` — it treats same-named test files across packages as the same module.

**Root cause:** pytest's default import mode (`prepend`) adds the test file's parent directory
to `sys.path` and imports by basename. Two files named `test_activities.py` in different
packages become the same module `test_activities`, causing a collision.

**Fix:** Add `addopts = "--import-mode=importlib"` to `[tool.pytest.ini_options]` in
`pyproject.toml`. Importlib mode uses unique module names based on full file paths, so
`packages/config-access/tests/test_activities.py` and `packages/data-access/tests/test_activities.py`
are imported as distinct modules.

**Rule:** Any monorepo with multiple Python packages that have identically-named test files must
use `--import-mode=importlib`. This should be the default for all new monorepo setups.

## 2026-02-20: Pydantic field name "schema" shadows BaseModel internals

**Problem:** `RetrieveViewResult(PlatformResult)` had a field named `schema` which triggered
a Pydantic `UserWarning: Field name "schema" shadows an attribute in parent`. This can cause
subtle serialization bugs since `BaseModel` uses `schema` internally for JSON Schema generation.

**Fix:** Renamed to `schema_def`. The warning would have become an error in future Pydantic versions.

**Rule:** Never name Pydantic fields `schema`, `model_fields`, `model_config`, or any other
`BaseModel` attribute/method name. These are reserved by Pydantic's metaclass.

## 2026-02-20: fakeredis zrange(-1) requires Python slice adjustment

**Problem:** MockRedis's `zrange(key, 0, -1)` returned empty list because Python's `list[0:0]`
is empty. Redis uses -1 to mean "last element" (inclusive), but Python slicing treats -1 differently.

**Fix:** Handle negative stop index: `if stop < 0: stop = len(members) + stop` before slicing.

**Rule:** When building Redis mocks, always handle Redis's negative-index semantics (where -1 means
last element) explicitly. Python's native slice behavior doesn't match Redis range commands.

## 2026-02-20: Config Access uses business verbs, not CRUD

**Decision:** CFG_ACC exposes 9 business verb activities that pass the Righting Software test:
"If I switched from Redis to PostgreSQL, would this name still make sense?"

Verbs: `publish_schema`, `define_pipeline`, `activate_view`, `retrieve_view`, `grant_access`,
`revoke_access`, `clone_view`, `archive_schema`, `survey_configs`.

**Storage:** Upstash Redis with `cfg:` key prefix. JSON strings for objects, sorted sets for
time-ordered indexes, sets for status/relationship indexes, hashes for permissions.

**Multi-environment:** fakeredis for local dev (zero external dependency), Upstash SDK for
cloud (staging/production/PR preview). RedisAdapter normalizes the interface difference.

**Rule:** ResourceAccess components expose domain verbs, use JSON documents in Redis. Key patterns
should be readable as domain relationships (`cfg:view:idx:schema:{id}` = "views using this schema").

## 2026-02-20: Upstash deprecated regional database creation

**Problem:** `POST /v2/redis/database` with `"region": "us-east-1"` returns the JSON string
`"regional db creation is deprecated"`. This is a bare JSON string (not a dict), so
`json.load(sys.stdin)["endpoint"]` gives `TypeError: string indices must be integers`.

**Root cause:** Upstash deprecated regional databases. All new databases must be "global" with
a `primary_region` field.

**Fix:** Use `"region": "global", "primary_region": "us-east-1", "read_regions": []` in the
POST payload. For ephemeral PR preview databases, empty `read_regions` is fine — no need to
replicate across continents for a short-lived test database.

**Rule:** Always validate API responses before accessing fields. Add a guard that checks
`isinstance(data, str)` and `"error" in data` before parsing specific keys. API errors should
fail loudly with the actual error message, not with a confusing Python traceback.

## 2026-02-20: Upstash zadd format — don't use {"member": x, "score": y} with SDK

**Problem:** Live smoke tests against Upstash failed with `ERR value is not a valid float`.
All 6 tests failed on `publish_schema` because `zadd` couldn't write to sorted set indexes.

**Root cause:** The RedisAdapter had Upstash-specific `zadd` handling that passed
`{"member": uuid, "score": float}` — the Upstash SDK interpreted "member" and "score" as
literal member names in a `{member: score}` dict, so it tried to use the UUID string as a
score (not a valid float).

**Fix:** Both Upstash SDK and redis-py accept `{member_string: score_float}` format directly.
Removed the Upstash-specific handling entirely: `await self._client.zadd(key, mapping)`.

**Rule:** Live smoke tests against real infrastructure are essential for adapters that wrap
different SDKs. Mock tests can't catch format differences between SDKs — only real API calls
reveal these bugs. The CFG_ACC smoke tests caught this on the first run.

## 2026-02-20: uv workspace — `uv sync` alone doesn't resolve all packages

**Problem:** `uv run pytest` in GitHub Actions failed with `ModuleNotFoundError: No module
named 'unlock_config_access'` even after `uv sync`.

**Root cause:** In a uv workspace, `uv sync` installs the root project's dependencies but
doesn't necessarily make all workspace member packages importable. The CI workflow uses
`uv run --package unlock-workers` which ensures the full dependency tree is resolved.

**Fix:** Use `uv sync --all-packages` for the install step and
`uv run --package unlock-workers pytest ...` for the test step, matching the CI pattern.
