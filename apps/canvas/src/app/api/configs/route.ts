import { NextRequest, NextResponse } from "next/server";
import { requireAuth, requireAdmin, AuthError } from "@/lib/auth/session";
import { surveyConfigs } from "@/lib/redis/configs";

/**
 * GET /api/configs — list schemas or pipelines.
 * Direct Upstash read — bypasses Temporal for fast reads.
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

    const result = await surveyConfigs({
      configType,
      status: status ?? null,
      namePattern: name ?? null,
      limit,
      offset,
    });

    if (!result.success) {
      return NextResponse.json(result, { status: 500 });
    }

    return NextResponse.json(result, {
      headers: {
        "Cache-Control": "private, max-age=60",
      },
    });
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
