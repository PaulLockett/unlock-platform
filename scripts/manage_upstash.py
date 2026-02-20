"""Programmatic Upstash Redis database management via Developer API.

Creates, lists, and deletes Redis databases for each environment:
  - unlock-config-staging (persistent)
  - unlock-config-production (persistent)
  - unlock-config-pr-{number} (ephemeral, per-PR)

Uses the Upstash Developer API (api.upstash.com/v2) with Basic auth
(UPSTASH_EMAIL:UPSTASH_API_KEY). This replaces GUI-based database
creation — any developer (or CI) can run this script.

Usage:
  python scripts/manage_upstash.py create --name unlock-config-staging --region us-east-1
  python scripts/manage_upstash.py create --name unlock-config-production --region us-east-1
  python scripts/manage_upstash.py list
  python scripts/manage_upstash.py delete --name unlock-config-pr-42
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

API_BASE = "https://api.upstash.com/v2/redis"


def _get_auth() -> tuple[str, str]:
    """Read Upstash Developer API credentials from environment."""
    email = os.environ.get("UPSTASH_EMAIL", "")
    api_key = os.environ.get("UPSTASH_API_KEY", "")
    if not email or not api_key:
        print(
            "ERROR: UPSTASH_EMAIL and UPSTASH_API_KEY must be set.\n"
            "  Get them from https://console.upstash.com/account/api",
            file=sys.stderr,
        )
        sys.exit(1)
    return email, api_key


def _request(method: str, path: str, body: dict | None = None) -> dict | list:
    """Make an authenticated request to the Upstash Developer API."""
    email, api_key = _get_auth()
    url = f"{API_BASE}{path}"

    cmd = [
        "curl", "-s", "-X", method, url,
        "-u", f"{email}:{api_key}",
        "-H", "Content-Type: application/json",
    ]
    if body:
        cmd.extend(["-d", json.dumps(body)])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if not result.stdout.strip():
        if method == "DELETE":
            return {"status": "deleted"}
        print(f"ERROR: Empty response from {method} {url}", file=sys.stderr)
        sys.exit(1)

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON: {result.stdout[:200]}", file=sys.stderr)
        sys.exit(1)


def cmd_create(args: argparse.Namespace) -> None:
    """Create a Redis database (idempotent — returns existing if name matches)."""
    # Check if database already exists
    databases = _request("GET", "/databases")
    if isinstance(databases, list):
        for db in databases:
            if db.get("database_name") == args.name:
                print(f"Database '{args.name}' already exists (id: {db['database_id']})")
                print(f"  REST URL:   {db.get('endpoint', 'N/A')}")
                print(f"  REST Token: {db.get('rest_token', 'N/A')}")
                return

    data = _request("POST", "/database", {
        "name": args.name,
        "region": args.region,
        "tls": True,
    })

    if "error" in data:
        print(f"ERROR: {data['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"Created database '{args.name}' (id: {data.get('database_id', 'N/A')})")
    print(f"  REST URL:   https://{data.get('endpoint', 'N/A')}")
    print(f"  REST Token: {data.get('rest_token', 'N/A')}")
    print()
    print("Add to .env or GitHub secrets:")
    print(f"  UPSTASH_REDIS_REST_URL=https://{data.get('endpoint', '')}")
    print(f"  UPSTASH_REDIS_REST_TOKEN={data.get('rest_token', '')}")


def cmd_list(args: argparse.Namespace) -> None:
    """List all Redis databases."""
    databases = _request("GET", "/databases")
    if not isinstance(databases, list):
        print(f"ERROR: Unexpected response: {databases}", file=sys.stderr)
        sys.exit(1)

    if not databases:
        print("No databases found.")
        return

    print(f"{'Name':<40} {'ID':<40} {'Region':<15} {'State'}")
    print("-" * 110)
    for db in databases:
        name = db.get("database_name", "N/A")
        db_id = db.get("database_id", "N/A")
        region = db.get("region", "N/A")
        state = db.get("state", "N/A")
        print(f"{name:<40} {db_id:<40} {region:<15} {state}")


def cmd_delete(args: argparse.Namespace) -> None:
    """Delete a Redis database by name."""
    databases = _request("GET", "/databases")
    if not isinstance(databases, list):
        print(f"ERROR: Unexpected response: {databases}", file=sys.stderr)
        sys.exit(1)

    target = None
    for db in databases:
        if db.get("database_name") == args.name:
            target = db
            break

    if not target:
        print(f"Database '{args.name}' not found.")
        return

    db_id = target["database_id"]
    _request("DELETE", f"/database/{db_id}")
    print(f"Deleted database '{args.name}' (id: {db_id})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage Upstash Redis databases")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    create_p = subparsers.add_parser("create", help="Create a database")
    create_p.add_argument("--name", required=True, help="Database name")
    create_p.add_argument("--region", default="us-east-1", help="Region (default: us-east-1)")

    # list
    subparsers.add_parser("list", help="List all databases")

    # delete
    delete_p = subparsers.add_parser("delete", help="Delete a database by name")
    delete_p.add_argument("--name", required=True, help="Database name to delete")

    args = parser.parse_args()

    if args.command == "create":
        cmd_create(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "delete":
        cmd_delete(args)


if __name__ == "__main__":
    main()
