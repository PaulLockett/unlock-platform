"""
Auth E2E Integration Test — Magic Link Flow

Exercises the complete Supabase magic link authentication flow end-to-end:

  1. Create a Browserbase cloud browser session (recorded)
  2. Navigate to the Vercel preview /login page
  3. Submit a magic link request with a unique test email
  4. Poll the Resend inbound API until the magic link email arrives
  5. Extract the magic link URL from the email HTML
  6. Navigate to the magic link (Supabase verifies → redirects to /auth/callback)
  7. Verify logged-in state (user email displayed or "Sign out" button present)

Outputs JSON with pass/fail, Browserbase recording URL, step details, and duration.

Usage:
    VERCEL_PREVIEW_URL=https://... \\
    BROWSERBASE_API_KEY=... \\
    BROWSERBASE_PROJECT_ID=... \\
    RESEND_API_KEY=... \\
    VERCEL_PROTECTION_BYPASS_TOKEN=... \\
    python scripts/auth_e2e_test.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from urllib.parse import urlparse

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

RESEND_DOMAIN = os.environ.get(
    "RESEND_TESTING_RECIPIENT_DOMAIN", "hpidome.resend.app"
)

# Polling config
EMAIL_POLL_INTERVAL = 3  # seconds between Resend API checks
EMAIL_POLL_TIMEOUT = 120  # max seconds to wait for the email
PAGE_LOAD_TIMEOUT = 15_000  # ms — Playwright page load timeout


class _StepFailure(Exception):
    """Raised when a test step fails. Caught internally to produce result JSON."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def create_browserbase_session() -> dict:
    """Create a Browserbase cloud browser session via REST API."""
    resp = httpx.post(
        "https://api.browserbase.com/v1/sessions",
        headers={
            "X-BB-API-Key": BROWSERBASE_API_KEY,
            "Content-Type": "application/json",
        },
        json={"projectId": BROWSERBASE_PROJECT_ID},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def poll_resend_for_email(
    recipient: str, *, timeout: float = EMAIL_POLL_TIMEOUT
) -> dict:
    """Poll Resend's sending API until the magic link email for *recipient* appears.

    Supabase sends magic link emails through Resend SMTP, so they appear in the
    outbound/sending API (GET /emails), not the inbound/receiving API.  We poll
    the list endpoint until we find a match, then fetch the full email (with HTML
    body) via GET /emails/{id}.
    """
    deadline = time.monotonic() + timeout
    headers = {"Authorization": f"Bearer {RESEND_API_KEY}"}

    while time.monotonic() < deadline:
        resp = httpx.get(
            "https://api.resend.com/emails",
            headers=headers,
            params={"limit": 50},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        for email in data.get("data", []):
            recipients = email.get("to", [])
            if recipient in recipients:
                # Fetch full email to get the HTML body
                detail = httpx.get(
                    f"https://api.resend.com/emails/{email['id']}",
                    headers=headers,
                    timeout=15,
                )
                detail.raise_for_status()
                return detail.json()

        time.sleep(EMAIL_POLL_INTERVAL)

    raise TimeoutError(
        f"Magic link email for {recipient} not received within {timeout}s"
    )


def extract_magic_link(html: str) -> str:
    """Extract the magic link URL from the email HTML.

    Supabase magic link emails contain a confirmation URL that looks like:
      https://<project>.supabase.co/auth/v1/verify?token=...&type=magiclink&redirect_to=...
    """
    # Match href containing /auth/v1/verify or type=magiclink
    pattern = r'href=["\']([^"\']*(?:/auth/v1/verify|type=magiclink)[^"\']*)["\']'
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        return match.group(1)

    # Fallback: look for any long URL containing "token=" in the body
    pattern_fallback = r'(https?://[^\s"\'<>]+token=[^\s"\'<>]+)'
    match = re.search(pattern_fallback, html)
    if match:
        return match.group(1)

    raise ValueError("Could not extract magic link from email HTML")


# ---------------------------------------------------------------------------
# Main test
# ---------------------------------------------------------------------------


def run_test() -> dict:
    """Run the full E2E auth test. Returns a result dict (even on failure)."""
    test_email = f"auth-e2e-{int(time.time())}@{RESEND_DOMAIN}"
    steps: list[dict] = []
    start = time.monotonic()
    recording_url = ""
    screenshot_path = os.environ.get(
        "SCREENSHOT_PATH", "/tmp/auth-e2e-screenshot.png"
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

    print(f"Auth E2E Test — {VERCEL_PREVIEW_URL}")
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

            # --- Step 2: Bypass Vercel deployment protection ---
            # Cookie-based bypass doesn't work from third-party browsers
            # (Browserbase) due to SameSite restrictions. Instead, hit
            # any page with the bypass query params — Vercel sets the
            # cookie on the response, which persists for subsequent navs.
            bypass_url = (
                f"{VERCEL_PREVIEW_URL}/"
                f"?x-vercel-protection-bypass={BYPASS_TOKEN}"
                f"&x-vercel-set-bypass-cookie=samesitenone"
            )
            page.goto(bypass_url, wait_until="networkidle")
            # Verify we didn't get redirected to Vercel login
            if "vercel.com/login" in page.url:
                step(
                    "Bypassed Vercel deployment protection",
                    passed=False,
                    detail=f"Still redirected to Vercel login: {page.url}",
                )
            step("Bypassed Vercel deployment protection")

            # --- Step 3: Navigate to /login ---
            login_url = f"{VERCEL_PREVIEW_URL}/login"
            page.goto(login_url, wait_until="networkidle")
            step(
                "Navigated to /login",
                passed=page.url.rstrip("/").endswith("/login"),
                detail=page.url,
            )

            # --- Step 4: Fill in email and submit ---
            email_input = page.locator('input[type="email"]')
            email_input.fill(test_email)
            page.locator('button[type="submit"]').click()

            # Wait for the "Check your email" confirmation text
            try:
                page.wait_for_selector("text=Check your email", timeout=10_000)
                step("Submitted magic link request", detail=test_email)
            except _StepFailure:
                raise
            except Exception as exc:
                error_el = page.locator("p.text-red-600, p.text-red-400")
                error_text = (
                    error_el.text_content() if error_el.count() > 0 else str(exc)
                )
                step(
                    "Submitted magic link request",
                    passed=False,
                    detail=f"Error: {error_text}",
                )

            # --- Step 5: Poll Resend for the magic link email ---
            print(f"  Polling Resend for email to {test_email}...")
            email_start = time.monotonic()
            try:
                email_data = poll_resend_for_email(test_email)
            except (TimeoutError, httpx.HTTPStatusError) as exc:
                step("Received magic link email", passed=False, detail=str(exc))
            email_wait = round(time.monotonic() - email_start, 1)
            step("Received magic link email", detail=f"{email_wait}s")

            # --- Step 6: Extract magic link from email ---
            html_body = email_data.get("html", "") or email_data.get("text", "")
            try:
                magic_link = extract_magic_link(html_body)
            except ValueError as exc:
                step("Extracted magic link URL", passed=False, detail=str(exc))
            step("Extracted magic link URL", detail=magic_link[:80] + "...")

            # --- Step 7: Navigate to magic link ---
            page.goto(magic_link, wait_until="networkidle")
            step("Navigated to magic link", detail=page.url)

            # --- Step 8: Verify logged-in state ---
            # After the magic link flow, we should land on "/" and see either
            # the test email or a "Sign out" button — proving the session was
            # created.
            page.wait_for_load_state("networkidle")
            body_text = page.text_content("body") or ""
            logged_in = (
                test_email in body_text
                or "sign out" in body_text.lower()
                or "log out" in body_text.lower()
            )

            if "/login" in page.url:
                step(
                    "Verified logged-in state",
                    passed=False,
                    detail=(
                        "Redirected back to /login — callback may have failed. "
                        f"URL: {page.url}"
                    ),
                )
            else:
                step(
                    "Verified logged-in state",
                    passed=logged_in,
                    detail=f"URL: {page.url}, found_indicators: {logged_in}",
                )

            # --- Screenshot ---
            page.screenshot(path=screenshot_path, full_page=True)
            browser.close()

    except _StepFailure:
        pass  # Already recorded in steps — fall through to build result
    except Exception as exc:
        steps.append(
            {"name": "Unexpected error", "passed": False,
             "detail": str(exc), "elapsed_s": round(time.monotonic() - start, 1)}
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

    # Write result JSON for CI to parse
    output_path = os.environ.get("RESULT_JSON", "/tmp/auth-e2e-result.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    sys.exit(0 if result["passed"] else 1)
