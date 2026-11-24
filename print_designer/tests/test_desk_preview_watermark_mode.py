"""Explicit sidebar modes take precedence over global watermark defaults."""

from unittest.mock import patch

import frappe
import pytest

from print_designer.overrides import printview_watermark as renderer


@pytest.mark.parametrize(
    "mode,expected", [("Original on First Page", 1), ("Copy on All Pages", 2), ("None", 0)]
)
def test_sidebar_watermark_wins_over_global_none(mode, expected):
    settings = {
        "watermark_settings": mode,
        "page_number_display": "Show",
        "enable_multiple_copies": 1,
        "default_copy_count": 2,
    }
    with (
        patch.object(renderer, "original_get_html_and_style", return_value={"html": '<div class="print-format">Quotation</div>', "style": ""}),
        patch.object(renderer, "log_to_print_designer"),
        patch.object(frappe, "get_doc", return_value=frappe._dict()),
        patch.object(frappe, "get_single", return_value=frappe._dict()),
        patch.object(frappe, "_", side_effect=lambda value: value),
        patch("print_designer.api.watermark.get_watermark_config_for_print_format", return_value={"enabled": True, "watermark_mode": "None"}),
    ):
        result = renderer.get_html_and_style_with_watermark(
            doc={"doctype": "Quotation", "name": "TEST"},
            print_format="Quotation - Example",
            settings=settings,
        )
    assert result["html"].count('class="pd-preview-copy-watermark"') == expected
    assert result["html"].count('class="pd-preview-page-number"') == 2
