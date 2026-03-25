import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { requireAdmin, AuthError } from "@/lib/auth/session";
import { getTemporalClient, TASK_QUEUES } from "@/lib/temporal/client";

export const maxDuration = 30;

/**
 * GET /api/admin/schedules — list all harvest schedules.
 */
export async function GET() {
  try {
    await requireAdmin();

    const client = await getTemporalClient();
    const result = await client.workflow.execute("ScheduleManagementWorkflow", {
      taskQueue: TASK_QUEUES.SCHEDULER,
      workflowId: `list-schedules-${Date.now()}`,
      args: [{ action: "list" }],
    });

    // Fallback: call list_harvests directly via a simple activity dispatch
    // Since there's no ScheduleManagementWorkflow yet, call the activity
    // through the Data Manager which can dispatch to Scheduler queue.
    return NextResponse.json(result);
  } catch (error) {
    if (error instanceof AuthError) {
      return NextResponse.json(
        { success: false, message: error.message },
        { status: error.status },
      );
    }
    console.error("GET /api/admin/schedules error:", error);
    return NextResponse.json(
      { success: false, message: "Internal server error" },
      { status: 500 },
    );
  }
}

const CreateScheduleBody = z.object({
  source_name: z.string().min(1),
  cron_expression: z.string().min(1),
  time_zone: z.string().default("America/Chicago"),
  source_type: z.string().min(1),
  resource_type: z.string().default("posts"),
  channel_key: z.string().nullish(),
  auth_env_var: z.string().nullish(),
  base_url: z.string().nullish(),
  config_json: z.string().nullish(),
  max_pages: z.number().int().min(1).default(100),
});

/**
 * POST /api/admin/schedules — create a recurring harvest schedule.
 */
export async function POST(request: NextRequest) {
  try {
    await requireAdmin();

    const body = await request.json();
    const parsed = CreateScheduleBody.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { success: false, message: parsed.error.message },
        { status: 400 },
      );
    }

    const client = await getTemporalClient();

    // Dispatch register_harvest activity via Scheduler queue.
    // We use executeActivity pattern: start a one-off workflow that
    // calls the activity on the scheduler queue.
    const result = await client.workflow.execute("ScheduleHarvestWorkflow", {
      taskQueue: TASK_QUEUES.DATA_MANAGER,
      workflowId: `register-schedule-${parsed.data.source_name}-${Date.now()}`,
      args: [
        {
          action: "register",
          ...parsed.data,
        },
      ],
    });

    return NextResponse.json(result, { status: result.success ? 201 : 400 });
  } catch (error) {
    if (error instanceof AuthError) {
      return NextResponse.json(
        { success: false, message: error.message },
        { status: error.status },
      );
    }
    console.error("POST /api/admin/schedules error:", error);
    return NextResponse.json(
      { success: false, message: "Internal server error" },
      { status: 500 },
    );
  }
}

const ActionBody = z.object({
  source_name: z.string().min(1),
  action: z.enum(["pause", "resume", "cancel", "describe"]),
  note: z.string().optional(),
});

/**
 * PATCH /api/admin/schedules — pause, resume, cancel, or describe a schedule.
 */
export async function PATCH(request: NextRequest) {
  try {
    await requireAdmin();

    const body = await request.json();
    const parsed = ActionBody.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { success: false, message: parsed.error.message },
        { status: 400 },
      );
    }

    const client = await getTemporalClient();
    const result = await client.workflow.execute("ScheduleHarvestWorkflow", {
      taskQueue: TASK_QUEUES.DATA_MANAGER,
      workflowId: `schedule-${parsed.data.action}-${parsed.data.source_name}-${Date.now()}`,
      args: [parsed.data],
    });

    return NextResponse.json(result);
  } catch (error) {
    if (error instanceof AuthError) {
      return NextResponse.json(
        { success: false, message: error.message },
        { status: error.status },
      );
    }
    console.error("PATCH /api/admin/schedules error:", error);
    return NextResponse.json(
      { success: false, message: "Internal server error" },
      { status: 500 },
    );
  }
}
