import { NextResponse } from "next/server";
import { getRedisClient } from "@/lib/redis/client";

/**
 * GET /api/sources — list available data sources from Redis.
 *
 * Scans for data:records:* keys and returns source names + record counts.
 * Used by the panel editor to populate the source selector dropdown.
 */
export async function GET() {
  try {
    const redis = getRedisClient();
    const sources: { key: string; record_count: number; sample_fields: string[] }[] = [];

    // Scan for all data:records:* keys
    let cursor = 0;
    const allKeys: string[] = [];

    do {
      const [nextCursor, keys] = await redis.scan(cursor, {
        match: "data:records:*",
        count: 100,
      });
      cursor = typeof nextCursor === "string" ? parseInt(nextCursor, 10) : nextCursor;
      allKeys.push(...(keys as string[]));
    } while (cursor !== 0);

    // For each key, get record count and sample fields
    for (const key of allKeys) {
      const records = await redis.get<Record<string, unknown>[]>(key);
      if (records && Array.isArray(records) && records.length > 0) {
        const sourceKey = key.replace("data:records:", "");
        const sampleFields = Object.keys(records[0]);
        sources.push({
          key: sourceKey,
          record_count: records.length,
          sample_fields: sampleFields,
        });
      }
    }

    return NextResponse.json({
      success: true,
      sources,
    });
  } catch (error) {
    console.error("GET /api/sources error:", error);
    return NextResponse.json(
      { success: false, message: "Failed to list sources", sources: [] },
      { status: 500 },
    );
  }
}
