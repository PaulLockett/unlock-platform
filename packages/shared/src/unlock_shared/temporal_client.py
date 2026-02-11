"""Temporal client connection factory.

Handles the two connection modes transparently:

1. **Local dev**: Connect to `localhost:7233` — the Temporal dev server started
   by docker-compose or `temporal server start-dev`. No auth needed.

2. **Temporal Cloud**: Connect using TEMPORAL_ADDRESS, TEMPORAL_NAMESPACE, and
   TEMPORAL_API_KEY environment variables. Uses API key authentication, which
   Temporal Cloud supports as an alternative to mTLS.

The calling code doesn't need to know which mode it's in — it just calls
`connect()` and gets a ready-to-use client.
"""

import os

from temporalio.client import Client


async def connect() -> Client:
    """Create a connected Temporal client.

    Checks for TEMPORAL_ADDRESS in the environment:
    - If set, connects to Temporal Cloud with API key auth.
    - If unset, connects to localhost:7233 (local dev server).
    """
    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    namespace = os.environ.get("TEMPORAL_NAMESPACE", "default")
    api_key = os.environ.get("TEMPORAL_API_KEY")

    if api_key:
        # Temporal Cloud — API key auth passes the key as metadata on every gRPC call.
        # The "temporal-namespace" header tells the proxy which namespace to route to.
        return await Client.connect(
            address,
            namespace=namespace,
            rpc_metadata={"temporal-namespace": namespace},
            api_key=api_key,
        )

    # Local dev server — no auth, default namespace
    return await Client.connect(address, namespace=namespace)
