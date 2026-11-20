"""Opt-in browser regression for the Invoice Schedule milestone dropdown.

Run with PRINT_DESIGNER_E2E=1 and PRINT_DESIGNER_E2E_SITE_URL set to the
site to test. Credentials are loaded from the app's .env. The Sales Order is
only read in the browser, it is never saved and no invoice is created.
"""

import os
from pathlib import Path

import pytest

MILESTONE_LOOKUP = "print_designer.custom.invoice_schedule.search_milestone_payment_terms"


@pytest.mark.skipif(
    os.environ.get("PRINT_DESIGNER_E2E") != "1",
    reason="Requires opt-in authenticated browser access",
)
def test_the_milestone_field_suggests_payment_terms_and_keeps_free_text():
    from dotenv import load_dotenv
    from playwright.sync_api import expect, sync_playwright

    load_dotenv(Path(__file__).parents[2] / ".env")
    site = os.environ["PRINT_DESIGNER_E2E_SITE_URL"].rstrip("/")
    sales_order = os.environ.get("PRINT_DESIGNER_E2E_SALES_ORDER", "SO-69-08-00001")

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
            requests = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("request", lambda request: requests.append(request.url))

            page.goto(f"{site}/desk/login")
            page.locator("#login_email:visible").fill(os.environ["SITE_USERNAME"])
            page.locator("#login_password:visible").fill(os.environ["SITE_PASSWORD"])
            page.locator(".btn-login:visible").click()
            page.wait_for_url("**/desk**", timeout=45000)

            page.goto(f"{site}/desk/form/Sales%20Order/{sales_order}")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)

            # The Invoice Schedule lives in the Terms tab, the grid is not
            # rendered while the tab is closed.
            page.locator(".nav-link", has_text="Terms").first.click()
            page.wait_for_timeout(1500)

            state = page.evaluate(
                """() => {
					const cur = window.cur_frm;
					const grid = cur.fields_dict.pd_custom_invoice_schedule?.grid;
					const df = grid?.docfields?.find((d) => d.fieldname === "payment_term");
					return {
						fieldtype: df?.fieldtype,
						ignore_validation: df?.ignore_validation,
						get_query: grid?.get_field("payment_term")?.get_query?.query,
						scoped: !!cur.cscript?.payment_term?.pd_milestone_scoped,
					};
				}"""
            )
            assert state["fieldtype"] == "Autocomplete", state
            assert state["ignore_validation"] == 1, state
            assert state["get_query"] == MILESTONE_LOOKUP, state
            assert state["scoped"], state

            terms = page.evaluate(
                """async (method) => {
					const response = await frappe.call({method: method, args: {txt: ""}});
					return response.message || [];
				}""",
                MILESTONE_LOOKUP,
            )
            if not terms:
                pytest.skip("the site has no Payment Term to suggest")

            cells = page.locator('.rows [data-fieldname="payment_term"]')
            expect(cells.last).to_be_visible(timeout=20000)
            cells.last.click()
            page.wait_for_timeout(1000)

            editor = page.locator('.rows [data-fieldname="payment_term"] .field-area input')
            expect(editor).to_be_visible(timeout=20000)

            # an existing Payment Term is suggested
            editor.fill(terms[0]["value"])
            page.wait_for_timeout(2500)
            suggestions = page.evaluate(
                """() => {
					const open = Array.from(document.querySelectorAll(".awesomplete ul")).filter(
						(ul) => ul.offsetParent !== null
					);
					return open.flatMap((ul) =>
						Array.from(ul.querySelectorAll("li")).map((li) => li.innerText.trim())
					);
				}"""
            )
            assert terms[0]["value"] in suggestions, suggestions

            # a milestone name that is not a Payment Term stays free text
            editor.fill("Milestone without a payment term")
            page.wait_for_timeout(2000)
            assert editor.input_value() == "Milestone without a payment term"

            # the legacy ERPNext payment term handler must not run for the
            # invoice schedule
            legacy = [
                url for url in requests if "payment_term" in url and MILESTONE_LOOKUP not in url
            ]
            assert not legacy, legacy
            assert not errors, errors
        finally:
            browser.close()
