import { NextRequest, NextResponse } from "next/server";
import { requireAuth, AuthError } from "@/lib/auth/session";
import { getTemporalClient } from "@/lib/temporal/client";

export const maxDuration = 30;

/**
 * GET /api/workflow/[workflowId] — check workflow status and get result.
 *
 * Lightweight check: calls Temporal's describe() (instant) to get status,
 * then result() (instant if completed) to get the output.
 *
 * Returns:
 *   { status: "RUNNING" }
 *   { status: "COMPLETED", result: {...} }
 *   { status: "FAILED", error: "..." }
 *   { status: "TIMED_OUT" }
 */
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ workflowId: string }> },
) {
  try {
    await requireAuth();
    const { workflowId } = await params;
    const client = await getTemporalClient();
    const handle = client.workflow.getHandle(workflowId);

    const desc = await handle.describe();
    const status = desc.status.name;

    if (status === "COMPLETED") {
      const result = await handle.result();
      return NextResponse.json({ status: "COMPLETED", result });
    }

    if (status === "FAILED" || status === "CANCELLED" || status === "TERMINATED") {
      return NextResponse.json({
        status,
        error: `Workflow ${status.toLowerCase()}`,
      });
    }

    if (status === "TIMED_OUT") {
      return NextResponse.json({ status: "TIMED_OUT" });
    }

    // RUNNING or other transient states
    return NextResponse.json({ status });
  } catch (error) {
    if (error instanceof AuthError) {
      return NextResponse.json(
        { status: "ERROR", error: error.message },
        { status: error.status },
      );
    }
    const err = error as Error;
    if (err.message?.includes("not found")) {
      return NextResponse.json(
        { status: "NOT_FOUND", error: "Workflow not found" },
        { status: 404 },
      );
    }
    console.error("GET /api/workflow/[workflowId] error:", error);
    return NextResponse.json(
      { status: "ERROR", error: "Failed to check workflow status" },
      { status: 500 },
    );
  }
}
