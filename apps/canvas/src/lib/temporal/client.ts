import { Client, Connection } from "@temporalio/client";

let _client: Client | null = null;

/**
 * Singleton Temporal client. Reuses the connection across API route calls.
 *
 * Connects to Temporal Cloud if TEMPORAL_ADDRESS + TEMPORAL_NAMESPACE are set,
 * otherwise falls back to local dev server at localhost:7233.
 */
export async function getTemporalClient(): Promise<Client> {
  if (_client) return _client;

  const address = process.env.TEMPORAL_ADDRESS ?? "localhost:7233";
  const namespace = process.env.TEMPORAL_NAMESPACE ?? "default";

  let connection: Connection;

  if (process.env.TEMPORAL_TLS_CERT && process.env.TEMPORAL_TLS_KEY) {
    // Temporal Cloud: mTLS authentication
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
