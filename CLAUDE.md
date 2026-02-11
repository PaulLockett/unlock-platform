# Unlock Alabama Data Platform - Claude Code Context

## Working with Paul

### Communication Style
- **Be direct and efficient.** Skip preamble and get to the point.
- **Show reasoning, not just conclusions.** Externalize thinking so Paul can push back or adopt frameworks.
- **Mutual respect over status games.** Neither condescending nor falsely humble—just accurate signal.
- **Notice drift, name it.** When exploring tangents, flag it: "We've drifted into X. Continue or return to Y?"

### What Paul Values
- **Depth AND velocity.** He wants to understand WHY things work while also shipping fast.
- **Build to understand.** Creating things IS the learning, not preparation for it.
- **Reduce "what to do" ambiguity.** Clear next steps > vague directions. Help structure ambiguous tasks.
- **Concrete solutions + better ways of thinking.** Both outcomes matter.

### The Depth vs Velocity Tension

Paul operates with two drives that create productive tension:

**Depth:** He loves first-principles thinking, understanding _why_ things work, connecting ideas across domains. He wants to understand the system, not just build it.

**Velocity:** He also wants to move fast, ship work, iterate on real feedback rather than endless planning.

Neither is wrong. The best work honors both—deep enough to be sound, fast enough to get feedback. Help Paul find the right balance for each task rather than defaulting to one mode.

### Growth Edge
Paul is actively building conscientiousness—following through on commitments, especially small recurring ones. Support this with systems that reduce willpower load rather than pushing harder. When he seems stuck on a low-interest task, help break it into smaller steps rather than lecturing about mindset.

### Mindset Triggers

**Critical feedback** hits hardest. If something isn't working, frame it as "the approach" not "you."

**High-effort + low-interest tasks** create a conscientiousness trap. For boring-but-important work, help build systems that reduce willpower load rather than pushing harder.

### Task-Switching Depletes Willpower

Paul can code for hours without noticing time pass. But switching between cognitively different tasks drains willpower fast. The more ambiguity about _what to do_ (vs _how to perform_), the faster it depletes.

**What helps:**
- Clear systems and frameworks that reduce in-the-moment decision-making
- Having context on tasks before starting (not figuring it out on the fly)
- The task structure in Monday.com exists precisely for this

---

## Project Overview

**Unlock Alabama Data Platform** is a comprehensive data transformation and analytics system for aggregating, cleaning, and presenting civic/business data across Alabama. The platform enables citizens, researchers, and policymakers to access unified, clean data through an intuitive analytics interface.

**Primary goal:** Build a production-ready data platform that transforms raw civic data sources into actionable insights with proper access controls and schema management.

**Architecture:** 15 building blocks following Righting Software methodology (volatility-based decomposition, layered architecture).

---

## What We're Building

A data platform that:

1. **Ingests** data from multiple civic sources (APIs, files, scraped content)
2. **Transforms** raw data through configurable pipelines using the Transformation Engine
3. **Validates** and evolves schemas automatically via Schema Evolution Engine
4. **Controls access** through role-based permissions via Access Control Engine
5. **Presents** data through an Analytics Canvas for exploration and visualization
6. **Orchestrates** all workflows through a centralized Data Manager

**Key Insight:** The platform separates concerns by volatility—data sources change often, transformation rules evolve, but the orchestration layer remains stable.

**Output:** Clean, unified data accessible via API and interactive Analytics Canvas.

---

## Architecture (Righting Software Methodology)

This architecture was designed using **volatility-based decomposition**, NOT functional decomposition. Each component encapsulates an area of likely change—this is the core insight that makes the design resilient.

### Why This Matters

When you're implementing, constantly ask:
- "What might change here?" not "What does this do?"
- "Would this force changes elsewhere if requirements shift?"
- "Is this the right layer for this logic?"

If you catch yourself naming something by its function (ReportingService, DataProcessor), stop. That's functional decomposition. Name it by what volatility it encapsulates.

### Layered Structure (15 Building Blocks)

```
CLIENTS (WHO uses it)
└── CANVAS: Analytics Canvas - Interactive data exploration UI

MANAGERS (WHAT workflows/sequences)
└── DATA_MGR: Data Manager - Orchestrates ingestion, transformation, delivery

ENGINES (HOW business logic works)
├── TRANS_ENG: Transformation Engine - Configurable data pipelines
├── SCHEMA_ENG: Schema Evolution Engine - Automatic schema migration
└── ACC_ENG: Access Control Engine - Role-based permissions

RESOURCE ACCESS (WHERE data lives)
├── SRC_ACC: Source Access - Raw data source operations
├── DATA_ACC: Data Access - Transformed data operations
└── CFG_ACC: Config Access - Pipeline and schema configurations

UTILITIES (cross-cutting)
├── LLM_GW: LLM Gateway - AI-powered data quality and extraction
├── AUTH: Auth Service - Authentication and session management
└── SCHED: Scheduler - Recurring pipeline execution

ARCHITECTURE (foundation)
├── INFRA: Infrastructure - Repo, CI/CD, dev environment
├── INT_TEST: Integration Testing - Component integration validation
├── SYS_TEST: System Testing - End-to-end validation
├── DOCS: Documentation - API specs, guides
└── DEPLOY: Deployment - Production infrastructure
```

### Component Type Context

| Layer           | Role                 | What It Should Do                      | What It Should NOT Do           |
| --------------- | -------------------- | -------------------------------------- | ------------------------------- |
| Client          | Present interface    | Accept requests, return responses      | Contain business logic          |
| Manager         | Orchestrate workflow | Coordinate components, handle sequence | Implement algorithms            |
| Engine          | Execute logic        | Implement business rules               | Store data, orchestrate others  |
| Resource Access | Abstract storage     | Business verb operations               | CRUD operations, business logic |
| Utility         | Cross-cutting        | One capability, used anywhere          | Orchestrate workflows           |

**The hallmark of a bad design is when any change affects the client.** If you find yourself modifying Client code because business logic changed, something is in the wrong layer.

### Key Constraints

- **15 building blocks** - Well-factored (~10 recommended, up to ~20 acceptable)
- **1 Manager only** - 8+ Managers = design failure
- **Closed architecture** - Calls flow DOWN: Clients → Managers → Engines → Resources
- **Managers don't call Managers synchronously** - Creates hidden coupling
- **ResourceAccess exposes business verbs, NOT CRUD** - If you see Read/Write/Update, wrong abstraction

---

## Righting Software Principles

### Decompose by Volatility, Not Function
Components encapsulate what might change. If a component is named after a function (ReportingService), that's a smell. Ask: "What volatility does this contain?"

### ~10 Building Blocks
We have 15—appropriate for this complexity. 30+ = over-decomposed. 3 = hiding complexity.

### Architecture IS the Project
One activity per component. Dependencies between activities = dependencies between components.

### PERT Estimation
```
Expected = (Optimistic + 4×MostLikely + Pessimistic) / 6
```
Use 5-day quantum. Map to Fibonacci: 2, 3, 5, 8, 13.

### Risk Target: 0.50
Target project risk ≤ 0.50. Risk > 0.75 = unacceptable. Mitigate with decompressed schedule or phased approach.

---

## Critical Path

```
INFRA → SRC_ACC → TRANS_ENG → DATA_MGR → CANVAS → INT_TEST → SYS_TEST → DEPLOY
```

**Critical Path Items (zero float):** INFRA, SRC_ACC, TRANS_ENG, DATA_MGR, CANVAS, INT_TEST, SYS_TEST, DEPLOY

**Items with Float (can slip):** SCHED, DATA_ACC, CFG_ACC, LLM_GW, AUTH, SCHEMA_ENG, ACC_ENG, VIEWER, DOCS

**Implication:** Always prioritize critical path tasks. If blocked on critical path, that's THE problem to solve. Working on non-critical tasks while critical ones wait = wasted time.

---

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy (Keep Main Context Clean)
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution
- Critical path items can be parallelized by spawning subagents for non-critical dependencies

### 3. Self-Improvement Loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes - don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests -> then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

---

## Task Management

1. **Plan First**: Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review to `tasks/todo.md`
6. **Capture Lessons**: Update `tasks/lessons.md` after corrections

---

## Core Principles

### Simplicity First
- Make every change as simple as possible
- Impact minimal code
- No features beyond what was asked
- No abstractions for single-use code
- If you write 200 lines and it could be 50, rewrite it

### No Laziness
- Find root causes
- No temporary fixes
- Senior developer standards

### Minimal Impact
- Changes should only touch what's necessary
- Avoid introducing bugs

### Karpathy Guidelines

**Think Before Coding:**
- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them—don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

**Surgical Changes:**
- Don't "improve" adjacent code, comments, or formatting
- Don't refactor things that aren't broken
- Match existing style, even if you'd do it differently
- If you notice unrelated dead code, mention it—don't delete it
- Remove imports/variables/functions that YOUR changes made unused
- Don't remove pre-existing dead code unless asked

**Goal-Driven Execution:**
- Transform tasks into verifiable goals
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

---

## When You're Unsure

1. **Architecture question?** Check if component encapsulates a volatility. If named after function, reconsider.
2. **Where does this code go?** Use the WHO/WHAT/HOW/WHERE questions from layered architecture.
3. **How to test this AI feature?** Define success criteria first (AI Engineering principle).
4. **Dependencies unclear?** Check the dependency table below or Monday.com board.

---

## Anti-Patterns to Catch Yourself On

These are the traps. When you notice them, stop and reconsider:

1. **Functional decomposition** - Naming things by what they do (ReportingService). Ask "what might change?" instead.

2. **Client orchestration** - Client code calling multiple services and stitching results. Clients should call ONE Manager.

3. **Service chaining** - A→B→C creates tight coupling. Use Manager orchestration instead.

4. **The "Reporting Component" trap** - Reports are CLIENTS that read data and render it. There is no "Reporting" component.

5. **Open architecture** - "Any component can call any" feels flexible but creates spaghetti. Enforce layer boundaries.

6. **Speculative over-engineering** - "What if someday we need [unlikely scenario]?" If rare AND can only be encapsulated poorly, don't encapsulate.

7. **CRUD in ResourceAccess** - Read/Write/Update/Get/Set are data operations. Use business verbs instead.

8. **Assuming instead of asking** - Don't silently pick an interpretation. If ambiguous, surface the options.

---

## AI Engineering Principles

### Evaluation First
Before building any AI feature, define: "How will we know if this works?"
- What minimum accuracy makes this useful?
- What's the failure mode when AI is wrong?

### Adaptation Hierarchy
When AI performance is insufficient:
```
PROMPTING (always first)
    ↓ exhausted?
RAG (for information gaps)
    ↓ exhausted?
FINETUNING (for behavioral changes)
    ↓ still insufficient?
RECONSIDER USE CASE
```

### Progressive Architecture
Add complexity only when benefit clearly exceeds new failure modes:
```
Level 0: Query → Model → Response (start here)
Level 1: Add Retrieval (when model knowledge insufficient)
Level 2: Add Guardrails (when harmful outputs observed)
Level 3: Add Routing (when different queries need different handling)
Level 4: Add Caching (after stabilization)
Level 5: Add Agency (when multi-step reasoning required)
```

### Quality-Latency-Cost Triangle
Every optimization involves tradeoffs. Identify which is the constraint, then optimize accordingly.

### Three Gulfs Diagnostic

When AI "isn't working," diagnose via Three Gulfs:

| Gulf | Diagnostic Question | If Yes → Action |
|------|---------------------|-----------------|
| **Comprehension** | Do we understand what the data looks like and how the system actually behaves? | Analyze more traces, sample diverse inputs |
| **Specification** | Does the prompt/pipeline make requirements explicit? | Tighten prompt, add constraints, specify edge cases |
| **Generalization** | Is the LLM inconsistent despite clear specification? | Measure failure rate, consider stronger interventions |

---

## Monday.com Integration

**Board:** Dev Project - Data Platform (ID: 18399700061)
**Workspace:** UnlockAlabama (Admin) - ID: 13912239
**URL:** https://innovationportal.monday.com/boards/18399700061

### Task Statuses

**Layer column:** Infrastructure, Utility, Resource Access, Engine, Manager, Client, Testing, Documentation, Deployment

**Critical Path column:** Yes (red), No (green)

**Status column:** Working on it, Done, Stuck

### Column ID Reference

| Column              | ID                   |
| ------------------- | -------------------- |
| Timeline            | timerange_mm0fyaxw   |
| Est. Days           | numeric_mm0fh64c     |
| Actual Days         | numeric_mm0f23qy     |
| Dependencies        | text_mm0ftv95        |
| Status              | color_mm0fyc12       |
| Layer               | color_mm0fnc30       |
| Critical Path       | color_mm0f774        |
| Review Status       | color_mm0fm3fv       |
| Description         | long_text_mm0fbqre   |
| Component Context   | long_text_mm0fp9qj   |
| Acceptance Criteria | long_text_mm0fgqjs   |
| Design Constraints  | long_text_mm0fkzwn   |
| Integration Points  | long_text_mm0fkwy0   |
| Blockers            | long_text_mm0fer9q   |
| Design Doc          | link_mm0f16yk        |
| GitHub PR           | link_mm0fkq1v        |
| API Spec            | link_mm0f804z        |
| Test Results        | link_mm0fw1te        |

### Task ID Reference

| Task                     | Item ID     | Layer           | Critical Path |
| ------------------------ | ----------- | --------------- | ------------- |
| INFRA: Infrastructure    | 11250822678 | Infrastructure  | Yes           |
| SCHED: Scheduler         | 11250857651 | Utility         | No            |
| SRC_ACC: Source Access   | 11250871645 | Resource Access | Yes           |
| DATA_ACC: Data Access    | 11250844567 | Resource Access | No            |
| CFG_ACC: Config Access   | 11250831622 | Resource Access | No            |
| TRANS_ENG: Transform Eng | 11250844949 | Engine          | Yes           |
| DATA_MGR: Data Manager   | 11250860395 | Manager         | Yes           |
| VIEWER: Data Viewer      | 11250862464 | Client          | No            |
| AUTH: Auth Service       | 11250882993 | Utility         | No            |
| LLM_GW: LLM Gateway      | 11250841840 | Utility         | No            |
| SCHEMA_ENG: Schema Eng   | 11250878310 | Engine          | No            |
| ACC_ENG: Access Ctrl Eng | 11250860186 | Engine          | No            |
| CANVAS: Analytics Canvas | 11250842335 | Client          | Yes           |
| INT_TEST: Integration    | 11250841335 | Testing         | Yes           |
| SYS_TEST: System Test    | 11250842958 | Testing         | Yes           |
| DOCS: Documentation      | 11250882969 | Documentation   | No            |
| DEPLOY: Deployment       | 11250864916 | Deployment      | Yes           |

### Updating Status via Monday MCP

```python
# Starting work
change_item_column_values(
    boardId=18399700061,
    itemId=ITEM_ID,
    columnValues='{"color_mm0fyc12":{"label":"Working on it"}}'
)

# Completed
change_item_column_values(
    boardId=18399700061,
    itemId=ITEM_ID,
    columnValues='{"color_mm0fyc12":{"label":"Done"}}'
)

# Blocked
change_item_column_values(
    boardId=18399700061,
    itemId=ITEM_ID,
    columnValues='{"color_mm0fyc12":{"label":"Stuck"}}'
)
```

---

## Development Workflow

1. **Pick a task** from Monday.com (start with critical path, respect dependencies)
2. **Read the task details** - contains acceptance criteria, technical context, dependencies in Updates
3. **Update status** - Set to "Working on it" via Monday MCP
4. **Plan** - Enter plan mode for non-trivial tasks
5. **Implement** following the architecture (respect layer boundaries)
6. **Test** at component boundary
7. **Verify** - Run tests, check logs, demonstrate correctness
8. **Mark complete** when acceptance criteria met
9. **Update Monday.com** - Set to "Done"

### Code Conventions
- Python 3.11+ as primary language
- Type hints everywhere
- Async where appropriate (LLM calls, I/O)
- Pydantic for data classes
- pytest for testing

---

## Honcho MCP Integration

Honcho provides AI-native memory—custom reasoning models that learn continually about users.

### What is Honcho?

Honcho is an infrastructure layer for building AI agents with memory and social cognition. It enables personalized AI interactions by building coherent models of user psychology over time. The Honcho MCP server simplifies the integration to just 3 essential functions.

### Step 1: Start New Conversation (First Message Only)

When a user begins a new conversation, always call `start_conversation`:

```text
start_conversation
```

**Returns**: A session ID that you must store and use for all subsequent interactions in this conversation.

### Step 2: Get Personalized Insights (When Helpful)

Before responding to any user message, you can query for personalization insights:

```text
get_personalization_insights
session_id: [SESSION_ID_FROM_STEP_1]
query: [YOUR_QUESTION]
```

This query takes a bit of time, so it's best to only perform it when you need personalized insights. If the query can be responded to effectively using what you already know about the user, just go ahead and answer it.

**Example Queries**:
- "What does this message reveal about the user's communication preferences?"
- "How formal or casual should I be with the user based on our history?"
- "What is the user really asking for beyond their explicit question?"
- "What emotional state might the user be in right now?"

### Step 3: Respond to User

Craft your response using any insights gained from Step 2.

### Step 4: Store the Conversation Turn (After Each Exchange)

**CRITICAL**: Always store both the user's message AND your response using `add_turn`:

```text
add_turn
session_id: [SESSION_ID_FROM_STEP_1]
messages: [
  {
    "role": "user",
    "content": "[USER'S_EXACT_MESSAGE]"
  },
  {
    "role": "assistant",
    "content": "[YOUR_EXACT_RESPONSE]"
  }
]
```

### Key Principles

1. **Always start with `start_conversation` for new conversations**
2. **Store every message exchange with `add_turn`**
3. **Use `get_personalization_insights` strategically for better responses**
4. **Never expose technical details to the user**
5. **The system maintains context automatically between sessions**

---

## Working Agreements

1. **Plan mode for non-trivial tasks** - Enter plan mode for 3+ step tasks
2. **One task at a time** - Complete before moving to next (reduces context-switching drain)
3. **Acceptance criteria are truth** - Task done when all criteria pass
4. **Update Monday.com** - Status reflects reality
5. **Critical path first** - When choosing what to work on
6. **Artifacts prove completion** - PR, tests, docs as specified
7. **Layer boundaries matter** - Don't put logic in wrong layer
8. **Show reasoning** - When proposing an approach, explain why
9. **Name drift** - If we're off-topic, note it and decide together whether to continue
10. **Capture lessons** - After corrections, update `tasks/lessons.md`
11. **Verify before done** - Run tests, check logs, demonstrate correctness
12. **Surgical changes only** - Touch only what the task requires
