"""Browser checks of the actual print-view and table Jinja templates."""

import os
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

APP = Path(__file__).parents[1]
MACROS = APP / "print_designer/page/print_designer/jinja/macros"


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        instance = playwright.chromium.launch(
            headless=True,
            executable_path=os.environ.get(
                "PLAYWRIGHT_CHROMIUM_EXECUTABLE",
                "/home/frappe/frappe-bench/chromium/chrome-linux/headless_shell",
            ),
        )
        yield instance
        instance.close()


@pytest.mark.parametrize("designer,copies", [(True, 1), (True, 2), (False, 1)])
def test_footer_visibility_in_screen_and_print(browser, designer, copies):
    footer = '<div id="footer-html">Signature footer</div>'
    body = "".join(
        f'<div class="pd-preview-copy"><div id="__print_designer">{footer}</div></div>'
        if designer else footer
        for _ in range(copies)
    )
    template = Environment().from_string((APP / "www/printview.html").read_text())
    html = template.render(
        body=body,
        lang="th",
        layout_direction="ltr",
        title="Footer regression",
        print_style=".visible-pdf{display:none}@media print{.hidden-pdf{display:none!important}.visible-pdf{display:block!important}}",
        include_style=lambda _: "",
        _=lambda value: value,
        trigger_print=False,
    )
    page = browser.new_page()
    try:
        page.set_content(html)
        for media in ("screen", "print"):
            page.emulate_media(media=media)
            footers = page.locator('[id="footer-html"]')
            assert footers.count() == copies
            for index in range(copies):
                assert footers.nth(index).is_visible() == (designer or media == "screen")
    finally:
        page.close()


@pytest.mark.parametrize("height_mode", ["auto", "fixed", "auto-min-height"])
@pytest.mark.parametrize("row_count", [1, 15])
def test_table_height_mode_with_rows(browser, height_mode, row_count):
    env = Environment(loader=FileSystemLoader(MACROS))
    template = env.from_string(
        '{% from "table.html" import table with context %}{{ table(element, {}, "fixed") }}'
    )
    element = {
        "heightType": height_mode, "height": 220, "width": 600,
        "startX": 0, "startY": 0, "classes": [], "minRows": 0,
        "table": {"fieldname": "items"}, "headerStyle": {}, "style": {},
        "altStyle": {}, "columns": [{"label": "Item", "dynamicContent": [{}]}],
    }
    html = template.render(
        element=element,
        settings={"schema_version": "1.3.0"},
        doc={"items": [{"idx": index + 1} for index in range(row_count)]},
        convert_css=lambda _: "padding: 4px;",
        span_tag=lambda *args: "Single item",
        _=lambda value: value,
    )
    page = browser.new_page()
    try:
        page.set_content(html)
        height = page.locator("table").bounding_box()["height"]
        if row_count > 1:
            assert height > 220
        elif height_mode == "auto":
            assert height < 100
        else:
            assert height >= 219
    finally:
        page.close()


@pytest.mark.parametrize("copies", [1, 2])
def test_browser_print_preserves_footer_bottom_and_whitespace(browser, copies):
    from io import BytesIO

    from pypdf import PdfReader

    env = Environment(loader=FileSystemLoader(MACROS))
    styles = env.from_string(
        '{% from "styles.html" import render_styles with context %}{{ render_styles(settings) }}'
    ).render(
        settings={"page": {
            "width": 793.701, "height": 1122.52,
            "headerHeightWithMargin": 340.157,
            "footerHeightWithMargin": 188.976,
            "marginTop": 0, "marginBottom": 0, "marginLeft": 0, "marginRight": 0,
        }},
        convert_uom=lambda number, to_uom: f"{number if to_uom == 'px' else number * 25.4 / 96}{to_uom}",
    )
    body = styles + "".join(
        f'<div class="pd-preview-copy" style="break-before: {"page" if index else "auto"}">'
        '<div id="__print_designer"><div id="header-html">Header</div>'
        '<div id="body-content">Short body leaves whitespace</div>'
        '<div id="footer-html">Signature footer</div></div></div>'
        for index in range(copies)
    )
    template = Environment().from_string((APP / "www/printview.html").read_text())
    page = browser.new_page()
    try:
        html = template.render(
            body=body, lang="th", layout_direction="ltr", title="Footer placement",
            include_style=lambda _: "", _=lambda value: value, trigger_print=False,
        )
        page.route("https://printview.test/printview", lambda route: route.fulfill(
            content_type="text/html", body=html,
        ))
        page.goto("https://printview.test/printview")
        for media in ("screen", "print"):
            page.emulate_media(media=media)
            for index in range(copies):
                root = page.locator('[id="__print_designer"]').nth(index)
                footer = root.locator('[id="footer-html"]')
                root_box, footer_box = root.bounding_box(), footer.bounding_box()
                assert abs(root_box["height"] - 1122.52) < 1
                assert abs(footer_box["y"] - root_box["y"] - 933.544) < 1
                assert abs(footer_box["y"] + footer_box["height"] - root_box["y"] - root_box["height"]) < 1
        pdf = PdfReader(BytesIO(page.pdf(prefer_css_page_size=True)))
        assert len(pdf.pages) == copies
        for pdf_page in pdf.pages:
            assert "Signature footer" in pdf_page.extract_text()
        import pymupdf

        with pymupdf.open(stream=page.pdf(prefer_css_page_size=True), filetype="pdf") as printed:
            for printed_page in printed:
                signatures = printed_page.search_for("Signature footer")
                assert signatures and signatures[0].y0 > printed_page.rect.height * 0.8
    finally:
        page.close()


@pytest.mark.parametrize("show_page_number", [True, False])
def test_format_css_does_not_add_an_unconfigured_pdf_page_counter(browser, show_page_number):
    """Server PDF rendering must not get an extra CSS margin-box counter."""
    import re
    from io import BytesIO

    from pypdf import PdfReader

    styles = Environment(loader=FileSystemLoader(MACROS)).from_string(
        '{% from "styles.html" import render_styles with context %}{{ render_styles(settings) }}'
    ).render(
        settings={"page": {
            "width": 793.701, "height": 1122.52,
            "headerHeightWithMargin": 100, "footerHeightWithMargin": 100,
            "marginTop": 0, "marginBottom": 0, "marginLeft": 0, "marginRight": 0,
        }},
        convert_uom=lambda number, to_uom: f"{number if to_uom == 'px' else number * 25.4 / 96}{to_uom}",
    )
    page = browser.new_page()
    try:
        # The configured app number is separate from CSS page-margin content.
        configured_number = '<div class="pd-page-number">Page 1 / 1</div>' if show_page_number else "Body"
        page.set_content(styles + configured_number)
        pdf = PdfReader(BytesIO(page.pdf(format="A4", prefer_css_page_size=True)))
        assert len(pdf.pages) == 1
        text = pdf.pages[0].extract_text()
        assert len(re.findall(r"\b1\s*/\s*1\b", text)) == int(show_page_number), text
    finally:
        page.close()
