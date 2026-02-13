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
