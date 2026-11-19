"""Browser printview must not duplicate a general watermark into every copy."""

import json
from unittest.mock import patch

import frappe
import pytest
from bs4 import BeautifulSoup

from print_designer.www import printview

BASE_HTML = '''<div id="__print_designer">
<div id="header-html"><div id="header-render-container">Header</div></div>
<div id="body-content">Quotation</div>
<div id="footer-html"><div id="footer-render-container">Footer</div></div>
</div>'''


def render_context(settings, format_mode=None, defaults=None):
    format_doc = frappe._dict(
        print_designer=1, print_designer_body='saved design',
        print_designer_settings=json.dumps({'watermark': {'mode': format_mode}}),
    )
    with (
        patch.object(printview, 'core_get_context', return_value={'body': BASE_HTML}),
        patch.object(printview, 'log_to_print_designer'),
        patch.object(frappe, 'form_dict', frappe._dict(
            format='Quotation - AWS Solution', settings=json.dumps(settings),
        )),
        patch.object(frappe, 'get_doc', return_value=format_doc),
        patch.object(frappe, 'get_single', return_value=frappe._dict(defaults or {})),
        patch.object(frappe, '_', side_effect=lambda value: value),
    ):
        return printview.get_context(frappe._dict())['body']


@pytest.mark.parametrize('mode,expected', [
    ('Original on First Page', [['Original'], [], []]),
    ('Copy on All Pages', [['Copy'], ['Copy'], ['Copy']]),
    ('Original,Copy on Sequence', [['Original'], ['Copy'], ['Original']]),
    ('None', [[], [], []]),
])
def test_each_copy_has_only_its_own_watermark(mode, expected):
    body = render_context({
        'enable_multiple_copies': 1, 'default_copy_count': 3,
        'watermark_settings': mode, 'page_number_display': 'Show',
    })
    soup = BeautifulSoup(body, 'html.parser')
    copies = soup.select('.pd-preview-copy')
    assert len(copies) == 3
    assert soup.select('.pd-watermark') == []
    assert [[w.get_text(strip=True) for w in c.select('.pd-preview-copy-watermark')]
            for c in copies] == expected
    assert [len(c.select('.pd-page-number')) for c in copies] == [1, 1, 1]


@pytest.mark.parametrize('enabled,count', [(0, 2), (1, 1)])
def test_single_copy_keeps_one_general_watermark(enabled, count):
    body = render_context({
        'enable_multiple_copies': enabled, 'default_copy_count': count,
        'watermark_settings': 'Original on First Page', 'page_number_display': 'Show',
    })
    soup = BeautifulSoup(body, 'html.parser')
    assert len(soup.select('.pd-watermark')) == 1
    assert soup.select('.pd-preview-copy') == []
    assert len(soup.select('.pd-page-number')) == 1


def test_copy_renderer_preserves_format_watermark_fallback():
    body = render_context(
        {'enable_multiple_copies': 1, 'default_copy_count': 2},
        format_mode='Original on First Page',
    )
    soup = BeautifulSoup(body, 'html.parser')
    assert [len(c.select('.pd-preview-copy-watermark'))
            for c in soup.select('.pd-preview-copy')] == [1, 0]
    assert soup.select('.pd-watermark') == []


def test_global_copy_defaults_use_only_the_copy_watermark_renderer():
    body = render_context(
        {'watermark_settings': 'Original on First Page'},
        defaults={'enable_multiple_copies': 1, 'default_copy_count': 2},
    )
    soup = BeautifulSoup(body, 'html.parser')
    assert [len(c.select('.pd-preview-copy-watermark'))
            for c in soup.select('.pd-preview-copy')] == [1, 0]
    assert soup.select('.pd-watermark') == []
