import { Client, Connection } from "@temporalio/client";

let _client: Client | null = null;

/**
 * Singleton Temporal client. Reuses the connection across API route calls.
 *
 * Three connection modes (checked in order):
 * 1. API key auth: TEMPORAL_API_KEY + TEMPORAL_REGIONAL_ENDPOINT (Temporal Cloud)
 * 2. mTLS auth: TEMPORAL_TLS_CERT + TEMPORAL_TLS_KEY (Temporal Cloud, legacy)
 * 3. Local dev: localhost:7233, no auth
 *
 * Uses eager Connection.connect() with a 10s timeout so cold-start failures
 * surface quickly instead of hanging the serverless function.
 */
export async function getTemporalClient(): Promise<Client> {
  if (_client) return _client;

  const namespace = process.env.TEMPORAL_NAMESPACE ?? "default";

  // Race the connection against a hard 15s timeout.
  // Connection.connect()'s connectTimeout only covers gRPC readiness,
  // not DNS/TLS-level hangs that can block indefinitely in serverless.
  const connectWithTimeout = async (): Promise<Client> => {
    let connection: Connection;

    if (process.env.TEMPORAL_API_KEY) {
      const address =
        process.env.TEMPORAL_REGIONAL_ENDPOINT ??
        process.env.TEMPORAL_ADDRESS ??
        "localhost:7233";
      connection = await Connection.connect({
        address,
        apiKey: process.env.TEMPORAL_API_KEY,
        tls: true,
        connectTimeout: "10s",
        metadata: { "temporal-namespace": namespace },
      });
    } else if (process.env.TEMPORAL_TLS_CERT && process.env.TEMPORAL_TLS_KEY) {
      const address = process.env.TEMPORAL_ADDRESS ?? "localhost:7233";
      connection = await Connection.connect({
        address,
        connectTimeout: "10s",
        tls: {
          clientCertPair: {
            crt: Buffer.from(process.env.TEMPORAL_TLS_CERT, "base64"),
            key: Buffer.from(process.env.TEMPORAL_TLS_KEY, "base64"),
          },
        },
      });
    } else {
      const address = process.env.TEMPORAL_ADDRESS ?? "localhost:7233";
      connection = await Connection.connect({
        address,
        connectTimeout: "10s",
      });
    }

    return new Client({ connection, namespace });
  };

  const client = await Promise.race([
    connectWithTimeout(),
    new Promise<never>((_, reject) =>
      setTimeout(
        () => reject(new Error("Temporal connection timed out (15s)")),
        15_000,
      ),
    ),
  ]);

  _client = client;
  return _client;
}

/** Task queue constants — must match Python definitions. */
export const TASK_QUEUES = {
  DATA_MANAGER: "data-manager-queue",
  CONFIG_ACCESS: "config-access-queue",
  SCHEDULER: "scheduler-queue",
} as const;
