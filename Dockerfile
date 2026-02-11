# Single Dockerfile for all worker services.
#
# Each Railway service sets COMPONENT=<name> in its environment variables.
# The runner reads COMPONENT to decide which workflows/activities to register.
#
# Local usage:
#   COMPONENT=data-manager uv run python -m unlock_workers.runner

FROM python:3.12-slim

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy workspace definition + lockfile first (cache layer if deps don't change)
COPY pyproject.toml uv.lock ./
COPY packages/ packages/
COPY workers/ workers/

# Install all workspace packages
RUN uv sync --frozen --no-dev --package unlock-workers

# COMPONENT is set per Railway service (e.g., COMPONENT=source-access).
# Default to data-manager for local Docker testing.
ENV COMPONENT=data-manager

CMD ["uv", "run", "--package", "unlock-workers", "python", "-m", "unlock_workers.runner"]
