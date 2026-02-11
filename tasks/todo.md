# INFRA: Infrastructure Setup — Progress

## Phase 1: Repository & Directory Structure
- [ ] Initialize git repo
- [ ] Create full directory skeleton
- [ ] Root pyproject.toml with uv workspace
- [ ] Component packages with pyproject.toml + init files
- [ ] Worker runner package
- [ ] .gitignore, .env.example, .python-version
- [ ] `uv sync` succeeds

## Phase 2: Hello-World Temporal Workflows + Activities
- [ ] Shared package: task queue constants + temporal client factory
- [ ] Data Manager: scaffold 4 workflows (ingest, query, configure, share)
- [ ] Source Access: hello_source_access activity
- [ ] Worker runner dispatches to correct component
- [ ] Verification script runs hello-world workflow

## Phase 3: .devcontainer + Docker Compose
- [ ] devcontainer.json with Python 3.12 + Node 22
- [ ] docker-compose.yml with Temporal + PostgreSQL
- [ ] Verify: Temporal UI accessible, Postgres connectable

## Phase 4: GitHub Repo + CI/CD
- [ ] Create repo: PaulLockett/unlock-platform
- [ ] ci.yml: lint + test + typecheck
- [ ] deploy.yml skeleton
- [ ] Push initial commit, CI passes

## Phase 5: Next.js Canvas Scaffold
- [ ] create-next-app in apps/canvas
- [ ] Platform heading page
- [ ] Build succeeds

## Phase 6: Supabase Setup
- [ ] supabase init
- [ ] Cloud project via MCP
- [ ] Initial migration: unlock schema + platform_metadata

## Phase 7–10: Railway, Temporal Cloud, Vercel, E2E (requires manual steps)
