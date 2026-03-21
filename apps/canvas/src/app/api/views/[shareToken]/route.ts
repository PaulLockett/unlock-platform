import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { getSessionUser, requireAuth, AuthError } from "@/lib/auth/session";
import { retrieveView } from "@/lib/redis/views";
import { getTemporalClient, TASK_QUEUES } from "@/lib/temporal/client";

export const maxDuration = 60;

/**
 * GET /api/views/[shareToken] — get view config + schema + permissions.
 * Direct Upstash read — bypasses Temporal for fast reads.
 * Auth optional: public views are accessible without login.
 */
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ shareToken: string }> },
) {
  try {
    const { shareToken } = await params;

    const result = await retrieveView(shareToken);

    if (!result.success) {
      const status = result.message?.includes("not found") ? 404 : 500;
      return NextResponse.json(result, { status });
    }

    // Check visibility: if not public, require auth
    const view = result.view;
    if (view?.visibility !== "public") {
      const user = await getSessionUser();
      if (!user) {
        return NextResponse.json(
          { success: false, message: "Authentication required for this view" },
          { status: 401 },
        );
      }
    }

    // Visibility-dependent caching
    const cacheHeader =
      view?.visibility === "public"
        ? "public, max-age=120, stale-while-revalidate=300"
        : "private, max-age=60, stale-while-revalidate=120";

    return NextResponse.json(result, {
      headers: { "Cache-Control": cacheHeader },
    });
  } catch (error) {
    console.error("GET /api/views/[shareToken] error:", error);
    return NextResponse.json(
      { success: false, message: "Internal server error" },
      { status: 500 },
    );
  }
}

const PatchBody = z.object({
  name: z.string().min(1).optional(),
  description: z.string().nullish(),
  layout_config: z.record(z.string(), z.unknown()).optional(),
  visibility: z.string().optional(),
});

/**
 * PATCH /api/views/[shareToken] — update view config (panels, name, visibility).
 * Requires write+ permission. Mutations stay on Temporal.
 */
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ shareToken: string }> },
) {
  try {
    const { shareToken } = await params;
    const body = await request.json();
    const parsed = PatchBody.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { success: false, message: parsed.error.message },
        { status: 400 },
      );
    }

    const user = await requireAuth();

    // First retrieve the view to get its current state
    const viewResult = await retrieveView(shareToken);

    if (!viewResult.success || !viewResult.view) {
      return NextResponse.json(
        { success: false, message: "View not found" },
        { status: 404 },
      );
    }

    // Check write permission: owner or write+ grant
    const view = viewResult.view;
    const isOwner = view.created_by === user.id;
    const hasWrite = viewResult.permissions?.some(
      (p) =>
        p.principal_id === user.id &&
        (p.permission === "write" || p.permission === "admin"),
    );

    if (!isOwner && !hasWrite && user.role !== "admin") {
      return NextResponse.json(
        { success: false, message: "Write access required" },
        { status: 403 },
      );
    }

    // Update via configure workflow (mutations stay on Temporal)
    const client = await getTemporalClient();
    const result = await client.workflow.execute("ConfigureWorkflow", {
      taskQueue: TASK_QUEUES.DATA_MANAGER,
      workflowId: `patch-view-${shareToken}-${Date.now()}`,
      args: [
        {
          config_type: "view",
          name: parsed.data.name ?? view.name,
          description:
            parsed.data.description !== undefined
              ? parsed.data.description
              : view.description,
          schema_id: view.schema_id,
          filters: view.filters ?? {},
          layout_config: parsed.data.layout_config ?? view.layout_config ?? {},
          visibility: parsed.data.visibility ?? view.visibility ?? "public",
          created_by: view.created_by ?? user.id,
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
    console.error("PATCH /api/views/[shareToken] error:", error);
    return NextResponse.json(
      { success: false, message: "Internal server error" },
      { status: 500 },
    );
  }
}
