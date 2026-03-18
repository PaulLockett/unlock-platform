import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { requireAuth, requireAdmin, AuthError } from "@/lib/auth/session";
import { getTemporalClient, TASK_QUEUES } from "@/lib/temporal/client";

export const maxDuration = 30;

const ConfigureBody = z.object({
  config_type: z.enum(["schema", "pipeline", "view"]),
  name: z.string().min(1),
  description: z.string().nullish(),
  // Schema-specific
  schema_type: z.string().optional(),
  fields: z.array(z.record(z.string(), z.unknown())).optional(),
  funnel_stages: z.array(z.record(z.string(), z.unknown())).optional(),
  // Pipeline-specific
  source_type: z.string().optional(),
  transform_rules: z.array(z.record(z.string(), z.unknown())).optional(),
  schedule_cron: z.string().nullish(),
  // View-specific
  schema_id: z.string().optional(),
  filters: z.record(z.string(), z.unknown()).optional(),
  layout_config: z.record(z.string(), z.unknown()).optional(),
  visibility: z.string().optional(),
});

/**
 * POST /api/configure — create schema, pipeline, or view.
 * Schemas/pipelines require admin. Views require auth.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const parsed = ConfigureBody.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { success: false, message: parsed.error.message },
        { status: 400 },
      );
    }

    // Schema/pipeline = admin only. View = any authenticated user.
    let user;
    if (
      parsed.data.config_type === "schema" ||
      parsed.data.config_type === "pipeline"
    ) {
      user = await requireAdmin();
    } else {
      user = await requireAuth();
    }

    const client = await getTemporalClient();
    const result = await client.workflow.execute("ConfigureWorkflow", {
      taskQueue: TASK_QUEUES.DATA_MANAGER,
      workflowId: `configure-${parsed.data.config_type}-${Date.now()}`,
      args: [
        {
          ...parsed.data,
          created_by: user.id,
        },
      ],
    });

    if (!result.success) {
      return NextResponse.json(result, { status: 400 });
    }

    return NextResponse.json(result, { status: 201 });
  } catch (error) {
    if (error instanceof AuthError) {
      return NextResponse.json(
        { success: false, message: error.message },
        { status: error.status },
      );
    }
    console.error("POST /api/configure error:", error);
    return NextResponse.json(
      { success: false, message: "Internal server error" },
      { status: 500 },
    );
  }
}
