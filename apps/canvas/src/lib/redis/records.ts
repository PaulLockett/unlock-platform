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

  const raw = await redis.get<Record<string, unknown>[]>(
    keys.dataRecords(sourceKey),
  );

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
