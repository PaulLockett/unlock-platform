-- LM Call Logging table — captures every LLM call for offline evals
--
-- Every DSPy program invocation (including sub-calls from ReAct) is logged here.
-- Enables: exploratory offline evals, cost tracking, debugging, A/B testing,
-- and traceability back to Temporal workflow executions.

CREATE TABLE IF NOT EXISTS unlock.lm_calls (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_name   TEXT NOT NULL,
    model           TEXT NOT NULL,
    prompt_messages TEXT NOT NULL,
    completion      TEXT,
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    latency_ms      DOUBLE PRECISION,
    error           TEXT,
    caller_workflow_id TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_lm_calls_activity_name ON unlock.lm_calls (activity_name);
CREATE INDEX IF NOT EXISTS idx_lm_calls_model ON unlock.lm_calls (model);
CREATE INDEX IF NOT EXISTS idx_lm_calls_created_at ON unlock.lm_calls (created_at);
