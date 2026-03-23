import { Redis } from "@upstash/redis";

let _redis: Redis | null = null;

/**
 * Singleton Upstash Redis client for direct reads.
 * Bypasses Temporal for read-only operations to eliminate gRPC cold-start latency.
 */
export function getRedisClient(): Redis {
  if (_redis) return _redis;

  const url = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;

  if (!url || !token) {
    throw new Error(
      "Missing UPSTASH_REDIS_REST_URL or UPSTASH_REDIS_REST_TOKEN",
    );
  }

  _redis = new Redis({ url, token });
  return _redis;
}

// ---------------------------------------------------------------------------
// Key helpers — mirrors packages/config-access/src/unlock_config_access/keys.py
// ---------------------------------------------------------------------------

export const keys = {
  // Schema
  schema: (id: string) => `cfg:schema:${id}`,
  schemaIdxAll: () => "cfg:schema:idx:all",
  schemaIdxStatus: (status: string) => `cfg:schema:idx:status:${status}`,
  schemaIdxName: (name: string) => `cfg:schema:idx:name:${name}`,

  // Pipeline
  pipeline: (id: string) => `cfg:pipeline:${id}`,
  pipelineIdxAll: () => "cfg:pipeline:idx:all",
  pipelineIdxStatus: (status: string) => `cfg:pipeline:idx:status:${status}`,

  // View
  view: (id: string) => `cfg:view:${id}`,
  viewIdxAll: () => "cfg:view:idx:all",
  viewIdxToken: (token: string) => `cfg:view:idx:token:${token}`,
  viewIdxSchema: (schemaId: string) => `cfg:view:idx:schema:${schemaId}`,
  viewIdxStatus: (status: string) => `cfg:view:idx:status:${status}`,

  // Permission
  perm: (viewId: string) => `cfg:perm:${viewId}`,
  permIdxPrincipal: (principalId: string) =>
    `cfg:perm:idx:principal:${principalId}`,
} as const;
