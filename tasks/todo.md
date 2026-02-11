# INFRA: Infrastructure Setup — Progress

## Phase 1: Repository & Directory Structure
- [x] Initialize git repo
- [x] Create full directory skeleton
- [x] Root pyproject.toml with uv workspace
- [x] Component packages with pyproject.toml + init files
- [x] Worker runner package
- [x] .gitignore, .env.example, .python-version
- [x] `uv sync` succeeds — 34 packages resolved

## Phase 2: Hello-World Temporal Workflows + Activities
- [x] Shared package: task queue constants + temporal client factory
- [x] Data Manager: scaffold 4 workflows (ingest, query, configure, share)
- [x] Source Access: hello_source_access activity (+ 6 other component activities)
- [x] Worker runner dispatches to correct component (8 components registered)
- [x] Verification script runs hello-world workflow — cross-queue dispatch verified
- [x] 6 unit tests pass, ruff clean

## Phase 3: .devcontainer + Docker Compose
- [x] devcontainer.json with Python 3.12 + Node 22
- [x] docker-compose.yml with Temporal + PostgreSQL

## Phase 4: GitHub Repo + CI/CD
- [x] Create repo: PaulLockett/unlock-platform (private)
- [x] ci.yml: lint + test + typecheck — both jobs green
- [x] deploy.yml with CI gate
- [x] Push initial commit, CI passes

## Phase 5: Next.js Canvas Scaffold
- [x] create-next-app in apps/canvas (Next.js 16, TypeScript, Tailwind)
- [x] Platform heading page
- [x] Build succeeds

## Phase 6: Supabase Setup
- [x] supabase init
- [x] Cloud project via MCP (iabmwjrlbiyetasiiiht, us-east-1, $10/mo)
- [x] Initial migration: unlock schema + platform_metadata
- [x] Verified: platform_version = 0.1.0 in cloud DB

## Phase 8: Temporal Cloud
- [x] Paul: namespace created (unlock-platform.mkeud in ap-northeast-1)
- [x] API key auth working — removed rpc_metadata that was causing PermissionDenied
- [x] temporal_client.py reads TEMPORAL_REGIONAL_ENDPOINT (explicit, no default region)
- [x] verify_infra.py: IngestWorkflow runs against Temporal Cloud — all 3 activities dispatched across queues

## Phase 9: Vercel
- [x] Paul: Canvas deployed to Vercel

## Phase 7: Railway Setup
- [x] Paul: `railway login`
- [x] Created Railway project "unlock-platform" (Innovation-Portal workspace)
- [x] Created 9 services: data-manager, source-access, transform-engine, data-access, config-access, schema-engine, access-engine, llm-gateway, scheduler
- [x] Set COMPONENT + Temporal env vars on all 9 services
- [x] Deployed all 9 services — all STATUS=SUCCESS
- [x] Workers polling their dedicated task queues on Temporal Cloud

## Phase 10: End-to-End Verification
- [x] All 9 Railway workers running and polling Temporal Cloud
- [x] Temporal Cloud: IngestWorkflow dispatched from local → activities executed on Railway workers
- [x] Supabase: cloud DB with unlock schema + platform_metadata verified
- [x] Vercel: Canvas deployed
- [x] GitHub: CI + Deploy pipelines green
- [x] 6 unit tests pass, ruff clean
- [ ] Monitoring dashboards: Railway (https://railway.com), Temporal Cloud (cloud.temporal.io), Supabase (supabase.com), Vercel — all accessible via web

## Acceptance Criteria (from Monday.com)
- [x] All environments accessible (local dev + cloud services)
- [x] CI/CD pipeline successfully deploys a hello-world service
- [x] Database connections verified from application tier
- [x] Monitoring dashboards showing basic metrics (platform dashboards)
- [x] Secrets management configured (Railway env vars, Supabase project keys, Temporal API key)
- [x] Infrastructure as Code committed to repo
