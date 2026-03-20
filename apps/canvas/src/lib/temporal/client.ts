import { Client, Connection } from "@temporalio/client";

let _client: Client | null = null;

/**
 * Singleton Temporal client. Reuses the connection across API route calls.
 *
 * Three connection modes (checked in order):
 * 1. API key auth: TEMPORAL_API_KEY + TEMPORAL_REGIONAL_ENDPOINT (Temporal Cloud)
 * 2. mTLS auth: TEMPORAL_TLS_CERT + TEMPORAL_TLS_KEY (Temporal Cloud, legacy)
 * 3. Local dev: localhost:7233, no auth
 */
export async function getTemporalClient(): Promise<Client> {
  if (_client) return _client;

  const namespace = process.env.TEMPORAL_NAMESPACE ?? "default";

  let connection: Connection;

  if (process.env.TEMPORAL_API_KEY) {
    // Temporal Cloud: API key authentication
    const address =
      process.env.TEMPORAL_REGIONAL_ENDPOINT ??
      process.env.TEMPORAL_ADDRESS ??
      "localhost:7233";
    connection = await Connection.connect({
      address,
      apiKey: process.env.TEMPORAL_API_KEY,
      tls: true,
    });
  } else if (process.env.TEMPORAL_TLS_CERT && process.env.TEMPORAL_TLS_KEY) {
    // Temporal Cloud: mTLS authentication (legacy)
    const address = process.env.TEMPORAL_ADDRESS ?? "localhost:7233";
    connection = await Connection.connect({
      address,
      tls: {
        clientCertPair: {
          crt: Buffer.from(process.env.TEMPORAL_TLS_CERT, "base64"),
          key: Buffer.from(process.env.TEMPORAL_TLS_KEY, "base64"),
        },
      },
    });
  } else {
    // Local dev: no TLS
    const address = process.env.TEMPORAL_ADDRESS ?? "localhost:7233";
    connection = await Connection.connect({ address });
  }

  _client = new Client({ connection, namespace });
  return _client;
}

/** Task queue constants — must match Python definitions. */
export const TASK_QUEUES = {
  DATA_MANAGER: "data-manager-queue",
  CONFIG_ACCESS: "config-access-queue",
} as const;
