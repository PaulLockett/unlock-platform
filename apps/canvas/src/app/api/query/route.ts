import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { getSessionUser } from "@/lib/auth/session";
import { getTemporalClient, TASK_QUEUES } from "@/lib/temporal/client";

export const maxDuration = 60;

const QueryBody = z.object({
  share_token: z.string(),
  channel_key: z.string().nullish(),
  engagement_type: z.string().nullish(),
  since: z.string().nullish(),
  until: z.string().nullish(),
  limit: z.number().int().min(1).max(1000).default(100),
  offset: z.number().int().min(0).default(0),
});

/**
 * POST /api/query — per-panel data query.
 * Auth is optional: public views allow anonymous reads.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const parsed = QueryBody.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { success: false, message: parsed.error.message },
        { status: 400 },
      );
    }

    const user = await getSessionUser();

    const client = await getTemporalClient();
    const result = await client.workflow.execute("QueryWorkflow", {
      taskQueue: TASK_QUEUES.DATA_MANAGER,
      workflowId: `query-${parsed.data.share_token}-${Date.now()}`,
      args: [
        {
          share_token: parsed.data.share_token,
          user_id: user?.id ?? "anonymous",
          user_type: user ? "user" : "anonymous",
          channel_key: parsed.data.channel_key ?? null,
          engagement_type: parsed.data.engagement_type ?? null,
          since: parsed.data.since ?? null,
          until: parsed.data.until ?? null,
          limit: parsed.data.limit,
          offset: parsed.data.offset,
        },
      ],
    });

    if (!result.success) {
      const status = result.message?.includes("Access denied") ? 403 : 500;
      return NextResponse.json(result, { status });
    }

    return NextResponse.json(result);
  } catch (error) {
    console.error("POST /api/query error:", error);
    return NextResponse.json(
      { success: false, message: "Internal server error" },
      { status: 500 },
    );
  }
}
