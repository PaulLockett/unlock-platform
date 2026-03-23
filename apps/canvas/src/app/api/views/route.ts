import { NextResponse } from "next/server";
import { requireAuth, AuthError } from "@/lib/auth/session";
import { listActiveViews } from "@/lib/redis/views";

/**
 * GET /api/views — list views accessible to the current user.
 * Direct Upstash read — bypasses Temporal for fast reads.
 */
export async function GET() {
  try {
    const user = await requireAuth();

    const result = await listActiveViews(user.id, user.role);

    if (!result.success) {
      return NextResponse.json(result, { status: 500 });
    }

    return NextResponse.json(result, {
      headers: {
        "Cache-Control": "private, max-age=30, stale-while-revalidate=60",
      },
    });
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
