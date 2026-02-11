# PRE-1: Requirements & Detailed Design

## Digital Presence Operating System

**Activity:** X-01 | **Status:** In Progress | **Phase:** 1 — Foundation + Identity
**Linear Issue:** PRE-1 | **Critical Path:** Yes (Float: 0.0)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Service Architecture & Monorepo Structure](#2-service-architecture--monorepo-structure)
3. [Temporal Architecture](#3-temporal-architecture)
4. [API & Contract Design](#4-api--contract-design)
5. [Auth & RBAC Model](#5-auth--rbac-model)
6. [Data Model (R1-R5)](#6-data-model-r1-r5)
7. [Platform Integration](#7-platform-integration)
8. [Developer Experience](#8-developer-experience)
9. [Cross-Cutting Concerns](#9-cross-cutting-concerns)
10. [Testing, Observability & Operational Readiness](#10-testing-observability--operational-readiness)
11. [Acceptance Criteria Checklist](#11-acceptance-criteria-checklist)

---

## 1. Executive Summary

This document formalizes the detailed design for the Digital Presence Operating System — an AI-powered autonomous agent platform for managing social media presences across multiple brands and channels. It translates 23 use case documents (with Mermaid sequence diagrams) into buildable contracts: service boundaries, Temporal workflow/activity definitions, API schemas, data models, testing/observability specifications, and developer experience specifications. The architecture contains 25 components across 4 layers + utilities (the original 24 plus U5: AI Utility, extracted as a cross-cutting concern).

### Key Architecture Decisions (Resolved)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Orchestration | **Temporal Cloud** | Managers = Workflows, Engines/RA = Activities. Durable, observable, debuggable. |
| ORM | **Drizzle ORM** | Lightweight, TypeScript-native, explicit SQL control for RLS |
| Database | **Supabase PostgreSQL + pgvector** | Managed, branching per PR, RLS built-in, vector search |
| Blob Storage | **Supabase Object Storage** | Co-located with DB, no separate S3 config |
| AI Integration | **Vercel AI SDK + OpenRouter** | Unified model interface, provider-agnostic |
| Message Bus (I1) | **Thin REST/SSE layer** | Temporal handles durable orchestration; I1 is just real-time client updates |
| Cache / Rate Limit | **Upstash Redis** | Serverless Redis, no infra management |
| Frontend | **Next.js on Vercel** | PR preview deploys, SSR, App Router |
| App Hosting | **Railway** | Separate services, internal networking, PR environments |
| Platforms v1 | **X, LinkedIn, Substack** | Native APIs for full control |
| AI Models v1 | **Single model via OpenRouter** | Baseline, experiment later |
| Monorepo | **pnpm workspaces + Turborepo** | Task orchestration, caching, works with Temporal Cloud |

---

## 2. Service Architecture & Monorepo Structure

### 2.1 Monorepo Directory Layout

```
presence-os/
│
├── apps/                                 # Deployable frontend applications
│   ├── task-ui/                          # C1: Task Interface
│   │   ├── src/
│   │   │   ├── app/                      #   Next.js App Router
│   │   │   ├── components/               #   UI components
│   │   │   ├── hooks/                    #   React hooks (SSE, auth, etc.)
│   │   │   └── lib/                      #   Client-side utilities
│   │   ├── next.config.ts
│   │   ├── package.json
│   │   └── vercel.json
│   │
│   ├── admin-portal/                     # C2: Admin Portal
│   │   ├── src/
│   │   │   ├── app/                      #   Next.js App Router
│   │   │   ├── components/               #   Admin-specific UI
│   │   │   └── lib/                      #   Client-side utilities
│   │   ├── next.config.ts
│   │   ├── package.json
│   │   └── vercel.json
│   │
│   └── api-gateway/                      # C3: API Gateway
│       ├── src/
│       │   ├── routes/                   #   Route handlers (webhooks, REST API)
│       │   ├── middleware/               #   Auth, rate limiting, validation
│       │   └── index.ts                  #   Hono server entry
│       ├── package.json
│       └── railway.json
│
├── workers/                              # Deployable Temporal worker services
│   ├── presence/                         # Presence subsystem worker
│   │   ├── src/
│   │   │   ├── worker.ts                 #   Worker entry: registers M1 workflows + activities
│   │   │   └── config.ts                 #   Task queue, connection config
│   │   ├── package.json
│   │   └── railway.json
│   │
│   ├── automation/                       # Automation subsystem worker
│   │   ├── src/
│   │   │   ├── worker.ts                 #   Worker entry: registers M2 workflows + activities
│   │   │   └── config.ts
│   │   ├── package.json
│   │   └── railway.json
│   │
│   ├── account/                          # Account subsystem worker
│   │   ├── src/
│   │   │   ├── worker.ts                 #   Worker entry: registers M3 workflows + activities
│   │   │   └── config.ts
│   │   ├── package.json
│   │   └── railway.json
│   │
│   └── realtime/                         # I1: Real-time SSE server
│       ├── src/
│       │   ├── sse.ts                    #   SSE endpoint handlers
│       │   ├── channels.ts              #   Channel subscription management
│       │   └── index.ts                  #   Hono server entry
│       ├── package.json
│       └── railway.json
│
├── packages/                             # Shared libraries (not independently deployed)
│   ├── temporal-workflows/               # Temporal workflow definitions (V8 sandbox)
│   │   ├── src/
│   │   │   ├── presence/                 #   M1: Presence Manager workflows
│   │   │   │   ├── operate.workflow.ts
│   │   │   │   ├── evolve.workflow.ts
│   │   │   │   ├── content-approval.workflow.ts
│   │   │   │   ├── campaign.workflow.ts
│   │   │   │   ├── engagement.workflow.ts
│   │   │   │   ├── growth-tasks.workflow.ts
│   │   │   │   ├── voice-discovery.workflow.ts
│   │   │   │   ├── multi-brand-batch.workflow.ts
│   │   │   │   ├── microsite.workflow.ts
│   │   │   │   ├── ab-test.workflow.ts
│   │   │   │   ├── user-correction.workflow.ts
│   │   │   │   ├── cross-brand-transfer.workflow.ts
│   │   │   │   ├── workflow-creation.workflow.ts
│   │   │   │   └── index.ts
│   │   │   ├── automation/               #   M2: Process Manager workflows
│   │   │   │   ├── execute.workflow.ts
│   │   │   │   ├── monitor.workflow.ts
│   │   │   │   ├── degrade.workflow.ts
│   │   │   │   └── index.ts
│   │   │   ├── account/                  #   M3: Tenant Manager workflows
│   │   │   │   ├── onboard.workflow.ts
│   │   │   │   ├── configure-brand.workflow.ts
│   │   │   │   ├── billing.workflow.ts
│   │   │   │   ├── team.workflow.ts
│   │   │   │   └── index.ts
│   │   │   └── index.ts                  #   Root export
│   │   └── package.json
│   │
│   ├── temporal-activities/              # Temporal activity implementations (Node.js)
│   │   ├── src/
│   │   │   ├── engines/                  #   E1-E4 Engine activities
│   │   │   │   ├── content.activities.ts       # E1: Content Engine
│   │   │   │   ├── identity.activities.ts      # E2: Identity Engine
│   │   │   │   ├── analytics.activities.ts     # E3: Analytics Engine
│   │   │   │   ├── knowledge.activities.ts     # E4: Knowledge Engine
│   │   │   │   └── index.ts
│   │   │   ├── resource-access/          #   RA1-RA4 ResourceAccess activities
│   │   │   │   ├── channel.activities.ts       # RA1: Channel Access
│   │   │   │   ├── service.activities.ts       # RA2: Service Access
│   │   │   │   ├── conversation.activities.ts  # RA3: Conversation Access
│   │   │   │   ├── store.activities.ts         # RA4: Store Access
│   │   │   │   └── index.ts
│   │   │   ├── utilities/                #   U1-U4 as activities
│   │   │   │   ├── notification.activities.ts  # U4: Notification
│   │   │   │   └── index.ts
│   │   │   └── index.ts                  #   Root export (all activities)
│   │   └── package.json
│   │
│   ├── db/                               # Database layer
│   │   ├── src/
│   │   │   ├── schema/                   #   Drizzle schema definitions
│   │   │   │   ├── brand.ts              #     R1: Brand Store tables
│   │   │   │   ├── content.ts            #     R2: Content Store tables
│   │   │   │   ├── task.ts               #     R3: Task Store tables
│   │   │   │   ├── knowledge.ts          #     R4: Knowledge Store tables
│   │   │   │   ├── performance.ts        #     R5: Performance Store tables
│   │   │   │   ├── tenant.ts             #     Tenant + auth tables
│   │   │   │   └── index.ts              #     Aggregated schema export
│   │   │   ├── client.ts                 #   Drizzle client initialization
│   │   │   ├── rls.ts                    #   RLS policy helpers
│   │   │   └── migrate.ts               #   Migration runner
│   │   ├── drizzle.config.ts
│   │   └── package.json
│   │
│   ├── schemas/                          # Zod schemas (shared types)
│   │   ├── src/
│   │   │   ├── brand.schemas.ts          #   Brand-related types
│   │   │   ├── content.schemas.ts        #   Content lifecycle types
│   │   │   ├── task.schemas.ts           #   Task queue types
│   │   │   ├── knowledge.schemas.ts      #   Knowledge framework types
│   │   │   ├── performance.schemas.ts    #   Analytics/performance types
│   │   │   ├── auth.schemas.ts           #   Auth/RBAC types
│   │   │   ├── events.schemas.ts         #   SSE event payloads
│   │   │   ├── temporal.schemas.ts       #   Workflow/activity input/output types
│   │   │   ├── platform.schemas.ts       #   Platform-specific types (X, LinkedIn, Substack)
│   │   │   ├── api.schemas.ts            #   API request/response types
│   │   │   └── index.ts
│   │   └── package.json
│   │
│   ├── auth/                             # U1: Auth utilities
│   │   ├── src/
│   │   │   ├── supabase.ts               #   Supabase Auth client
│   │   │   ├── jwt.ts                    #   JWT utilities (decode, validate)
│   │   │   ├── rbac.ts                   #   Role-based access control helpers
│   │   │   ├── middleware.ts             #   Auth middleware for Hono
│   │   │   └── index.ts
│   │   └── package.json
│   │
│   ├── temporal-client/                  # Temporal client utilities
│   │   ├── src/
│   │   │   ├── connection.ts             #   Connection factory (local vs. Cloud)
│   │   │   ├── client.ts                 #   Workflow client helpers
│   │   │   ├── schedules.ts              #   U2: Schedule management
│   │   │   ├── task-queues.ts            #   Task queue name constants
│   │   │   └── index.ts
│   │   └── package.json
│   │
│   ├── ui/                               # Shared UI library
│   │   ├── src/
│   │   │   ├── components/               #   Reusable components (Shadcn-based)
│   │   │   ├── hooks/                    #   Shared React hooks
│   │   │   └── index.ts
│   │   └── package.json
│   │
│   ├── ai/                               # U5: AI Utility
│   │   ├── src/
│   │   │   ├── complete.ts              #   Text completion (Vercel AI SDK + OpenRouter)
│   │   │   ├── structure.ts             #   Structured output (schema-constrained generation)
│   │   │   ├── embed.ts                 #   Embedding generation (text-embedding-3-small)
│   │   │   ├── providers.ts             #   OpenRouter provider configuration
│   │   │   └── index.ts
│   │   └── package.json
│   │
│   ├── testing/                          # Shared test utilities and fixtures
│   │   ├── fixtures/
│   │   │   ├── ai/                      #   Deterministic AI response fixtures
│   │   │   ├── platforms/               #   Mock platform API responses
│   │   │   └── billing/                 #   Mock Stripe webhook payloads
│   │   ├── factories/                   #   Test data factories (TypeScript)
│   │   ├── helpers/                     #   Temporal test env, Supabase helpers, auth
│   │   └── package.json
│   │
│   └── config/                           # Shared configurations
│       ├── eslint/
│       ├── tsconfig/
│       └── tailwind/
│
├── tests/                                # System-level tests (not in packages)
│   ├── e2e/                             #   End-to-end use case tests
│   └── load/                            #   k6 load test scenarios
│       ├── scenarios/
│       ├── helpers/
│       └── thresholds.json
│
├── supabase/                             # Supabase project config
│   ├── config.toml                       #   Supabase project settings
│   ├── migrations/                       #   SQL migrations (generated by Drizzle)
│   ├── seed.sql                          #   Development seed data
│   └── functions/                        #   Supabase Edge Functions (if needed)
│
├── .devcontainer/                        # Dev container specification
│   ├── devcontainer.json
│   ├── docker-compose.yml                #   Full local dev stack
│   └── post-create.sh                    #   Setup script
│
├── .github/
│   └── workflows/
│       ├── ci.yml                        #   Test + lint on every push
│       ├── preview.yml                   #   PR preview environment orchestration
│       └── deploy.yml                    #   Production deploy on main merge
│
├── pnpm-workspace.yaml
├── turbo.json                            #   Turborepo pipeline config
├── package.json                          #   Root package.json
└── tsconfig.base.json                    #   Base TypeScript config
```

### 2.2 Package Dependency Graph

```
apps/task-ui          → packages/schemas, packages/auth, packages/ui, packages/temporal-client
apps/admin-portal     → packages/schemas, packages/auth, packages/ui, packages/temporal-client
apps/api-gateway      → packages/schemas, packages/auth, packages/temporal-client

workers/presence      → packages/temporal-workflows, packages/temporal-activities, packages/db, packages/schemas
workers/automation    → packages/temporal-workflows, packages/temporal-activities, packages/db, packages/schemas
workers/account       → packages/temporal-workflows, packages/temporal-activities, packages/db, packages/schemas
workers/realtime      → packages/schemas, packages/auth, packages/db

packages/temporal-workflows   → packages/schemas (types only — V8 sandbox, no runtime deps)
packages/temporal-activities  → packages/db, packages/schemas, packages/auth, packages/ai
packages/db                   → packages/schemas
packages/auth                 → packages/schemas
packages/ai                   → packages/schemas (U5: AI Utility, Vercel AI SDK + OpenRouter)
packages/temporal-client      → packages/schemas
packages/testing              → packages/schemas, packages/db, packages/auth, packages/ai
```

### 2.3 Railway Service Topology

Each service is a separate Railway deployment in the same project, communicating via Railway's internal private network.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Railway Project: presence-os                                        │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ api-gateway      │  │ realtime         │  │ presence-worker  │  │
│  │ (C3)             │  │ (I1)             │  │ (M1 workflows)   │  │
│  │                  │  │                  │  │                  │  │
│  │ Public domain    │  │ Public domain    │  │ Internal only    │  │
│  │ Port: 8000       │  │ Port: 8001       │  │ Long-running     │  │
│  │ Hono server      │  │ SSE endpoints    │  │ Temporal worker  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐                        │
│  │ automation-worker │  │ account-worker   │                        │
│  │ (M2 workflows)   │  │ (M3 workflows)   │                        │
│  │                  │  │                  │                        │
│  │ Internal only    │  │ Internal only    │                        │
│  │ Long-running     │  │ Long-running     │                        │
│  │ Temporal worker  │  │ Temporal worker  │                        │
│  └──────────────────┘  └──────────────────┘                        │
│                                                                      │
│  Shared via Railway reference variables:                             │
│   • TEMPORAL_ADDRESS  → Temporal Cloud endpoint                      │
│   • DATABASE_URL      → Supabase PostgreSQL connection               │
│   • REDIS_URL         → Upstash Redis connection                     │
│   • SUPABASE_URL      → Supabase API endpoint                       │
│   • OPENROUTER_API_KEY → OpenRouter model access                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Vercel: presence-os-frontends                                       │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐                        │
│  │ task-ui          │  │ admin-portal     │                        │
│  │ (C1)             │  │ (C2)             │                        │
│  │                  │  │                  │                        │
│  │ app.presence.io  │  │ admin.presence.io│                        │
│  │ Next.js SSR      │  │ Next.js SSR      │                        │
│  │ PR previews      │  │ PR previews      │                        │
│  └──────────────────┘  └──────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.4 Service Communication Patterns

| From | To | Mechanism | Route |
|------|----|-----------|-------|
| C1/C2 (Vercel) → Temporal | Start workflow, query, signal | HTTPS → API Gateway → Temporal Client | Vercel → Railway api-gateway → Temporal Cloud |
| C1/C2 → Real-time updates | SSE subscription | HTTPS → Realtime service | Vercel → Railway realtime (public domain) |
| API Gateway → Temporal | Start workflow on webhook | Temporal Client SDK | Railway internal → Temporal Cloud |
| Workers → Temporal Cloud | Poll for tasks, complete | gRPC (Temporal SDK) | Railway → Temporal Cloud |
| Workers → Supabase | Database queries | PostgreSQL connection | Railway → Supabase (connection pooler) |
| Workers → Upstash Redis | Cache, rate limit | Redis protocol over TLS | Railway → Upstash endpoint |
| Workers → OpenRouter | AI model calls | HTTPS | Railway → OpenRouter API |
| Workers → Honcho | Conversation memory | HTTPS | Railway → Honcho API |
| Workers → Platform APIs | Publish, pull analytics | HTTPS | Railway → X/LinkedIn/Substack |
| Realtime → Upstash Redis | Pub/sub for SSE events | Redis Pub/Sub | Railway internal → Upstash |

### 2.5 pnpm-workspace.yaml

```yaml
packages:
  - 'apps/*'
  - 'workers/*'
  - 'packages/*'
```

### 2.6 turbo.json

```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**", "node_modules/.cache/turbo/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "lint": {},
    "test": {
      "dependsOn": ["^build"]
    },
    "typecheck": {
      "dependsOn": ["^build"]
    },
    "db:generate": {
      "cache": false
    },
    "db:migrate": {
      "cache": false
    }
  }
}
```

---

## 3. Temporal Architecture

### 3.1 Core Mapping: Architecture → Temporal

| Architecture Layer | Temporal Concept | Deployment |
|--------------------|------------------|------------|
| **Managers** (M1, M2, M3) | Temporal Workflows | Registered on subsystem workers |
| **Engines** (E1-E4) | Temporal Activities | Registered on subsystem workers |
| **ResourceAccess** (RA1-RA4) | Temporal Activities | Registered on subsystem workers |
| **Utilities** (U2: Scheduling) | Temporal Schedules | Managed via Temporal Client |
| **Utilities** (U4: Notification) | Temporal Activity | Registered on all workers |
| **Manager → Manager** (QUEUED) | Child Workflows or Signals | Cross-queue via workflow ID |
| **I1: Message Bus** | Thin SSE layer (NOT Temporal) | Separate Railway service |

### 3.2 Task Queues

```typescript
// packages/temporal-client/src/task-queues.ts

export const TASK_QUEUES = {
  PRESENCE:   'presence-queue',     // M1 workflows + E1-E4, RA1-RA4 activities
  AUTOMATION: 'automation-queue',   // M2 workflows + E1-E4, RA1-RA4 activities
  ACCOUNT:    'account-queue',      // M3 workflows + RA2, RA4 activities
} as const;

export type TaskQueue = typeof TASK_QUEUES[keyof typeof TASK_QUEUES];
```

Note: Engine and RA activities are registered on each subsystem's worker because they're stateless and need to be callable from that subsystem's workflows. This replicates activity code across workers but avoids cross-queue latency for the common path. If activity scaling becomes an issue, we can split to a dedicated activity queue later.

### 3.3 Workflow Definitions (Managers)

#### M1: Presence Manager Workflows

| Workflow Type ID | Use Case | Input | Output | Signals |
|-----------------|----------|-------|--------|---------|
| `presence.operate` | CUC1: Operate a Presence | `{ tenantId, brandId, input: UserInput }` | `{ tasks: Task[], content?: Content[] }` | `approval.response`, `revision.request` |
| `presence.evolve` | CUC2: Evolve Understanding | `{ tenantId, brandId, trigger: 'scheduled' \| 'book_upload' }` | `{ knowledgeUpdates: KnowledgeUpdate[] }` | — |
| `presence.assessGraduation` | CUC3 Phase A+B | `{ tenantId, brandId, workflowId }` | `{ ready: boolean, proposal?: GraduationProposal }` | `graduation.approve`, `graduation.reject` |
| `presence.contentApproval` | VUC-P1 | `{ tenantId, brandId, contentId }` | `{ status: 'approved' \| 'revised' \| 'rejected' }` | `approval.response` |
| `presence.campaign` | VUC-P2 | `{ tenantId, brandId, campaignConfig }` | `{ campaignId, contentPlan: ContentItem[] }` | `campaign.pause`, `campaign.resume` |
| `presence.engagementResponse` | VUC-P3 | `{ tenantId, brandId, engagementEvent }` | `{ response?: Content, logged: boolean }` | — |
| `presence.growthTasks` | VUC-P4 | `{ tenantId, brandId }` | `{ tasks: Task[] }` | — |
| `presence.voiceDiscovery` | VUC-P5 | `{ tenantId, brandId, samples: VoiceSample[] }` | `{ voiceModel: VoiceModelUpdate }` | — |
| `presence.multiBrandBatch` | VUC-P6 | `{ tenantId, brandIds: string[] }` | `{ results: Map<brandId, ContentBatch> }` | — |
| `presence.micrositeGeneration` | VUC-P7 | `{ tenantId, brandId, micrositeConfig }` | `{ deploymentUrl: string }` | — |
| `presence.abTest` | VUC-K1 | `{ tenantId, brandId, testConfig }` | `{ testId, variants: Variant[] }` | `test.evaluate` |
| `presence.userCorrection` | VUC-K2 | `{ tenantId, brandId, correction }` | `{ updated: boolean }` | — |
| `presence.crossBrandTransfer` | VUC-K3 | `{ tenantId, sourceBrandId, targetBrandId, frameworkIds }` | `{ transferred: string[] }` | — |
| `presence.workflowCreation` | VUC-W1 | `{ tenantId, brandId, workflowDef }` | `{ workflowId, status: 'experimental' }` | — |

#### M2: Process Manager Workflows

| Workflow Type ID | Use Case | Input | Output | Signals |
|-----------------|----------|-------|--------|---------|
| `automation.execute` | CUC3 Phase C | `{ tenantId, brandId, workflowId, workflowDef }` | `{ contentProduced: Content[], published: boolean }` | `execution.cancel` |
| `automation.monitor` | VUC-W3 | `{ tenantId, brandId, workflowId }` | `{ status, metrics }` | — |
| `automation.degrade` | VUC-W2 | `{ tenantId, brandId, workflowId, reason }` | `{ degraded: boolean, handedBackTo: 'presence' }` | — |

#### M3: Tenant Manager Workflows

| Workflow Type ID | Use Case | Input | Output | Signals |
|-----------------|----------|-------|--------|---------|
| `account.onboard` | VUC-A1 | `{ email, plan, paymentMethod }` | `{ tenantId, brandId }` | — |
| `account.configureBrand` | VUC-A2 | `{ tenantId, brandConfig }` | `{ brandId, channelsConnected: string[] }` | — |
| `account.billing` | VUC-A3 | `{ tenantId, action: 'upgrade' \| 'downgrade' \| 'cancel', planId? }` | `{ success: boolean, newPlan? }` | — |
| `account.team` | VUC-A4 | `{ tenantId, action: 'invite' \| 'remove' \| 'updateRole', member }` | `{ success: boolean }` | — |

### 3.4 Activity Definitions (Engines + ResourceAccess + Utilities)

All interfaces use **atomic business verbs** per Löwy's method. No CRUD operations (`get`, `set`, `create`, `update`, `delete`) or implementation-leaking verbs (`pull`, `call`, `fetch`). Engines communicate through **versioned annotations** on shared business entities in the database — never through parameter passing via the Manager.

#### The Annotation Pattern

Engines don't pass data to each other. Instead, each Engine leaves **versioned, timestamped annotations** on business entities (content, brands, etc.) in the database via RA4. When another Engine needs context, it reads annotations from the DB as part of its own work. The Manager orchestrates the sequence but never shuttles data between Engines.

```
CUC1 Flow with Annotations:
1. M1 → E4.brief(brandId, context)          E4 writes a ContentBrief annotation to DB
2. M1 → E1.produce(brandId, platforms)       E1 reads the brief, produces content drafts
3. M1 → E2.evaluate(contentId)              E2 reads content, writes VoiceAlignment annotation
4. M1 → E3.assess(contentId)                E3 reads content, writes PerformanceInsight annotation
5. M1 → E1.revise(contentId)                E1 reads all annotations since last revision, updates content
6. M1 → RA1.distribute(contentId, platform) Publish final content

Key: Engines read/write annotations via RA4 internally. The Manager never passes
voiceParams, performanceContext, or frameworks between Engines.
```

#### E1: Content Engine — Encapsulates content production volatility

```typescript
export interface ContentEngineActivities {
  /**
   * Produce initial content drafts for target platforms.
   * Reads ContentBrief annotations (from E4) and brand identity prompt via RA4.
   * Writes content versions to R2 via RA4.
   */
  produce(params: {
    tenantId: string;
    brandId: string;
    targetPlatforms: Platform[];
    userInput?: UserInput;
  }): Promise<{ contentIds: string[] }>;

  /**
   * Revise existing content based on Engine annotations accumulated since last revision.
   * Reads VoiceAlignment (E2), PerformanceInsight (E3), and StrategicGuidance (E4)
   * annotations via RA4. Writes new content version.
   */
  revise(params: {
    tenantId: string;
    contentId: string;
  }): Promise<{ versionId: string }>;

  /**
   * Compose a microsite from brand identity and content plan.
   * Reads identity prompt and content brief annotations via RA4.
   */
  compose(params: {
    tenantId: string;
    brandId: string;
    config: MicrositeConfig;
  }): Promise<{ artifactId: string }>;

  /**
   * Sequence an email series from content plan and brand identity.
   * Reads identity prompt, strategic guidance, and performance insight annotations.
   */
  sequence(params: {
    tenantId: string;
    brandId: string;
    sequenceConfig: EmailSequenceConfig;
  }): Promise<{ sequenceId: string }>;
}
```

#### E2: Identity Engine — Encapsulates brand identity modeling volatility

```typescript
export interface IdentityEngineActivities {
  /**
   * Evaluate content against brand identity. Reads the brand's identity prompt
   * and the content from RA4. Writes a versioned VoiceAlignment annotation:
   * alignment score, specific misalignments, suggested adjustments.
   */
  evaluate(params: {
    tenantId: string;
    contentId: string;
  }): Promise<{ annotationId: string; aligned: boolean }>;

  /**
   * Refine the brand identity prompt from new signal samples (user input,
   * approved content, voice memos). Reads current identity prompt + samples
   * via RA4. Writes new version of the identity prompt.
   */
  refine(params: {
    tenantId: string;
    brandId: string;
    samples: VoiceSample[];
  }): Promise<{ identityVersion: number }>;

  /**
   * Absorb identity signals from raw user interaction. Extracts personality
   * patterns, vocabulary preferences, tone indicators from input. Writes
   * IdentitySignal annotations for later refinement cycles.
   */
  absorb(params: {
    tenantId: string;
    brandId: string;
    input: UserInput;
  }): Promise<{ signalCount: number }>;
}
```

#### E3: Analytics Engine — Encapsulates performance measurement volatility

```typescript
export interface AnalyticsEngineActivities {
  /**
   * Assess content and write a versioned PerformanceInsight annotation.
   * Reads historical performance data, audience metrics, comparable content
   * performance from RA4. The annotation includes: predicted engagement,
   * optimal posting windows, audience fit score, comparable content references.
   */
  assess(params: {
    tenantId: string;
    contentId: string;
  }): Promise<{ annotationId: string }>;

  /**
   * Synthesize monthly performance across all channels for a brand.
   * Reads metrics from R5, produces a MonthlyAnalysis report written to RA4.
   * Includes: trend identification, top/bottom performers, anomaly detection.
   */
  synthesizePerformance(params: {
    tenantId: string;
    brandId: string;
    period: string; // YYYY-MM
  }): Promise<{ analysisId: string }>;

  /**
   * Evaluate workflow graduation readiness against thresholds.
   * Reads workflow execution history from R5 via RA4. Writes assessment annotation.
   */
  evaluateWorkflow(params: {
    tenantId: string;
    workflowId: string;
    thresholds: GraduationThresholds;
  }): Promise<{ ready: boolean; assessmentId: string }>;

  /**
   * Record an engagement event from platform webhook.
   * Writes to R5 via RA4. Updates running metrics for content performance.
   */
  recordEngagement(params: {
    tenantId: string;
    brandId: string;
    event: EngagementEvent;
  }): Promise<void>;

  /**
   * Conclude an A/B test: evaluate statistical significance, declare winner.
   * Reads variant performance from R5. Writes conclusion annotation.
   */
  concludeExperiment(params: {
    tenantId: string;
    testId: string;
  }): Promise<{ winnerId: string | null; significance: number }>;
}
```

#### E4: Knowledge Engine — Encapsulates strategic knowledge volatility

```typescript
export interface KnowledgeEngineActivities {
  /**
   * Brief: Produce a versioned StrategicGuidance annotation BEFORE content
   * production. Reads: historical performance data (R5), trend analysis (R5),
   * knowledge frameworks (R4), recent ingested sources, brand context (R1).
   * Writes: ContentBrief annotation with recommended angles, frameworks to
   * apply, audience insights, timing recommendations, risk flags.
   */
  brief(params: {
    tenantId: string;
    brandId: string;
    contentContext: ContentContext; // topic, platforms, campaign
  }): Promise<{ briefId: string }>;

  /**
   * Annotate existing content with strategic guidance.
   * Similar to brief() but reacts to specific content rather than
   * pre-producing guidance. Writes StrategicGuidance annotation.
   */
  annotate(params: {
    tenantId: string;
    contentId: string;
  }): Promise<{ annotationId: string }>;

  /**
   * Ingest a new knowledge source (book, article, URL, upload).
   * Extracts frameworks, generates embeddings, catalogs in R4 via RA4.
   * Links source materials to object store folder.
   */
  ingest(params: {
    tenantId: string;
    source: KnowledgeSource;
  }): Promise<{ frameworkCount: number; sourceId: string }>;

  /**
   * Reconcile empirical evidence against framework predictions.
   * Reads monthly analysis + framework predictions. Updates confidence
   * scores. Flags contradictions for human review.
   */
  reconcile(params: {
    tenantId: string;
    brandId: string;
    analysisId: string; // From E3.synthesizePerformance
  }): Promise<{ updated: number; contradictions: number }>;
}
```

#### RA1: Channel Access — Encapsulates platform API volatility

All platforms (X, LinkedIn, Substack) are accessed through the same interface. Implementation details (REST API, undocumented API, email-to-post, browser automation) are encapsulated in per-platform adapters. Authentication is handled internally — `connect` handles the full OAuth lifecycle.

```typescript
export interface ChannelAccessActivities {
  /**
   * Distribute content to a platform. Handles: authentication, format
   * translation, rate limiting, retries, scheduling. The adapter knows
   * how to reach the platform (official API, undocumented API, email,
   * browser automation) — callers don't.
   */
  distribute(params: {
    tenantId: string;
    brandId: string;
    platform: Platform;
    contentId: string; // Reads content from RA4 internally
    scheduledAt?: Date;
  }): Promise<{ publishedUrl?: string; platformPostId: string }>;

  /**
   * Harvest metrics from a platform. Handles: authentication, pagination,
   * rate limiting, normalization of platform-specific metric formats.
   * Writes normalized metrics to R5 via RA4.
   */
  harvest(params: {
    tenantId: string;
    brandId: string;
    platform: Platform;
    period: DateRange;
  }): Promise<{ metricsCount: number }>;

  /**
   * Connect a brand to a platform. Handles the full lifecycle: OAuth flow
   * initiation, callback processing, token storage, webhook registration.
   * Writes connection record to R1 via RA4.
   */
  connect(params: {
    tenantId: string;
    brandId: string;
    platform: Platform;
    callbackUrl: string;
    authorizationCode?: string; // If completing an OAuth callback
  }): Promise<{ connected: boolean; platformAccountId: string }>;

  /**
   * Disconnect a brand from a platform. Revokes tokens, unregisters webhooks.
   */
  disconnect(params: {
    tenantId: string;
    brandId: string;
    platform: Platform;
  }): Promise<void>;
}
```

#### RA2: Service Access — Encapsulates external service API volatility (billing, deployment)

AI model access has been extracted to U5 (AI Utility) since it's cross-cutting infrastructure used by every layer. RA2 now handles only non-AI external services.

```typescript
export interface ServiceAccessActivities {
  /**
   * Process a billing action. Encapsulates Stripe (or future billing provider).
   * Handles: customer creation, subscription management, webhook reconciliation,
   * invoice retrieval. The caller specifies the business action, not the Stripe API call.
   */
  processBilling(params: {
    tenantId: string;
    action: BillingAction; // 'subscribe' | 'upgrade' | 'downgrade' | 'cancel' | 'reconcile'
    planId?: string;
    paymentMethodId?: string;
    webhookPayload?: unknown; // For reconcile action
  }): Promise<BillingResult>;

  /**
   * Deploy an asset to a hosting provider. Encapsulates Vercel (or future provider).
   * Reads the artifact from object storage via RA4 internally.
   */
  deployAsset(params: {
    tenantId: string;
    brandId: string;
    artifactId: string; // Reads artifact from RA4 internally
    domain?: string;
  }): Promise<{ deploymentUrl: string }>;
}
```

#### RA3: Conversation Access — Encapsulates conversational memory volatility

```typescript
export interface ConversationAccessActivities {
  /**
   * Remember an interaction in conversational memory.
   * Encapsulates Honcho (or future memory provider). Handles session
   * lifecycle internally — creates sessions as needed.
   */
  remember(params: {
    tenantId: string;
    brandId: string;
    message: ConversationMessage;
    metadata?: Record<string, unknown>;
  }): Promise<void>;

  /**
   * Recall relevant conversation context for a brand interaction.
   * Returns contextually relevant prior interactions using Honcho's
   * social cognition / dialectic capabilities.
   */
  recall(params: {
    tenantId: string;
    brandId: string;
    context: string; // What are we trying to recall for?
    limit?: number;
  }): Promise<ConversationContext>;
}
```

#### RA4: Store Access — Encapsulates internal storage technology volatility

Exposes **atomic business verbs** grouped by resource domain. No generic CRUD. If the underlying storage changes from PostgreSQL to CockroachDB, from pgvector to Qdrant, or from Supabase Object Storage to R2, these verbs remain stable because they describe business actions, not storage operations.

```typescript
export interface StoreAccessActivities {
  // ── R1: Brand Store ──────────────────────────────────────────────

  /** Configure a brand's settings (autonomy level, growth stage, pillars) */
  configureBrand(p: { tenantId: string; brandId: string; config: BrandConfig }): Promise<Brand>;

  /** Persist a new version of the brand's identity prompt */
  evolveIdentity(p: { tenantId: string; brandId: string; prompt: string }): Promise<{ version: number }>;

  /** Record a channel connection for a brand */
  registerChannel(p: { tenantId: string; brandId: string; platform: Platform; connection: ChannelConnection }): Promise<void>;

  /** Revoke a channel connection */
  revokeChannel(p: { tenantId: string; brandId: string; platform: Platform }): Promise<void>;

  // ── R2: Content Store ────────────────────────────────────────────

  /** Stage a new content version (immutable — creates new version, never overwrites) */
  stageContent(p: { tenantId: string; content: ContentInput }): Promise<{ contentId: string; version: number }>;

  /** Advance content through its lifecycle (draft→review→approved→scheduled→published→archived) */
  advanceContent(p: { tenantId: string; contentId: string; toStatus: ContentStatus }): Promise<void>;

  /** Attach an annotation to content (VoiceAlignment, PerformanceInsight, StrategicGuidance) */
  annotateContent(p: { tenantId: string; contentId: string; annotation: ContentAnnotation }): Promise<{ annotationId: string }>;

  /** Read annotations attached to content since a given timestamp */
  readAnnotations(p: { tenantId: string; contentId: string; since?: Date; types?: AnnotationType[] }): Promise<ContentAnnotation[]>;

  /** Archive a media asset to object storage, linked to content */
  archiveMedia(p: { tenantId: string; contentId: string; data: Buffer; contentType: string }): Promise<{ assetUrl: string }>;

  // ── R3: Task Store ───────────────────────────────────────────────

  /** Dispatch a task to the human task queue */
  dispatchTask(p: { tenantId: string; task: TaskInput }): Promise<{ taskId: string }>;

  /** Fulfill a task with a human response, signaling the waiting workflow */
  fulfillTask(p: { tenantId: string; taskId: string; response: TaskResponse }): Promise<void>;

  // ── R4: Knowledge Store ──────────────────────────────────────────

  /** Catalog a framework in the knowledge base with embedding for semantic search */
  catalogFramework(p: { tenantId: string; framework: FrameworkInput }): Promise<{ frameworkId: string }>;

  /** Discover relevant frameworks via semantic search */
  discoverKnowledge(p: { tenantId: string; query: string; limit?: number; threshold?: number }): Promise<Framework[]>;

  /** Reconcile evidence against a framework (update confidence, flag contradictions) */
  reconcileEvidence(p: { tenantId: string; frameworkId: string; evidence: Evidence }): Promise<void>;

  /** Link a knowledge source to its summary files in object storage */
  linkSourceMaterial(p: { tenantId: string; frameworkId: string; sourceRef: SourceReference }): Promise<void>;

  // ── R5: Performance Store ────────────────────────────────────────

  /** Capture a performance metric (engagement, reach, impressions, etc.) */
  captureMetric(p: { tenantId: string; metric: MetricInput }): Promise<void>;

  /** Snapshot audience state for a brand+platform at a point in time */
  snapshotAudience(p: { tenantId: string; brandId: string; platform: Platform; snapshot: AudienceSnapshot }): Promise<void>;

  /** Track an experiment (create, update status, record conclusion) */
  trackExperiment(p: { tenantId: string; experiment: ExperimentInput }): Promise<{ experimentId: string }>;

  /** Assess workflow health metrics (success rate, override rate, quality) */
  assessWorkflowHealth(p: { tenantId: string; workflowId: string }): Promise<WorkflowHealth>;
}
```

#### U4: Notification — Cross-cutting notification infrastructure

```typescript
export interface NotificationActivities {
  /** Alert a user in real-time via SSE (through Upstash Redis pub/sub) */
  alert(params: {
    tenantId: string;
    userId?: string;
    event: SSEEvent;
  }): Promise<void>;

  /** Notify a user via email */
  notify(params: {
    to: string;
    template: EmailTemplate;
    data: Record<string, unknown>;
  }): Promise<void>;
}
```

#### U5: AI — Cross-cutting AI model access infrastructure

AI model access is a **Utility**, not a ResourceAccess component. It passes the cappuccino machine test — any system could use AI model access. It's used across every layer: Engines for prompt execution, RA for resilience/retries, Clients for chatbot interfaces, even other Utilities for smart logging.

The Vercel AI SDK + OpenRouter serves as the implementation.

```typescript
export interface AIUtility {
  /**
   * Generate a text completion. Used by all Engines for their domain-specific
   * prompts, by RA for smart error handling, by Clients for conversational UI.
   */
  complete(params: {
    messages: AIMessage[];
    model?: string;         // Defaults to config, overridable per call
    tools?: AITool[];
    temperature?: number;
    maxTokens?: number;
  }): Promise<AICompletion>;

  /**
   * Generate a structured response conforming to a Zod schema.
   * Primary pattern for Engine activities that need typed outputs.
   */
  structure<T>(params: {
    messages: AIMessage[];
    schema: z.ZodType<T>;
    schemaName: string;
    model?: string;
  }): Promise<T>;

  /**
   * Generate a vector embedding for semantic search.
   * Used by E4 (knowledge indexing) and RA4 (vector search).
   */
  embed(params: {
    text: string;
    model?: string; // Defaults to text-embedding-3-small
  }): Promise<{ embedding: number[] }>;
}
```

### 3.5 Worker Registration

```typescript
// workers/presence/src/worker.ts

import { Worker, NativeConnection } from '@temporalio/worker';
import * as presenceWorkflows from '@presence-os/temporal-workflows/presence';
import * as activities from '@presence-os/temporal-activities';
import { TASK_QUEUES } from '@presence-os/temporal-client';
import { getConnection } from './config';

async function run() {
  const connection = await getConnection();
  const worker = await Worker.create({
    connection,
    namespace: process.env.TEMPORAL_NAMESPACE!,
    taskQueue: TASK_QUEUES.PRESENCE,
    workflowsPath: require.resolve('@presence-os/temporal-workflows/presence'),
    activities, // All E1-E4, RA1-RA4, U4 activities
    maxActivityTaskExecutors: 100,
    maxWorkflowTaskExecutors: 50,
  });
  await worker.run();
}

run().catch(console.error);
```

### 3.6 Manager → Manager Communication (QUEUED)

Per Löwy's architecture, Manager-to-Manager calls must be asynchronous. This maps to Temporal child workflows or signal-based invocation:

```typescript
// In presence.assessGraduation workflow (M1):
// When graduation is approved, start the M2 automation.execute workflow

import { startChild } from '@temporalio/workflow';
import { TASK_QUEUES } from '@presence-os/temporal-client';

// M1 → M2: Queued handoff via child workflow on different task queue
const automationHandle = await startChild('automation.execute', {
  taskQueue: TASK_QUEUES.AUTOMATION, // Routes to automation worker
  args: [{
    tenantId,
    brandId,
    workflowId,
    workflowDef: graduatedDef,
  }],
  workflowId: `automation-execute-${workflowId}-${Date.now()}`,
  parentClosePolicy: 'ABANDON', // M2 continues even if M1 workflow completes
});
```

### 3.7 Temporal Schedules (U2: Scheduling)

Temporal Schedules replace the U2: Scheduling utility for all recurring triggers:

```typescript
// packages/temporal-client/src/schedules.ts

import { Client, ScheduleOverlapPolicy } from '@temporalio/client';
import { TASK_QUEUES } from './task-queues';

export async function createPresenceSchedules(client: Client, tenantId: string, brandId: string) {
  // CUC2: Monthly knowledge evolution cycle
  await client.schedule.create({
    scheduleId: `evolve-${tenantId}-${brandId}`,
    action: {
      type: 'startWorkflow',
      workflowType: 'presence.evolve',
      args: [{ tenantId, brandId, trigger: 'scheduled' }],
      taskQueue: TASK_QUEUES.PRESENCE,
    },
    spec: {
      calendars: [{ hour: [2], dayOfMonth: [1] }], // 1st of month, 2am UTC
    },
    policies: { overlap: ScheduleOverlapPolicy.SKIP },
  });

  // CUC3: Weekly workflow graduation assessment
  await client.schedule.create({
    scheduleId: `assess-graduation-${tenantId}-${brandId}`,
    action: {
      type: 'startWorkflow',
      workflowType: 'presence.assessGraduation',
      args: [{ tenantId, brandId, workflowId: '*' }], // Assess all workflows
      taskQueue: TASK_QUEUES.PRESENCE,
    },
    spec: {
      calendars: [{ hour: [3], dayOfWeek: [1] }], // Monday 3am UTC
    },
    policies: { overlap: ScheduleOverlapPolicy.SKIP },
  });
}
```

---

## 4. API & Contract Design

### 4.1 Inter-Service HTTP Endpoints

Only two services expose HTTP endpoints publicly: API Gateway (C3) and Realtime (I1). The frontends (C1, C2) call these services and also interact with Temporal workflows via the API Gateway.

#### API Gateway (C3) — Hono Server

```
POST   /api/v1/workflows/start          Start a Temporal workflow (authenticated)
GET    /api/v1/workflows/:id/status     Query workflow status
POST   /api/v1/workflows/:id/signal     Send signal to running workflow

POST   /api/v1/webhooks/stripe          Stripe billing webhooks
POST   /api/v1/webhooks/x               X/Twitter platform webhooks
POST   /api/v1/webhooks/linkedin        LinkedIn platform webhooks

POST   /api/v1/content/submit           External content idea submission (API key auth)
GET    /api/v1/analytics/export          Analytics export API (API key auth)

GET    /api/v1/auth/callback/:platform   OAuth callback handler
GET    /health                           Health check
```

#### Realtime Server (I1) — SSE Endpoints

```
GET    /events/:tenantId                SSE stream for tenant (JWT auth)
GET    /events/:tenantId/:brandId       SSE stream filtered to brand
GET    /health                          Health check
```

### 4.2 Zod Schema Organization

All shared types are defined as Zod schemas in `packages/schemas/`. These serve triple duty: runtime validation, TypeScript type generation, and OpenAPI spec generation (via `zod-to-openapi`).

#### Core Entity Schemas

```typescript
// packages/schemas/src/brand.schemas.ts

import { z } from 'zod';

export const PlatformEnum = z.enum(['x', 'linkedin', 'substack']);
export type Platform = z.infer<typeof PlatformEnum>;

export const AutonomyLevel = z.enum(['manual', 'suggest', 'draft', 'autonomous']);

export const BrandSchema = z.object({
  id: z.string().uuid(),
  tenantId: z.string().uuid(),
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
  audienceDemographics: z.record(z.unknown()).optional(),
  autonomyLevel: AutonomyLevel.default('manual'),
  activePlatforms: z.array(PlatformEnum),
  createdAt: z.date(),
  updatedAt: z.date(),
});
export type Brand = z.infer<typeof BrandSchema>;

export const VoiceParametersSchema = z.object({
  brandId: z.string().uuid(),
  personality: z.object({
    formality: z.number().min(0).max(1),     // 0 = casual, 1 = formal
    humor: z.number().min(0).max(1),          // 0 = serious, 1 = humorous
    warmth: z.number().min(0).max(1),         // 0 = distant, 1 = warm
    authority: z.number().min(0).max(1),      // 0 = peer, 1 = expert
  }),
  vocabulary: z.object({
    preferred: z.array(z.string()),
    avoided: z.array(z.string()),
    jargonLevel: z.enum(['none', 'light', 'moderate', 'heavy']),
  }),
  toneExamples: z.array(z.object({
    content: z.string(),
    context: z.string(),
    rating: z.number().min(1).max(5),
  })),
  audienceProfile: z.string(), // Natural language description
  updatedAt: z.date(),
});
export type VoiceParameters = z.infer<typeof VoiceParametersSchema>;
```

```typescript
// packages/schemas/src/content.schemas.ts

export const ContentStatusEnum = z.enum([
  'idea', 'draft', 'review', 'approved', 'scheduled', 'published', 'archived'
]);

export const ContentDraftSchema = z.object({
  id: z.string().uuid(),
  tenantId: z.string().uuid(),
  brandId: z.string().uuid(),
  type: z.enum(['post', 'thread', 'article', 'newsletter', 'microsite', 'email_sequence']),
  status: ContentStatusEnum,
  platform: PlatformEnum,
  title: z.string().optional(),
  body: z.string(),
  mediaUrls: z.array(z.string().url()).optional(),
  metadata: z.record(z.unknown()).optional(),
  workflowRunId: z.string().optional(), // Temporal workflow run ID
  createdAt: z.date(),
  updatedAt: z.date(),
});
export type ContentDraft = z.infer<typeof ContentDraftSchema>;
```

```typescript
// packages/schemas/src/task.schemas.ts

export const TaskTypeEnum = z.enum([
  'content_approval', 'content_revision', 'knowledge_review',
  'graduation_proposal', 'voice_input', 'growth_action',
  'brand_configuration', 'engagement_response', 'general'
]);

export const TaskStatusEnum = z.enum([
  'pending', 'assigned', 'in_progress', 'completed', 'expired', 'cancelled'
]);

export const TaskSchema = z.object({
  id: z.string().uuid(),
  tenantId: z.string().uuid(),
  brandId: z.string().uuid(),
  type: TaskTypeEnum,
  status: TaskStatusEnum,
  priority: z.enum(['low', 'medium', 'high', 'urgent']),
  title: z.string(),
  description: z.string(),
  context: z.record(z.unknown()), // Type-specific context payload
  assignedTo: z.string().uuid().optional(),
  dueAt: z.date().optional(),
  workflowId: z.string().optional(),      // Temporal workflow ID to signal on response
  workflowSignal: z.string().optional(),   // Signal name to send
  createdAt: z.date(),
  completedAt: z.date().optional(),
});
export type Task = z.infer<typeof TaskSchema>;

export const TaskResponseSchema = z.object({
  taskId: z.string().uuid(),
  response: z.discriminatedUnion('type', [
    z.object({ type: z.literal('approval'), approved: z.boolean(), notes: z.string().optional() }),
    z.object({ type: z.literal('revision'), instructions: z.string() }),
    z.object({ type: z.literal('text_input'), text: z.string() }),
    z.object({ type: z.literal('voice_input'), audioUrl: z.string().url() }),
    z.object({ type: z.literal('selection'), selectedOption: z.string() }),
  ]),
});
export type TaskResponse = z.infer<typeof TaskResponseSchema>;
```

```typescript
// packages/schemas/src/knowledge.schemas.ts

export const ConfidenceLevelEnum = z.enum(['low', 'medium', 'high', 'validated']);

export const FrameworkSchema = z.object({
  id: z.string().uuid(),
  tenantId: z.string().uuid(),
  title: z.string(),
  description: z.string(),
  source: z.object({
    type: z.enum(['book', 'empirical', 'user_correction', 'synthesis']),
    reference: z.string(), // Book title, experiment ID, etc.
    capturedAt: z.date(),
  }),
  confidence: z.object({
    level: ConfidenceLevelEnum,
    score: z.number().min(0).max(1),
    lastEvaluated: z.date(),
    evidence: z.array(z.object({
      type: z.enum(['authority', 'empirical', 'contradiction']),
      description: z.string(),
      date: z.date(),
    })),
  }),
  embedding: z.array(z.number()).optional(), // pgvector embedding
  tags: z.array(z.string()),
  relatedFrameworkIds: z.array(z.string().uuid()),
  createdAt: z.date(),
  updatedAt: z.date(),
});
export type Framework = z.infer<typeof FrameworkSchema>;
```

#### Workflow Input/Output Schemas

```typescript
// packages/schemas/src/temporal.schemas.ts

export const WorkflowStartRequestSchema = z.object({
  workflowType: z.string(),
  taskQueue: z.enum(['presence-queue', 'automation-queue', 'account-queue']),
  args: z.array(z.unknown()),
  workflowId: z.string().optional(), // Auto-generated if not provided
});

export const WorkflowStatusSchema = z.object({
  workflowId: z.string(),
  runId: z.string(),
  status: z.enum(['RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'TERMINATED', 'TIMED_OUT']),
  result: z.unknown().optional(),
  error: z.string().optional(),
});

export const WorkflowSignalRequestSchema = z.object({
  signalName: z.string(),
  args: z.array(z.unknown()),
});
```

### 4.3 SSE Event Schemas (I1: Message Bus)

```typescript
// packages/schemas/src/events.schemas.ts

export const SSEEventTypeEnum = z.enum([
  // Task lifecycle
  'task.created', 'task.updated', 'task.completed',
  // Content lifecycle
  'content.drafted', 'content.approved', 'content.published',
  // Workflow lifecycle
  'workflow.started', 'workflow.completed', 'workflow.failed',
  'workflow.graduation_proposed',
  // Knowledge updates
  'knowledge.updated', 'knowledge.conflict_detected',
  // Notifications
  'notification.new',
  // System
  'system.heartbeat',
]);
export type SSEEventType = z.infer<typeof SSEEventTypeEnum>;

export const SSEEventSchema = z.object({
  id: z.string().uuid(),
  type: SSEEventTypeEnum,
  tenantId: z.string().uuid(),
  brandId: z.string().uuid().optional(),
  timestamp: z.date(),
  data: z.record(z.unknown()),
});
export type SSEEvent = z.infer<typeof SSEEventSchema>;

// Typed event payloads
export const TaskCreatedEventSchema = SSEEventSchema.extend({
  type: z.literal('task.created'),
  data: z.object({
    taskId: z.string().uuid(),
    taskType: TaskTypeEnum,
    priority: z.enum(['low', 'medium', 'high', 'urgent']),
    title: z.string(),
  }),
});

export const ContentPublishedEventSchema = SSEEventSchema.extend({
  type: z.literal('content.published'),
  data: z.object({
    contentId: z.string().uuid(),
    platform: PlatformEnum,
    url: z.string().url().optional(),
  }),
});
```

### 4.4 OpenAPI Generation

OpenAPI specs are auto-generated from Zod schemas at build time, not hand-written:

```typescript
// apps/api-gateway/src/openapi.ts

import { OpenAPIRegistry } from '@asteasolutions/zod-to-openapi';
import { WorkflowStartRequestSchema, WorkflowStatusSchema } from '@presence-os/schemas';

const registry = new OpenAPIRegistry();

registry.registerPath({
  method: 'post',
  path: '/api/v1/workflows/start',
  description: 'Start a Temporal workflow',
  request: { body: { content: { 'application/json': { schema: WorkflowStartRequestSchema } } } },
  responses: { 200: { content: { 'application/json': { schema: WorkflowStatusSchema } } } },
});

// Generated at build: turbo run build --filter=api-gateway
// Output: apps/api-gateway/dist/openapi.json
```

---

## 5. Auth & RBAC Model

### 5.1 Authentication Flow

```
User → Supabase Auth (email/password or OAuth) → JWT issued
JWT → Sent in Authorization header on every request
API Gateway / SSE Server → Validate JWT via Supabase Auth library
Temporal Activities → Receive tenantId from workflow input (trusted, not from JWT)
```

### 5.2 JWT Structure

Supabase Auth issues JWTs with custom claims added via a database trigger:

```typescript
// JWT payload (decoded)
{
  sub: "user-uuid",                    // Supabase auth.users.id
  email: "paul@example.com",
  app_metadata: {
    tenant_id: "tenant-uuid",
    role: "owner",                     // owner | operator | viewer | api
    brand_permissions: {
      "brand-uuid-1": ["read", "write", "approve", "publish"],
      "brand-uuid-2": ["read"]
    }
  },
  aud: "authenticated",
  exp: 1709251200
}
```

### 5.3 RBAC Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| **Owner** | Tenant account owner | Full access: billing, team, all brands, all actions |
| **Operator** | Content team member | Brand-scoped: create content, approve tasks, publish (per brand assignment) |
| **Viewer** | Read-only team member | Brand-scoped: view tasks, content, analytics. No write actions. |
| **API** | Programmatic access | API key auth. Scoped to specific endpoints (content submit, analytics export) |

### 5.4 Brand-Level Permissions

Permissions are assigned per brand per user. An Operator on Brand A may have full write access while only having read access on Brand B.

```typescript
// packages/auth/src/rbac.ts

export const BrandPermissions = z.enum([
  'read',       // View brand content, tasks, analytics
  'write',      // Create/edit content, respond to tasks
  'approve',    // Approve content for publishing
  'publish',    // Directly publish (bypass approval)
  'configure',  // Modify brand settings, autonomy levels, channels
]);

export function canUserPerformAction(
  jwt: DecodedJWT,
  brandId: string,
  requiredPermission: BrandPermission
): boolean {
  if (jwt.app_metadata.role === 'owner') return true;
  const brandPerms = jwt.app_metadata.brand_permissions?.[brandId];
  return brandPerms?.includes(requiredPermission) ?? false;
}
```

### 5.5 RLS Policy Design

Every table includes `tenant_id` for row-level security. Supabase RLS policies enforce tenant isolation at the database level:

```sql
-- Pattern: All tables follow this structure
ALTER TABLE brands ENABLE ROW LEVEL SECURITY;

-- Tenant isolation: users can only see their own tenant's data
CREATE POLICY "tenant_isolation" ON brands
  USING (tenant_id = (auth.jwt() ->> 'app_metadata')::jsonb ->> 'tenant_id');

-- Brand-level read: user must have 'read' permission for the brand
CREATE POLICY "brand_read" ON content
  FOR SELECT USING (
    tenant_id = current_tenant_id()
    AND (
      current_role() = 'owner'
      OR brand_id = ANY(brands_with_permission('read'))
    )
  );

-- Brand-level write: user must have 'write' permission for the brand
CREATE POLICY "brand_write" ON content
  FOR INSERT WITH CHECK (
    tenant_id = current_tenant_id()
    AND (
      current_role() = 'owner'
      OR brand_id = ANY(brands_with_permission('write'))
    )
  );

-- Helper functions (created as Supabase SQL functions)
CREATE OR REPLACE FUNCTION current_tenant_id() RETURNS uuid AS $$
  SELECT ((auth.jwt() ->> 'app_metadata')::jsonb ->> 'tenant_id')::uuid;
$$ LANGUAGE sql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION current_role() RETURNS text AS $$
  SELECT (auth.jwt() ->> 'app_metadata')::jsonb ->> 'role';
$$ LANGUAGE sql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION brands_with_permission(perm text) RETURNS uuid[] AS $$
  SELECT array_agg(key::uuid)
  FROM jsonb_each((auth.jwt() ->> 'app_metadata')::jsonb -> 'brand_permissions')
  WHERE value ? perm;
$$ LANGUAGE sql SECURITY DEFINER;
```

### 5.6 Service-Level Auth (Workers)

Temporal workers use a service role connection to Supabase (bypassing RLS) since tenant isolation is enforced at the workflow level — every workflow receives `tenantId` as input and passes it to every activity. Activities use Drizzle queries that always include `WHERE tenant_id = $tenantId`.

```typescript
// packages/db/src/client.ts

import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';

// Service role connection for workers (bypasses RLS)
const serviceConnection = postgres(process.env.DATABASE_URL!, {
  max: 20,
  idle_timeout: 30,
});

export const db = drizzle(serviceConnection);

// All queries MUST include tenant_id filter
// This is enforced by typed helper functions, not RLS
export function forTenant(tenantId: string) {
  return {
    brands: () => db.select().from(brands).where(eq(brands.tenantId, tenantId)),
    content: () => db.select().from(content).where(eq(content.tenantId, tenantId)),
    // ... etc
  };
}
```

---

## 6. Data Model (R1-R5)

High-level schema design. Detailed column-level schema is the deliverable of X-02 (PRE-2).

**Design principles for this data model:**

1. **Versioning for mutable entities.** Any entity that changes over time (identity prompts, content, knowledge frameworks) uses append-only version rows with `version` + `is_current` flags. Engines that detect patterns and trends need the full history — not just the latest state.

2. **Annotations table.** The annotation pattern (§3.4) requires a shared annotations table where Engines write versioned observations about content. E1 reads these when producing or revising. This table is the Engine-to-Engine communication channel, mediated by the database.

3. **Versioned DSL for JSONB.** Every JSONB column carries a `dsl_version` field inside the JSON object itself. This allows the type system to validate structure per-version and supports non-breaking schema evolution. The DSL version is a semver string (e.g., `"1.0.0"`). Breaking changes = major version bump. New optional fields = minor bump.

4. **Column descriptions.** Every column has a comment explaining its purpose. These are enforced as Drizzle schema comments and propagated to the database.

5. **Single identity prompt.** Brand identity uses a single freeform prompt (versioned) instead of separate personality/vocabulary/tone columns. The AI interprets the prompt holistically — splitting identity into dimensions is premature optimization that constrains the model.

6. **Audience demographics as a static, growing schema.** Demographic categories (age ranges, genders, regions, interests) are static in the real world — new categories may be added but existing ones don't disappear. The schema reflects this with a defined structure that only grows.

---

### 6.1 R1: Brand Store

```sql
-- tenants: Top-level account entity. One per paying customer.
tenants (
  id            uuid PK DEFAULT gen_random_uuid(),
  name          text NOT NULL,           -- Display name for the account (company or individual)
  email         text NOT NULL UNIQUE,    -- Primary billing contact email
  stripe_customer_id text UNIQUE,        -- Stripe customer ID for billing integration
  plan_tier     text NOT NULL DEFAULT 'free'
                CHECK (plan_tier IN ('free', 'starter', 'pro', 'enterprise')),
                                         -- Determines feature limits and pricing
  feature_flags jsonb NOT NULL DEFAULT '{"dsl_version": "1.0.0"}'::jsonb,
                                         -- Per-tenant feature toggles, versioned
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);

-- brands: A distinct identity/presence managed by the system.
-- Each brand has its own voice, channels, content pipeline, and analytics.
brands (
  id            uuid PK DEFAULT gen_random_uuid(),
  tenant_id     uuid NOT NULL REFERENCES tenants(id),
  name          text NOT NULL,           -- Brand display name (e.g., "Acme Blog")
  description   text,                    -- Freeform description of the brand's purpose
  autonomy_level text NOT NULL DEFAULT 'manual'
                CHECK (autonomy_level IN ('manual', 'suggest', 'draft', 'autonomous')),
                                         -- How much the system does without human approval
  growth_stage  text NOT NULL DEFAULT 'launch'
                CHECK (growth_stage IN ('launch', 'growth', 'mature')),
                                         -- Lifecycle stage, affects content strategy
  content_pillars text[] NOT NULL DEFAULT '{}',
                                         -- Thematic categories the brand publishes about
                                         -- e.g., ['Technical Deep Dives', 'Industry News', 'Team Culture']
  audience_demographics jsonb NOT NULL DEFAULT '{"dsl_version": "1.0.0"}'::jsonb,
                                         -- See §6.7 Audience Demographics Schema
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);

-- brand_identities: The brand's voice/personality as a single AI prompt.
-- Versioned: every refinement creates a new row. Engines and diffs use history.
brand_identities (
  id            uuid PK DEFAULT gen_random_uuid(),
  brand_id      uuid NOT NULL REFERENCES brands(id),
  tenant_id     uuid NOT NULL REFERENCES tenants(id),
  identity_prompt text NOT NULL,         -- The complete identity instruction for AI models.
                                         -- Freeform: includes personality, tone, vocabulary,
                                         -- audience awareness, do/don't rules. E2 reads this
                                         -- to evaluate content alignment.
  version       int NOT NULL DEFAULT 1,  -- Monotonically increasing. E2.refine() bumps this.
  is_current    boolean NOT NULL DEFAULT true,
                                         -- Only one row per brand is current. Previous versions
                                         -- remain for trend analysis and rollback.
  refined_from  uuid REFERENCES brand_identities(id),
                                         -- Points to the previous version this was refined from.
                                         -- NULL for the first version (created during onboarding).
  refinement_reason text,                -- Why this version was created (e.g., "user voice samples",
                                         -- "monthly identity refresh", "manual edit")
  created_at    timestamptz NOT NULL DEFAULT now()
);
-- UNIQUE constraint: only one is_current=true per brand_id
-- CREATE UNIQUE INDEX idx_brand_identities_current ON brand_identities (brand_id) WHERE is_current = true;

-- channel_connections: OAuth credentials and state for a brand's platform account.
channel_connections (
  id            uuid PK DEFAULT gen_random_uuid(),
  brand_id      uuid NOT NULL REFERENCES brands(id),
  tenant_id     uuid NOT NULL REFERENCES tenants(id),
  platform      text NOT NULL CHECK (platform IN ('x', 'linkedin', 'substack')),
                                         -- Target social platform
  oauth_token_encrypted text,            -- AES-256 encrypted OAuth access token
  oauth_refresh_token_encrypted text,    -- AES-256 encrypted refresh token
  token_expires_at timestamptz,          -- When the access token expires (RA1 auto-refreshes)
  platform_account_id text,              -- Platform's unique identifier for the connected account
  platform_account_name text,            -- Display name on the platform (for UI)
  is_active     boolean NOT NULL DEFAULT true,
                                         -- Soft-disable without losing credentials
  last_used_at  timestamptz,             -- Last time RA1 used this connection (for health monitoring)
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);

-- team_members: Maps auth.users to tenants with role-based permissions.
team_members (
  id            uuid PK DEFAULT gen_random_uuid(),
  tenant_id     uuid NOT NULL REFERENCES tenants(id),
  user_id       uuid NOT NULL REFERENCES auth.users(id),
  role          text NOT NULL CHECK (role IN ('owner', 'operator', 'viewer')),
                                         -- owner: full control. operator: brand-scoped work.
                                         -- viewer: read-only dashboards.
  brand_permissions jsonb NOT NULL DEFAULT '{}'::jsonb,
                                         -- Per-brand permission grants: { "brand_uuid": ["read", "write"] }
                                         -- Owners have implicit full access to all brands.
  invited_at    timestamptz NOT NULL DEFAULT now(),
  accepted_at   timestamptz              -- NULL until invitation accepted
);
```

### 6.2 R2: Content Store

```sql
-- content: A piece of content at a specific version. Versioned: edits create new rows.
-- The annotation pattern reads/writes annotations against content IDs.
content (
  id            uuid PK DEFAULT gen_random_uuid(),
  tenant_id     uuid NOT NULL REFERENCES tenants(id),
  brand_id      uuid NOT NULL REFERENCES brands(id),
  content_group_id uuid NOT NULL,        -- Groups all versions of the same logical content.
                                         -- First version sets this to its own id.
  version       int NOT NULL DEFAULT 1,  -- Monotonically increasing per content_group_id.
  is_current    boolean NOT NULL DEFAULT true,
                                         -- Only one row per content_group_id is current.
  type          text NOT NULL CHECK (type IN (
                  'post', 'thread', 'article', 'newsletter', 'microsite', 'email_sequence'
                )),                       -- Content format category
  status        text NOT NULL DEFAULT 'draft'
                CHECK (status IN (
                  'idea', 'draft', 'review', 'approved', 'scheduled', 'published', 'archived'
                )),                       -- Lifecycle state. advanceContent() moves this forward.
  platform      text NOT NULL CHECK (platform IN ('x', 'linkedin', 'substack')),
                                         -- Target platform (one content row per platform adaptation)
  title         text,                    -- Optional title (articles, newsletters have titles; tweets don't)
  body          text NOT NULL,           -- The actual content text. Platform formatting applied at publish.
  media_urls    text[] NOT NULL DEFAULT '{}',
                                         -- URLs to associated media in Supabase Object Storage
  metadata      jsonb NOT NULL DEFAULT '{"dsl_version": "1.0.0"}'::jsonb,
                                         -- Platform-specific metadata. See §6.8 Content Metadata DSL.
                                         -- Examples: thread ordering, hashtags, link previews
  campaign_id   uuid REFERENCES campaigns(id),
                                         -- NULL if standalone content; set if part of a campaign
  workflow_run_id text,                  -- Temporal workflow run ID that created/last modified this content
  scheduled_at  timestamptz,             -- When to publish (NULL = unscheduled)
  published_at  timestamptz,             -- When actually published (set by RA1.distribute)
  published_url text,                    -- URL on the platform after publishing
  platform_post_id text,                 -- Platform's native ID for the published post (for metrics linking)
  produced_by   text NOT NULL DEFAULT 'system',
                                         -- 'system' (AI-generated), 'human' (manual), 'hybrid' (AI + edits)
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);
-- UNIQUE constraint: one is_current per content_group_id
-- CREATE UNIQUE INDEX idx_content_current ON content (content_group_id) WHERE is_current = true;

-- content_annotations: The annotation pattern hub. Engines write here; E1 reads here.
-- Each annotation is immutable — new observations create new rows, never update existing.
content_annotations (
  id            uuid PK DEFAULT gen_random_uuid(),
  tenant_id     uuid NOT NULL REFERENCES tenants(id),
  content_id    uuid NOT NULL REFERENCES content(id),
                                         -- The content this annotation refers to
  annotation_type text NOT NULL CHECK (annotation_type IN (
                  'voice_alignment',     -- Written by E2: brand identity alignment assessment
                  'performance_insight', -- Written by E3: predicted engagement, audience fit
                  'strategic_guidance',  -- Written by E4: recommended angles, frameworks, timing
                  'content_brief'        -- Written by E4: pre-production guidance (before content exists)
                )),
  engine        text NOT NULL CHECK (engine IN ('E1', 'E2', 'E3', 'E4')),
                                         -- Which engine produced this annotation
  payload       jsonb NOT NULL,          -- Annotation-type-specific data. See §6.9 Annotation DSL.
                                         -- Always contains {"dsl_version": "1.0.0", ...}
  created_at    timestamptz NOT NULL DEFAULT now()
                                         -- Immutable: no updated_at. New observations = new rows.
);
-- Index for E1 to efficiently find latest annotations per content
-- CREATE INDEX idx_annotations_content_type ON content_annotations (content_id, annotation_type, created_at DESC);

-- campaigns: A coordinated content effort across multiple posts/platforms.
campaigns (
  id            uuid PK DEFAULT gen_random_uuid(),
  tenant_id     uuid NOT NULL REFERENCES tenants(id),
  brand_id      uuid NOT NULL REFERENCES brands(id),
  name          text NOT NULL,           -- Campaign display name
  description   text,                    -- Campaign goals and context
  status        text NOT NULL DEFAULT 'draft'
                CHECK (status IN ('draft', 'active', 'paused', 'completed')),
  start_date    date,                    -- Planned campaign start
  end_date      date,                    -- Planned campaign end
  content_plan  jsonb NOT NULL DEFAULT '{"dsl_version": "1.0.0"}'::jsonb,
                                         -- See §6.8 Content Plan DSL. Defines the planned
                                         -- content sequence, themes, platform targets, cadence.
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);

-- templates: Reusable content structures with variable placeholders.
templates (
  id            uuid PK DEFAULT gen_random_uuid(),
  tenant_id     uuid REFERENCES tenants(id),
                                         -- NULL = system-wide template available to all tenants
  brand_id      uuid REFERENCES brands(id),
                                         -- NULL = available to all brands in the tenant
  name          text NOT NULL,           -- Template display name
  description   text,                    -- What this template is for
  type          text NOT NULL,           -- Content type this template produces
  platform      text NOT NULL,           -- Target platform
  template_body text NOT NULL,           -- Template text with {{ variable }} placeholders
  variables     jsonb NOT NULL DEFAULT '{"dsl_version": "1.0.0"}'::jsonb,
                                         -- Variable definitions: name, type, description, default
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);
```

### 6.3 R3: Task Store

```sql
-- tasks: Human action items created by Managers when the system needs input/approval.
tasks (
  id            uuid PK DEFAULT gen_random_uuid(),
  tenant_id     uuid NOT NULL REFERENCES tenants(id),
  brand_id      uuid NOT NULL REFERENCES brands(id),
  type          text NOT NULL,           -- Task category. See TaskTypeEnum in shared schemas.
                                         -- Examples: 'content_review', 'voice_approval',
                                         -- 'input_needed', 'brand_config', 'experiment_review'
  status        text NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled', 'expired')),
                                         -- Lifecycle. fulfillTask() advances this.
  priority      text NOT NULL DEFAULT 'medium'
                CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
                                         -- Determines ordering in C1 task queue
  title         text NOT NULL,           -- Human-readable task title shown in C1
  description   text,                    -- Detailed context about what needs to happen
  context       jsonb NOT NULL DEFAULT '{"dsl_version": "1.0.0"}'::jsonb,
                                         -- Type-specific payload. For content_review: includes
                                         -- content_id, diff_from_previous, annotation summaries.
                                         -- Versioned via DSL.
  assigned_to   uuid REFERENCES team_members(id),
                                         -- NULL = unassigned (available to any team member with access)
  due_at        timestamptz,             -- Optional deadline. Overdue tasks get priority boost.
  workflow_id   text,                    -- Temporal workflow ID waiting for this task's response.
                                         -- Used to signal the workflow when task is completed.
  workflow_signal text,                  -- The Temporal signal name to send when task completes
  created_at    timestamptz NOT NULL DEFAULT now(),
  completed_at  timestamptz,             -- When the task was completed or cancelled
  updated_at    timestamptz NOT NULL DEFAULT now()
);

-- task_responses: The human's response to a task. Immutable per response.
task_responses (
  id            uuid PK DEFAULT gen_random_uuid(),
  task_id       uuid NOT NULL REFERENCES tasks(id),
  tenant_id     uuid NOT NULL REFERENCES tenants(id),
  responded_by  uuid NOT NULL REFERENCES team_members(id),
                                         -- Who responded
  response_type text NOT NULL CHECK (response_type IN (
                  'approval', 'rejection', 'revision', 'text_input', 'voice_input', 'selection'
                )),                       -- What kind of response this is
  response_data jsonb NOT NULL DEFAULT '{"dsl_version": "1.0.0"}'::jsonb,
                                         -- Response payload. For revision: includes edit instructions.
                                         -- For approval: may include optional notes.
  created_at    timestamptz NOT NULL DEFAULT now()
);
```

### 6.4 R4: Knowledge Store

```sql
-- knowledge_frameworks: Extracted strategic frameworks from ingested sources.
-- Versioned: reconciliation updates create new versions with updated confidence.
knowledge_frameworks (
  id            uuid PK DEFAULT gen_random_uuid(),
  tenant_id     uuid NOT NULL REFERENCES tenants(id),
  framework_group_id uuid NOT NULL,      -- Groups versions of the same framework
  version       int NOT NULL DEFAULT 1,  -- Bumped by E4.reconcile() when evidence updates confidence
  is_current    boolean NOT NULL DEFAULT true,
  title         text NOT NULL,           -- Framework name (e.g., "Hook-Story-Offer for LinkedIn posts")
  description   text NOT NULL,           -- What the framework recommends and when to apply it
  source_id     uuid REFERENCES knowledge_sources(id),
                                         -- Which source this was extracted from
  source_type   text NOT NULL CHECK (source_type IN (
                  'book', 'empirical', 'user_correction', 'synthesis'
                )),                       -- Origin: book = from ingested material, empirical = from
                                         -- performance data, user_correction = human override,
                                         -- synthesis = AI-combined from multiple sources
  confidence_score float NOT NULL DEFAULT 0.5
                CHECK (confidence_score BETWEEN 0 AND 1),
                                         -- How much evidence supports this framework.
                                         -- Starts at 0.5, adjusted by E4.reconcile()
  confidence_level text NOT NULL DEFAULT 'medium'
                CHECK (confidence_level IN ('low', 'medium', 'high', 'validated')),
                                         -- Human-readable confidence bucket
  last_evaluated timestamptz,            -- When E4.reconcile() last checked this against data
  evidence      jsonb NOT NULL DEFAULT '{"dsl_version": "1.0.0", "entries": []}'::jsonb,
                                         -- Array of evidence entries: { date, analysis_id, delta,
                                         -- content_ids, notes }. Records each reconciliation.
  tags          text[] NOT NULL DEFAULT '{}',
                                         -- Categorical tags for discovery (e.g., ['linkedin', 'hooks', 'b2b'])
  related_framework_ids uuid[] NOT NULL DEFAULT '{}',
                                         -- Cross-references to related/complementary frameworks
  embedding     vector(1536),            -- pgvector embedding for semantic search.
                                         -- Generated by U5.embed() via text-embedding-3-small.
  created_at    timestamptz NOT NULL DEFAULT now()
);

-- knowledge_sources: Ingested materials (books, articles, uploads).
-- Links to Supabase Object Storage for raw source files.
knowledge_sources (
  id            uuid PK DEFAULT gen_random_uuid(),
  tenant_id     uuid NOT NULL REFERENCES tenants(id),
  type          text NOT NULL CHECK (type IN ('book', 'article', 'url', 'upload')),
                                         -- What kind of source material this is
  title         text NOT NULL,           -- Source title (book name, article headline, etc.)
  author        text,                    -- Source author if known
  content_hash  text NOT NULL,           -- SHA-256 hash of source content for deduplication
  object_store_path text,                -- Path in Supabase Object Storage to the raw source file.
                                         -- e.g., 'knowledge/tenant_uuid/books/righting-software/'
                                         -- Contains: original file, chapter summaries, extracted frameworks.
  summary       text,                    -- AI-generated summary of the source
  processed_at  timestamptz,             -- When E4.ingest() finished processing this source.
                                         -- NULL = not yet processed.
  framework_count int NOT NULL DEFAULT 0,-- How many frameworks were extracted from this source
  created_at    timestamptz NOT NULL DEFAULT now()
);
```

### 6.5 R5: Performance Store

```sql
-- content_performance: Point-in-time performance snapshots harvested from platforms.
-- Append-only: each harvest cycle adds new rows, never updates existing ones.
content_performance (
  id            uuid PK DEFAULT gen_random_uuid(),
  tenant_id     uuid NOT NULL REFERENCES tenants(id),
  brand_id      uuid NOT NULL REFERENCES brands(id),
  content_id    uuid NOT NULL REFERENCES content(id),
  platform      text NOT NULL,           -- Which platform these metrics are from
  impressions   int NOT NULL DEFAULT 0,  -- Number of times the content was shown
  engagements   int NOT NULL DEFAULT 0,  -- Sum of likes + comments + shares + saves
  clicks        int NOT NULL DEFAULT 0,  -- Link clicks or profile visits from this content
  reach         int NOT NULL DEFAULT 0,  -- Unique accounts that saw this content
  engagement_rate float NOT NULL DEFAULT 0,
                                         -- engagements / impressions. Pre-computed for queries.
  raw_platform_data jsonb NOT NULL DEFAULT '{"dsl_version": "1.0.0"}'::jsonb,
                                         -- Full platform API response preserved for future analysis.
                                         -- Structure varies by platform — DSL version tracks format.
  captured_at   timestamptz NOT NULL DEFAULT now()
                                         -- When RA1.harvest() captured this snapshot
);

-- audience_metrics: Point-in-time audience snapshots per platform.
-- Append-only: each harvest adds a new row for trend analysis.
audience_metrics (
  id            uuid PK DEFAULT gen_random_uuid(),
  tenant_id     uuid NOT NULL REFERENCES tenants(id),
  brand_id      uuid NOT NULL REFERENCES brands(id),
  platform      text NOT NULL,           -- Which platform
  followers     int NOT NULL DEFAULT 0,  -- Total follower/subscriber count at capture time
  follower_growth int NOT NULL DEFAULT 0,-- Delta since previous capture
  demographics  jsonb NOT NULL DEFAULT '{"dsl_version": "1.0.0"}'::jsonb,
                                         -- See §6.7 Audience Demographics Schema.
                                         -- Platform-reported demographic breakdown.
  active_times  jsonb NOT NULL DEFAULT '{"dsl_version": "1.0.0"}'::jsonb,
                                         -- When the audience is most active.
                                         -- { hour_of_day: { "0": count, "1": count, ... },
                                         --   day_of_week: { "mon": count, ... } }
  captured_at   timestamptz NOT NULL DEFAULT now()
);

-- ab_tests: A/B experiment definitions and results.
ab_tests (
  id            uuid PK DEFAULT gen_random_uuid(),
  tenant_id     uuid NOT NULL REFERENCES tenants(id),
  brand_id      uuid NOT NULL REFERENCES brands(id),
  name          text NOT NULL,           -- Experiment name (e.g., "Hook style A vs B")
  hypothesis    text NOT NULL,           -- What we're testing and what we expect
  status        text NOT NULL DEFAULT 'draft'
                CHECK (status IN ('draft', 'running', 'concluded')),
  variants      jsonb NOT NULL DEFAULT '{"dsl_version": "1.0.0", "variants": []}'::jsonb,
                                         -- Array of { id, description, content_ids[] }.
                                         -- Each variant is a distinct treatment.
  winner_variant_id text,                -- Set by E3.concludeExperiment() when significance reached
  statistical_significance float,        -- p-value or confidence level at conclusion
  started_at    timestamptz,
  concluded_at  timestamptz
);

-- workflow_performance: Tracks how well automated workflows perform over time.
-- Used by M2 (automation.workflowGraduation) to decide autonomy level changes.
workflow_performance (
  id            uuid PK DEFAULT gen_random_uuid(),
  tenant_id     uuid NOT NULL REFERENCES tenants(id),
  brand_id      uuid NOT NULL REFERENCES brands(id),
  workflow_type text NOT NULL,           -- Temporal workflow type name
  execution_count int NOT NULL DEFAULT 0,-- Total executions tracked
  success_rate  float NOT NULL DEFAULT 0,-- Successful completions / total executions
  human_override_rate float NOT NULL DEFAULT 0,
                                         -- How often a human overrode the system's decision.
                                         -- High override rate = not ready for more autonomy.
  quality_score float NOT NULL DEFAULT 0,-- Composite quality metric (engagement + alignment + timeliness)
  last_executed_at timestamptz,          -- When this workflow last ran
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);

-- audit_log: High-value state changes for compliance and debugging.
-- Append-only. Never deleted. Queryable for incident investigation.
audit_log (
  id            uuid PK DEFAULT gen_random_uuid(),
  tenant_id     uuid NOT NULL REFERENCES tenants(id),
  actor_id      uuid,                    -- Who performed the action (NULL = system/automated)
  actor_type    text NOT NULL CHECK (actor_type IN ('user', 'system', 'workflow')),
  action        text NOT NULL,           -- What happened: 'content.published', 'brand.created',
                                         -- 'workflow.graduated', 'identity.refined', etc.
  entity_type   text NOT NULL,           -- Which entity type was affected
  entity_id     uuid NOT NULL,           -- Which specific entity
  details       jsonb NOT NULL DEFAULT '{}'::jsonb,
                                         -- Action-specific details (before/after, reason, etc.)
  created_at    timestamptz NOT NULL DEFAULT now()
);
```

### 6.6 Cross-Cutting: Versioning Strategy

All mutable entities follow the same versioning pattern:

```
entity_group_id  — Groups all versions of the same logical entity (uuid)
version          — Monotonically increasing integer (1, 2, 3, ...)
is_current       — Boolean, exactly one true per group
```

**Which entities are versioned:**

| Entity | Version Column | Why |
|--------|---------------|-----|
| `brand_identities` | `version` + `is_current` | E2 needs identity history to detect drift. Rollback support. |
| `content` | `version` + `is_current` via `content_group_id` | E1.revise() creates new versions. Diff against previous for review tasks. |
| `knowledge_frameworks` | `version` + `is_current` via `framework_group_id` | E4.reconcile() updates confidence over time. Trend analysis. |

**Entities that are NOT versioned (append-only or immutable):**

| Entity | Why Not Versioned |
|--------|------------------|
| `content_annotations` | Already immutable — new observations = new rows |
| `content_performance` | Append-only time series — never updated |
| `audience_metrics` | Append-only snapshots |
| `audit_log` | Append-only by definition |
| `task_responses` | Immutable per response |

**Entities that are mutable but not versioned (simple updated_at):**

| Entity | Why |
|--------|-----|
| `tenants` | Changes are rare, low-value for history (name/email changes) |
| `brands` | Config changes are logged in audit_log, not worth full versioning |
| `channel_connections` | Token refreshes are frequent, history not valuable |
| `tasks` | Status transitions logged in audit_log |
| `campaigns` | Status changes, not content changes — audit_log sufficient |

### 6.7 Audience Demographics Schema

Audience demographics use a defined, growing schema. Categories are static in the real world — we add new categories but never remove existing ones.

```typescript
// packages/shared-types/src/demographics.ts — DSL v1.0.0

interface AudienceDemographics {
  dsl_version: '1.0.0';

  age_ranges?: {
    '13-17'?: number;   // Percentage of audience in this range
    '18-24'?: number;
    '25-34'?: number;
    '35-44'?: number;
    '45-54'?: number;
    '55-64'?: number;
    '65+'?: number;
  };

  genders?: {
    male?: number;      // Percentage
    female?: number;
    non_binary?: number;
    unspecified?: number;
  };

  regions?: {
    // ISO 3166-1 alpha-2 country codes → percentage
    [countryCode: string]: number;
  };

  languages?: {
    // BCP 47 language tags → percentage
    [languageTag: string]: number;
  };

  interests?: string[];  // Free-form interest categories reported by platform
                          // e.g., ['technology', 'entrepreneurship', 'marketing']

  professional_industries?: string[];  // LinkedIn-specific: industry categories
  company_sizes?: {
    '1-10'?: number;
    '11-50'?: number;
    '51-200'?: number;
    '201-500'?: number;
    '501-1000'?: number;
    '1001-5000'?: number;
    '5001+'?: number;
  };
}
```

**Growth rules:** New fields are added to the interface as optional properties. Existing fields are never removed or renamed. Consumers must handle missing fields gracefully. Major schema changes bump dsl_version.

### 6.8 JSONB DSL Versioning

Every JSONB column in the schema contains a `dsl_version` field. This enables type-safe parsing and non-breaking evolution.

```typescript
// packages/shared-types/src/dsl.ts

/**
 * Base type for all versioned JSONB payloads.
 * Every JSONB column wraps its data with this envelope.
 */
interface VersionedPayload {
  dsl_version: string; // Semver: "1.0.0", "1.1.0", "2.0.0"
}

/**
 * Content Plan DSL — stored in campaigns.content_plan
 */
interface ContentPlanV1 extends VersionedPayload {
  dsl_version: '1.0.0';
  entries: Array<{
    sequence_order: number;           // Position in the campaign timeline
    target_date?: string;             // ISO 8601 date
    platform: 'x' | 'linkedin' | 'substack';
    content_type: string;             // post, thread, article, etc.
    topic: string;                    // What this content should be about
    pillar?: string;                  // Which content pillar this belongs to
    notes?: string;                   // Additional guidance for E4/E1
  }>;
  cadence?: {
    posts_per_week: number;
    preferred_days?: string[];        // ['monday', 'wednesday', 'friday']
    preferred_times?: string[];       // ['09:00', '17:00'] in brand's timezone
  };
}

/**
 * Content Metadata DSL — stored in content.metadata
 */
interface ContentMetadataV1 extends VersionedPayload {
  dsl_version: '1.0.0';
  hashtags?: string[];                // Platform hashtags
  mentions?: string[];                // @mentions to include
  link_preview?: {                    // Open Graph / Twitter Card data
    url: string;
    title?: string;
    description?: string;
    image_url?: string;
  };
  thread_order?: number;              // For multi-tweet threads: position in thread
  thread_group_id?: string;           // Groups thread parts together
  newsletter_subject?: string;        // For Substack newsletters
  seo_keywords?: string[];            // For articles/microsites
}

/**
 * Annotation Payloads — stored in content_annotations.payload
 */

// E2 → voice_alignment
interface VoiceAlignmentAnnotationV1 extends VersionedPayload {
  dsl_version: '1.0.0';
  aligned: boolean;                   // Overall alignment verdict
  alignment_score: number;            // 0-1 continuous score
  identity_version: number;           // Which brand_identity version was used
  misalignments: Array<{
    location: string;                 // Where in the content (paragraph, sentence)
    issue: string;                    // What's wrong
    suggestion: string;               // How to fix it
  }>;
  strengths: string[];                // What's working well
}

// E3 → performance_insight
interface PerformanceInsightAnnotationV1 extends VersionedPayload {
  dsl_version: '1.0.0';
  predicted_engagement: {
    impressions: number;
    engagement_rate: number;
    confidence: number;               // How confident E3 is in this prediction
  };
  optimal_posting_windows: Array<{
    day_of_week: string;
    hour_utc: number;
    score: number;
  }>;
  audience_fit_score: number;         // 0-1: how well this matches the audience
  comparable_content_ids: string[];   // Similar past content for reference
  risk_factors: string[];             // Potential issues (controversial topic, saturated time slot)
}

// E4 → content_brief (pre-production)
interface ContentBriefAnnotationV1 extends VersionedPayload {
  dsl_version: '1.0.0';
  recommended_angles: string[];       // Content angle suggestions
  frameworks_to_apply: Array<{
    framework_id: string;
    framework_title: string;
    relevance_score: number;
  }>;
  audience_insights: string[];        // Current audience observations
  timing_recommendations: string[];   // Why now is good/bad for this topic
  risk_flags: string[];               // Topics to avoid, sensitivities
  competitive_context?: string;       // What competitors are saying about this topic
}

// E4 → strategic_guidance (post-production)
interface StrategicGuidanceAnnotationV1 extends VersionedPayload {
  dsl_version: '1.0.0';
  strategic_alignment_score: number;  // 0-1: how well content fits overall strategy
  framework_applications: Array<{
    framework_id: string;
    applied: boolean;
    notes: string;
  }>;
  improvement_suggestions: string[];  // Strategic improvements (not voice/identity)
  trend_relevance: number;            // 0-1: how timely this content is
}
```

**DSL evolution rules:**
1. Adding optional fields = minor version bump (1.0.0 → 1.1.0). Backward compatible.
2. Removing fields or changing types = major version bump (1.0.0 → 2.0.0). Migration required.
3. Parsers must handle unknown fields gracefully (ignore them).
4. Zod schemas validate per dsl_version: `discriminatedUnion('dsl_version', [v1Schema, v2Schema])`.
5. Database queries filter by dsl_version when structure matters.

---

## 7. Platform Integration

### 7.1 Platform Priority & API Requirements

| Platform | Priority | Auth Method | Posting API | Analytics API | Webhooks | Notes |
|----------|----------|-------------|-------------|---------------|----------|-------|
| **X (Twitter)** | P1 | OAuth 2.0 PKCE | `POST /2/tweets` | `GET /2/tweets/:id` + engagement metrics | Account Activity API | Paid API tier required ($100/mo Basic). Rate limits apply. |
| **LinkedIn** | P2 | OAuth 2.0 3-legged | `POST /ugcPosts` or `POST /posts` | `GET /organizationalEntityShareStatistics` | Webhooks (limited) | Requires Marketing Developer Platform approval. Company pages vs. personal profiles are different APIs. |
| **Substack** | P3 | TBD (see 7.2) | **No public API** | **No public API** | None | Major integration challenge. Decision deferred to P-07 (PRE-11). |

### 7.2 Substack Integration Approach

Substack does not offer a public API for posting or analytics. Three approaches to evaluate during P-07:

1. **Email-to-Post**: Substack supports publishing via email. RA1 adapter sends formatted email to Substack's import address. Limitations: no scheduling control, limited formatting, no analytics pull.

2. **Undocumented API**: Substack's web app uses internal APIs. Could reverse-engineer. Risk: breaking changes without notice, potential ToS violation.

3. **Browser Automation**: Use Playwright or similar to automate the Substack web interface. Most reliable for feature parity but highest maintenance cost.

**Architecture impact: None.** The RA1 adapter pattern (`ra1.publish(platform, content)`) abstracts the implementation. Whether RA1 uses a REST API, sends an email, or drives a browser is invisible to Managers and Engines. Decision can be deferred safely.

### 7.3 RA1 Platform Adapter Structure

RA1's public interface exposes only atomic business verbs (`distribute`, `harvest`, `connect`, `disconnect` — see §3.4). Internally, each platform gets an adapter that implements those verbs. The adapter encapsulates all platform volatility: official APIs, undocumented APIs, browser automation, email-to-post, OAuth flows, rate limit handling, and format translation.

```typescript
// packages/ra-channel/src/adapters/adapter.interface.ts

/**
 * Internal adapter interface. NOT the public RA1 contract.
 * Each platform implements this. The RA1 activity functions
 * select the right adapter by platform and delegate.
 *
 * Adapters know how to reach the platform (REST API, undocumented API,
 * email, Playwright automation) — callers don't.
 */
interface PlatformAdapter {
  /** Publish content. Handles format translation, auth, retries internally. */
  distribute(content: ContentPayload, credentials: EncryptedCredentials): Promise<DistributeResult>;

  /** Pull metrics. Handles pagination, normalization, rate limits internally. */
  harvest(period: DateRange, credentials: EncryptedCredentials): Promise<HarvestResult>;

  /** Full OAuth lifecycle: initiate or complete based on params. */
  authenticate(params: AuthParams): Promise<AuthResult>;

  /** Platform-specific format constraints. Used internally by distribute()
   *  to adapt content before posting — never exposed to callers. */
  readonly formatConstraints: PlatformFormatConstraints;
}

// Adapter registry — one per supported platform
const adapters: Record<Platform, PlatformAdapter> = {
  x: new XAdapter(),          // X API v2 (official) + undocumented endpoints as needed
  linkedin: new LinkedInAdapter(),  // Marketing Developer Platform API
  substack: new SubstackAdapter(),  // TBD in P-07: email-to-post, undocumented API, or Playwright
};

// RA1 activity functions delegate to the right adapter
// (see §3.4 for the public ChannelAccessActivities interface)
```

### 7.4 Platform Format Constraints (Internal)

```typescript
// packages/schemas/src/platform.schemas.ts

export const PlatformFormatRequirementsSchema = z.discriminatedUnion('platform', [
  z.object({
    platform: z.literal('x'),
    maxCharacters: z.literal(280), // Standard post
    maxThreadPosts: z.literal(25),
    mediaFormats: z.array(z.enum(['image/jpeg', 'image/png', 'image/gif', 'video/mp4'])),
    maxImages: z.literal(4),
    maxVideoLength: z.literal(140), // seconds
  }),
  z.object({
    platform: z.literal('linkedin'),
    maxCharacters: z.literal(3000), // Standard post
    articleMaxLength: z.literal(125000), // LinkedIn article
    mediaFormats: z.array(z.enum(['image/jpeg', 'image/png', 'video/mp4', 'application/pdf'])),
    maxImages: z.literal(20), // carousel
  }),
  z.object({
    platform: z.literal('substack'),
    maxCharacters: z.null(), // No hard limit
    supportsHTML: z.literal(true),
    mediaFormats: z.array(z.enum(['image/jpeg', 'image/png', 'image/gif'])),
    supportsSections: z.literal(true),
  }),
]);
```

---

## 8. Developer Experience

### 8.1 Local Development (.devcontainer)

Full local development environment runs all services with a single `docker compose up`:

```yaml
# .devcontainer/docker-compose.yml

version: '3.9'

services:
  # Development application container
  app:
    build:
      context: ..
      dockerfile: .devcontainer/Dockerfile
    volumes:
      - ..:/workspace:cached
    environment:
      NODE_ENV: development
      DATABASE_URL: postgresql://postgres:postgres@supabase-db:5432/postgres
      SUPABASE_URL: http://supabase-kong:8000
      SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY}
      SUPABASE_SERVICE_ROLE_KEY: ${SUPABASE_SERVICE_ROLE_KEY}
      TEMPORAL_ADDRESS: temporal:7233
      TEMPORAL_NAMESPACE: default
      REDIS_URL: redis://redis:6379
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
    depends_on:
      supabase-db:
        condition: service_healthy
      temporal:
        condition: service_started
      redis:
        condition: service_healthy
    ports:
      - "3000:3000"   # C1: Task UI
      - "3001:3001"   # C2: Admin Portal
      - "8000:8000"   # C3: API Gateway
      - "8001:8001"   # I1: Realtime SSE

  # Supabase PostgreSQL (with pgvector)
  supabase-db:
    image: supabase/postgres:15.6.1.143
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: postgres
    volumes:
      - supabase_db_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 10

  # Supabase Studio (web UI for DB inspection)
  supabase-studio:
    image: supabase/studio:latest
    environment:
      STUDIO_PG_META_URL: http://supabase-meta:8080
      SUPABASE_URL: http://supabase-kong:8000
      SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY}
      SUPABASE_SERVICE_ROLE_KEY: ${SUPABASE_SERVICE_ROLE_KEY}
    ports:
      - "54323:3000"
    depends_on:
      - supabase-db

  # Temporal dev server (all-in-one)
  temporal:
    image: temporalio/auto-setup:latest
    environment:
      - DB=postgresql
      - DB_PORT=5433
      - POSTGRES_USER=temporal
      - POSTGRES_PWD=temporal
      - POSTGRES_SEEDS=temporal-db
    depends_on:
      temporal-db:
        condition: service_healthy
    ports:
      - "7233:7233"

  # Temporal's own PostgreSQL (separate from app DB)
  temporal-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: temporal
      POSTGRES_PASSWORD: temporal
    volumes:
      - temporal_db_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U temporal"]
      interval: 5s
      timeout: 5s
      retries: 10

  # Temporal Web UI
  temporal-ui:
    image: temporalio/ui:latest
    environment:
      TEMPORAL_ADDRESS: temporal:7233
      TEMPORAL_CORS_ORIGINS: http://localhost:8080
    ports:
      - "8080:8080"
    depends_on:
      - temporal

  # Redis (Upstash-compatible for local dev)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 10

volumes:
  supabase_db_data:
  temporal_db_data:
  redis_data:
```

### 8.2 devcontainer.json

```json
{
  "name": "Presence OS",
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspace",
  "features": {
    "ghcr.io/devcontainers/features/node:1": { "version": "20" },
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },
  "postCreateCommand": "bash .devcontainer/post-create.sh",
  "forwardPorts": [3000, 3001, 5432, 6379, 7233, 8000, 8001, 8080, 54323],
  "portsAttributes": {
    "3000": { "label": "Task UI (C1)" },
    "3001": { "label": "Admin Portal (C2)" },
    "8000": { "label": "API Gateway (C3)" },
    "8001": { "label": "Realtime SSE (I1)" },
    "8080": { "label": "Temporal UI" },
    "54323": { "label": "Supabase Studio" },
    "5432": { "label": "PostgreSQL", "onAutoForward": "silent" },
    "6379": { "label": "Redis", "onAutoForward": "silent" },
    "7233": { "label": "Temporal gRPC", "onAutoForward": "silent" }
  }
}
```

### 8.3 Local Dev Scripts (root package.json)

```json
{
  "scripts": {
    "dev": "turbo dev",
    "dev:task-ui": "turbo dev --filter=task-ui",
    "dev:admin": "turbo dev --filter=admin-portal",
    "dev:gateway": "turbo dev --filter=api-gateway",
    "dev:realtime": "turbo dev --filter=realtime",
    "dev:workers": "concurrently \"turbo dev --filter=presence-worker\" \"turbo dev --filter=automation-worker\" \"turbo dev --filter=account-worker\"",
    "build": "turbo build",
    "test": "turbo test",
    "lint": "turbo lint",
    "typecheck": "turbo typecheck",
    "db:generate": "turbo db:generate --filter=@presence-os/db",
    "db:migrate": "turbo db:migrate --filter=@presence-os/db",
    "db:studio": "supabase studio",
    "db:reset": "supabase db reset"
  }
}
```

### 8.4 CI/CD Pipeline Design

#### ci.yml — Every Push

```yaml
name: CI
on: [push]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: pnpm turbo typecheck lint test
```

#### preview.yml — PR Preview Environments

```yaml
name: Preview
on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: pnpm turbo typecheck lint test

  deploy-previews:
    needs: test
    runs-on: ubuntu-latest
    steps:
      # Vercel: C1 Task UI preview
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_TASK_UI_PROJECT_ID }}
          working-directory: apps/task-ui

      # Vercel: C2 Admin Portal preview
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_ADMIN_PROJECT_ID }}
          working-directory: apps/admin-portal

      # Railway: PR environment for all backend services
      - uses: railway/deploy-action@v1
        with:
          railway-token: ${{ secrets.RAILWAY_TOKEN }}
          service: api-gateway
          environment: pr-${{ github.event.pull_request.number }}

      - uses: railway/deploy-action@v1
        with:
          railway-token: ${{ secrets.RAILWAY_TOKEN }}
          service: realtime
          environment: pr-${{ github.event.pull_request.number }}

      - uses: railway/deploy-action@v1
        with:
          railway-token: ${{ secrets.RAILWAY_TOKEN }}
          service: presence-worker
          environment: pr-${{ github.event.pull_request.number }}

      - uses: railway/deploy-action@v1
        with:
          railway-token: ${{ secrets.RAILWAY_TOKEN }}
          service: automation-worker
          environment: pr-${{ github.event.pull_request.number }}

      - uses: railway/deploy-action@v1
        with:
          railway-token: ${{ secrets.RAILWAY_TOKEN }}
          service: account-worker
          environment: pr-${{ github.event.pull_request.number }}

      # Supabase: Branch DB is handled automatically via Supabase GitHub integration
      # (configured in Supabase dashboard → Settings → Integrations)

      # Post PR comment with all preview URLs
      - uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## Preview Environment Ready
              | Service | URL |
              |---------|-----|
              | Task UI | [Preview](https://task-ui-pr-${context.issue.number}.vercel.app) |
              | Admin Portal | [Preview](https://admin-pr-${context.issue.number}.vercel.app) |
              | API Gateway | Railway PR env |
              | Database | Supabase branch (auto) |
              | Temporal | Shared dev namespace |`
            });
```

#### deploy.yml — Production (Main Branch)

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: pnpm turbo build

      # Supabase: Run migrations on production
      - uses: supabase/setup-cli@v1
      - run: supabase db push --project-ref ${{ secrets.SUPABASE_PROJECT_REF }}
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}

      # Vercel: Auto-deploys from main branch (configured in Vercel dashboard)
      # Railway: Auto-deploys from main branch (configured in Railway dashboard)
```

### 8.5 Infrastructure as Code Summary

| Concern | Location | Format |
|---------|----------|--------|
| Database schema | `packages/db/src/schema/` | Drizzle TypeScript |
| Database migrations | `supabase/migrations/` | Generated SQL |
| RLS policies | `supabase/migrations/` | SQL |
| Seed data | `supabase/seed.sql` | SQL |
| Railway service config | `workers/*/railway.json`, `apps/api-gateway/railway.json` | JSON |
| Vercel config | `apps/*/vercel.json` | JSON |
| CI/CD | `.github/workflows/` | YAML |
| Local dev | `.devcontainer/` | JSON + YAML |
| Turbo pipeline | `turbo.json` | JSON |
| TypeScript config | `tsconfig.base.json` + per-package | JSON |
| Temporal schedules | `packages/temporal-client/src/schedules.ts` | TypeScript (registered at deploy) |

**Everything is in the repo. No non-code configuration. Bad deploy = git revert.**

---

## 9. Cross-Cutting Concerns

### 9.1 U3: Logging / Monitoring

U3 is not a standalone service — it's a cross-cutting library used by every component. In our stack, it maps to:

**Structured Logging:** All services use a shared logging library (`packages/config/src/logger.ts`) built on [pino](https://getpino.io) that emits structured JSON logs with context fields (tenantId, brandId, workflowId, activityName, duration). Railway aggregates these automatically.

**Temporal Observability:** Temporal Cloud provides built-in visibility into workflow executions, activity completions, failures, and retries. The Temporal Web UI (exposed in dev at `:8080`) shows real-time workflow state. In production, Temporal Cloud's UI serves this role.

**Railway Metrics:** Railway provides built-in CPU/memory/network monitoring per service, log aggregation, and alerting. No separate monitoring service needed.

**Audit Trail:** Critical state changes (content published, workflow graduated, permission changed) are logged as structured events and can be queried via the logging backend. The `audit_log` table in the database captures high-value events for compliance.

```
packages/config/src/logger.ts → shared pino logger with tenant/brand context
Railway built-in → service metrics, log aggregation
Temporal Cloud → workflow/activity observability
audit_log table → high-value events for compliance queries
```

### 9.2 Integration Use Cases (VUC-I1, VUC-I2, VUC-I3)

The 3 Integration use cases don't require dedicated Temporal workflows — they route through existing ones via the API Gateway:

| Use Case | API Gateway Route | Routes To |
|----------|------------------|-----------|
| **VUC-I1: API Content Submission** | `POST /api/v1/content/submit` | Starts `presence.operate` workflow (same as CUC1, different entry point) |
| **VUC-I2: Platform Event Handling** | `POST /api/v1/webhooks/:platform` | Platform engagement → starts `presence.engagementResponse`. Billing webhooks → starts `account.billing`. |
| **VUC-I3: Analytics Export** | `GET /api/v1/analytics/export` | Direct database query via RA4 — no workflow needed (read-only operation) |

This means all 23 use cases are covered: 21 via dedicated Temporal workflows + 3 via API Gateway routing to existing workflows or direct queries.

### 9.3 Error Handling & Retry Strategy

Temporal provides built-in retry, timeout, and compensation. Default activity options per layer:

```typescript
// Engine activities: AI calls are expensive, retry cautiously
const engineDefaults = {
  startToCloseTimeout: '2 minutes',
  retry: {
    initialInterval: '5s',
    backoffCoefficient: 2,
    maximumAttempts: 3,
    nonRetryableErrorTypes: ['InvalidInputError', 'AuthenticationError'],
  },
};

// RA activities: External API calls, retry more aggressively
const raDefaults = {
  startToCloseTimeout: '30 seconds',
  retry: {
    initialInterval: '1s',
    backoffCoefficient: 2,
    maximumAttempts: 5,
    nonRetryableErrorTypes: ['NotFoundError', 'AuthenticationError'],
  },
};

// AI-specific activities: Long-running, expensive
const aiDefaults = {
  startToCloseTimeout: '5 minutes',
  scheduleToCloseTimeout: '15 minutes',
  retry: {
    initialInterval: '10s',
    maximumAttempts: 2, // AI calls are expensive, limit retries
    nonRetryableErrorTypes: ['ContentPolicyViolation', 'InvalidPromptError'],
  },
};
```

**Saga/Compensation Pattern:** For multi-step workflows (e.g., `presence.operate` that creates content then publishes), Temporal's built-in compensation handles rollback. If the publish activity fails after content was drafted, the workflow can catch the error and either retry, create a human task, or run compensating activities.

### 9.4 Rate Limiting & Quota Management

External API rate limits are handled at the RA layer:

| Service | Rate Limit Strategy |
|---------|-------------------|
| **OpenRouter** | Token bucket per tenant via Upstash Redis. Default: 100 req/min. Backpressure via Temporal activity retry with increasing delay. |
| **X API** | Per-app rate limits enforced in RA1 X adapter. 429 responses trigger exponential backoff via Temporal retry. |
| **LinkedIn API** | Per-app daily limits. RA1 LinkedIn adapter tracks daily usage in Redis. Rejects with clear error when limit approached. |
| **Stripe API** | Low-volume, not rate-limited in practice. Standard Temporal retry on 429/5xx. |

Tenant-level quotas (max content per day, max brands, max API calls) are enforced at the workflow level before activities are dispatched, reading quota config from the tenant's plan tier.

---

## 10. Testing, Observability & Operational Readiness

This section specifies the full testing strategy, observability stack, dashboards, alerting, on-call procedures, and operational runbooks. Every component, service, subsystem, workflow, and use case has a defined testing and monitoring contract. Nothing ships without passing every level of this pyramid.

### 10.1 Testing Strategy — The Pyramid

```
                    ┌──────────────┐
                    │   Load Tests │  ← System-wide capacity validation
                   ┌┴──────────────┴┐
                   │  Use Case Tests │  ← End-to-end use case scenarios
                  ┌┴────────────────┴┐
                  │  Workflow Tests    │  ← Temporal workflow execution
                 ┌┴──────────────────┴┐
                 │  Subsystem Tests    │  ← Vertical slice integration
                ┌┴────────────────────┴┐
                │  Service Tests        │  ← Single component integration
               ┌┴──────────────────────┴┐
               │  Module Tests           │  ← Intra-component modules
              ┌┴────────────────────────┴┐
              │  Unit Tests               │  ← Every exported function
              └──────────────────────────┘
```

**Tooling:**

| Concern | Tool | Why |
|---------|------|-----|
| Test Runner | **Vitest** | TypeScript-native, fast, workspace-aware, compatible with Turborepo caching |
| Temporal Testing | **@temporalio/testing** | In-process test server, time skipping, activity mocking |
| HTTP Mocking | **msw** (Mock Service Worker) | Intercepts at network level for RA1/RA2 platform API mocks |
| Database Testing | **Supabase local** (via Docker) | Real PostgreSQL with RLS, same engine as production |
| Load Testing | **k6** | Scriptable in JS/TS, CLI-driven, integrates with CI |
| Coverage | **v8 coverage** (via Vitest) | Built-in, no extra config |
| Snapshot/Contract | **Zod schema tests** | Schemas ARE the contracts — test schema parsing against fixtures |

**CI Integration:** All unit, module, service, and subsystem tests run in `ci.yml` on every PR. Workflow and use case tests run in `ci.yml` with the Temporal test server. Load tests run nightly on a schedule and on release tags.

---

### 10.2 Unit Testing — Every Exported Function

Every exported function in every package has at least one unit test. Unit tests are co-located in `__tests__/` directories adjacent to source files.

**By component type:**

| Component Type | What's Unit Tested | Mocking Strategy |
|----------------|-------------------|------------------|
| **E1-E4 Engines** | Prompt construction, annotation parsing, output validation, transformation logic | U5 AI responses mocked (deterministic fixtures), RA4 mocked |
| **RA1 Channel Access** | Platform adapter format translation, OAuth token refresh logic, metric normalization | HTTP responses mocked via msw |
| **RA2 Service Access** | Billing action routing, webhook payload parsing, deployment config generation | Stripe/Vercel APIs mocked via msw |
| **RA3 Conversation Access** | Message formatting, context window construction, recall ranking | Honcho API mocked |
| **RA4 Store Access** | Query construction, annotation serialization/deserialization, DSL version handling | In-memory database stubs |
| **U1 Auth** | JWT validation, RBAC permission checks, RLS policy helper functions | No external deps |
| **U2 Scheduling** | Schedule construction, cron expression generation, timezone handling | Temporal client mocked |
| **U3 Logging** | Log formatter, context enrichment, audit event construction | No external deps |
| **U4 Notification** | Notification routing logic, template rendering, delivery channel selection | Transport mocked |
| **U5 AI** | Provider routing, token counting, schema-constrained output parsing, retry logic | HTTP mocked via msw |
| **C1/C2 (Frontend)** | React component rendering, hook behavior, form validation | React Testing Library |
| **C3 API Gateway** | Route matching, middleware chains, request validation, error formatting | Supertest with mocked downstream |

**Naming convention:** `<function-name>.test.ts` adjacent to source. Test names follow `it('should <expected behavior> when <condition>')`.

**Coverage targets:**

| Package Type | Line Coverage | Branch Coverage |
|-------------|--------------|-----------------|
| Engines (E1-E4) | ≥ 90% | ≥ 85% |
| ResourceAccess (RA1-RA4) | ≥ 90% | ≥ 85% |
| Utilities (U1-U5) | ≥ 95% | ≥ 90% |
| Shared schemas | 100% | 100% |
| Frontend components | ≥ 80% | ≥ 75% |
| API Gateway routes | ≥ 90% | ≥ 85% |

---

### 10.3 Integration Testing — Module Through Use Case

Integration tests validate real component interactions at increasing scope. Each level adds real infrastructure and removes mocks.

#### 10.3.1 Module Tests — Intra-Component

Test internal module interactions within a single component. Example: E1's prompt builder → U5 AI call → annotation writer, all within the Content Engine package.

```typescript
// packages/engine-content/src/__tests__/produce.integration.test.ts
describe('E1.produce integration', () => {
  // Uses: real U5 AI (with test fixtures), mocked RA4
  it('should read ContentBrief annotation and produce platform-adapted content');
  it('should read VoiceAlignment annotation and apply corrections on revise');
  it('should handle missing annotations gracefully with default behavior');
});
```

**What's real:** Intra-package code, U5 AI utility (with deterministic test fixtures).
**What's mocked:** RA4 Store Access, external APIs.

#### 10.3.2 Service Tests — Single Component

Test a single component against real infrastructure. Example: RA1 Channel Access against a mock X API server, with a real Supabase DB.

```typescript
// packages/ra-channel/src/__tests__/distribute.service.test.ts
describe('RA1.distribute service test', () => {
  // Uses: real RA4 → real Supabase (local), msw for platform APIs
  it('should distribute content to X with correct format translation');
  it('should handle OAuth token refresh transparently');
  it('should write metrics to R5 via RA4 after successful harvest');
  it('should return clear error on rate limit (429) without retrying at this level');
});
```

**What's real:** The component under test, RA4, Supabase local, Redis local.
**What's mocked:** External platform APIs (via msw), Temporal (no workflows running).

#### 10.3.3 Subsystem Tests — Vertical Slice

Test a full vertical slice through the architecture. Each of the 5 subsystems has a test suite that validates Manager → Engine → ResourceAccess → Resource interaction.

| Subsystem | Test Scope | Key Scenarios |
|-----------|-----------|---------------|
| **Foundation** | U1-U5 + RA4 + R1-R5 | Auth flows, schema migrations, AI utility routing, store CRUD via atomic verbs |
| **Presence** | M1 + E1-E4 + RA1 + RA4 + R1-R5 | Full content production cycle including annotation pattern |
| **Account** | M3 + RA2 + RA4 + R1 | Onboarding, billing lifecycle, team management |
| **Automation** | M2 + E3 + RA4 + R5 | Workflow graduation, schedule management, A/B test conclusion |
| **Integration** | C3 + M1/M2/M3 | Webhook routing, API content submission, analytics export |

**What's real:** All components in the subsystem, Supabase local, Redis local, Temporal test server.
**What's mocked:** External APIs (platform, Stripe, Vercel) via msw.

#### 10.3.4 Workflow Tests — Temporal Execution

Every Temporal workflow has a dedicated test using `@temporalio/testing`'s `TestWorkflowEnvironment`. Activities are mocked to isolate workflow orchestration logic.

```typescript
// workers/presence/src/__tests__/presence-operate.workflow.test.ts
import { TestWorkflowEnvironment } from '@temporalio/testing';

describe('presence.operate workflow', () => {
  let env: TestWorkflowEnvironment;

  beforeAll(async () => {
    env = await TestWorkflowEnvironment.createLocal();
  });

  it('should execute annotation pattern: E4.brief → E1.produce → E2.evaluate → E3.assess → E1.revise → RA1.distribute');
  it('should create human review task when E2.evaluate returns aligned=false above threshold');
  it('should handle E1.produce failure with compensation (no orphan content)');
  it('should respect autonomy level: full-auto skips human approval');
  it('should respect autonomy level: supervised creates review task after production');
  it('should use time-skipping to validate scheduled publish timing');
  it('should propagate tenant/brand context through all activity calls');
});
```

**Workflow test matrix (all 21 workflows):**

| Manager | Workflow | Test Count (min) |
|---------|----------|-----------------|
| M1 | presence.operate | 8 |
| M1 | presence.engagementResponse | 4 |
| M1 | presence.analysisCycle | 5 |
| M1 | presence.experimentLifecycle | 6 |
| M1 | presence.identityRefinement | 4 |
| M1 | presence.knowledgeIngestion | 4 |
| M1 | presence.campaignOrchestration | 5 |
| M1 | presence.contentCalendarGeneration | 3 |
| M1 | presence.micrositeGeneration | 4 |
| M1 | presence.emailSequenceGeneration | 4 |
| M1 | presence.multiPlatformAdaptation | 3 |
| M1 | presence.knowledgeReconciliation | 3 |
| M1 | presence.voiceOnboarding | 4 |
| M1 | presence.collaborativeEditing | 3 |
| M2 | automation.workflowGraduation | 5 |
| M2 | automation.scheduleManagement | 3 |
| M2 | automation.experimentConclusion | 4 |
| M3 | account.onboarding | 5 |
| M3 | account.billing | 4 |
| M3 | account.teamManagement | 3 |
| M3 | account.brandConfiguration | 4 |

#### 10.3.5 Use Case Tests — End-to-End

Full use case tests exercise the entire system from Client entry to final state change. These run against the complete local stack (Supabase, Temporal test server, Redis, msw for external APIs).

Each of the 23 use cases (3 Core + 17 Variation + 3 Integration) has at least one happy-path and one error-path test.

```typescript
// tests/e2e/cuc1-operate-presence.e2e.test.ts
describe('CUC1: Operate a Presence — end-to-end', () => {
  it('happy path: user input → brief → produce → evaluate → assess → revise → distribute → metrics written');
  it('error path: platform publish fails → compensation → human task created');
  it('autonomy: full-auto completes without human intervention');
  it('autonomy: manual creates task at every decision point');
});
```

---

### 10.4 Load Testing

Load tests validate that the system handles expected and peak traffic without degradation. Run nightly in CI and before every release.

**Tool:** k6 (scriptable in JavaScript, CLI-driven, Grafana Cloud integration available).

**Scenarios:**

| Scenario | Description | Target | Success Criteria |
|----------|-------------|--------|-----------------|
| **Steady state** | 10 brands, each producing 3 content pieces/day, with background analysis cycles | Sustained 30 min | p95 workflow completion < 60s, zero errors |
| **Burst content** | 50 content pieces submitted simultaneously (campaign launch) | Peak burst | All workflows start within 10s, p95 completion < 120s |
| **Harvest storm** | All brands harvest metrics simultaneously (daily cron) | Concurrent 10 brands × 3 platforms | p95 < 30s per platform, no rate limit failures (backpressure works) |
| **Onboarding spike** | 5 new tenants onboarding simultaneously | Concurrent 5 | All complete within 60s |
| **Webhook flood** | 100 platform webhooks arrive in 10s | Burst | All processed, zero dropped, p95 < 5s |

**Load test infrastructure:** k6 scripts in `tests/load/`, running against a dedicated Railway environment (not preview, not production). Database seeded with representative data.

```
tests/
├── load/
│   ├── scenarios/
│   │   ├── steady-state.js
│   │   ├── burst-content.js
│   │   ├── harvest-storm.js
│   │   ├── onboarding-spike.js
│   │   └── webhook-flood.js
│   ├── helpers/
│   │   ├── auth.js           # Generate test JWTs
│   │   └── seed.js           # Seed test data
│   └── thresholds.json       # Pass/fail criteria
```

---

### 10.5 Observability Stack

We use existing managed tools — no self-hosted Grafana or Prometheus. The stack is cheap, low-ops, and sufficient for a small team.

| Layer | Tool | What It Provides |
|-------|------|-----------------|
| **Application Logs** | **Railway built-in** | Structured log aggregation, search, tail, per-service filtering |
| **Temporal Observability** | **Temporal Cloud UI** | Workflow execution history, activity timelines, failure traces, retry counts |
| **Application Metrics** | **PostHog** (free tier) | Custom events, funnels, dashboards, feature flags. Engines/RAs emit business metrics as PostHog events. |
| **Uptime & Endpoints** | **Better Uptime** (or Railway health checks) | Endpoint monitoring, status page, incident alerting |
| **Error Tracking** | **Sentry** (free tier) | Exception capture with stack traces, breadcrumbs, release tracking |
| **Database Monitoring** | **Supabase Dashboard** | Query performance, connection pooling, storage usage, RLS policy evaluation |
| **Redis Monitoring** | **Upstash Console** | Command count, memory, latency, rate limit hit counts |

**Why not Grafana/Prometheus:** For a team of 1-3 engineers, self-hosted monitoring is more burden than value. Railway + Temporal Cloud + PostHog + Sentry covers every observability need without infrastructure management. If we outgrow this, migrating to Grafana Cloud is straightforward because we emit structured logs and PostHog events with consistent schemas.

---

### 10.6 Metrics, SLIs & SLOs

#### 10.6.1 Service-Level Indicators (SLIs)

Every component emits metrics through structured logging (pino) and PostHog events. SLIs are computed from these emissions.

**Per-Engine SLIs:**

| Engine | SLI | Measurement |
|--------|-----|-------------|
| E1 Content | Production latency | Time from `produce()` call to content written |
| E1 Content | Revision rate | % of content requiring > 1 revision cycle |
| E2 Identity | Alignment rate | % of content where `evaluate()` returns `aligned: true` on first pass |
| E2 Identity | Evaluation latency | Time for `evaluate()` to complete |
| E3 Analytics | Assessment latency | Time for `assess()` to write annotation |
| E3 Analytics | Prediction accuracy | Predicted engagement vs. actual (measured after 7 days) |
| E4 Knowledge | Brief completeness | % of briefs that include ≥ 3 framework references |
| E4 Knowledge | Reconciliation delta | Average confidence score change per reconciliation cycle |

**Per-RA SLIs:**

| RA | SLI | Measurement |
|----|-----|-------------|
| RA1 Channel | Publish success rate | % of `distribute()` calls that succeed on first attempt |
| RA1 Channel | Harvest completeness | % of expected metrics successfully harvested per cycle |
| RA1 Channel | Platform latency | p95 response time per platform adapter |
| RA2 Service | Billing success rate | % of billing actions that complete without error |
| RA3 Conversation | Recall relevance | (Future: human-rated relevance of recalled context) |
| RA4 Store | Query latency | p95 for each atomic verb category |

**Per-Workflow SLIs:**

| Workflow | SLI | Target |
|----------|-----|--------|
| presence.operate | End-to-end latency (input → published) | p95 < 90s |
| presence.operate | Success rate | > 95% complete without human intervention (at full-auto) |
| presence.analysisCycle | Completion rate | 100% (scheduled, must complete) |
| automation.workflowGraduation | Assessment accuracy | (Future: human-validated graduation decisions) |
| account.onboarding | Time to first content | p95 < 5 min from signup |

#### 10.6.2 Service-Level Objectives (SLOs)

| SLO | Target | Window | Alerting Threshold |
|-----|--------|--------|--------------------|
| System availability | 99.5% | 30-day rolling | < 99% over 1 hour |
| Workflow completion rate | > 98% | 7-day rolling | < 95% over 1 hour |
| Content publish success | > 95% | 7-day rolling | < 90% over 4 hours |
| API Gateway p95 latency | < 500ms | 7-day rolling | > 1s over 15 min |
| Scheduled jobs on-time | > 99% | 7-day rolling | Any missed schedule |

---

### 10.7 Dashboards

Four dashboards, built in PostHog with data from structured logs and custom events.

#### Dashboard 1: System Health (ops — always visible)

| Panel | Source | Shows |
|-------|--------|-------|
| Workflow completion rate (24h) | Temporal Cloud metrics | Success / failure / timeout breakdown |
| Active workflow count | Temporal Cloud metrics | Current running workflows by type |
| Error rate by service | Sentry + structured logs | Errors per minute, grouped by worker/app |
| Railway service health | Railway metrics | CPU, memory, restarts per service |
| Database connections | Supabase dashboard | Active connections, pool utilization |
| Redis operations | Upstash console | Commands/sec, memory, rate limit hits |

#### Dashboard 2: Content Pipeline (product — daily review)

| Panel | Source | Shows |
|-------|--------|-------|
| Content produced today | PostHog events | Count by brand, platform, autonomy level |
| Annotation cycle health | PostHog events | Brief → Produce → Evaluate → Assess → Revise flow completion |
| Identity alignment trend | PostHog events | % aligned on first pass, 7-day trend |
| Platform publish status | PostHog events | Success/failure by platform, last 24h |
| Average time-to-publish | PostHog events | From user input to published, by brand |

#### Dashboard 3: Tenant & Billing (business — weekly review)

| Panel | Source | Shows |
|-------|--------|-------|
| Active tenants | PostHog events | Count, growth trend |
| Content volume by tenant | PostHog events | Usage vs. plan limits |
| AI token usage | PostHog events (from U5) | Tokens consumed per tenant, cost estimate |
| Billing events | PostHog events (from RA2) | Successful charges, failures, churn |
| Feature adoption | PostHog events | Which features each tenant uses |

#### Dashboard 4: Platform & External APIs (reliability — on-demand)

| Panel | Source | Shows |
|-------|--------|-------|
| Platform API success rate | PostHog events (from RA1) | Per-platform, 7-day trend |
| Platform API latency | PostHog events (from RA1) | p50/p95/p99 per platform |
| Rate limit hits | Redis + PostHog | Per-platform, per-tenant |
| OAuth token health | PostHog events (from RA1) | Tokens nearing expiry, refresh failures |
| External API dependency status | Better Uptime | Up/down for X API, LinkedIn API, Stripe, OpenRouter |

---

### 10.8 Alerting

Alerts are tiered by severity. All alerts route through the notification pipeline (U4) and external channels.

#### Alert Severity Levels

| Severity | Response Time | Channel | Examples |
|----------|--------------|---------|----------|
| **P1 — Critical** | < 15 min | SMS + Slack + PagerDuty | System down, all workflows failing, DB unreachable |
| **P2 — High** | < 1 hour | Slack + email | Platform publish failures > 50%, billing webhook failures |
| **P3 — Medium** | < 4 hours | Slack | Single platform degraded, AI latency elevated, error rate spike |
| **P4 — Low** | Next business day | Slack (low-priority channel) | Coverage gap, alignment trend declining, storage approaching limit |

#### Alert Rules

| Alert | Condition | Severity | Source |
|-------|-----------|----------|--------|
| Workflow failure spike | > 5 workflow failures in 15 min | P1 | Temporal Cloud |
| Database unreachable | Connection pool exhausted or connection timeout | P1 | Railway logs + Supabase |
| Worker crash loop | Any worker restarts > 3 times in 10 min | P1 | Railway |
| Platform publish failures | > 50% failure rate over 30 min | P2 | PostHog / Sentry |
| Billing webhook failures | Any Stripe webhook returns non-200 | P2 | Sentry |
| AI provider degraded | U5 p95 latency > 30s or error rate > 10% | P2 | PostHog / Sentry |
| Scheduled job missed | Any Temporal Schedule fires > 5 min late | P2 | Temporal Cloud |
| Single platform degraded | One platform error rate > 30% for 1 hour | P3 | PostHog |
| AI token burn rate | Tenant approaching daily token limit | P3 | PostHog |
| Error rate elevated | Any service > 5% error rate for 30 min | P3 | Sentry |
| Identity alignment declining | Brand alignment rate drops > 15% week-over-week | P4 | PostHog |
| Storage nearing limit | Supabase storage > 80% of plan | P4 | Supabase |
| Certificate/OAuth expiry | OAuth token expires within 7 days | P4 | PostHog (from RA1) |

---

### 10.9 On-Call Plan

#### Rotation

For a team of 1-3 engineers, the on-call model is simple:

- **Primary on-call:** Rotates weekly. Responsible for P1/P2 response.
- **Secondary on-call:** Available for escalation. Not paged unless primary doesn't acknowledge within 15 min.
- **Business hours coverage:** All engineers monitor Slack alerts channel.
- **Off-hours coverage:** Only P1 pages off-hours. P2-P4 wait until business hours unless trending toward P1.

#### Incident Response Procedure

```
1. ALERT FIRES
   ↓
2. ACKNOWLEDGE (< 5 min for P1, < 15 min for P2)
   ↓
3. ASSESS — Check the relevant runbook (§10.10)
   - What's the blast radius? (one tenant? all tenants? one platform?)
   - Is this a new failure or a known pattern?
   ↓
4. MITIGATE — Stop the bleeding
   - If platform API: disable the platform adapter (feature flag)
   - If AI provider: switch to fallback model via OpenRouter config
   - If database: check Supabase status page, connection pool
   - If worker: restart via Railway dashboard
   ↓
5. COMMUNICATE — Post in #incidents Slack channel
   - What: one-line description
   - Impact: who's affected
   - Status: mitigated / investigating / resolved
   ↓
6. RESOLVE — Fix the root cause
   ↓
7. POSTMORTEM — Within 48 hours for P1/P2
   - Timeline, root cause, mitigation, prevention
   - Blameless: focus on systems, not people
```

#### Escalation Path

| Step | Condition | Action |
|------|-----------|--------|
| 1 | Alert fires | Primary on-call paged |
| 2 | No ack in 15 min | Secondary on-call paged |
| 3 | No ack in 30 min | All engineers paged + Slack @channel |
| 4 | Incident > 1 hour unresolved | Evaluate: external help needed? (Supabase support, Temporal support, Railway support) |

---

### 10.10 Observability Write-ups — Operational Runbooks

Each subsystem has a runbook describing what "normal" looks like, what "bad" looks like, how to diagnose, and how to make safe changes.

#### 10.10.1 Presence Subsystem (M1 + E1-E4 + RA1)

**What normal looks like:**
- Workflow completion rate > 98%. Most workflows complete in 30-90 seconds.
- Annotation pattern completes in sequence: brief → produce → evaluate → assess → revise. Each annotation is timestamped within minutes of the previous.
- Identity alignment rate is stable (± 5% week-over-week). New brands start low (~60%) and climb over 2-4 weeks as the identity prompt refines.
- Platform publish success rate > 95%. Occasional 429s from X are expected and handled by Temporal retry.
- AI latency (U5) varies by model: 2-15s for generation, < 1s for embeddings.

**What bad looks like and how to diagnose:**

| Symptom | Likely Cause | Diagnosis Steps |
|---------|-------------|-----------------|
| Workflows stuck in "Running" for > 5 min | Activity timeout or worker crash | Check Temporal UI → find stuck workflow → check activity task queue → check Railway worker logs for OOM or crash |
| Annotation pattern incomplete (e.g., no VoiceAlignment written) | E2 activity failing silently | Check Temporal UI → workflow history → find failed E2 activity → check Sentry for E2 errors → check U5 AI responses |
| Alignment rate suddenly drops | Identity prompt corrupted or AI model change | Check brand's identity prompt version history → compare recent vs. previous → check if OpenRouter changed default model |
| Platform publish failures spike | Platform API change or rate limit | Check RA1 PostHog events → filter by platform → check msw-style error codes → check platform status page |
| Content quality degradation (human-reported) | Knowledge stale, frameworks outdated, or prompt drift | Check E4 knowledge freshness → last ingest date → reconciliation results → check E2 alignment annotations for patterns |

**Safe changes (non-degrading):**
- Adding a new platform adapter to RA1 (existing adapters unaffected)
- Updating AI model in OpenRouter config (roll back if alignment drops)
- Adjusting Temporal retry policy (only affects new workflow executions)
- Adding new annotation types (engines ignore annotations they don't recognize)

**Unsafe changes (require staged rollout):**
- Modifying the annotation pattern sequence in M1 workflows
- Changing identity prompt structure (affects all content production)
- Upgrading Temporal SDK version (test in preview env first)
- Modifying RA4 Store Access atomic verbs (breaks callers)

#### 10.10.2 Automation Subsystem (M2 + E3)

**What normal looks like:**
- Workflow graduation assessments run on schedule (weekly per brand).
- Most workflows stay at their current autonomy level. Graduations happen gradually (1-2 per month per brand).
- A/B tests run for their full duration. Conclusions happen at scheduled endpoints.
- Schedule management operations are rare (user-initiated).

**What bad looks like and how to diagnose:**

| Symptom | Likely Cause | Diagnosis Steps |
|---------|-------------|-----------------|
| Graduation assessment never fires | Temporal Schedule misconfigured or paused | Check Temporal Cloud → Schedules → find the brand's assessment schedule → check if paused or errored |
| Graduation thrashing (promoting then demoting) | Thresholds too tight or metrics volatile | Check E3 assessment history → look for oscillation pattern → review threshold config |
| A/B test never concludes | Insufficient traffic or experiment stuck | Check R5 experiment metrics → variant impression counts → if low, check if content is actually being produced for both variants |

**Safe changes:** Adjusting graduation thresholds, adding new experiment types.
**Unsafe changes:** Changing graduation state machine transitions, modifying schedule timing.

#### 10.10.3 Account Subsystem (M3 + RA2)

**What normal looks like:**
- Onboarding completes in < 5 minutes. Stripe customer created, default brand configured.
- Billing webhooks from Stripe process within seconds. Subscription state stays in sync.
- Team management operations are rare and always user-initiated.

**What bad looks like and how to diagnose:**

| Symptom | Likely Cause | Diagnosis Steps |
|---------|-------------|-----------------|
| Onboarding stuck | Stripe API failure or RA4 write failure | Check Temporal UI → onboarding workflow → find failed activity → check Sentry → check Stripe dashboard |
| Billing out of sync | Webhook delivery failure or processing error | Check Stripe webhook logs → check C3 API Gateway logs → check RA2 billing activity logs → compare Stripe state vs. R1 state |
| Team permissions wrong | RLS policy bug or role assignment error | Check user's JWT claims → check tenant_members table → check RLS policy evaluation in Supabase logs |

**Safe changes:** Adding new plan tiers, adjusting onboarding flow steps.
**Unsafe changes:** Modifying Stripe webhook processing, changing RLS policies.

#### 10.10.4 Foundation (U1-U5, RA4, I1)

**What normal looks like:**
- U1 Auth: JWT validation < 1ms. RLS policies add < 5ms to queries.
- U5 AI: Latency depends on model and task. Generation: 2-15s. Structured output: 3-20s. Embeddings: < 1s.
- RA4 Store: Query latency p95 < 50ms for simple reads, < 200ms for annotation queries with joins.
- I1 Realtime: SSE connections stable. Event delivery < 100ms from emission.

**What bad looks like and how to diagnose:**

| Symptom | Likely Cause | Diagnosis Steps |
|---------|-------------|-----------------|
| All requests 401 | Supabase Auth down or JWT signing key rotated | Check Supabase status → check JWT verification in U1 → check Supabase Auth config |
| AI responses slow or failing | OpenRouter provider degraded | Check OpenRouter status page → check U5 PostHog latency events → try fallback model |
| Database queries slow | Missing index, connection pool exhaustion, or large table scan | Check Supabase query performance dashboard → identify slow queries → check connection count → check for missing indexes on annotation tables |
| SSE connections dropping | Railway service restart or memory pressure | Check Railway service logs → check memory usage → check I1 connection count |

**Safe changes:** Adding new indexes, adding new utility functions, updating logging format.
**Unsafe changes:** Modifying RLS policies, changing JWT structure, upgrading Supabase schema.

---

### 10.11 Test Data & Fixtures

**Seed data strategy:** A `supabase/seed.sql` populates the local and test environments with representative data:

| Entity | Seed Count | Purpose |
|--------|-----------|---------|
| Tenants | 3 | Single-brand, multi-brand, max-plan |
| Brands | 5 | Different identity prompts, platforms, autonomy levels |
| Content (with annotations) | 50 | Various states: draft, reviewed, published, with full annotation chains |
| Knowledge frameworks | 10 | Representative frameworks with linked source materials |
| Performance metrics | 500 | 30 days of realistic engagement data across platforms |
| Team members | 8 | All 4 RBAC roles represented across tenants |

**AI fixture strategy:** For deterministic testing, U5 AI calls in test mode return pre-recorded fixtures. Fixtures are stored in `packages/testing/fixtures/ai/` and version-matched to prompt templates.

```
packages/testing/
├── fixtures/
│   ├── ai/                  # Deterministic AI response fixtures
│   │   ├── produce-v1.json
│   │   ├── evaluate-v1.json
│   │   ├── brief-v1.json
│   │   └── ...
│   ├── platforms/           # Mock platform API responses
│   │   ├── x-publish-success.json
│   │   ├── x-publish-rate-limited.json
│   │   ├── linkedin-metrics.json
│   │   └── ...
│   └── billing/             # Mock Stripe webhook payloads
│       ├── invoice-paid.json
│       ├── subscription-updated.json
│       └── ...
├── factories/               # Test data factories (TypeScript)
│   ├── brand.factory.ts
│   ├── content.factory.ts
│   ├── annotation.factory.ts
│   └── ...
└── helpers/
    ├── temporal.ts          # Temporal test environment setup
    ├── supabase.ts          # Local Supabase test helpers
    └── auth.ts              # Test JWT generation
```

---

## 11. Acceptance Criteria Checklist

### API & Contract Design

- [x] **OpenAPI specs defined for all inter-service HTTP endpoints** — §4.1 defines API Gateway and Realtime server endpoints. OpenAPI auto-generated from Zod schemas via `zod-to-openapi` (§4.4).
- [x] **Temporal Workflow definitions for all Managers** — §3.3 defines all M1 (14 workflows), M2 (3 workflows), M3 (4 workflows) with typed inputs/outputs/signals.
- [x] **Temporal Activity definitions for all Engines and ResourceAccess** — §3.4 defines all E1-E4 and RA1-RA4 activity interfaces with typed parameters and return types.
- [x] **Zod schemas for all shared types** — §4.2 defines entity schemas (Brand, Content, Task, Knowledge, Performance), workflow I/O types, and API contracts.
- [x] **I1 event schema defined** — §4.3 defines SSE event types, base event schema, and typed event payloads.
- [x] **Service-to-service communication patterns documented** — §2.4 maps all communication routes (Railway internal, Temporal Cloud, Supabase, Upstash, external APIs).

### Auth & Data Model

- [x] **Auth model defined** — §5.1-5.3 define JWT structure, 4 RBAC roles, brand-level permissions, Supabase Auth integration.
- [x] **RLS policy design** — §5.5 defines tenant isolation, brand-level read/write policies, and helper functions.
- [x] **Data model high-level design for R1-R5** — §6 defines all tables across 5 resource stores with key columns and relationships.

### Technology & Platform Decisions

- [x] **Platform priority list finalized** — §7.1 documents X, LinkedIn, Substack with API requirements per platform.
- [x] **AI model selection documented** — Single model via OpenRouter + Vercel AI SDK. AI is a cross-cutting Utility (U5) — see §3.4.
- [x] **Substack integration approach decided** — §7.2 documents three options, decision deferred to P-07 with zero architecture impact (adapter pattern).

### Service Architecture & Monorepo

- [x] **Monorepo directory structure defined** — §2.1 provides complete directory tree with service boundaries.
- [x] **Temporal Worker grouping decided** — §3.2 defines 3 task queues, §3.5 shows worker registration pattern.
- [x] **Railway service topology documented** — §2.3 diagrams all services with networking and deployment notes.

### Developer Experience (DX)

- [x] **.devcontainer spec** — §8.1-8.2 define Docker Compose with Supabase, Temporal dev server, Redis, and worker services.
- [x] **Local dev runs full system** — §8.1 all services start with Docker Compose, §8.3 provides script aliases.
- [x] **CI/CD pipeline design** — §8.4 defines ci.yml, preview.yml, and deploy.yml GitHub Actions workflows.
- [x] **Every PR produces isolated preview** — §8.4 preview.yml orchestrates Vercel + Supabase branch + Railway PR env.
- [x] **Production = merge to main** — §8.4 deploy.yml auto-deploys on main push. No non-code config.
- [x] **Infrastructure-as-Code** — §8.5 maps every concern to its in-repo location. Everything in the repo.

### Testing, Observability & Operational Readiness

- [x] **Unit test specification** — §10.2 defines unit testing for every exported function across all component types, with coverage targets and mocking strategies.
- [x] **Integration test specification** — §10.3 defines 5 levels: module, service, subsystem, workflow (all 21 workflows), and end-to-end use case (all 23 use cases).
- [x] **Load test specification** — §10.4 defines 5 k6 scenarios (steady state, burst, harvest, onboarding, webhook flood) with success criteria.
- [x] **Observability stack** — §10.5 selects Railway + Temporal Cloud + PostHog + Sentry + Better Uptime. No self-hosted infra.
- [x] **SLIs and SLOs** — §10.6 defines per-engine, per-RA, and per-workflow SLIs with measurable targets.
- [x] **Dashboards** — §10.7 specifies 4 dashboards (System Health, Content Pipeline, Tenant/Billing, Platform APIs) with panel definitions.
- [x] **Alerting** — §10.8 defines 4 severity levels, 13 alert rules, routing channels, and response time targets.
- [x] **On-call plan** — §10.9 defines rotation, incident response procedure, and escalation path.
- [x] **Operational runbooks** — §10.10 provides per-subsystem write-ups: normal behavior, failure symptoms, diagnosis steps, safe vs. unsafe changes.
- [x] **Test data strategy** — §10.11 defines seed data, AI fixtures, platform mocks, and test factories.
