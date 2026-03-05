import { NextRequest, NextResponse } from "next/server";
import { requireAuth, AuthError } from "@/lib/auth/session";

/**
 * POST /api/liveblocks-auth — authorize user for a Liveblocks room.
 * Returns a Liveblocks access token scoped to the requested room.
 */
export async function POST(request: NextRequest) {
  try {
    const user = await requireAuth();
    const body = await request.json();
    const room = body.room as string;

    if (!room) {
      return NextResponse.json(
        { success: false, message: "Room ID required" },
        { status: 400 },
      );
    }

    const LIVEBLOCKS_SECRET = process.env.LIVEBLOCKS_SECRET_KEY;
    if (!LIVEBLOCKS_SECRET) {
      return NextResponse.json(
        { success: false, message: "Liveblocks not configured" },
        { status: 503 },
      );
    }

    // Call Liveblocks authorize endpoint
    const response = await fetch(
      "https://api.liveblocks.io/v2/rooms/" +
        encodeURIComponent(room) +
        "/authorize",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${LIVEBLOCKS_SECRET}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          userId: user.id,
          userInfo: {
            name: user.email.split("@")[0],
            email: user.email,
          },
        }),
      },
    );

    if (!response.ok) {
      const text = await response.text();
      console.error("Liveblocks auth failed:", text);
      return NextResponse.json(
        { success: false, message: "Liveblocks authorization failed" },
        { status: response.status },
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    if (error instanceof AuthError) {
      return NextResponse.json(
        { success: false, message: error.message },
        { status: error.status },
      );
    }
    console.error("POST /api/liveblocks-auth error:", error);
    return NextResponse.json(
      { success: false, message: "Internal server error" },
      { status: 500 },
    );
  }
}
