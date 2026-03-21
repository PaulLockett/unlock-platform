"""
Canvas UI E2E Test — Visual Interaction Flow

Exercises the Canvas app through real browser interactions:

  1. Login as admin via magic link
  2. See dashboard home render (side nav, header, view cards)
  3. Click "Create New View" card
  4. Fill name + description in the modal, click "Create View"
  5. Wait for redirect to /v/[shareToken] view dashboard
  6. Verify view dashboard renders (title, panels, footer)
  7. Navigate back to home via "Back to Views" link
  8. Verify the new view card appears in the grid

Every step is a real browser interaction visible in the Browserbase recording.

Usage:
    VERCEL_PREVIEW_URL=https://... \\
    BROWSERBASE_API_KEY=... \\
    BROWSERBASE_PROJECT_ID=... \\
    RESEND_API_KEY=... \\
    VERCEL_PROTECTION_BYPASS_TOKEN=... \\
    TEST_ADMIN_EMAIL=canvas-admin@hpidome.resend.app \\
    python scripts/canvas_ui_e2e_test.py
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

EMAIL_POLL_INTERVAL = 3
EMAIL_POLL_TIMEOUT = 120
PAGE_TIMEOUT = 60_000


class _StepFailure(Exception):
    pass


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


def poll_resend_for_email(
    recipient: str, *, timeout: float = EMAIL_POLL_TIMEOUT
) -> dict:
    deadline = time.monotonic() + timeout
    headers = {"Authorization": f"Bearer {RESEND_API_KEY}"}

    def _get(url: str, **kwargs) -> httpx.Response:
        for attempt in range(4):
            resp = httpx.get(url, headers=headers, timeout=15, **kwargs)
            if resp.status_code != 429:
                resp.raise_for_status()
                return resp
            time.sleep(2 ** attempt)
        resp.raise_for_status()
        return resp

    while time.monotonic() < deadline:
        data = _get(
            "https://api.resend.com/emails",
            params={"limit": 20},
        ).json()
        for email in data.get("data", []):
            if recipient in email.get("to", []):
                return _get(
                    f"https://api.resend.com/emails/{email['id']}"
                ).json()
        time.sleep(EMAIL_POLL_INTERVAL)

    raise TimeoutError(f"Email not received within {timeout}s")


def extract_magic_link(html: str) -> str:
    pattern = (
        r'href=["\']([^"\']*'
        r'(?:/auth/v1/verify|type=magiclink)[^"\']*)["\']'
    )
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        return html_mod.unescape(match.group(1))
    fallback = r'(https?://[^\s"\'<>]+token=[^\s"\'<>]+)'
    match = re.search(fallback, html)
    if match:
        return html_mod.unescape(match.group(1))
    raise ValueError("Could not extract magic link from email")


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------


def run_test() -> dict:
    test_email = (
        TEST_ADMIN_EMAIL
        or f"canvas-ui-{int(time.time())}@{RESEND_DOMAIN}"
    )
    steps: list[dict] = []
    start = time.monotonic()
    recording_url = ""
    screenshot_path = os.environ.get(
        "SCREENSHOT_PATH", "/tmp/canvas-ui-screenshot.png"
    )

    def step(
        name: str, *, passed: bool = True, detail: str = ""
    ) -> None:
        elapsed = round(time.monotonic() - start, 1)
        steps.append(
            {
                "name": name,
                "passed": passed,
                "detail": detail,
                "elapsed_s": elapsed,
            }
        )
        status = "PASS" if passed else "FAIL"
        print(
            f"  [{status}] {name}"
            + (f" ({detail})" if detail else "")
        )
        if not passed:
            raise _StepFailure(f"{name} — {detail}")

    def build_result() -> dict:
        duration = round(time.monotonic() - start, 1)
        all_passed = bool(steps) and all(
            s["passed"] for s in steps
        )
        return {
            "passed": all_passed,
            "test_email": test_email,
            "recording_url": recording_url,
            "screenshot_path": screenshot_path,
            "duration_s": duration,
            "preview_url": VERCEL_PREVIEW_URL,
            "steps": steps,
        }

    print(f"Canvas UI E2E Test — {VERCEL_PREVIEW_URL}")
    print(f"  Test email: {test_email}")
    print()

    try:
        # --- Step 1: Browserbase session ---
        session = create_browserbase_session()
        session_id = session["id"]
        connect_url = session["connectUrl"]
        recording_url = (
            f"https://www.browserbase.com/sessions/{session_id}"
        )
        step("Created Browserbase session", detail=session_id)

        with sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(connect_url)
            context = browser.contexts[0]
            page = (
                context.pages[0]
                if context.pages
                else context.new_page()
            )
            page.set_default_timeout(PAGE_TIMEOUT)

            # --- Step 2: Bypass Vercel protection ---
            bypass_url = (
                f"{VERCEL_PREVIEW_URL}/"
                f"?x-vercel-protection-bypass={BYPASS_TOKEN}"
                f"&x-vercel-set-bypass-cookie=samesitenone"
            )
            page.goto(bypass_url, wait_until="domcontentloaded")
            step("Bypassed Vercel protection")

            # --- Step 3: Login ---
            page.goto(
                f"{VERCEL_PREVIEW_URL}/login",
                wait_until="domcontentloaded",
            )
            step("Navigated to login page")

            # Submit magic link with retry
            login_url = f"{VERCEL_PREVIEW_URL}/login"
            magic_link_sent = False
            last_error = ""
            for attempt in range(1, 4):
                page.locator('input[type="email"]').fill(test_email)
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
                    el = page.locator("p.text-red-600, p.text-red-400")
                    last_error = (
                        el.text_content() if el.count() > 0 else str(exc)
                    )
                    if attempt < 3:
                        page.wait_for_timeout(10_000 * attempt)
                        page.goto(login_url, wait_until="domcontentloaded")

            step(
                "Submitted magic link",
                passed=magic_link_sent,
                detail=last_error if not magic_link_sent else test_email,
            )

            # --- Step 4: Get magic link email ---
            email_data = poll_resend_for_email(test_email)
            step("Received magic link email")

            html_body = email_data.get("html", "") or email_data.get(
                "text", ""
            )
            magic_link = extract_magic_link(html_body)
            page.goto(magic_link, wait_until="domcontentloaded")
            page.wait_for_url("**/", timeout=30000)
            step("Logged in via magic link", detail=page.url)

            # --- Step 5: Dashboard home loads ---
            # Wait for the page to hydrate and show real content
            page.wait_for_selector(
                "text=Welcome back", timeout=30000
            )
            body = page.inner_text("body")
            has_welcome = "Welcome back" in body
            has_views = "Views" in body or "VIEWS" in body
            step(
                "Dashboard home loaded",
                passed=has_welcome and has_views,
                detail=f"welcome={has_welcome} views={has_views}",
            )

            # --- Step 6: Click "Create New View" ---
            # Wait for view grid to finish loading (skeleton → cards)
            # The CreateViewCard renders after SurveyConfigsWorkflow
            # returns via Temporal, which can take 10-30s
            create_card = page.locator(
                "text=Create New View"
            ).first
            create_card.wait_for(state="visible", timeout=55000)
            create_card.click()
            step("Clicked Create New View")

            # --- Step 7: Fill modal and create ---
            # Wait for modal to be fully visible
            page.wait_for_selector(
                "text=New Dashboard", timeout=5000
            )

            # The name input has autoFocus — click it and type
            name_input = page.locator(
                'input[placeholder*="Q4 Revenue"]'
            )
            name_input.click()
            name_input.fill("")  # clear any existing value
            name_input.type("Meta Ads Overview", delay=50)

            desc_input = page.locator("textarea").first
            desc_input.click()
            desc_input.type(
                "Reach and impressions from Meta Ads campaign",
                delay=30,
            )

            # Verify the name was actually set
            name_value = name_input.input_value()
            step(
                "Filled modal form",
                passed=bool(name_value),
                detail=f"name='{name_value}'",
            )

            create_btn = page.locator(
                'button:has-text("Create View")'
            ).last
            create_btn.click()
            step("Clicked Create View")

            # --- Step 8: Wait for view creation ---
            # Modal starts workflow via POST /api/configure (returns
            # 202 + workflowId instantly), then polls
            # GET /api/workflow/{id} every 3s. On COMPLETED the modal
            # redirects to /v/{share_token}. Budget 90s for the full
            # async cycle.
            try:
                page.wait_for_url("**/v/**", timeout=90000)
            except Exception:
                # Capture the modal overlay text (appears at the end
                # of body DOM) — look for error/status messages.
                body_text = page.inner_text("body") or ""
                # Grab the LAST 500 chars — modal content is at the
                # end of the DOM, not the beginning.
                modal_tail = body_text[-500:].replace("\n", " ")
                # Also check for specific error/loading states
                has_error = any(
                    s in body_text
                    for s in [
                        "Failed",
                        "Error",
                        "did not complete",
                        "timed out",
                    ]
                )
                has_loading = "Creating" in body_text
                step(
                    "View creation completed",
                    passed=False,
                    detail=(
                        f"No redirect after 90s. "
                        f"error={has_error} loading={has_loading} "
                        f"url={page.url} "
                        f"tail={modal_tail}"
                    ),
                )
            share_token = page.url.split("/v/")[-1].split("?")[0]
            step(
                "Redirected to view dashboard",
                detail=f"share_token={share_token}",
            )

            # Wait for the view page to load
            import contextlib

            with contextlib.suppress(Exception):
                page.wait_for_selector(
                    "text=UNLOCK ALABAMA", timeout=50000
                )

            body = page.inner_text("body")
            has_title = "META ADS OVERVIEW" in body.upper()
            has_footer = "UNLOCK ALABAMA" in body
            has_no_panels = "NO PANELS" in body.upper()
            step(
                "View dashboard rendered",
                passed=has_title or has_footer,
                detail=(
                    f"title={has_title} "
                    f"footer={has_footer} "
                    f"no_panels={has_no_panels}"
                ),
            )

            # --- Step 9: Navigate back to home ---
            back_link = page.locator("text=Back to Views").first
            back_link.click()
            page.wait_for_url("**/", timeout=15000)
            step("Navigated back to home")

            # --- Step 10: Verify new view appears ---
            page.wait_for_selector(
                "text=Welcome back", timeout=30000
            )
            body = page.inner_text("body")
            has_new_view = "META ADS OVERVIEW" in body.upper()
            step(
                "New view card visible on home",
                passed=has_new_view,
                detail=f"found={has_new_view}",
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
    print(
        f"{'PASSED' if result['passed'] else 'FAILED'} "
        f"in {result['duration_s']}s"
    )
    print(f"Recording: {recording_url}")
    return result


if __name__ == "__main__":
    try:
        result = run_test()
    except Exception as exc:
        print(f"\nFATAL: {exc}", file=sys.stderr)
        sys.exit(1)

    output_path = os.environ.get(
        "RESULT_JSON", "/tmp/canvas-ui-result.json"
    )
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    sys.exit(0 if result["passed"] else 1)
