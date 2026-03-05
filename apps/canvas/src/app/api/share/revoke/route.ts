import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { requireAdmin, AuthError } from "@/lib/auth/session";
import { getTemporalClient, TASK_QUEUES } from "@/lib/temporal/client";

const RevokeBody = z.object({
  view_id: z.string(),
  principal_id: z.string(),
});

/**
 * POST /api/share/revoke — revoke access on a view.
 * Admin only.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const parsed = RevokeBody.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { success: false, message: parsed.error.message },
        { status: 400 },
      );
    }

    await requireAdmin();

    // Direct activity call via a lightweight workflow
    const client = await getTemporalClient();
    const result = await client.workflow.execute("RevokeAccessWorkflow", {
      taskQueue: TASK_QUEUES.DATA_MANAGER,
      workflowId: `revoke-${parsed.data.view_id}-${Date.now()}`,
      args: [
        {
          view_id: parsed.data.view_id,
          principal_id: parsed.data.principal_id,
        },
      ],
    });

    if (!result.success) {
      return NextResponse.json(result, { status: 400 });
    }

    return NextResponse.json(result);
  } catch (error) {
    if (error instanceof AuthError) {
      return NextResponse.json(
        { success: false, message: error.message },
        { status: error.status },
      );
    }
    console.error("POST /api/share/revoke error:", error);
    return NextResponse.json(
      { success: false, message: "Internal server error" },
      { status: 500 },
    );
  }
}
