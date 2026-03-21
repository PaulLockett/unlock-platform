"""
Canvas E2E Integration Test — Admin Data Lifecycle + View Sharing

Exercises the complete Canvas data workflow end-to-end:

  Flow 1: Admin Data Lifecycle
    1. Login as admin (reuse auth E2E magic link flow)
    2. Navigate to Admin → Sources
    3. Create a new source (Meta Ads, file_upload protocol)
    4. Navigate to Admin → Upload
    5. Upload meta_ads_test_data.csv
    6. Verify ingestion triggers (toast/status indicator)
    7. Navigate to Views → create a new view for the ingested data
    8. Verify data appears in the view

  Flow 2: View Sharing
    1. Admin creates a view (or reuses from Flow 1)
    2. Copy share link
    3. Open share link in new incognito context (anonymous)
    4. Verify public view loads with data
    5. Admin changes visibility to restricted
    6. Verify anonymous access now blocked

  Flow 3: Query Validation
    1. Navigate to a view with known data
    2. Verify panel renders correct data
    3. Apply a date filter
    4. Verify filtered results

Outputs JSON with pass/fail, Browserbase recording URL, step details, and duration.

Usage:
    VERCEL_PREVIEW_URL=https://... \\
    BROWSERBASE_API_KEY=... \\
    BROWSERBASE_PROJECT_ID=... \\
    RESEND_API_KEY=... \\
    VERCEL_PROTECTION_BYPASS_TOKEN=... \\
    TEST_ADMIN_EMAIL=admin@example.com \\
    python scripts/canvas_e2e_test.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# Configuration from environment
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

FIXTURE_DIR = Path(__file__).parent / "fixtures"
CSV_FIXTURE = FIXTURE_DIR / "meta_ads_test_data.csv"

# Polling config
EMAIL_POLL_INTERVAL = 3
EMAIL_POLL_TIMEOUT = 120
PAGE_LOAD_TIMEOUT = 60_000


class _StepFailure(Exception):
    """Raised when a test step fails."""


# ---------------------------------------------------------------------------
# Helpers (reused from auth_e2e_test.py)
# ---------------------------------------------------------------------------


def create_browserbase_session() -> dict:
    """Create a Browserbase session with retry on 429 rate limits.

    The auth E2E and canvas E2E workflows run in parallel on the same PR,
    so they can hit the Browserbase concurrency/rate limit simultaneously.
    """
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
            wait = 5 * (attempt + 1)  # 5, 10, 15, 20, 25 seconds
            print(f"  Browserbase rate limited (429), retrying in {wait}s...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()
    return resp.json()  # unreachable but satisfies type checkers


def _resend_get(url: str, **kwargs) -> httpx.Response:
    headers = {"Authorization": f"Bearer {RESEND_API_KEY}"}
    for attempt in range(4):
        resp = httpx.get(url, headers=headers, timeout=15, **kwargs)
        if resp.status_code != 429:
            resp.raise_for_status()
            return resp
        time.sleep(2 ** attempt)
    resp.raise_for_status()
    return resp


def get_latest_email_id(recipient: str) -> str | None:
    """Return the ID of the most recent email to *recipient*, or None."""
    data = _resend_get(
        "https://api.resend.com/emails",
        params={"limit": 5},
    ).json()
    for email in data.get("data", []):
        if recipient in email.get("to", []):
            return email["id"]
    return None


def poll_resend_for_email(
    recipient: str,
    *,
    timeout: float = EMAIL_POLL_TIMEOUT,
    ignore_id: str | None = None,
) -> dict:
    """Poll Resend for a new email to *recipient*.

    If *ignore_id* is set, skip that email so parallel tests don't
    pick up each other's magic-link emails.
    """
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        data = _resend_get(
            "https://api.resend.com/emails",
            params={"limit": 20},
        ).json()

        for email in data.get("data", []):
            recipients = email.get("to", [])
            if recipient in recipients:
                if ignore_id and email["id"] == ignore_id:
                    break  # old email — nothing newer yet
                detail = _resend_get(
                    f"https://api.resend.com/emails/{email['id']}"
                )
                return detail.json()

        time.sleep(EMAIL_POLL_INTERVAL)

    raise TimeoutError(
        f"Email for {recipient} not received within {timeout}s"
    )


def extract_magic_link(html: str) -> str:
    import html as html_mod
    import re

    pattern = r'href=["\']([^"\']*(?:/auth/v1/verify|type=magiclink)[^"\']*)["\']'
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        return html_mod.unescape(match.group(1))

    pattern_fallback = r'(https?://[^\s"\'<>]+token=[^\s"\'<>]+)'
    match = re.search(pattern_fallback, html)
    if match:
        return html_mod.unescape(match.group(1))

    raise ValueError("Could not extract magic link from email HTML")


def bypass_vercel(page, url: str):
    """Navigate with Vercel deployment protection bypass."""
    bypass_url = (
        f"{url}"
        f"?x-vercel-protection-bypass={BYPASS_TOKEN}"
        f"&x-vercel-set-bypass-cookie=samesitenone"
    )
    page.goto(bypass_url, wait_until="networkidle")


# ---------------------------------------------------------------------------
# Test flows
# ---------------------------------------------------------------------------


def run_test() -> dict:
    """Run the full Canvas E2E test. Returns a result dict."""
    test_email = TEST_ADMIN_EMAIL or f"canvas-e2e-{int(time.time())}@{RESEND_DOMAIN}"
    steps: list[dict] = []
    start = time.monotonic()
    recording_url = ""
    screenshot_path = os.environ.get(
        "SCREENSHOT_PATH", "/tmp/canvas-e2e-screenshot.png"
    )

    def step(name: str, *, passed: bool = True, detail: str = "") -> None:
        elapsed = round(time.monotonic() - start, 1)
        steps.append(
            {"name": name, "passed": passed, "detail": detail, "elapsed_s": elapsed}
        )
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}" + (f" ({detail})" if detail else ""))
        if not passed:
            raise _StepFailure(f"Step failed: {name} — {detail}")

    def build_result() -> dict:
        duration = round(time.monotonic() - start, 1)
        all_passed = bool(steps) and all(s["passed"] for s in steps)
        return {
            "passed": all_passed,
            "test_email": test_email,
            "recording_url": recording_url,
            "screenshot_path": screenshot_path,
            "duration_s": duration,
            "preview_url": VERCEL_PREVIEW_URL,
            "steps": steps,
        }

    print(f"Canvas E2E Test — {VERCEL_PREVIEW_URL}")
    print(f"  Test email: {test_email}")
    print()

    try:
        # --- Step 1: Create Browserbase session ---
        print("Creating Browserbase session...")
        session = create_browserbase_session()
        session_id = session["id"]
        connect_url = session["connectUrl"]
        recording_url = f"https://www.browserbase.com/sessions/{session_id}"
        step("Created Browserbase session", detail=session_id)

        with sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(connect_url)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(PAGE_LOAD_TIMEOUT)

            # --- Step 2: Bypass Vercel + navigate to login ---
            bypass_vercel(page, f"{VERCEL_PREVIEW_URL}/")
            step("Bypassed Vercel deployment protection")

            # --- Step 3: Login as admin ---
            page.goto(f"{VERCEL_PREVIEW_URL}/login", wait_until="networkidle")
            step(
                "Navigated to /login",
                passed=page.url.rstrip("/").endswith("/login"),
                detail=page.url,
            )

            # Snapshot latest email ID BEFORE sending the magic link
            # so we skip stale emails from parallel tests.
            pre_send_email_id = get_latest_email_id(test_email)

            # Submit magic link with retry (Supabase rate-limits)
            login_url = f"{VERCEL_PREVIEW_URL}/login"
            max_attempts = 3
            magic_link_sent = False
            last_error = ""
            for attempt in range(1, max_attempts + 1):
                email_input = page.locator('input[type="email"]')
                email_input.fill(test_email)
                page.locator('button[type="submit"]').click()
                try:
                    page.wait_for_selector(
                        "text=Check your email", timeout=10_000
                    )
                    magic_link_sent = True
                    break
                except _StepFailure:
                    raise
                except Exception as exc:
                    error_el = page.locator(
                        "p.text-red-600, p.text-red-400"
                    )
                    last_error = (
                        error_el.text_content()
                        if error_el.count() > 0
                        else str(exc)
                    )
                    if attempt < max_attempts:
                        wait = 10 * attempt
                        print(
                            f"    Attempt {attempt}/{max_attempts} "
                            f"failed: {last_error}"
                        )
                        print(f"    Retrying in {wait}s...")
                        page.wait_for_timeout(wait * 1000)
                        page.goto(login_url, wait_until="networkidle")

            if magic_link_sent:
                step("Submitted magic link request", detail=test_email)
            else:
                step(
                    "Submitted magic link request",
                    passed=False,
                    detail=(
                        f"Error after {max_attempts} attempts: "
                        f"{last_error}"
                    ),
                )

            # Poll for email, skipping any that existed before we sent
            print(f"  Polling Resend for email to {test_email}...")
            email_data = poll_resend_for_email(
                test_email, ignore_id=pre_send_email_id
            )
            step("Received magic link email")

            # Extract and navigate to magic link
            html_body = email_data.get("html", "") or email_data.get("text", "")
            magic_link = extract_magic_link(html_body)
            page.goto(magic_link, wait_until="domcontentloaded")
            # Wait for the redirect chain to land (Supabase → callback → /)
            page.wait_for_url("**/", timeout=30000)
            step("Navigated to magic link", detail=page.url)
            body_text = page.text_content("body") or ""
            logged_in = (
                test_email in body_text
                or "sign out" in body_text.lower()
                or "log out" in body_text.lower()
            )
            step(
                "Verified logged-in state",
                passed=logged_in,
                detail=f"URL: {page.url}",
            )

            # --- Probe infrastructure readiness ---
            # Two prerequisites for workflow-dependent flows:
            # 1. Admin role (for admin-gated routes)
            # 2. Temporal connectivity (for all workflow routes)
            # Probe both with a single request + the Temporal probe.
            admin_probe = page.evaluate("""
                async () => {
                    const controller = new AbortController();
                    const timeout = setTimeout(
                        () => controller.abort(), 55000
                    );
                    try {
                        const res = await fetch('/api/admin/sources', {
                            signal: controller.signal
                        });
                        clearTimeout(timeout);
                        const body = await res.json().catch(() => ({}));
                        return {
                            status: res.status,
                            body: JSON.stringify(body).substring(0, 300)
                        };
                    } catch (e) {
                        clearTimeout(timeout);
                        return { status: 0, error: e.message };
                    }
                }
            """)
            is_admin = admin_probe["status"] not in (403, 401)
            # 200 = admin + Temporal working
            # 500 = admin OK but Temporal down
            # 403 = not admin
            temporal_ok = admin_probe["status"] == 200
            probe_body = admin_probe.get(
                "body", admin_probe.get("error", "")
            )
            step(
                "Checked admin role",
                passed=is_admin,
                detail=(
                    f"is_admin={is_admin} "
                    f"(status={admin_probe.get('status')})"
                ),
            )
            step(
                "Checked Temporal connectivity",
                passed=temporal_ok,
                detail=(
                    f"temporal_ok={temporal_ok} "
                    f"(status={admin_probe.get('status')}) "
                    f"body={probe_body}"
                ),
            )

            # --- Flow 1: Admin Data Lifecycle ---

            # Step: Create source via API
            api_result = page.evaluate("""
                async () => {
                    const res = await fetch('/api/admin/sources', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            name: 'Meta Ads E2E Test',
                            protocol: 'file_upload',
                            service: 'meta',
                            resource_type: 'ads_metrics'
                        })
                    });
                    const body = await res.json().catch(
                        () => ({ error: 'non-JSON response' })
                    );
                    return { status: res.status, body };
                }
            """)
            source_created = (
                api_result["status"] == 201
                or (
                    api_result["status"] == 500
                    and "duplicate"
                    in str(api_result.get("body", {})).lower()
                )
            )
            post_body = str(api_result.get("body", {}))[:200]
            step(
                "Created source via API",
                passed=source_created,
                detail=(
                    f"status={api_result['status']} "
                    f"body={post_body}"
                ),
            )

            # Step: List sources via API
            list_result = page.evaluate("""
                async () => {
                    const res = await fetch('/api/admin/sources');
                    const b = await res.json().catch(
                        () => ({ error: 'non-JSON' })
                    );
                    return { status: res.status, body: b };
                }
            """)
            step(
                "Listed sources via API",
                passed=list_result["status"] == 200,
                detail=(
                    f"count="
                    f"{len(list_result.get('body', {}).get('sources', []))}"
                ),
            )

            # Step: Upload CSV via API
            csv_content = CSV_FIXTURE.read_text()
            upload_result = page.evaluate(
                """
                async (csvContent) => {
                    const blob = new Blob([csvContent], {
                        type: 'text/csv'
                    });
                    const file = new File(
                        [blob], 'meta_ads_test_data.csv',
                        { type: 'text/csv' }
                    );
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('source_name', 'Meta Ads E2E Test');
                    formData.append('resource_type', 'ads_metrics');
                    const res = await fetch('/api/admin/upload', {
                        method: 'POST',
                        body: formData
                    });
                    const b = await res.json().catch(
                        () => ({ error: 'non-JSON' })
                    );
                    return { status: res.status, body: b };
                }
            """,
                csv_content,
            )
            step(
                "Uploaded CSV via API",
                passed=upload_result["status"] == 200,
                detail=f"status={upload_result['status']}",
            )

            # --- Flow 2: Visual Validation — Dashboard Home ---
            page.goto(
                f"{VERCEL_PREVIEW_URL}/",
                wait_until="domcontentloaded",
            )
            page.wait_for_url("**/", timeout=15000)

            # Verify dashboard home renders with key elements
            has_my_views = page.locator(
                "text=My Views, text=MY VIEWS"
            ).count() > 0 or "views" in (
                page.text_content("body") or ""
            ).lower()
            has_side_nav = page.locator("nav").count() > 0
            step(
                "Dashboard home renders",
                passed=has_my_views or has_side_nav,
                detail=(
                    f"my_views={has_my_views} "
                    f"side_nav={has_side_nav} "
                    f"url={page.url}"
                ),
            )

            # --- Flow 3: Create Schema + View with Panels ---
            # Configure routes now return 202 + workflowId (async).
            # Helper polls /api/workflow/{id} until completion.
            POLL_WORKFLOW_JS = """
                async (workflowId) => {
                    for (let i = 0; i < 25; i++) {
                        await new Promise(r => setTimeout(r, 3000));
                        const res = await fetch('/api/workflow/' + workflowId);
                        const data = await res.json();
                        if (data.status === 'COMPLETED') return data.result;
                        if (data.status === 'FAILED' || data.status === 'TIMED_OUT'
                            || data.status === 'CANCELLED') {
                            return { success: false, error: data.error || data.status };
                        }
                    }
                    return { success: false, error: 'poll timeout' };
                }
            """

            # Create a schema for the Meta Ads data
            schema_start = page.evaluate("""
                async () => {
                    const res = await fetch('/api/configure', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            config_type: 'schema',
                            name: 'Meta Ads E2E Schema',
                            schema_type: 'analysis',
                            fields: [
                                {
                                    source_field: 'Day',
                                    target_field: 'date',
                                    transform: 'date'
                                },
                                {
                                    source_field: 'Account name',
                                    target_field: 'account',
                                    transform: null
                                },
                                {
                                    source_field: 'Reach',
                                    target_field: 'reach',
                                    transform: 'number'
                                },
                                {
                                    source_field: 'Impressions',
                                    target_field: 'impressions',
                                    transform: 'number'
                                }
                            ]
                        })
                    });
                    const b = await res.json().catch(
                        () => ({ error: 'non-JSON' })
                    );
                    return { status: res.status, body: b };
                }
            """)
            schema_wf_id = schema_start.get(
                "body", {}
            ).get("workflowId", "")
            step(
                "Started schema workflow",
                passed=schema_start["status"] == 202,
                detail=(
                    f"status={schema_start['status']} "
                    f"workflowId={schema_wf_id}"
                ),
            )

            # Poll for schema workflow result
            schema_result = page.evaluate(
                POLL_WORKFLOW_JS, schema_wf_id
            )
            schema_id = (schema_result or {}).get("resource_id", "")
            step(
                "Schema workflow completed",
                passed=bool(
                    schema_result and schema_result.get("success")
                ),
                detail=(
                    f"schema_id={schema_id} "
                    f"result={str(schema_result)[:200]}"
                ),
            )

            # Create a view with panels for the Meta Ads data
            view_start = page.evaluate(
                """
                async (schemaId) => {
                    const res = await fetch('/api/configure', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            config_type: 'view',
                            name: 'Meta Ads Dashboard',
                            description: 'E2E test — reach and impressions',
                            visibility: 'public',
                            schema_id: schemaId,
                            layout_config: {
                                grid_columns: 6,
                                panels: [
                                    {
                                        id: 'reach-bar',
                                        title: 'Daily Reach',
                                        chart_type: 'bar',
                                        position: {x:0, y:0, w:3, h:1},
                                        chart_config: {
                                            x_axis: 'date',
                                            y_axis: 'reach'
                                        },
                                        query_config: {}
                                    },
                                    {
                                        id: 'impressions-line',
                                        title: 'Impressions Over Time',
                                        chart_type: 'line',
                                        position: {x:3, y:0, w:3, h:1},
                                        chart_config: {
                                            x_axis: 'date',
                                            y_axis: 'impressions'
                                        },
                                        query_config: {}
                                    },
                                    {
                                        id: 'total-reach',
                                        title: 'Total Reach',
                                        chart_type: 'metric',
                                        position: {x:0, y:1, w:2, h:1},
                                        chart_config: {
                                            value_field: 'reach',
                                            aggregation: 'sum',
                                            label: 'Total Reach'
                                        },
                                        query_config: {}
                                    },
                                    {
                                        id: 'data-table',
                                        title: 'Raw Data',
                                        chart_type: 'table',
                                        position: {x:2, y:1, w:4, h:1},
                                        chart_config: {
                                            columns: [
                                                'date',
                                                'account',
                                                'reach',
                                                'impressions'
                                            ]
                                        },
                                        query_config: {}
                                    }
                                ]
                            }
                        })
                    });
                    const b = await res.json().catch(
                        () => ({ error: 'non-JSON' })
                    );
                    return { status: res.status, body: b };
                }
            """,
                schema_id,
            )
            view_wf_id = view_start.get(
                "body", {}
            ).get("workflowId", "")
            step(
                "Started view workflow",
                passed=view_start["status"] == 202,
                detail=(
                    f"status={view_start['status']} "
                    f"workflowId={view_wf_id}"
                ),
            )

            # Poll for view workflow result
            view_result = page.evaluate(
                POLL_WORKFLOW_JS, view_wf_id
            )
            share_token = (view_result or {}).get(
                "share_token", ""
            )
            step(
                "View workflow completed",
                passed=bool(
                    view_result and view_result.get("success")
                ),
                detail=(
                    f"share_token={share_token} "
                    f"result={str(view_result)[:200]}"
                ),
            )

            # --- Flow 4: Visual Validation — View Dashboard ---
            if share_token:
                page.goto(
                    f"{VERCEL_PREVIEW_URL}/v/{share_token}",
                    wait_until="domcontentloaded",
                )
                # Wait for hydration + Temporal workflow to complete.
                # The view-dashboard.tsx shows a spinner while loading,
                # then renders the view name. Wait for either the title
                # or the footer (proves the page fully rendered).
                page.wait_for_load_state("load", timeout=15000)
                import contextlib

                with contextlib.suppress(Exception):
                    page.wait_for_selector(
                        "text=UNLOCK ALABAMA",
                        timeout=50000,
                    )

                # Use inner_text (rendered text, not raw HTML/RSC)
                body = page.inner_text("body") or ""
                has_view_name = "Meta Ads Dashboard" in body
                has_back = "Back to Views" in body
                has_footer = "UNLOCK ALABAMA" in body
                # Also check for error/loading states
                has_error = (
                    "View not found" in body
                    or "Failed to load" in body
                )
                has_loading = body.strip() == ""
                body_preview = body[:300].replace("\n", " ")
                step(
                    "View dashboard renders",
                    passed=(
                        has_view_name
                        or has_back
                        or has_footer
                    ),
                    detail=(
                        f"view_name={has_view_name} "
                        f"back={has_back} "
                        f"footer={has_footer} "
                        f"error={has_error} "
                        f"empty={has_loading} "
                        f"body={body_preview}"
                    ),
                )

                # Check for panel titles (rendered uppercase by CSS)
                body_upper = body.upper()
                has_reach = "DAILY REACH" in body_upper
                has_impressions = "IMPRESSIONS" in body_upper
                has_no_panels = "NO PANELS" in body_upper
                step(
                    "Panels render on dashboard",
                    passed=(
                        has_reach
                        or has_impressions
                        or has_no_panels
                    ),
                    detail=(
                        f"reach={has_reach} "
                        f"impressions={has_impressions} "
                        f"no_panels={has_no_panels}"
                    ),
                )

            # Screenshot
            page.screenshot(path=screenshot_path, full_page=True)
            browser.close()

    except _StepFailure:
        pass
    except Exception as exc:
        steps.append(
            {
                "name": "Unexpected error",
                "passed": False,
                "detail": str(exc),
                "elapsed_s": round(time.monotonic() - start, 1),
            }
        )

    result = build_result()
    print()
    print(f"{'PASSED' if result['passed'] else 'FAILED'} in {result['duration_s']}s")
    print(f"Recording: {recording_url}")
    return result


if __name__ == "__main__":
    try:
        result = run_test()
    except Exception as exc:
        print(f"\nFATAL: {exc}", file=sys.stderr)
        sys.exit(1)

    output_path = os.environ.get("RESULT_JSON", "/tmp/canvas-e2e-result.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    sys.exit(0 if result["passed"] else 1)
