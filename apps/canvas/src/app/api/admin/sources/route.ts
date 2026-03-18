import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { requireAdmin, AuthError } from "@/lib/auth/session";
import { getTemporalClient, TASK_QUEUES } from "@/lib/temporal/client";

/**
 * GET /api/admin/sources — list registered data sources.
 * Admin only. Routes through ManageSourceWorkflow → identify_source activity.
 */
export async function GET() {
  try {
    await requireAdmin();

    const client = await getTemporalClient();
    const result = await client.workflow.execute("ManageSourceWorkflow", {
      taskQueue: TASK_QUEUES.DATA_MANAGER,
      workflowId: `identify-sources-${Date.now()}`,
      args: [{ action: "identify" }],
    });

    if (!result.success) {
      return NextResponse.json(result, { status: 500 });
    }

    return NextResponse.json({
      success: true,
      sources: result.all_sources ?? [],
    });
  } catch (error) {
    if (error instanceof AuthError) {
      return NextResponse.json(
        { success: false, message: error.message },
        { status: error.status },
      );
    }
    console.error("GET /api/admin/sources error:", error);
    return NextResponse.json(
      { success: false, message: "Internal server error" },
      { status: 500 },
    );
  }
}

const CreateSourceBody = z.object({
  name: z.string().min(1),
  protocol: z.enum([
    "rest_api",
    "file_upload",
    "webhook",
    "s3",
    "database",
    "smtp",
  ]),
  service: z.string().optional(),
  base_url: z.string().optional(),
  auth_method: z.string().optional(),
  auth_env_var: z.string().optional(),
  resource_type: z.string().default("posts"),
  channel_key: z.string().optional(),
  config: z.record(z.string(), z.unknown()).optional(),
});

/**
 * POST /api/admin/sources — register a new data source.
 * Admin only. Routes through ManageSourceWorkflow → register_source activity.
 */
export async function POST(request: NextRequest) {
  try {
    await requireAdmin();
    const body = await request.json();
    const parsed = CreateSourceBody.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { success: false, message: parsed.error.message },
        { status: 400 },
      );
    }

    const client = await getTemporalClient();
    const result = await client.workflow.execute("ManageSourceWorkflow", {
      taskQueue: TASK_QUEUES.DATA_MANAGER,
      workflowId: `register-source-${parsed.data.name}-${Date.now()}`,
      args: [
        {
          action: "register",
          ...parsed.data,
        },
      ],
    });

    if (!result.success) {
      return NextResponse.json(result, { status: 500 });
    }

    return NextResponse.json(
      { success: true, source: result.source },
      { status: 201 },
    );
  } catch (error) {
    if (error instanceof AuthError) {
      return NextResponse.json(
        { success: false, message: error.message },
        { status: error.status },
      );
    }
    console.error("POST /api/admin/sources error:", error);
    return NextResponse.json(
      { success: false, message: "Internal server error" },
      { status: 500 },
    );
  }
}
