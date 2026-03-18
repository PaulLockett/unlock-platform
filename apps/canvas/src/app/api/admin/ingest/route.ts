import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { requireAdmin, AuthError } from "@/lib/auth/session";
import { getTemporalClient, TASK_QUEUES } from "@/lib/temporal/client";

export const maxDuration = 30;

const IngestBody = z.object({
  source_name: z.string().min(1),
  source_type: z.string().min(1),
  resource_type: z.string().default("posts"),
  channel_key: z.string().nullish(),
  auth_env_var: z.string().nullish(),
  base_url: z.string().nullish(),
  config_json: z.string().nullish(),
  since: z.string().nullish(),
  max_pages: z.number().int().min(1).max(1000).default(100),
});

/**
 * POST /api/admin/ingest — trigger ingestion for a data source.
 * Admin only.
 */
export async function POST(request: NextRequest) {
  try {
    await requireAdmin();
    const body = await request.json();
    const parsed = IngestBody.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { success: false, message: parsed.error.message },
        { status: 400 },
      );
    }

    const client = await getTemporalClient();
    const result = await client.workflow.execute("IngestWorkflow", {
      taskQueue: TASK_QUEUES.DATA_MANAGER,
      workflowId: `ingest-${parsed.data.source_name}-${Date.now()}`,
      args: [parsed.data],
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
    console.error("POST /api/admin/ingest error:", error);
    return NextResponse.json(
      { success: false, message: "Internal server error" },
      { status: 500 },
    );
  }
}
