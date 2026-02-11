"""Source Access activities.

These run on the source-access worker (SOURCE_ACCESS_QUEUE). The Data Manager's
IngestWorkflow dispatches to this queue when it needs to fetch raw data from
external sources (APIs, files, scraped content).

This hello-world implementation proves the cross-queue dispatch pattern works:
the workflow runs on data-manager-queue but the activity executes on
source-access-queue — a completely separate worker process.
"""

from temporalio import activity


@activity.defn
async def hello_source_access(source_name: str) -> str:
    """Placeholder activity that simulates fetching data from a source.

    In production, this would connect to an external API, read a file,
    or scrape a webpage. For now, it just proves the worker is alive
    and receiving activity dispatches from the Data Manager workflows.
    """
    activity.logger.info(f"Source Access: fetching from '{source_name}'")
    return f"Hello from Source Access — fetched '{source_name}'"
