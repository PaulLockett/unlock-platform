import { NextResponse } from "next/server";
import { getTemporalClient, TASK_QUEUES } from "@/lib/temporal/client";

/**
 * GET /api/debug-temporal — diagnostic endpoint for Temporal connectivity.
 * Returns connection status and environment variable presence.
 * TEMPORARY: remove after debugging.
 */
export async function GET() {
  const env = {
    TEMPORAL_API_KEY: !!process.env.TEMPORAL_API_KEY,
    TEMPORAL_NAMESPACE: process.env.TEMPORAL_NAMESPACE ?? "(not set)",
    TEMPORAL_REGIONAL_ENDPOINT:
      process.env.TEMPORAL_REGIONAL_ENDPOINT ?? "(not set)",
    TEMPORAL_ADDRESS: process.env.TEMPORAL_ADDRESS ?? "(not set)",
    TEMPORAL_TLS_CERT: !!process.env.TEMPORAL_TLS_CERT,
    TEMPORAL_TLS_KEY: !!process.env.TEMPORAL_TLS_KEY,
  };

  try {
    const start = Date.now();
    const client = await getTemporalClient();
    const connectMs = Date.now() - start;

    // Try a lightweight operation
    const handle = client.workflow.getHandle("debug-test-nonexistent");
    try {
      await handle.describe();
    } catch {
      // Expected: workflow not found
    }
    const totalMs = Date.now() - start;

    return NextResponse.json({
      success: true,
      env,
      connectMs,
      totalMs,
      taskQueues: TASK_QUEUES,
    });
  } catch (error) {
    const err = error as Error;
    return NextResponse.json(
      {
        success: false,
        env,
        error: err.message,
        stack: err.stack?.split("\n").slice(0, 5),
      },
      { status: 500 },
    );
  }
}
