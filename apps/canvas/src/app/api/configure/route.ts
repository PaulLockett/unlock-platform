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
 *
 * Starts the ConfigureWorkflow asynchronously and returns the workflowId
 * immediately. The frontend checks /api/workflow/[workflowId] for the result.
 *
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

    const workflowId = `configure-${parsed.data.config_type}-${Date.now()}`;
    const client = await getTemporalClient();

    // Start workflow asynchronously — returns immediately
    await client.workflow.start("ConfigureWorkflow", {
      taskQueue: TASK_QUEUES.DATA_MANAGER,
      workflowId,
      args: [
        {
          ...parsed.data,
          created_by: user.id,
        },
      ],
    });

    return NextResponse.json(
      {
        success: true,
        message: "Workflow started",
        workflowId,
        config_type: parsed.data.config_type,
      },
      { status: 202 },
    );
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
