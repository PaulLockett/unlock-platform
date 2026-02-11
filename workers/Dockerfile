# Single Dockerfile for all worker services.
#
# Each Railway service uses the same image with a different CMD:
#   CMD ["python", "-m", "unlock_workers.runner", "source-access"]
#   CMD ["python", "-m", "unlock_workers.runner", "data-manager"]
#   etc.

FROM python:3.12-slim

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy workspace definition first (cache layer if deps don't change)
COPY pyproject.toml uv.lock* ./
COPY packages/ packages/
COPY workers/ workers/

# Install all workspace packages
RUN uv sync --frozen --no-dev --package unlock-workers

# Default: start the data-manager worker. Override CMD per Railway service.
CMD ["uv", "run", "--package", "unlock-workers", "python", "-m", "unlock_workers.runner", "data-manager"]
