"""Opt-in browser regression for table selection and column resizing.

Run with PRINT_DESIGNER_E2E=1 and PRINT_DESIGNER_E2E_SITE_URL set to the
site to test. Credentials are loaded from the app's .env. No format is saved.
"""

import os
from pathlib import Path
from urllib.parse import quote

import pytest


@pytest.mark.skipif(
    os.environ.get("PRINT_DESIGNER_E2E") != "1",
    reason="Requires opt-in authenticated browser access",
)
def test_select_and_resize_table_column_without_collapsing():
    from dotenv import load_dotenv
    from playwright.sync_api import expect, sync_playwright

    load_dotenv(Path(__file__).parents[2] / ".env")
    site = os.environ["PRINT_DESIGNER_E2E_SITE_URL"].rstrip("/")
    print_format = os.environ.get(
        "PRINT_DESIGNER_E2E_FORMAT", "Quotation - Example"
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path=os.environ.get(
                "PLAYWRIGHT_CHROMIUM_EXECUTABLE",
                "/home/frappe/frappe-bench/chromium/chrome-linux/headless_shell",
            ),
        )
        try:
            page = browser.new_page(viewport={"width": 1600, "height": 1000})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{site}/login")
            page.locator("#login_email:visible").fill(os.environ["SITE_USERNAME"])
            page.locator("#login_password:visible").fill(os.environ["SITE_PASSWORD"])
            page.locator(".btn-login:visible").click()
            page.wait_for_url("**/desk**", timeout=45000)
            page.goto(f"{site}/desk/print-designer/{quote(print_format, safe='')}")
            table = page.locator(".table-container").first
            headers = table.locator("th")
            expect(headers.nth(1)).to_be_visible(timeout=45000)
            # Allow the document preview fetch and its table refresh to finish.
            page.wait_for_timeout(1500)
            def the_box(locator):
                """The bounding box of an element, which is always present here."""
                the_value = locator.bounding_box()
                assert the_value is not None
                return the_value

            initial_height = the_box(table)["height"]
            assert initial_height > 0
            labels = headers.all_text_contents()
            header = headers.nth(1)
            header.click()
            expect(header).to_have_class("current-column")
            page.wait_for_timeout(300)
            assert abs(the_box(table)["height"] - initial_height) < 1

            width_before = the_box(header)["width"]
            handle = the_box(header.locator(".resizer"))
            x, y = handle["x"] + 2, handle["y"] + 8
            page.mouse.move(x, y)
            page.mouse.down()
            page.mouse.move(x + 30, y, steps=8)
            page.mouse.up()
            expect(header).to_have_class("current-column")
            assert the_box(header)["width"] > width_before + 10
            assert headers.all_text_contents() == labels
            assert abs(the_box(table)["height"] - initial_height) < 1

            # Reopening properties must not apply the default Min Rows height.
            page.locator(".table-container").nth(1).locator("th").nth(1).click()
            header.click()
            expect(header).to_have_class("current-column")
            page.wait_for_timeout(300)
            assert abs(the_box(table)["height"] - initial_height) < 1
            assert not errors, errors
        finally:
            browser.close()
