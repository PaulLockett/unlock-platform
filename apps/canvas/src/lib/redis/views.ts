import { getRedisClient, keys } from "./client";

interface ViewRecord {
  id: string;
  created_by?: string;
  visibility?: string;
  [key: string]: unknown;
}

/**
 * List active views accessible to the given user.
 * Mirrors the SurveyConfigsWorkflow for config_type="view", status="active".
 */
export async function listActiveViews(
  userId: string,
  role: string,
): Promise<{ success: boolean; items: ViewRecord[] }> {
  const redis = getRedisClient();

  // Get all active view IDs from the status index set
  const activeIds = await redis.smembers(keys.viewIdxStatus("active"));
  if (!activeIds || activeIds.length === 0) {
    return { success: true, items: [] };
  }

  // Batch-fetch view JSON objects
  const pipeline = redis.pipeline();
  for (const id of activeIds) {
    pipeline.get(keys.view(id));
  }
  const results = await pipeline.exec<(ViewRecord | null)[]>();

  // Filter: admin sees all, regular user sees only own views
  const items = results
    .filter((v): v is ViewRecord => v !== null)
    .filter((v) => role === "admin" || v.created_by === userId);

  return { success: true, items };
}

/**
 * Retrieve a view by share token — returns view + schema + permissions.
 * Mirrors the RetrieveViewWorkflow.
 */
export async function retrieveView(
  shareToken: string,
): Promise<{
  success: boolean;
  message?: string;
  view?: ViewRecord;
  schema?: Record<string, unknown> | null;
  permissions?: Array<{ principal_id: string; permission: string; [key: string]: unknown }>;
}> {
  const redis = getRedisClient();

  // Token → view ID
  const viewId = await redis.get<string>(keys.viewIdxToken(shareToken));
  if (!viewId) {
    return { success: false, message: "View not found" };
  }

  // Fetch view JSON
  const view = await redis.get<ViewRecord>(keys.view(viewId));
  if (!view) {
    return { success: false, message: "View not found" };
  }

  // Fetch schema if referenced
  const schemaId = view.schema_id as string | undefined;
  let schema: Record<string, unknown> | null = null;
  if (schemaId) {
    schema = await redis.get<Record<string, unknown>>(keys.schema(schemaId));
  }

  // Fetch permissions hash
  const permHash = await redis.hgetall<Record<string, string>>(
    keys.perm(viewId),
  );
  const permissions = permHash
    ? Object.entries(permHash).flatMap(([principalId, json]) => {
        try {
          const parsed =
            typeof json === "string" ? JSON.parse(json) : json;
          return [{ principal_id: principalId, ...parsed }];
        } catch {
          console.warn(`Malformed permission entry for principal ${principalId}, skipping`);
          return [];
        }
      })
    : [];

  return { success: true, view, schema, permissions };
}
