import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { requireAuth, AuthError } from "@/lib/auth/session";
import { getTemporalClient, TASK_QUEUES } from "@/lib/temporal/client";

export const maxDuration = 30;

const ShareBody = z.object({
  share_token: z.string(),
  recipient_id: z.string(),
  recipient_type: z.string().default("user"),
  permission: z.enum(["read", "write", "admin"]),
});

/**
 * POST /api/share — grant access on a view.
 * Requires write+ permission (enforced by ShareWorkflow).
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const parsed = ShareBody.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { success: false, message: parsed.error.message },
        { status: 400 },
      );
    }

    const user = await requireAuth();

    const client = await getTemporalClient();
    const result = await client.workflow.execute("ShareWorkflow", {
      taskQueue: TASK_QUEUES.DATA_MANAGER,
      workflowId: `share-${parsed.data.share_token}-${Date.now()}`,
      args: [
        {
          share_token: parsed.data.share_token,
          granter_id: user.id,
          recipient_id: parsed.data.recipient_id,
          recipient_type: parsed.data.recipient_type,
          permission: parsed.data.permission,
        },
      ],
    });

    if (!result.success) {
      const status = result.message?.includes("Access denied") ? 403 : 400;
      return NextResponse.json(result, { status });
    }

    return NextResponse.json(result);
  } catch (error) {
    if (error instanceof AuthError) {
      return NextResponse.json(
        { success: false, message: error.message },
        { status: error.status },
      );
    }
    console.error("POST /api/share error:", error);
    return NextResponse.json(
      { success: false, message: "Internal server error" },
      { status: 500 },
    );
  }
}
