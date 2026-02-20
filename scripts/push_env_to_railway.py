"""Push environment variables from .env to Railway services via GraphQL API.

Reads variables from a .env file and/or OS environment, then upserts them
onto the correct Railway services in the specified environment. This replaces
GUI-based variable management — any developer (or CI) can run this script
to sync secrets.

Variable routing:
  - Source connector keys → source-access service
  - LLM keys → llm-gateway service
  - Temporal keys → ALL services (shared infrastructure)
  - Supabase keys → data-access service

The script skips local-only variables (HONCHO_*, MONDAY_TOKEN, EXA_API_KEY)
since those aren't needed by Railway workers.

Usage (local — reads .env file, auth from Railway CLI):
  python scripts/push_env_to_railway.py                    # defaults to staging
  python scripts/push_env_to_railway.py --env production   # target production
  python scripts/push_env_to_railway.py --dry-run          # preview without pushing

Usage (CI — reads OS environment, auth from RAILWAY_TOKEN env var):
  python scripts/push_env_to_railway.py --env production --from-env

Prerequisites (local):
  - Railway CLI authenticated (`railway login`)
  - .env file populated with the keys you want to push
Prerequisites (CI):
  - RAILWAY_TOKEN environment variable set
  - Routed vars set as environment variables
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Railway project topology
# ---------------------------------------------------------------------------

PROJECT_ID = "e82fd2fa-c0e2-4d11-9aad-845c349d02d9"

ENVIRONMENTS = {
    "production": "2ae8dd20-9bfe-4c01-b0c9-ebc46acefbe1",
    "staging": "90f5c442-0021-45ff-a6e1-e9cd67ce2971",
}

SERVICES = {
    "source-access": "b049f036-8b28-40f2-9a8f-5e743e7d5f0c",
    "llm-gateway": "8e14c58f-960f-47c0-92dd-91f5cd370212",
    "data-manager": "7a3ceb79-57e7-4dd2-a245-6e31e151efcc",
    "data-access": "ccf09b67-4573-43d7-bb9c-b6daccbd7235",
    "transform-engine": "fd32e6c0-2e65-400d-8e19-1962145db77c",
    "config-access": "34ffad38-2e3e-4677-8115-e3ec0ac87cf4",
    "schema-engine": "f84c4239-0308-4383-9b21-cdb304c21951",
    "access-engine": "9309f266-8f14-4b1b-b4bf-9dd9b7c85610",
    "scheduler": "ea49a3e2-6f56-44e9-800e-7d9eddc1ecf7",
}

# ---------------------------------------------------------------------------
# Variable → service routing
#
# Each key maps an env var name to the list of service names it should be
# pushed to.  "ALL" is a shorthand for every service in SERVICES.
# ---------------------------------------------------------------------------

VAR_ROUTING: dict[str, list[str]] = {
    # Source connector credentials — only needed on source-access worker,
    # which is where the connector activities execute.
    "UNIPILE_API_KEY": ["source-access"],
    "UNIPILE_DSN": ["source-access"],
    "X_BEARER_TOKEN": ["source-access"],
    "X_CONSUMER_KEY": ["source-access"],
    "X_SECRET_KEY": ["source-access"],
    "X_USERNAME": ["source-access"],
    "POSTHOG_API_KEY": ["source-access"],
    "POSTHOG_PROJECT_ID": ["source-access"],
    "RB2B_API_KEY": ["source-access"],
    # Data Access — Supabase direct connection
    "SUPABASE_DB_URL": ["data-access"],
    # Config Access — Upstash Redis
    "UPSTASH_REDIS_REST_URL": ["config-access"],
    "UPSTASH_REDIS_REST_TOKEN": ["config-access"],
    # LLM Gateway
    "OPENROUTER_API_KEY": ["llm-gateway"],
    # Temporal — shared infrastructure, every worker needs these
    "TEMPORAL_API_KEY": ["ALL"],
    "TEMPORAL_NAMESPACE": ["ALL"],
    "TEMPORAL_REGIONAL_ENDPOINT": ["ALL"],
}

# Variables to skip — local dev / CI only, not needed on Railway
SKIP_VARS = {
    "HONCHO_API_KEY",
    "HONCHO_PEER_NAME",
    "HONCHO_WORKSPACE",
    "MONDAY_TOKEN",
    "EXA_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
}


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a .env file into a dict, respecting quotes and skipping comments."""
    env: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # Strip surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        env[key] = value
    return env


def collect_from_environment() -> dict[str, str]:
    """Collect routed variables from OS environment (for CI)."""
    import os

    env: dict[str, str] = {}
    for var_name in VAR_ROUTING:
        value = os.environ.get(var_name)
        if value:
            env[var_name] = value
    return env


def get_railway_token() -> str:
    """Read the Railway auth token from env var or CLI config."""
    import os

    # CI: RAILWAY_TOKEN env var takes priority
    token = os.environ.get("RAILWAY_TOKEN", "")
    if token:
        return token

    # Local: fall back to Railway CLI config
    config_path = Path.home() / ".railway" / "config.json"
    if not config_path.exists():
        print("ERROR: Railway CLI not authenticated. Run `railway login` first.", file=sys.stderr)
        print("  Or set RAILWAY_TOKEN environment variable for CI usage.", file=sys.stderr)
        sys.exit(1)
    config = json.loads(config_path.read_text())
    token = config.get("user", {}).get("token", "")
    if not token:
        print("ERROR: No token in Railway config. Run `railway login` first.", file=sys.stderr)
        sys.exit(1)
    return token


def upsert_variables(
    token: str,
    project_id: str,
    environment_id: str,
    service_id: str,
    variables: dict[str, str],
) -> bool:
    """Upsert a batch of variables onto a Railway service via GraphQL.

    Uses variableCollectionUpsert which accepts a JSON object of key-value
    pairs — much more efficient than individual upserts.
    """
    # Railway's variableCollectionUpsert mutation
    mutation = """
    mutation($input: VariableCollectionUpsertInput!) {
      variableCollectionUpsert(input: $input)
    }
    """
    input_obj = {
        "projectId": project_id,
        "environmentId": environment_id,
        "serviceId": service_id,
        "variables": variables,
    }
    payload = json.dumps({"query": mutation, "variables": {"input": input_obj}})

    result = subprocess.run(
        [
            "curl", "-s", "-X", "POST",
            "https://backboard.railway.com/graphql/v2",
            "-H", f"Authorization: Bearer {token}",
            "-H", "Content-Type: application/json",
            "-d", payload,
        ],
        capture_output=True,
        text=True,
    )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  ERROR: Unexpected response: {result.stdout[:200]}", file=sys.stderr)
        return False

    if "errors" in data:
        print(f"  ERROR: {data['errors']}", file=sys.stderr)
        return False

    return True


def resolve_services(targets: list[str]) -> list[str]:
    """Expand 'ALL' to every service name."""
    if "ALL" in targets:
        return list(SERVICES.keys())
    return targets


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Push .env variables to Railway services via API"
    )
    parser.add_argument(
        "--env",
        default="staging",
        choices=list(ENVIRONMENTS.keys()),
        help="Railway environment to target (default: staging)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be pushed without actually pushing",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to .env file (default: .env in project root)",
    )
    parser.add_argument(
        "--from-env",
        action="store_true",
        help="Read variables from OS environment instead of .env file (for CI)",
    )
    args = parser.parse_args()

    env_id = ENVIRONMENTS[args.env]

    if args.from_env:
        env_vars = collect_from_environment()
        source_label = "OS environment"
    else:
        project_root = Path(__file__).resolve().parent.parent
        env_path = project_root / args.env_file
        if not env_path.exists():
            print(f"ERROR: {env_path} not found", file=sys.stderr)
            sys.exit(1)
        env_vars = parse_env_file(env_path)
        source_label = str(env_path)

    # Build per-service variable batches
    # service_name → {var_name: var_value}
    batches: dict[str, dict[str, str]] = {}
    skipped: list[str] = []
    unmapped: list[str] = []

    for var_name, var_value in env_vars.items():
        if var_name in SKIP_VARS:
            skipped.append(var_name)
            continue

        if var_name not in VAR_ROUTING:
            unmapped.append(var_name)
            continue

        targets = resolve_services(VAR_ROUTING[var_name])
        for svc_name in targets:
            batches.setdefault(svc_name, {})[var_name] = var_value

    # Report plan
    print(f"Target: {args.env} ({env_id})")
    print(f"Source: {source_label}")
    print()

    for svc_name, svc_vars in sorted(batches.items()):
        var_names = ", ".join(sorted(svc_vars.keys()))
        print(f"  {svc_name}: {var_names}")
    print()

    if skipped:
        print(f"  Skipped (local-only): {', '.join(sorted(skipped))}")
    if unmapped:
        print(f"  Unmapped (not in routing table): {', '.join(sorted(unmapped))}")
    print()

    if args.dry_run:
        print("DRY RUN — no changes made.")
        return

    # Push variables
    token = get_railway_token()
    success_count = 0
    fail_count = 0

    for svc_name, svc_vars in sorted(batches.items()):
        svc_id = SERVICES[svc_name]
        print(f"  Pushing {len(svc_vars)} vars to {svc_name}...", end=" ")
        ok = upsert_variables(token, PROJECT_ID, env_id, svc_id, svc_vars)
        if ok:
            print("OK")
            success_count += 1
        else:
            print("FAILED")
            fail_count += 1

    print()
    if fail_count:
        print(f"Done: {success_count} services updated, {fail_count} failed")
        sys.exit(1)
    else:
        print(f"Done: {success_count} services updated successfully")


if __name__ == "__main__":
    main()
