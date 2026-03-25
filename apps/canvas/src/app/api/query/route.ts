import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { getSessionUser } from "@/lib/auth/session";
import { retrieveView } from "@/lib/redis/views";
import { fetchSourceRecords } from "@/lib/redis/records";
import { getTemporalClient, TASK_QUEUES } from "@/lib/temporal/client";

export const maxDuration = 60;

const QueryBody = z.object({
  share_token: z.string(),
  source_key: z.string().nullish(),
  channel_key: z.string().nullish(),
  engagement_type: z.string().nullish(),
  since: z.string().nullish(),
  until: z.string().nullish(),
  limit: z.number().int().min(1).max(1000).default(100),
  offset: z.number().int().min(0).default(0),
});

/**
 * POST /api/query — per-panel data query.
 *
 * Two-tier query strategy:
 * 1. Direct Redis: check for cached source records (fast path for ingested CSV/API data)
 * 2. Temporal fallback: QueryWorkflow → survey_engagement (for engagement graph data)
 *
 * Auth is optional: public views allow anonymous reads.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const parsed = QueryBody.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { success: false, message: parsed.error.message },
        { status: 400 },
      );
    }

    const user = await getSessionUser();

    // Step 1: Retrieve view config to find the source and schema
    const viewResult = await retrieveView(parsed.data.share_token);

    if (viewResult.success && viewResult.view) {
      const view = viewResult.view;
      const schema = viewResult.schema as {
        fields?: Array<{
          source_field: string;
          target_field: string;
          transform?: string | null;
        }>;
      } | null;

      // Check visibility: public views allow anonymous, others require auth
      if (view.visibility !== "public" && !user) {
        return NextResponse.json(
          { success: false, message: "Authentication required" },
          { status: 401 },
        );
      }

      // Try direct Redis read for cached source records.
      // Priority: explicit source_key from panel > view.source_key > view.name > scan fallback
      const explicitKey = parsed.data.source_key ?? "";
      const viewSourceKey = (view.source_key as string) || "";

      const keysToTry = [
        explicitKey,
        viewSourceKey,
        view.name as string,
      ].filter(Boolean);

      // De-duplicate while preserving priority order
      const uniqueKeys = [...new Set(keysToTry)];

      for (const key of uniqueKeys) {
        const directResult = await fetchSourceRecords(key, schema, {
          limit: parsed.data.limit,
          offset: parsed.data.offset,
        });

        if (directResult.records.length > 0) {
          return NextResponse.json({
            success: true,
            message: `Retrieved ${directResult.total_count} records from '${view.name}'`,
            records: directResult.records,
            total_count: directResult.total_count,
            has_more:
              directResult.total_count >
              parsed.data.offset + parsed.data.limit,
            view_name: view.name as string,
            schema_id: view.schema_id as string,
          });
        }
      }

      // Last resort: scan fallback (fetchSourceRecords with empty key triggers scan)
      if (uniqueKeys.length > 0) {
        const scanResult = await fetchSourceRecords("", schema, {
          limit: parsed.data.limit,
          offset: parsed.data.offset,
        });
        if (scanResult.records.length > 0) {
          return NextResponse.json({
            success: true,
            message: `Retrieved ${scanResult.total_count} records from '${view.name}' (scan)`,
            records: scanResult.records,
            total_count: scanResult.total_count,
            has_more:
              scanResult.total_count >
              parsed.data.offset + parsed.data.limit,
            view_name: view.name as string,
            schema_id: view.schema_id as string,
          });
        }
      }
    }

    // Step 2: Fall back to Temporal QueryWorkflow for engagement data
    const client = await getTemporalClient();
    const result = await client.workflow.execute("QueryWorkflow", {
      taskQueue: TASK_QUEUES.DATA_MANAGER,
      workflowId: `query-${parsed.data.share_token}-${Date.now()}`,
      args: [
        {
          share_token: parsed.data.share_token,
          user_id: user?.id ?? "anonymous",
          user_type: user ? "user" : "anonymous",
          channel_key: parsed.data.channel_key ?? null,
          engagement_type: parsed.data.engagement_type ?? null,
          since: parsed.data.since ?? null,
          until: parsed.data.until ?? null,
          limit: parsed.data.limit,
          offset: parsed.data.offset,
        },
      ],
    });

    if (!result.success) {
      const status = result.message?.includes("Access denied") ? 403 : 500;
      return NextResponse.json(result, { status });
    }

    return NextResponse.json(result);
  } catch (error) {
    console.error("POST /api/query error:", error instanceof Error ? error.message : error, error instanceof Error ? error.stack : "");
    return NextResponse.json(
      { success: false, message: "Internal server error" },
      { status: 500 },
    );
  }
}
