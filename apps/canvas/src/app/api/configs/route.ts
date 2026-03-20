import { NextRequest, NextResponse } from "next/server";
import { requireAuth, requireAdmin, AuthError } from "@/lib/auth/session";
import { getTemporalClient, TASK_QUEUES } from "@/lib/temporal/client";

export const maxDuration = 60;

/**
 * GET /api/configs — list schemas or pipelines.
 * Query params: type (schema|pipeline), status, name, limit, offset.
 * Schemas/pipelines require admin. Views use /api/views instead.
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const configType = searchParams.get("type") ?? "schema";
    const status = searchParams.get("status");
    const name = searchParams.get("name");
    const limit = parseInt(searchParams.get("limit") ?? "100", 10);
    const offset = parseInt(searchParams.get("offset") ?? "0", 10);

    if (configType === "schema" || configType === "pipeline") {
      await requireAdmin();
    } else {
      await requireAuth();
    }

    const client = await getTemporalClient();
    const result = await client.workflow.execute("SurveyConfigsWorkflow", {
      taskQueue: TASK_QUEUES.DATA_MANAGER,
      workflowId: `survey-${configType}-${Date.now()}`,
      args: [
        {
          config_type: configType,
          status: status ?? null,
          name_pattern: name ?? null,
          limit,
          offset,
        },
      ],
    });

    if (!result.success) {
      return NextResponse.json(result, { status: 500 });
    }

    return NextResponse.json(result);
  } catch (error) {
    if (error instanceof AuthError) {
      return NextResponse.json(
        { success: false, message: error.message },
        { status: error.status },
      );
    }
    console.error("GET /api/configs error:", error);
    return NextResponse.json(
      { success: false, message: "Internal server error" },
      { status: 500 },
    );
  }
}
