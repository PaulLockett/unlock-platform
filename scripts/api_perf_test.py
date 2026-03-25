"""
API Route Latency Test — measures cold + warm read/write latency per Canvas route.

Uses Browserbase + Playwright for authenticated fetch (same pattern as canvas_api_test.py),
then measures latency via page.evaluate() with Date.now() timing.

Routes measured (3 runs each: cold + warm + warm):
- GET /api/views
- GET /api/views/{shareToken}
- GET /api/configs?type=schema
- POST /api/configure (start + poll to completion — write path)

Outputs JSON with per-route latencies, thresholds, and pass/fail.

Usage:
    VERCEL_PREVIEW_URL=https://... \
    BROWSERBASE_API_KEY=... \
    BROWSERBASE_PROJECT_ID=... \
    RESEND_API_KEY=... \
    VERCEL_PROTECTION_BYPASS_TOKEN=... \
    TEST_ADMIN_EMAIL=admin@example.com \
    python scripts/api_perf_test.py
"""

from __future__ import annotations

import html as html_mod
import json
import os
import re
import sys
import time

import httpx
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VERCEL_PREVIEW_URL = os.environ["VERCEL_PREVIEW_URL"].rstrip("/")
BROWSERBASE_API_KEY = os.environ["BROWSERBASE_API_KEY"]
BROWSERBASE_PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]
RESEND_API_KEY = os.environ["RESEND_API_KEY"]
BYPASS_TOKEN = os.environ["VERCEL_PROTECTION_BYPASS_TOKEN"]
TEST_ADMIN_EMAIL = os.environ.get("TEST_ADMIN_EMAIL", "")
RESEND_DOMAIN = os.environ.get(
    "RESEND_TESTING_RECIPIENT_DOMAIN", "hpidome.resend.app"
)

# Thresholds
COLD_READ_THRESHOLD = 2000
WARM_READ_THRESHOLD = 500
WRITE_THRESHOLD = 5000


# ---------------------------------------------------------------------------
# Helpers (shared with canvas_api_test.py)
# ---------------------------------------------------------------------------


def create_browserbase_session() -> dict:
    for attempt in range(5):
        resp = httpx.post(
            "https://api.browserbase.com/v1/sessions",
            headers={
                "X-BB-API-Key": BROWSERBASE_API_KEY,
                "Content-Type": "application/json",
            },
            json={"projectId": BROWSERBASE_PROJECT_ID},
            timeout=30,
        )
        if resp.status_code == 429:
            wait = 5 * (attempt + 1)
            print(f"  Browserbase rate limited, retrying in {wait}s...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()
    return resp.json()


def _resend_get(url: str, **kwargs) -> httpx.Response:
    headers = {"Authorization": f"Bearer {RESEND_API_KEY}"}
    for attempt in range(4):
        resp = httpx.get(url, headers=headers, timeout=15, **kwargs)
        if resp.status_code != 429:
            resp.raise_for_status()
            return resp
        time.sleep(2**attempt)
    resp.raise_for_status()
    return resp


def get_latest_email_id(recipient: str) -> str | None:
    data = _resend_get(
        "https://api.resend.com/emails", params={"limit": 5}
    ).json()
    for email in data.get("data", []):
        if recipient in email.get("to", []):
            return email["id"]
    return None


def poll_resend_for_email(
    recipient: str, *, timeout: float = 120, ignore_id: str | None = None
) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        data = _resend_get(
            "https://api.resend.com/emails", params={"limit": 20}
        ).json()
        for email in data.get("data", []):
            if recipient in email.get("to", []):
                if ignore_id and email["id"] == ignore_id:
                    break
                detail = _resend_get(
                    f"https://api.resend.com/emails/{email['id']}"
                )
                return detail.json()
        time.sleep(3)
    raise TimeoutError(f"Email for {recipient} not received within {timeout}s")


def extract_magic_link(html: str) -> str:
    pattern = r'href=["\']([^"\']*(?:/auth/v1/verify|type=magiclink)[^"\']*)["\']'
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        return html_mod.unescape(match.group(1))
    pattern_fallback = r"(https?://[^\s\"'<>]+token=[^\s\"'<>]+)"
    match = re.search(pattern_fallback, html)
    if match:
        return html_mod.unescape(match.group(1))
    raise ValueError("Could not extract magic link from email HTML")


def bypass_vercel(page, url: str):
    bypass_url = (
        f"{url}"
        f"?x-vercel-protection-bypass={BYPASS_TOKEN}"
        f"&x-vercel-set-bypass-cookie=samesitenone"
    )
    page.goto(bypass_url, wait_until="networkidle")


# ---------------------------------------------------------------------------
# Latency measurement
# ---------------------------------------------------------------------------

MEASURE_FETCH_JS = """
async ({ method, url, body }) => {
    const opts = { method, headers: {} };
    if (body) {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(body);
    }
    const start = Date.now();
    const res = await fetch(url, opts);
    const elapsed = Date.now() - start;
    const data = await res.json().catch(() => ({}));
    return { elapsed_ms: elapsed, status: res.status, body: data };
}
"""

POLL_WORKFLOW_JS = """
async (workflowId) => {
    const start = Date.now();
    for (let i = 0; i < 25; i++) {
        await new Promise(r => setTimeout(r, 3000));
        const res = await fetch('/api/workflow/' + workflowId);
        const data = await res.json();
        if (data.status === 'COMPLETED') {
            return { elapsed_ms: Date.now() - start, result: data.result };
        }
        if (['FAILED', 'TIMED_OUT', 'CANCELLED'].includes(data.status)) {
            return { elapsed_ms: Date.now() - start, error: data.error || data.status };
        }
    }
    return { elapsed_ms: Date.now() - start, error: 'poll timeout' };
}
"""


def measure_route(page, method: str, url: str, body=None, runs: int = 3):
    """Measure latency for a route across multiple runs. Returns list of ms values."""
    timings = []
    for _ in range(runs):
        result = page.evaluate(
            MEASURE_FETCH_JS, {"method": method, "url": url, "body": body}
        )
        timings.append(result["elapsed_ms"])
    return timings


def run_test() -> dict:
    test_email = (
        TEST_ADMIN_EMAIL or f"perf-{int(time.time())}@{RESEND_DOMAIN}"
    )
    start = time.monotonic()
    routes: list[dict] = []
    recording_url = ""

    print(f"API Perf Test — {VERCEL_PREVIEW_URL}")
    print(f"  Test email: {test_email}")
    print()

    try:
        # --- Create Browserbase session ---
        session = create_browserbase_session()
        session_id = session["id"]
        connect_url = session["connectUrl"]
        recording_url = f"https://www.browserbase.com/sessions/{session_id}"
        print(f"  Browserbase session: {session_id}")

        with sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(connect_url)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(60_000)

            # --- Auth (with retry — Supabase rate-limits magic links) ---
            bypass_vercel(page, f"{VERCEL_PREVIEW_URL}/")
            page.goto(
                f"{VERCEL_PREVIEW_URL}/login", wait_until="networkidle"
            )
            pre_send_email_id = get_latest_email_id(test_email)

            magic_link_sent = False
            login_url = f"{VERCEL_PREVIEW_URL}/login"
            for attempt in range(1, 4):
                email_input = page.locator('input[type="email"]')
                email_input.fill(test_email)
                page.locator('button[type="submit"]').click()
                try:
                    page.wait_for_selector(
                        "text=Check your email", timeout=15_000
                    )
                    magic_link_sent = True
                    break
                except Exception as exc:
                    if attempt < 3:
                        print(
                            f"    Attempt {attempt}/3 failed: {exc}"
                        )
                        page.wait_for_timeout(10_000 * attempt)
                        page.goto(
                            login_url, wait_until="networkidle"
                        )

            if not magic_link_sent:
                raise RuntimeError("Failed to send magic link after 3 attempts")

            print("  Polling for magic link email...")
            email_data = poll_resend_for_email(
                test_email, ignore_id=pre_send_email_id
            )
            html_body = email_data.get("html", "") or email_data.get(
                "text", ""
            )
            magic_link = extract_magic_link(html_body)
            page.goto(magic_link, wait_until="domcontentloaded")

            # Wait for redirect to home — retry if stuck on /login
            for _nav_attempt in range(3):
                try:
                    page.wait_for_url("**/", timeout=15_000)
                    if "/login" not in page.url:
                        break
                except Exception:
                    pass
                page.goto(
                    f"{VERCEL_PREVIEW_URL}/",
                    wait_until="domcontentloaded",
                )

            if "/login" in page.url:
                raise RuntimeError(
                    f"Auth failed — stuck on login after 3 attempts: {page.url}"
                )
            print("  Authenticated successfully")

            # --- Discover a share token for single-view tests ---
            views_probe = page.evaluate(MEASURE_FETCH_JS, {
                "method": "GET",
                "url": "/api/views",
                "body": None,
            })
            share_token = None
            items = views_probe.get("body", {}).get("items", [])
            if items:
                share_token = items[0].get("share_token")
            print(
                f"  Share token for view test: "
                f"{share_token or '(none — will skip)'}"
            )

            # --- Measure reads ---
            print("\n  Measuring GET /api/views...")
            timings = measure_route(page, "GET", "/api/views")
            routes.append({
                "route": "GET /api/views",
                "cold_ms": timings[0],
                "warm_avg_ms": round(sum(timings[1:]) / len(timings[1:])),
                "all_ms": timings,
                "threshold_cold": COLD_READ_THRESHOLD,
                "threshold_warm": WARM_READ_THRESHOLD,
                "status": (
                    "pass"
                    if timings[0] < COLD_READ_THRESHOLD
                    and (sum(timings[1:]) / len(timings[1:]))
                    < WARM_READ_THRESHOLD
                    else "fail"
                ),
            })
            print(
                f"    cold={timings[0]}ms  warm_avg="
                f"{routes[-1]['warm_avg_ms']}ms"
            )

            if share_token:
                print(
                    f"  Measuring GET /api/views/{share_token}..."
                )
                timings = measure_route(
                    page, "GET", f"/api/views/{share_token}"
                )
                routes.append({
                    "route": "GET /api/views/{shareToken}",
                    "cold_ms": timings[0],
                    "warm_avg_ms": round(
                        sum(timings[1:]) / len(timings[1:])
                    ),
                    "all_ms": timings,
                    "threshold_cold": COLD_READ_THRESHOLD,
                    "threshold_warm": WARM_READ_THRESHOLD,
                    "status": (
                        "pass"
                        if timings[0] < COLD_READ_THRESHOLD
                        and (sum(timings[1:]) / len(timings[1:]))
                        < WARM_READ_THRESHOLD
                        else "fail"
                    ),
                })
                print(
                    f"    cold={timings[0]}ms  warm_avg="
                    f"{routes[-1]['warm_avg_ms']}ms"
                )

            print("  Measuring GET /api/configs?type=schema...")
            timings = measure_route(
                page, "GET", "/api/configs?type=schema"
            )
            routes.append({
                "route": "GET /api/configs?type=schema",
                "cold_ms": timings[0],
                "warm_avg_ms": round(sum(timings[1:]) / len(timings[1:])),
                "all_ms": timings,
                "threshold_cold": COLD_READ_THRESHOLD,
                "threshold_warm": WARM_READ_THRESHOLD,
                "status": (
                    "pass"
                    if timings[0] < COLD_READ_THRESHOLD
                    and (sum(timings[1:]) / len(timings[1:]))
                    < WARM_READ_THRESHOLD
                    else "fail"
                ),
            })
            print(
                f"    cold={timings[0]}ms  warm_avg="
                f"{routes[-1]['warm_avg_ms']}ms"
            )

            # --- Measure write (POST /api/configure) ---
            print("  Measuring POST /api/configure (write path)...")
            write_body = {
                "config_type": "schema",
                "name": f"Perf Test Schema {int(time.time())}",
                "schema_type": "analysis",
                "fields": [
                    {
                        "source_field": "test",
                        "target_field": "test",
                        "transform": None,
                    }
                ],
            }
            start_result = page.evaluate(
                MEASURE_FETCH_JS,
                {
                    "method": "POST",
                    "url": "/api/configure",
                    "body": write_body,
                },
            )
            wf_id = (
                start_result.get("body", {}).get("workflowId", "")
            )
            start_ms = start_result["elapsed_ms"]

            if wf_id:
                poll_result = page.evaluate(POLL_WORKFLOW_JS, wf_id)
                total_ms = start_ms + poll_result.get("elapsed_ms", 0)
            else:
                total_ms = start_ms

            routes.append({
                "route": "POST /api/configure",
                "cold_ms": total_ms,
                "warm_avg_ms": total_ms,
                "all_ms": [total_ms],
                "threshold_cold": WRITE_THRESHOLD,
                "threshold_warm": WRITE_THRESHOLD,
                "status": "pass" if total_ms < WRITE_THRESHOLD else "fail",
            })
            print(f"    total={total_ms}ms")

            browser.close()

    except Exception as exc:
        print(f"\n  ERROR: {exc}")
        routes.append({
            "route": "ERROR",
            "cold_ms": 0,
            "warm_avg_ms": 0,
            "all_ms": [],
            "threshold_cold": 0,
            "threshold_warm": 0,
            "status": "error",
            "error": str(exc),
        })

    all_passed = all(r["status"] == "pass" for r in routes)
    duration = round(time.monotonic() - start, 1)

    result = {
        "passed": all_passed,
        "duration_s": duration,
        "recording_url": recording_url,
        "preview_url": VERCEL_PREVIEW_URL,
        "routes": routes,
    }

    print(f"\n{'PASSED' if all_passed else 'FAILED'} in {duration}s")
    print(f"Recording: {recording_url}")
    return result


if __name__ == "__main__":
    try:
        result = run_test()
    except Exception as exc:
        print(f"\nFATAL: {exc}", file=sys.stderr)
        sys.exit(1)

    output_path = os.environ.get(
        "RESULT_JSON", "/tmp/api-perf-result.json"
    )
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    sys.exit(0 if result["passed"] else 1)
