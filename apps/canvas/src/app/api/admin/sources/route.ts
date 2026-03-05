import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { requireAdmin, AuthError } from "@/lib/auth/session";
import { createClient } from "@/lib/supabase/server";

/**
 * GET /api/admin/sources — list registered data sources.
 * Admin only. Reads from Supabase directly (source registry).
 */
export async function GET() {
  try {
    await requireAdmin();
    const supabase = await createClient();

    const { data, error } = await supabase
      .from("data_sources")
      .select("*")
      .order("created_at", { ascending: false });

    if (error) {
      return NextResponse.json(
        { success: false, message: error.message },
        { status: 500 },
      );
    }

    return NextResponse.json({ success: true, sources: data ?? [] });
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
 * Admin only.
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

    const supabase = await createClient();
    const { data, error } = await supabase
      .from("data_sources")
      .insert({
        ...parsed.data,
        status: "active",
      })
      .select()
      .single();

    if (error) {
      return NextResponse.json(
        { success: false, message: error.message },
        { status: 500 },
      );
    }

    return NextResponse.json({ success: true, source: data }, { status: 201 });
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
