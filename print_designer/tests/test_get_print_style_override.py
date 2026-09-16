"""
E2E Test: Verify get_print_style override uses our standard.css

Tests that when PDF is generated, our override in:
    print_designer/www/printview.py
is called instead of Frappe's original:
    frappe/www/printview.py

This test:
1. Calls the PDF download API
2. Checks the log file for our debug messages
3. Verifies the CSS loaded is from our file

Run with:
    cd /home/frappe/frappe-bench/apps/print_designer
    python -m pytest print_designer/tests/test_get_print_style_override.py -v -s
"""

import os
import time
from pathlib import Path

import pytest

# Load credentials from .env
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

SITE_URL = os.getenv("SITE_URL", "")
USERNAME = os.getenv("SITE_USERNAME", "")
PASSWORD = os.getenv("SITE_PASSWORD", "")

# Test data
DOCTYPE = "Stock Entry"
DOC_NAME = "MAT-STE-2026-00001"
PRINT_FORMAT = "DGS Stock Transfer - Form 4"

# Log file to check
LOG_FILE = "/home/frappe/frappe-bench/sites/digisoft-erp.bunchee.online/logs/print_designer/print_designer.log"


def get_log_content():
    """Read the print_designer log file."""
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def clear_log():
    """Clear the log file before test."""
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("")
    except Exception:
        pass


def test_get_print_style_override_is_called():
    """
    Test that our get_print_style_with_our_css override is called.

    Steps:
    1. Clear log
    2. Navigate to print preview (triggers the override)
    3. Check log for our debug messages
    """
    clear_log()
    print("\n" + "=" * 60)
    print("TEST: get_print_style override is called")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path="/home/frappe/frappe-bench/chromium/chrome-linux/headless_shell",
        )
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        # Login
        print("\n1. Logging in...")
        page.goto(f"{SITE_URL}/desk/login")
        page.fill("#login_email", USERNAME or "")
        page.fill("#login_password", PASSWORD or "")
        page.click(".btn-login")
        page.wait_for_url(f"{SITE_URL}/desk/**", timeout=30000)
        time.sleep(3)

        # Navigate to print preview
        print("\n2. Navigating to print preview...")
        url = f"{SITE_URL}/desk/print/{DOCTYPE}%2F{DOC_NAME}?format={PRINT_FORMAT}"
        print(f"   URL: {url}")
        page.goto(url)
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(5)

        # Click PDF download button to trigger the API call
        print("\n3. Clicking PDF download button...")
        try:
            # Try to find and click the PDF download button
            page.click(
                "button:has-text('PDF'), a:has-text('PDF'), [data-action='pdf']", timeout=5000
            )
            time.sleep(3)
            print("   PDF download triggered")
        except Exception as e:
            print(f"   Could not click PDF button: {e}")
            print("   Trying direct API call instead...")
            # Direct API call
            api_url = f"{SITE_URL}/api/method/frappe.utils.print_format.download_pdf?doctype={DOCTYPE}&name={DOC_NAME}&format={PRINT_FORMAT}&no_letterhead=0&pdf_generator=chrome"
            page.goto(api_url)
            time.sleep(3)
            print(f"   API call triggered: {api_url[:100]}...")

        browser.close()

    # Wait for logs to be written
    time.sleep(2)

    # Check log for our override
    print("\n3. Checking log file for override...")
    log_content = get_log_content()

    # Look for our debug messages
    has_override_call = "[GET_PRINT_STYLE] ===== CALLED OUR OVERRIDE =====" in log_content
    has_our_css_path = (
        "[GET_PRINT_STYLE] Loading CSS from: print_designer/templates/styles/standard.css"
        in log_content
    )
    has_frappe_path = (
        "templates/styles/standard.css" in log_content and "print_designer" not in log_content
    )

    print(f"\n   Our override was called: {has_override_call}")
    print(f"   Loading our CSS path: {has_our_css_path}")
    print(f"   Loading Frappe CSS path (BAD): {has_frappe_path}")

    # Print relevant log lines
    print("\n4. Relevant log lines:")
    for line in log_content.split("\n"):
        if "GET_PRINT_STYLE" in line:
            print(f"   {line}")

    # Assertions
    print("\n5. Assertions:")
    assert has_override_call, "FAIL: Our get_print_style override was NOT called!"
    print("   PASS: Our override was called")

    assert has_our_css_path, "FAIL: CSS was NOT loaded from our file!"
    print("   PASS: CSS loaded from our print_designer/templates/styles/standard.css")

    # This should NOT happen if our override is working
    if has_frappe_path and not has_our_css_path:
        pytest.fail("FAIL: Frappe's CSS was loaded instead of ours!")
    else:
        print("   PASS: Not using Frappe's CSS path")

    print("\n" + "=" * 60)
    print("TEST PASSED: Our get_print_style override is working!")
    print("=" * 60)


def test_pdf_uses_our_css():
    """
    Test that the PDF download uses our CSS.

    Steps:
    1. Clear debugging folder
    2. Download PDF (triggers signature_stamp.py with our CSS)
    3. Check if our CSS is in the generated HTML
    """
    from print_designer.utils.signature_stamp import download_pdf_with_signature_stamp

    clear_log()
    print("\n" + "=" * 60)
    print("TEST: PDF uses our CSS")
    print("=" * 60)

    # Import and check the override is registered

    print("\n1. Calling PDF download API...")

    # This will call our get_print_style_with_our_css via the override
    try:
        result = download_pdf_with_signature_stamp(
            doctype=DOCTYPE,
            name=DOC_NAME,
            format=PRINT_FORMAT,
            no_letterhead=0,
            letterhead=None,
        )
        print(f"   PDF generated, length: {len(result) if result else 0}")
    except Exception as e:
        print(f"   Error: {e}")
        # Continue to check logs

    # Wait for logs
    time.sleep(2)

    # Check log
    print("\n2. Checking log for CSS loading...")
    log_content = get_log_content()

    # Look for our CSS being loaded
    has_our_css = "print_designer/templates/styles/standard.css" in log_content
    has_css_length = "CSS loaded, length=" in log_content

    print(f"   Our CSS path in log: {has_our_css}")
    print(f"   CSS was loaded: {has_css_length}")

    # Print relevant lines
    print("\n3. Relevant log lines:")
    for line in log_content.split("\n"):
        if "GET_PRINT_STYLE" in line or "standard.css" in line:
            print(f"   {line}")

    # Assertions
    print("\n4. Assertions:")
    assert has_our_css, "FAIL: Our CSS file was NOT loaded!"
    print("   PASS: Our standard.css was loaded")

    print("\n" + "=" * 60)
    print("TEST PASSED: PDF uses our CSS!")
    print("=" * 60)


if __name__ == "__main__":
    # Run manually
    test_get_print_style_override_is_called()
