"""Real-browser checks of preview-only borders and quiet blank padding rows."""

from pathlib import Path

import pytest
from jinja2 import ChoiceLoader, Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

from print_designer.print_designer.page.print_designer.print_designer import convert_css
from print_designer.utils.print_labels import translate_table_column_label

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


def render_table(row_count, legacy=False, preset=None, columns=None, translate=lambda value: value):
    env = Environment(loader=ChoiceLoader([FileSystemLoader(MACROS), FileSystemLoader(APP)]))
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
            'borderPreset': preset,
            'width': 500, 'startX': 0, 'startY': 0, 'classes': [],
            'headerStyle': {'textAlign': 'center', 'backgroundColor': '#cdcbf2'},
            'style': {'textAlign': 'right', 'verticalAlign': 'top', 'borderColor': '#ECAD4B'},
            'altStyle': {'borderColor': '#ff0000'},
            'columns': columns if columns is not None else [
                {'label': 'Hidden left', 'dynamicContent': [{}], 'applyStyleToHeader': True,
                 'style': {'borderLeftStyle': 'hidden', 'borderColor': '#4F9DD9'}},
                {'label': 'Visible', 'dynamicContent': [{}], 'style': {}},
            ],
        },
        settings={'schema_version': '1.3.0'},
        doc={'items': [{'idx': i + 1} for i in range(row_count)]},
        convert_css=convert_css, translate_table_column_label=translate,
        span_tag=lambda *args: 'Populated item',
        render_spantag=lambda *args: 'Populated item',
    )


@pytest.mark.parametrize('legacy', [False, True])
@pytest.mark.parametrize('language, expected', [
    ('en', ['Order', 'Receive', 'Document Type', 'Document Number', 'Name']),
    ('th', ['ลำดับที่', 'รับชำระ', 'ประเภทเอกสาร', 'เลขที่เอกสาร', 'Name']),
])
def test_standard_column_captions_are_global_but_custom_captions_are_literal(
    browser, legacy, language, expected
):
    columns = [
        {'label': 'No.', 'style': {}},
        {'label': 'Allocated', 'style': {}},
        {'label': 'Type', 'style': {}},
        {'label': 'Name', 'style': {}},
        {'label': 'Name', 'labelIsCustom': True, 'style': {}},
    ]
    page = browser.new_page()
    try:
        page.set_content(render_table(
            0, legacy, columns=columns,
            translate=lambda value: translate_table_column_label(value, language),
        ))
        assert page.locator('th').all_inner_texts() == expected
    finally:
        page.close()


@pytest.mark.parametrize('legacy', [False, True])
def test_custom_column_caption_prints_literally_in_both_schemas(browser, legacy):
    columns = [
        {'label': 'รับชำระ', 'labelIsCustom': True, 'dynamicContent': [], 'style': {}},
        {'label': 'Allocated', 'dynamicContent': [], 'style': {}},
    ]
    page = browser.new_page()
    try:
        page.set_content(render_table(
            1, legacy, columns=columns,
            translate=lambda value: 'Translated default',
        ))
        assert page.locator('th').all_inner_texts() == ['รับชำระ', 'Translated default']
    finally:
        page.close()


@pytest.mark.parametrize('legacy', [False, True])
def test_header_inherits_explicit_column_styles_only_when_linked(browser, legacy):
    columns = [
        {'label': 'Blank fill', 'applyStyleToHeader': True, 'dynamicContent': [],
         'style': {'backgroundColor': '', 'borderColor': '#CB2929'},
         'linkedHeaderBorderStyle': {'borderColor': '#B4CD29'}},
        {'label': 'Explicit fill', 'applyStyleToHeader': True, 'dynamicContent': [],
         'style': {'backgroundColor': '#ECAD4B'}},
        {'label': 'Unlinked', 'applyStyleToHeader': False, 'dynamicContent': [],
         'style': {'backgroundColor': '#ECAD4B'},
         'linkedHeaderBorderStyle': {'borderColor': '#B4CD29'},
         'headerBorderStyle': {'borderColor': '#4F9DD9'}},
    ]
    page = browser.new_page()
    try:
        page.set_content(render_table(1, legacy, preset='full-grid', columns=columns))
        headers = page.locator('th').evaluate_all('''cells => cells.map(cell => {
          const style = getComputedStyle(cell);
          return [style.backgroundColor, style.borderTopColor];
        })''')
        assert headers == [
            ['rgb(205, 203, 242)', 'rgb(180, 205, 41)'],
            ['rgb(236, 173, 75)', 'rgb(0, 0, 0)'],
            ['rgb(205, 203, 242)', 'rgb(79, 157, 217)'],
        ]
    finally:
        page.close()


@pytest.mark.parametrize('legacy', [False, True])
@pytest.mark.parametrize('preset, expected', [
    ('no-grid', [False] * 6),
    ('full-grid', [True, True, True, True, False, True]),
    ('outline', [True, True, False, False, False, True]),
    ('horizontal', [True, False, False, True, False, True]),
])
def test_presets_keep_their_edge_layout_in_print_and_desk(browser, legacy, preset, expected):
    page = browser.new_page()
    try:
        page.set_content(
            '<div id="tbs__print__page__preview"><div id="__print_designer">'
            + render_table(2, legacy, preset) + '</div></div>'
        )
        read_edges = """table => {
            const visible = (cell, side) => parseFloat(getComputedStyle(cell)[side]) > 0;
            const [firstHeader] = table.tHead.rows[0].cells;
            const [firstData, , firstPadding, lastPadding] = table.tBodies[0].rows;
            return [
                visible(firstHeader, 'borderTopWidth'),
                visible(firstData.cells[0], 'borderLeftWidth'),
                visible(firstData.cells[1], 'borderLeftWidth'),
                visible(firstData.cells[0], 'borderBottomWidth'),
                visible(firstPadding.cells[0], 'borderBottomWidth'),
                visible(lastPadding.cells[0], 'borderBottomWidth'),
            ];
        }"""
        table = page.locator('table.printTable')
        page.emulate_media(media='print')
        assert table.evaluate(read_edges) == expected
        page.emulate_media(media='screen')
        page.evaluate('() => {' + BORDER_SCRIPT + '\napplyPDPreviewTableBorders(document);}')
        assert table.evaluate(read_edges) == expected
    finally:
        page.close()


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
