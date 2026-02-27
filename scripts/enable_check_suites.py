"""Enable checkSuites on Railway deployment triggers.

Railway can auto-deploy on push OR wait until CI check suites pass first.
This script queries all deployment triggers for an environment and enables
checkSuites on any that don't have it — ensuring Railway never deploys code
that hasn't passed CI.

Usage:
  python scripts/enable_check_suites.py --dry-run          # preview current state
  python scripts/enable_check_suites.py --env production    # enable on production
  python scripts/enable_check_suites.py --env staging       # enable on staging

Prerequisites:
  - Railway CLI authenticated (`railway login`)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
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

# Reverse lookup: service ID → name
SERVICE_NAMES = {v: k for k, v in SERVICES.items()}


def get_railway_token() -> str:
    """Read the Railway auth token from the CLI config."""
    config_path = Path.home() / ".railway" / "config.json"
    if not config_path.exists():
        print("ERROR: Railway CLI not authenticated. Run `railway login` first.", file=sys.stderr)
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
        sys.exit(1)

    if "errors" in data:
        print(f"ERROR: {json.dumps(data['errors'], indent=2)}", file=sys.stderr)
        sys.exit(1)

    return data.get("data", {})


def get_deployment_triggers(token: str, env_id: str) -> list[dict]:
    """Query all deployment triggers for services in the project, filtered by environment."""
    query = """
    query($projectId: String!) {
      project(id: $projectId) {
        services {
          edges {
            node {
              id
              name
              repoTriggers {
                edges {
                  node {
                    id
                    environmentId
                    branch
                    checkSuites
                    repository
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    data = graphql(token, query, {"projectId": PROJECT_ID})
    triggers = []
    for svc_edge in data.get("project", {}).get("services", {}).get("edges", []):
        svc = svc_edge["node"]
        for trig_edge in svc.get("repoTriggers", {}).get("edges", []):
            trig = trig_edge["node"]
            if trig["environmentId"] == env_id:
                triggers.append({
                    "trigger_id": trig["id"],
                    "service_id": svc["id"],
                    "service_name": svc["name"],
                    "branch": trig.get("branch", ""),
                    "check_suites": trig.get("checkSuites", False),
                    "repository": trig.get("repository", ""),
                })
    return triggers


def update_trigger(token: str, trigger_id: str, check_suites: bool) -> bool:
    """Update a deployment trigger to enable/disable checkSuites."""
    mutation = """
    mutation($id: String!, $input: DeploymentTriggerUpdateInput!) {
      deploymentTriggerUpdate(id: $id, input: $input) {
        id
      }
    }
    """
    data = graphql(token, mutation, {
        "id": trigger_id,
        "input": {"checkSuites": check_suites},
    })
    return "deploymentTriggerUpdate" in data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enable checkSuites on Railway deployment triggers"
    )
    parser.add_argument(
        "--env",
        default="production",
        choices=list(ENVIRONMENTS.keys()),
        help="Railway environment to target (default: production)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show current trigger state without making changes",
    )
    args = parser.parse_args()

    env_id = ENVIRONMENTS[args.env]
    token = get_railway_token()

    print(f"Environment: {args.env} ({env_id})")
    print()

    triggers = get_deployment_triggers(token, env_id)

    if not triggers:
        print("No deployment triggers found for this environment.")
        return

    # Display current state
    print(f"{'Service':<20} {'Branch':<15} {'checkSuites':<12} {'Repository'}")
    print(f"{'─' * 20} {'─' * 15} {'─' * 12} {'─' * 40}")
    for t in sorted(triggers, key=lambda x: x["service_name"]):
        cs = "✅ true" if t["check_suites"] else "❌ false"
        print(f"{t['service_name']:<20} {t['branch']:<15} {cs:<12} {t['repository']}")

    # Find triggers that need updating
    needs_update = [t for t in triggers if not t["check_suites"]]

    print()
    if not needs_update:
        print("All triggers already have checkSuites enabled.")
        return

    print(f"{len(needs_update)} trigger(s) need checkSuites enabled:")
    for t in needs_update:
        print(f"  - {t['service_name']} ({t['branch']})")
    print()

    if args.dry_run:
        print("DRY RUN — no changes made.")
        return

    # Apply updates
    success_count = 0
    fail_count = 0
    for t in needs_update:
        print(f"  Enabling checkSuites on {t['service_name']}...", end=" ")
        ok = update_trigger(token, t["trigger_id"], True)
        if ok:
            print("OK")
            success_count += 1
        else:
            print("FAILED")
            fail_count += 1

    print()
    if fail_count:
        print(f"Done: {success_count} updated, {fail_count} failed")
        sys.exit(1)
    else:
        print(
            f"Done: {success_count} triggers updated"
            " — Railway will now wait for CI before deploying."
        )


if __name__ == "__main__":
    main()
