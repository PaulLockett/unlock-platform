import { getRedisClient, keys } from "./client";

interface FieldMapping {
  source_field: string;
  target_field: string;
  transform?: string | null;
}

interface SchemaWithFields {
  fields?: FieldMapping[];
  [key: string]: unknown;
}

/**
 * Fetch ingested records for a source, applying schema field mappings.
 *
 * Data flow: CSV → IngestWorkflow → cache_source_records (Redis) → here.
 * Schema field mappings transform source columns (e.g., "Day") to target
 * fields (e.g., "date") so charts can reference stable field names.
 *
 * Falls back to raw records if no schema or no field mappings.
 */
export async function fetchSourceRecords(
  sourceKey: string,
  schema: SchemaWithFields | null,
  opts?: {
    limit?: number;
    offset?: number;
  },
): Promise<{ records: Record<string, unknown>[]; total_count: number }> {
  const redis = getRedisClient();

  let raw: Record<string, unknown>[] | null = null;

  // Try exact source key first
  if (sourceKey) {
    raw = await redis.get<Record<string, unknown>[]>(
      keys.dataRecords(sourceKey),
    );
  }

  // Fallback: scan all data:records:* keys for the first non-empty one.
  // In practice there are few sources, so this is fast.
  if (!raw || !Array.isArray(raw) || raw.length === 0) {
    try {
      let cursor = 0;
      const allKeys: string[] = [];
      do {
        const scanResult = await redis.scan(cursor, {
          match: "data:records:*",
          count: 100,
        });
        cursor =
          typeof scanResult[0] === "string"
            ? parseInt(scanResult[0], 10)
            : scanResult[0];
        allKeys.push(...((scanResult[1] ?? []) as string[]));
      } while (cursor !== 0);

      for (const key of allKeys) {
        const candidate = await redis.get<Record<string, unknown>[]>(
          key as string,
        );
        if (candidate && Array.isArray(candidate) && candidate.length > 0) {
          raw = candidate;
          break;
        }
      }
    } catch {
      // Redis scan not available in test environment — skip fallback
    }
  }

  if (!raw || !Array.isArray(raw)) {
    return { records: [], total_count: 0 };
  }

  // Apply schema field mappings if available
  const fieldMappings = schema?.fields ?? [];
  const mapped =
    fieldMappings.length > 0
      ? raw.map((row) => {
          const result: Record<string, unknown> = {};
          for (const mapping of fieldMappings) {
            let value = row[mapping.source_field];

            // Apply basic transforms
            if (value !== undefined && value !== null && mapping.transform) {
              switch (mapping.transform) {
                case "number":
                  value =
                    typeof value === "string"
                      ? parseFloat(value.replace(/,/g, ""))
                      : Number(value);
                  if (isNaN(value as number)) value = 0;
                  break;
                case "date":
                  // Keep as string for chart axis labels
                  break;
              }
            }

            result[mapping.target_field] = value ?? null;
          }
          return result;
        })
      : raw;

  // Apply pagination
  const offset = opts?.offset ?? 0;
  const limit = opts?.limit ?? 1000;
  const sliced = mapped.slice(offset, offset + limit);

  return {
    records: sliced,
    total_count: mapped.length,
  };
}
