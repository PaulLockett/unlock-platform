import { getRedisClient, keys } from "./client";

interface ConfigRecord {
  id: string;
  name?: string;
  [key: string]: unknown;
}

/**
 * Survey configs by type — mirrors SurveyConfigsWorkflow for schema/pipeline types.
 * Views use listActiveViews() from ./views.ts instead.
 */
export async function surveyConfigs(params: {
  configType: string;
  status?: string | null;
  namePattern?: string | null;
  limit?: number;
  offset?: number;
}): Promise<{ success: boolean; items: ConfigRecord[] }> {
  const { configType, status, namePattern, limit = 100, offset = 0 } = params;
  const redis = getRedisClient();

  // Determine which IDs to fetch
  let ids: string[];
  if (status) {
    // Use status index set
    const statusKey =
      configType === "schema"
        ? keys.schemaIdxStatus(status)
        : keys.pipelineIdxStatus(status);
    ids = await redis.smembers(statusKey);
  } else {
    // Use the "all" sorted set — returns IDs sorted by timestamp
    const allKey =
      configType === "schema" ? keys.schemaIdxAll() : keys.pipelineIdxAll();
    ids = await redis.zrange(allKey, 0, -1);
  }

  if (!ids || ids.length === 0) {
    return { success: true, items: [] };
  }

  // Batch-fetch config objects
  const keyFn = configType === "schema" ? keys.schema : keys.pipeline;
  const pipeline = redis.pipeline();
  for (const id of ids) {
    pipeline.get(keyFn(id));
  }
  const results = await pipeline.exec<(ConfigRecord | null)[]>();

  let items = results.filter((c): c is ConfigRecord => c !== null);

  // Filter by name pattern (simple substring match, case-insensitive)
  if (namePattern) {
    const pattern = namePattern.toLowerCase();
    items = items.filter((c) =>
      (c.name ?? "").toLowerCase().includes(pattern),
    );
  }

  // Paginate
  items = items.slice(offset, offset + limit);

  return { success: true, items };
}
