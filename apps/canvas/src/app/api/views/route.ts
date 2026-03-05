import { NextResponse } from "next/server";
import { requireAuth, AuthError } from "@/lib/auth/session";
import { getTemporalClient, TASK_QUEUES } from "@/lib/temporal/client";

/**
 * GET /api/views — list views accessible to the current user.
 * Returns all active views (survey_configs with config_type="view").
 */
export async function GET() {
  try {
    const user = await requireAuth();

    const client = await getTemporalClient();

    // Survey all active views
    const result = await client.workflow.execute("SurveyConfigsWorkflow", {
      taskQueue: TASK_QUEUES.DATA_MANAGER,
      workflowId: `survey-views-${user.id}-${Date.now()}`,
      args: [
        {
          config_type: "view",
          status: "active",
          created_by: user.role === "admin" ? null : user.id,
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
    console.error("GET /api/views error:", error);
    return NextResponse.json(
      { success: false, message: "Internal server error" },
      { status: 500 },
    );
  }
}
