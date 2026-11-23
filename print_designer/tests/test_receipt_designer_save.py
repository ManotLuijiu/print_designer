"""Opt-in browser regression for Receipt saves and preview language changes.

Intercept layout and thumbnail writes so the saved print format remains intact.
"""

import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest


@pytest.mark.skipif(
    os.environ.get("PRINT_DESIGNER_E2E") != "1",
    reason="Requires opt-in authenticated browser access",
)
def test_receipt_footer_save_and_language_preserve_open_design():
    from dotenv import load_dotenv
    from playwright.sync_api import expect, sync_playwright

    load_dotenv(Path(__file__).parents[2] / ".env")
    site = os.environ["PRINT_DESIGNER_E2E_SITE_URL"].rstrip("/")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.environ.get(
                "PLAYWRIGHT_CHROMIUM_EXECUTABLE",
                "/home/frappe/frappe-bench/chromium/chrome-linux/headless_shell",
            ),
        )
        try:
            page = browser.new_page(viewport={"width": 1600, "height": 1000})
            errors = []
            saves = []
            layout_reads = []
            replay_saved_layout = False
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{site}/login")
            page.locator("#login_email:visible").fill(os.environ["SITE_USERNAME"])
            page.locator("#login_password:visible").fill(os.environ["SITE_PASSWORD"])
            page.locator(".btn-login:visible").click()
            page.wait_for_url("**/desk**", timeout=45000)

            def protect_print_format(route):
                request = route.request
                url = urlsplit(request.url)
                endpoint = url.path.rsplit("/", 1)[-1]
                if endpoint == "upload_file":
                    route.fulfill(
                        json={
                            "message": {
                                "doctype": "File",
                                "file_url": "/private/files/receipt-test.jpg",
                            }
                        }
                    )
                elif endpoint == "frappe.client.delete":
                    route.fulfill(json={"message": None})
                elif endpoint == "frappe.client.set_value":
                    fields = parse_qs(request.post_data or "").get("fieldname", [])
                    if any("print_designer_body" in field for field in fields):
                        saves.append(json.loads(fields[0]))
                    route.fulfill(json={"message": {}})
                else:
                    if endpoint == "frappe.client.get_value" and "print_designer_body" in url.query:
                        layout_reads.append(endpoint)
                        if replay_saved_layout:
                            response = route.fetch()
                            result = response.json()
                            for key in result["message"]:
                                if key in saves[-1]:
                                    result["message"][key] = saves[-1][key]
                            route.fulfill(response=response, json=result)
                            return
                    route.continue_()

            page.route("**/api/method/**", protect_print_format)
            page.goto(f"{site}/desk/print-designer/Receipt")
            canvas = page.locator(".main-container").first
            expect(canvas).to_be_visible(timeout=45000)
            with page.expect_console_message(
                predicate=lambda message: message.text.startswith(
                    "[Print Designer Save] thumbnail complete"
                ),
                timeout=30000,
            ):
                page.get_by_role("button", name="Save", exact=True).click()

            footer = (
                page.locator(".header-footer-overlay")
                .filter(has_text="Double Click to edit footer")
                .first
            )
            footer.evaluate("(el) => { el.style.display = 'flex'; }")
            footer.dblclick()
            with page.expect_console_message(
                predicate=lambda message: message.text.startswith(
                    "[Print Designer Save] layout saved"
                ),
            ):
                page.get_by_role("button", name="Save Footer", exact=True).click()
            expect(
                page.locator(".properties-panel").get_by_text("Page Size", exact=True)
            ).to_be_visible()
            assert len(saves) == 2

            width = (
                page.locator(".properties-panel label")
                .filter(has_text="Width")
                .locator("..")
                .locator("input")
                .first
            )
            original_width = canvas.evaluate("(el) => el.style.width")
            width.fill("222mm")
            width.press("Tab")
            assert canvas.evaluate("(el) => el.style.width") != original_width
            edited_width = canvas.evaluate("(el) => getComputedStyle(el).width")
            height = (
                page.locator(".properties-panel label")
                .filter(has_text="Height")
                .locator("..")
                .locator("input")
                .first
            )
            original_height = canvas.evaluate("(el) => el.style.height")
            height.fill("310mm")
            height.press("Tab")
            assert canvas.evaluate("(el) => el.style.height") != original_height
            edited_height = canvas.evaluate("(el) => getComputedStyle(el).height")
            reads_before_toggle = len(layout_reads)

            def set_preview_language(language):
                page.locator(".language-toggle-container .tool-icons").click()
                option = page.locator(".language-options label").filter(has_text=language)
                if option.locator("input").is_checked():
                    page.locator(".language-menu .close-btn").click()
                    return
                with page.expect_console_message(
                    predicate=lambda message: message.text.startswith(
                        "[PD] syncTableColumnHeaderLabels called"
                    ),
                ):
                    option.click()

            for language in ("ไทย", "English", "System Default"):
                set_preview_language(language)
                expect(canvas).to_have_css("width", edited_width)
                expect(canvas).to_have_css("height", edited_height)

            assert len(layout_reads) == reads_before_toggle

            set_preview_language("ไทย")
            heading = canvas.locator("table.printTable thead th").nth(4)
            heading.dblclick()
            custom_heading = "รับชำระจริง"
            page.locator("#column-name").fill(custom_heading)
            page.get_by_role("button", name="Confirm", exact=True).click()
            expect(heading).to_have_text(custom_heading)
            for language in ("English", "ไทย"):
                set_preview_language(language)
                expect(heading).to_have_text(custom_heading)
            with page.expect_console_message(
                predicate=lambda message: message.text.startswith(
                    "[Print Designer Save] layout saved"
                ),
            ):
                page.get_by_role("button", name="Save", exact=True).click()
            for field in ("print_designer_body", "print_designer_print_format"):
                assert f'"label":"{custom_heading}"' in saves[-1][field]
                assert '"labelIsCustom":true' in saves[-1][field]

            replay_saved_layout = True
            with page.expect_console_message(
                predicate=lambda message: message.text.startswith(
                    "[PD] syncTableColumnHeaderLabels called"
                ),
            ):
                page.reload()
            expect(heading).to_have_text(custom_heading)
            heading.dblclick()
            expect(page.locator("#column-name")).to_have_value(custom_heading)
            assert not errors, errors
        finally:
            browser.close()
