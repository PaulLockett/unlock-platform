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
