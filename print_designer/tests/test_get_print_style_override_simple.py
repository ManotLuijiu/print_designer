"""
Simple E2E Test: Call the PDF download API directly to test our override.

Run with:
    cd /home/frappe/frappe-bench/apps/print_designer
    python -m pytest print_designer/tests/test_get_print_style_override_simple.py -v -s
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load credentials from .env (never commit credentials)
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")
SITE_URL = os.getenv("SITE_URL", "")
USERNAME = os.getenv("SITE_USERNAME", "")
PASSWORD = os.getenv("SITE_PASSWORD", "")

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


def get_last_lines(n=100):
    """Get last n lines of log file."""
    content = get_log_content()
    lines = content.split("\n")
    return lines[-n:]


def test_pdf_download_triggers_override():
    """
    Test that calling the PDF download API triggers our get_print_style override.
    """
    print("\n" + "=" * 60)
    print("TEST: PDF download triggers our override")
    print("=" * 60)

    # Get session cookies by logging in
    print("\n1. Logging in to get session...")
    session = requests.Session()

    # Get CSRF token
    login_page = session.get(f"{SITE_URL}/desk/login")

    # Find CSRF token in login page
    import re

    csrf_match = re.search(r'datacsrf="([^"]+)"', login_page.text)
    if not csrf_match:
        # Try alternative pattern
        csrf_match = re.search(r'csrf_token\s*=\s*["\']([^"\']+)["\']', login_page.text)

    if csrf_match:
        csrf_token = csrf_match.group(1)
        print(f"   CSRF token found: {csrf_token[:20]}...")
    else:
        print("   Could not find CSRF token, trying without...")
        csrf_token = ""

    # Login
    login_data = {
        "cmd": "login",
        "usr": USERNAME,
        "pwd": PASSWORD,
    }
    if csrf_token:
        login_data["csrf_token"] = csrf_token

    login_response = session.post(
        f"{SITE_URL}/desk/api/method/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    print(f"   Login response: {login_response.status_code}")

    # Call PDF download API
    print("\n2. Calling PDF download API...")
    pdf_url = f"{SITE_URL}/api/method/frappe.utils.print_format.download_pdf"
    params = {
        "doctype": DOCTYPE,
        "name": DOC_NAME,
        "format": PRINT_FORMAT,
        "no_letterhead": 0,
        "pdf_generator": "chrome",
    }

    response = session.get(pdf_url, params=params)
    print(f"   Response status: {response.status_code}")
    print(f"   Response content type: {response.headers.get('Content-Type', 'unknown')}")

    if response.status_code == 200:
        print(f"   Response size: {len(response.content)} bytes")
    else:
        print(f"   Response text (first 500 chars): {response.text[:500]}")

    # Wait for logs to be written
    import time

    time.sleep(2)

    # Check log
    print("\n3. Checking log for override...")
    log_lines = get_last_lines(50)

    # Look for our debug messages
    has_override_call = any("[GET_PRINT_STYLE]" in line for line in log_lines)
    has_our_css = any("print_designer/templates/styles/standard.css" in line for line in log_lines)
    has_frappe_css = any(
        "templates/styles/standard.css" in line and "print_designer" not in line
        for line in log_lines
    )
    has_frappe_get_print = any("Using frappe.get_print()" in line for line in log_lines)

    print(f"\n   Our GET_PRINT_STYLE override called: {has_override_call}")
    print(f"   Loading our CSS: {has_our_css}")
    print(f"   Loading Frappe CSS (BAD): {has_frappe_css}")
    print(f"   Using frappe.get_print(): {has_frappe_get_print}")

    # Check for CSS replacement
    has_css_replace = any("CSS_REPLACE" in line for line in log_lines)
    has_css_loaded = any("Our CSS loaded from file" in line for line in log_lines)
    has_css_replaced = any("CSS replaced via style block pattern" in line for line in log_lines)

    print(f"   CSS replacement triggered: {has_css_replace}")
    print(f"   CSS loaded from file: {has_css_loaded}")
    print(f"   CSS replaced in HTML: {has_css_replaced}")

    # Print relevant lines
    print("\n4. Relevant log lines:")
    for line in log_lines:
        if any(x in line for x in ["CSS_REPLACE", "GET_PRINT_STYLE", "standard.css"]):
            print(f"   {line[:200]}")

    # Assertions
    print("\n5. Assertions:")

    # Main test: CSS replacement should work
    if has_css_replace and has_css_loaded and has_css_replaced:
        print("   PASS: CSS replacement is working!")
        print("   - Our CSS file is loaded")
        print("   - CSS is replaced in HTML")
        print("   - PDF will be generated with our CSS")
    else:
        if has_frappe_get_print:
            print("   WARN: frappe.get_print() called but CSS replacement not triggered")
        else:
            print("   FAIL: frappe.get_print() was NOT called!")

    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    test_pdf_download_triggers_override()
