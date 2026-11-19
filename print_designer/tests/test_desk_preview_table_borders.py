"""Real-browser checks of preview-only borders and quiet blank padding rows."""

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

from print_designer.print_designer.page.print_designer.print_designer import convert_css

APP = Path(__file__).parents[1]
MACROS = APP / 'print_designer/page/print_designer/jinja/macros'
BORDER_SCRIPT = (APP / 'public/js/print_table_borders.js').read_text()


@pytest.fixture(scope='module')
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path='/home/frappe/frappe-bench/chromium/chrome-linux/headless_shell',
        )
        yield browser
        browser.close()


def render_table(row_count, legacy=False):
    env = Environment(loader=FileSystemLoader(MACROS))
    if legacy:
        source = (MACROS.parent / 'old_print_format.html').read_text()
        start = source.index('{% macro render_table(')
        end = source.index('{%- endmacro', start)
        end = source.index('%}', end) + 2
        template = env.from_string(source[start:end] + '{{ render_table(element, {}) }}')
    else:
        template = env.from_string(
            '{% from "table.html" import table with context %}{{ table(element, {}, "auto") }}'
        )
    return template.render(
        element={
            'heightType': 'auto', 'table': {'fieldname': 'items'}, 'minRows': 4,
            'width': 500, 'startX': 0, 'startY': 0, 'classes': [],
            'headerStyle': {'textAlign': 'center'},
            'style': {'textAlign': 'right', 'verticalAlign': 'top', 'borderColor': '#ECAD4B'},
            'altStyle': {'borderColor': '#ff0000'},
            'columns': [
                {'label': 'Hidden left', 'dynamicContent': [{}], 'applyStyleToHeader': True,
                 'style': {'borderLeftStyle': 'hidden', 'borderColor': '#4F9DD9'}},
                {'label': 'Visible', 'dynamicContent': [{}], 'style': {}},
            ],
        },
        settings={'schema_version': '1.3.0'},
        doc={'items': [{'idx': i + 1} for i in range(row_count)]},
        convert_css=convert_css, translate_print_label=lambda value: value,
        span_tag=lambda *args: 'Populated item',
        render_spantag=lambda *args: 'Populated item',
    )


@pytest.mark.parametrize('row_count', [0, 1, 2])
@pytest.mark.parametrize('legacy', [False, True])
def test_populated_rows_have_lines_but_blank_padding_does_not(browser, row_count, legacy):
    page = browser.new_page()
    try:
        page.set_content(
            '<style>table{border-collapse:collapse}th,td{padding:6px}</style>'
            '<div id="tbs__print__page__preview" class="print-format">'
            '<div id="__print_designer">' + render_table(row_count, legacy) + '</div></div>'
        )
        page.evaluate('() => {' + BORDER_SCRIPT + '\napplyPDPreviewTableBorders(document);}')
        rows = page.locator('tbody > tr')
        assert rows.count() == 4
        for i in range(4):
            cell = rows.nth(i).locator('td').nth(1)
            styles = cell.evaluate('el => {const s=getComputedStyle(el);return {left:s.borderLeftWidth,right:s.borderRightWidth,top:s.borderTopWidth,bottom:s.borderBottomWidth,align:s.textAlign,vertical:s.verticalAlign,color:s.borderLeftColor}}')
            assert styles['left'] == styles['right'] == '1px'
            assert styles['align'] == 'right'
            assert styles['vertical'] == 'top'
            if i < row_count:
                assert styles['bottom'] == '1px'
            else:
                assert styles['top'] == '0px'
                assert styles['bottom'] == ('1px' if i == 3 else '0px')
            expected_color = 'rgb(255, 0, 0)' if i < row_count and i % 2 else 'rgb(236, 173, 75)'
            assert styles['color'] == expected_color
        assert page.locator('thead th').nth(1).evaluate('el=>getComputedStyle(el).borderLeftWidth') == '1px'
        assert page.locator('thead th').nth(1).evaluate('el=>getComputedStyle(el).textAlign') == 'center'
        assert page.locator('thead th').first.evaluate('el=>getComputedStyle(el).borderLeftStyle') == 'hidden'
        assert rows.first.locator('td').first.evaluate('el=>getComputedStyle(el).borderLeftStyle') == 'hidden'
    finally:
        page.close()


def test_other_renderers_and_unmarked_tables_are_unchanged(browser):
    page = browser.new_page()
    try:
        # Same generated table, without the Desk preview marker (e.g. printview).
        page.set_content('<div class="print-format"><div id="__print_designer">'
                         + render_table(2) + '</div></div>')
        before = page.locator('table').evaluate('el=>el.outerHTML')
        page.evaluate('() => {' + BORDER_SCRIPT + '\napplyPDPreviewTableBorders(document);}')
        assert page.locator('table').evaluate('el=>el.outerHTML') == before
    finally:
        page.close()


def test_browser_printview_applies_borders_to_every_copy_in_screen_and_print(browser):
    body = ''.join(
        f'<div class="pd-preview-copy" data-copy-index="{i}">'
        f'<div id="__print_designer">{render_table(2)}</div></div>'
        for i in (1, 2)
    )
    template = Environment().from_string((APP / 'www/printview.html').read_text())
    html = template.render(
        body=body, lang='th', layout_direction='ltr', title='Border regression',
        print_style='table{border-collapse:collapse}', include_style=lambda _: '',
        _=lambda value: value, trigger_print=False,
    )
    page = browser.new_page()
    try:
        page.route('https://pd.test/assets/print_designer/js/print_table_borders.js',
                   lambda route: route.fulfill(body=BORDER_SCRIPT, content_type='text/javascript'))
        page.route('https://pd.test/printview',
                   lambda route: route.fulfill(body=html, content_type='text/html'))
        page.goto('https://pd.test/printview')
        assert page.locator('body').evaluate("el=>el.classList.contains('pd-browser-printview')")
        assert page.locator('table.printTable').count() == 2
        for media in ('screen', 'print'):
            page.emulate_media(media=media)
            for table in page.locator('table.printTable').all():
                assert table.locator('thead th').nth(1).evaluate('el=>getComputedStyle(el).borderLeftWidth') == '1px'
                rows = table.locator('tbody tr')
                for i in range(4):
                    style = rows.nth(i).locator('td').nth(1).evaluate('el=>{const s=getComputedStyle(el);return {left:s.borderLeftWidth,bottom:s.borderBottomWidth}}')
                    assert style['left'] == '1px'
                    assert style['bottom'] == ('0px' if i == 2 else '1px')
    finally:
        page.close()
