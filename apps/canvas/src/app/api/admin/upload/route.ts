import { NextRequest, NextResponse } from "next/server";
import { requireAdmin, AuthError } from "@/lib/auth/session";
import { createClient } from "@/lib/supabase/server";
import { getTemporalClient, TASK_QUEUES } from "@/lib/temporal/client";

export const maxDuration = 60;

/**
 * POST /api/admin/upload — upload a file (CSV/JSON) and trigger ingestion.
 * Admin only. Uses Supabase Storage for the file, then starts IngestWorkflow.
 */
export async function POST(request: NextRequest) {
  try {
    await requireAdmin();

    const formData = await request.formData();
    const file = formData.get("file") as File | null;
    const sourceName = formData.get("source_name") as string | null;
    const resourceType = (formData.get("resource_type") as string) ?? "posts";
    const channelKey = formData.get("channel_key") as string | null;

    if (!file || !sourceName) {
      return NextResponse.json(
        { success: false, message: "file and source_name are required" },
        { status: 400 },
      );
    }

    // Validate file type
    const validTypes = [
      "text/csv",
      "application/json",
      "application/vnd.ms-excel",
    ];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(csv|json)$/i)) {
      return NextResponse.json(
        { success: false, message: "Only CSV and JSON files are supported" },
        { status: 400 },
      );
    }

    // Validate file size (50MB max)
    if (file.size > 50 * 1024 * 1024) {
      return NextResponse.json(
        { success: false, message: "File must be under 50MB" },
        { status: 400 },
      );
    }

    // Upload to Supabase Storage
    const supabase = await createClient();
    const fileName = `${Date.now()}-${file.name}`;
    const { error: uploadError } = await supabase.storage
      .from("data-uploads")
      .upload(fileName, file);

    if (uploadError) {
      return NextResponse.json(
        { success: false, message: `Upload failed: ${uploadError.message}` },
        { status: 500 },
      );
    }

    // Get public URL for the uploaded file
    const {
      data: { publicUrl },
    } = supabase.storage.from("data-uploads").getPublicUrl(fileName);

    // Trigger ingestion workflow
    const fileType = file.name.endsWith(".json") ? "json" : "csv";
    const client = await getTemporalClient();
    const result = await client.workflow.execute("IngestWorkflow", {
      taskQueue: TASK_QUEUES.DATA_MANAGER,
      workflowId: `upload-ingest-${sourceName}-${Date.now()}`,
      args: [
        {
          source_name: sourceName,
          source_type: `file_${fileType}`,
          resource_type: resourceType,
          channel_key: channelKey,
          base_url: publicUrl,
          max_pages: 1,
        },
      ],
    });

    return NextResponse.json({
      success: true,
      message: "File uploaded and ingestion started",
      file_url: publicUrl,
      ingest_result: result,
    });
  } catch (error) {
    if (error instanceof AuthError) {
      return NextResponse.json(
        { success: false, message: error.message },
        { status: error.status },
      );
    }
    console.error("POST /api/admin/upload error:", error);
    return NextResponse.json(
      { success: false, message: "Internal server error" },
      { status: 500 },
    );
  }
}
