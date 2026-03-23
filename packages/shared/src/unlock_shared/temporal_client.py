"""Temporal client connection factory.

Handles the two connection modes transparently:

1. **Local dev**: Connect to `localhost:7233` — the Temporal dev server started
   by docker-compose or `temporal server start-dev`. No auth needed.

2. **Temporal Cloud**: Connect using TEMPORAL_REGIONAL_ENDPOINT, TEMPORAL_NAMESPACE,
   and TEMPORAL_API_KEY environment variables. Uses API key authentication with TLS.

   Important: Temporal Cloud requires the **regional endpoint**
   (e.g., `ap-northeast-1.aws.api.temporal.io:7233`), NOT the namespace endpoint
   (`<ns>.tmprl.cloud:7233`). The namespace endpoint is only for HA namespaces.
   Set TEMPORAL_REGIONAL_ENDPOINT to the value shown in Temporal Cloud's
   namespace "Connect" dialog.

The calling code doesn't need to know which mode it's in — it just calls
`connect()` and gets a ready-to-use client.
"""

import os

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter


async def connect() -> Client:
    """Create a connected Temporal client.

    Checks for TEMPORAL_API_KEY in the environment to decide the mode:
    - If set, connects to Temporal Cloud via the regional endpoint with TLS.
    - If unset, connects to localhost:7233 (local dev server).

    Uses the Pydantic v2 data converter so that Pydantic models survive
    serialization round-trips across workflow/activity boundaries.
    """
    namespace = os.environ.get("TEMPORAL_NAMESPACE", "default")
    api_key = os.environ.get("TEMPORAL_API_KEY")

    if api_key:
        # TEMPORAL_REGIONAL_ENDPOINT comes from the Temporal Cloud "Connect"
        # dialog — it's region-specific and required for API key auth.
        address = os.environ.get("TEMPORAL_REGIONAL_ENDPOINT")
        if not address:
            raise ValueError(
                "TEMPORAL_API_KEY is set but TEMPORAL_REGIONAL_ENDPOINT is missing. "
                "Set it to the regional endpoint from the Temporal Cloud 'Connect' dialog "
                "(e.g., ap-northeast-1.aws.api.temporal.io:7233)."
            )
        return await Client.connect(
            address,
            namespace=namespace,
            api_key=api_key,
            tls=True,
            data_converter=pydantic_data_converter,
        )

    # Local dev server — no auth, default namespace
    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    return await Client.connect(
        address,
        namespace=namespace,
        data_converter=pydantic_data_converter,
    )
