"""Opt-in browser coverage for whole-table styling and presets on Receipt."""

import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest


def prepare_border_fixture(elements):
    for element in elements:
        if (
            element.get("type") == "table"
            and (element.get("table") or {}).get("fieldname") == "references"
        ):
            # The saved style can have individual sides before its shorthand.
            element["headerStyle"] = {
                "borderLeftStyle": "solid",
                "borderRightStyle": "solid",
                **element["headerStyle"],
                "backgroundColor": "#cdcbf2",
                "borderColor": "#000000",
                "borderStyle": "solid",
            }
            element["headerStyle"].pop("borderTopColor", None)
            for column in element["columns"]:
                column["applyStyleToHeader"] = True
                column.pop("headerBorderStyle", None)
                column.pop("linkedHeaderBorderStyle", None)
                column["style"]["borderColor"] = "#B4CD29"
                column["style"]["backgroundColor"] = ""
                column["style"].pop("borderTopColor", None)
        prepare_border_fixture(element.get("childrens") or [])


@pytest.mark.skipif(
    os.environ.get("PRINT_DESIGNER_E2E") != "1",
    reason="Requires opt-in authenticated browser access",
)
def test_receipt_bulk_border_controls_and_presets():
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
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{site}/login")
            page.locator("#login_email:visible").fill(os.environ["SITE_USERNAME"])
            page.locator("#login_password:visible").fill(os.environ["SITE_PASSWORD"])
            page.locator(".btn-login:visible").click()
            page.wait_for_url("**/desk**", timeout=45000)

            def intercept_writes(route):
                method = urlsplit(route.request.url).path.rsplit("/", 1)[-1]
                if method == "upload_file":
                    route.fulfill(
                        json={"message": {"doctype": "File", "file_url": "/private/files/test.jpg"}}
                    )
                elif method in ("frappe.client.set_value", "frappe.client.delete"):
                    route.fulfill(json={"message": {}})
                elif (
                    method == "frappe.client.get_value"
                    and "print_designer_body" in route.request.url
                ):
                    response = route.fetch()
                    result = response.json()
                    body = json.loads(result["message"]["print_designer_body"])
                    prepare_border_fixture(body)
                    result["message"]["print_designer_body"] = json.dumps(body)
                    route.fulfill(response=response, json=result)
                else:
                    route.continue_()

            page.route("**/api/method/**", intercept_writes)
            page.goto(f"{site}/desk/print-designer/Receipt")

            table = page.locator(".table-container table.printTable").first
            rows = table.locator("tbody tr:not(.reserved-row)")
            cells = rows.first.locator("td")
            header = table.locator("th")
            expect(cells.first).to_be_visible(timeout=45000)
            page.wait_for_timeout(1500)
            panel = page.locator(".properties-panel")
            cells.first.click(position={"x": 3, "y": 4})
            mode = panel.get_by_text("Style Mode :", exact=True).locator("..").locator("select")
            expect(mode).to_have_value("main")
            grid = panel.get_by_role("group", name="Table grid")
            expect(grid).to_be_visible()
            grid.get_by_role("button", name="Full Grid", exact=True).click()

            headers_before = [
                cell.evaluate("(el) => getComputedStyle(el).borderTopColor")
                for cell in header.all()
            ]
            saved_header_fill = table.evaluate("""table => {
                const style = table.closest('.table-container').piniaElementRef.headerStyle;
                const sample = document.createElement('span');
                sample.style.backgroundColor = style.backgroundColor;
                return sample.style.backgroundColor;
            }""")
            for cell in header.all():
                expect(cell).to_have_css("background-color", saved_header_fill)
            alignment_before = [
                cell.evaluate("(el) => getComputedStyle(el).textAlign") for cell in cells.all()
            ]
            color = panel.get_by_text("Border Color", exact=True).locator("..").locator("input")
            color.fill("#4F9DD9")
            color.press("Tab")
            dashed = panel.locator('svg:has(use[href="#borderStyleDashed"])')
            dashed.click()
            for cell in cells.all():
                expect(cell).to_have_css("border-top-color", "rgb(79, 157, 217)")
                expect(cell).to_have_css("border-bottom-style", "dashed")
            assert [
                cell.evaluate("(el) => getComputedStyle(el).borderTopColor")
                for cell in header.all()
            ] == headers_before
            assert [
                cell.evaluate("(el) => getComputedStyle(el).textAlign") for cell in cells.all()
            ] == alignment_before

            header.first.click(position={"x": 8, "y": 5})
            apply_header = (
                panel.get_by_text("Apply Style to Header", exact=True)
                .locator("..")
                .locator("select")
            )
            expect(apply_header).to_have_value("Yes")
            apply_header.select_option("No")
            expect(header.first).to_have_css("border-top-color", "rgb(0, 0, 0)")
            expect(header.first).to_have_css("background-color", saved_header_fill)
            expect(cells.first).to_have_css("border-top-color", "rgb(79, 157, 217)")
            header.nth(1).click(position={"x": 8, "y": 5})
            header.first.click(position={"x": 8, "y": 5})
            expect(apply_header).to_have_value("No")
            apply_header.select_option("Yes")
            expect(header.first).to_have_css("border-top-color", "rgb(79, 157, 217)")

            mode.select_option("header")
            color.fill("#CB2929")
            color.press("Tab")
            for cell in header.all():
                expect(cell).to_have_css("border-top-color", "rgb(203, 41, 41)")
            expect(cells.first).to_have_css("border-top-color", "rgb(79, 157, 217)")

            mode.select_option("main")
            for preset, first_left, inside_left, row_bottom, last_bottom in (
                ("No Grid", "none", "none", "none", "none"),
                ("Full Grid", "dashed", "dashed", "dashed", "dashed"),
                ("Outline Only", "dashed", "none", "none", "dashed"),
                ("Horizontal", "none", "none", "dashed", "dashed"),
            ):
                button = grid.get_by_role("button", name=preset, exact=True)
                button.click()
                expect(button).to_have_attribute("aria-pressed", "true")
                expect(cells.first).to_have_css("border-left-style", first_left)
                expect(cells.nth(1)).to_have_css("border-left-style", inside_left)
                expect(cells.first).to_have_css("border-bottom-style", row_bottom)
                expect(table.locator("tbody tr").last.locator("td").first).to_have_css(
                    "border-bottom-style", last_bottom
                )
                if preset in ("Horizontal", "No Grid"):
                    for cell in header.all():
                        expect(cell).to_have_css("border-left-style", "none")
                        expect(cell).to_have_css("border-right-style", "none")
                        if preset == "Horizontal":
                            expect(cell).not_to_have_css("border-top-width", "0px")
                            expect(cell).not_to_have_css("border-bottom-width", "0px")
            panel.get_by_role("button", name="Custom", exact=True).click()
            expect(table).not_to_have_attribute("data-pd-border-preset", "horizontal")

            grid.get_by_role("button", name="Outline Only", exact=True).click()
            with page.expect_request(
                lambda request: request.url.endswith("frappe.client.set_value")
            ) as pending:
                panel.get_by_role("button", name="Save", exact=True).click()
            fields = json.loads(parse_qs(pending.value.post_data)["fieldname"][0])
            for field in ("print_designer_body", "print_designer_print_format"):
                assert '"borderPreset":"outline"' in fields[field]
                assert '"headerBorderStyle"' in fields[field]
                assert '"linkedHeaderBorderStyle"' in fields[field]
                assert '"selectedColumn":null' in fields[field]
            assert not errors, errors
        finally:
            browser.close()
