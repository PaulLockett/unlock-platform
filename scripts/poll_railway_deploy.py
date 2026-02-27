"""Poll Railway deployments until all services finish deploying.

Waits for the latest deployment on each service in the target environment
to reach a terminal state (SUCCESS, FAILED, CRASHED). Used by the post-deploy
smoke test workflow to gate health checks on actual deployment completion.

Exit codes:
  0 — all services deployed successfully
  1 — one or more services FAILED or CRASHED
  2 — timed out waiting for deployments to finish

Usage:
  python scripts/poll_railway_deploy.py                          # defaults to production
  python scripts/poll_railway_deploy.py --env staging            # check staging
  python scripts/poll_railway_deploy.py --timeout 300            # 5 min timeout

In CI, reads RAILWAY_TOKEN from environment. Locally, reads from ~/.railway/config.json.

Outputs for GitHub Actions:
  status=success|failed|timeout  → written to $GITHUB_OUTPUT if set
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Railway project topology — same constants as push_env_to_railway.py
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

# Terminal deployment statuses
TERMINAL_STATUSES = {"SUCCESS", "FAILED", "CRASHED", "REMOVED"}
FAILURE_STATUSES = {"FAILED", "CRASHED"}


def get_railway_token() -> str:
    """Read Railway token from env (CI) or CLI config (local)."""
    token = os.environ.get("RAILWAY_TOKEN", "")
    if token:
        return token

    config_path = Path.home() / ".railway" / "config.json"
    if not config_path.exists():
        print("ERROR: No RAILWAY_TOKEN env var and Railway CLI not authenticated.", file=sys.stderr)
        sys.exit(1)
    config = json.loads(config_path.read_text())
    token = config.get("user", {}).get("token", "")
    if not token:
        print("ERROR: No token in Railway config. Run `railway login` first.", file=sys.stderr)
        sys.exit(1)
    return token


def graphql(token: str, query: str, variables: dict | None = None) -> dict:
    """Execute a Railway GraphQL query and return the parsed response."""
    payload = json.dumps({"query": query, "variables": variables or {}})
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
        print(f"ERROR: Unexpected response: {result.stdout[:200]}", file=sys.stderr)
        return {}

    if "errors" in data:
        print(f"ERROR: {json.dumps(data['errors'], indent=2)}", file=sys.stderr)
        return {}

    return data.get("data", {})


def get_latest_deployment(
    token: str, env_id: str, service_id: str
) -> dict:
    """Get the latest deployment for a service in the environment."""
    query = """
    query($input: DeploymentListInput!) {
      deployments(first: 1, input: $input) {
        edges {
          node {
            id
            status
            createdAt
          }
        }
      }
    }
    """
    data = graphql(token, query, {
        "input": {
            "projectId": PROJECT_ID,
            "environmentId": env_id,
            "serviceId": service_id,
        },
    })
    edges = data.get("deployments", {}).get("edges", [])
    if edges:
        deploy = edges[0]["node"]
        return {
            "id": deploy["id"],
            "status": deploy["status"],
            "created_at": deploy.get("createdAt", ""),
        }
    return {"id": "", "status": "NO_DEPLOYMENT", "created_at": ""}


def get_all_deployments(token: str, env_id: str) -> dict[str, dict]:
    """Get the latest deployment for each service in the environment.

    Returns: {service_name: {"status": ..., "id": ..., "created_at": ...}}
    """
    results = {}
    for name, service_id in SERVICES.items():
        results[name] = get_latest_deployment(token, env_id, service_id)
    return results


def write_github_output(key: str, value: str) -> None:
    """Write a key=value pair to $GITHUB_OUTPUT if running in Actions."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"{key}={value}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Poll Railway until all services finish deploying"
    )
    parser.add_argument(
        "--env",
        default="production",
        choices=list(ENVIRONMENTS.keys()),
        help="Railway environment to poll (default: production)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Timeout in seconds (default: 600 = 10 minutes)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Poll interval in seconds (default: 30)",
    )
    args = parser.parse_args()

    env_id = ENVIRONMENTS[args.env]
    token = get_railway_token()

    print(f"Polling {args.env} deployments (timeout: {args.timeout}s, interval: {args.interval}s)")
    print()

    start_time = time.time()

    while True:
        elapsed = time.time() - start_time
        if elapsed > args.timeout:
            print(f"\nTIMEOUT after {args.timeout}s — deployments did not finish.")
            write_github_output("status", "timeout")
            sys.exit(2)

        deployments = get_all_deployments(token, env_id)

        if not deployments:
            print("WARNING: No deployments found. Retrying...")
            time.sleep(args.interval)
            continue

        # Display current state
        all_terminal = True
        any_failed = False

        print(f"[{int(elapsed)}s] Deployment status:")
        for name in sorted(deployments):
            d = deployments[name]
            status = d["status"]
            icon = "✅" if status == "SUCCESS" else "❌" if status in FAILURE_STATUSES else "⏳"
            print(f"  {icon} {name:<20} {status}")

            if status not in TERMINAL_STATUSES:
                all_terminal = False
            if status in FAILURE_STATUSES:
                any_failed = True

        if all_terminal:
            print()
            if any_failed:
                failed = [n for n, d in deployments.items() if d["status"] in FAILURE_STATUSES]
                print(f"FAILED: {', '.join(failed)}")
                write_github_output("status", "failed")
                sys.exit(1)
            else:
                print("All services deployed successfully.")
                write_github_output("status", "success")
                sys.exit(0)

        print(f"  Waiting {args.interval}s...")
        print()
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
