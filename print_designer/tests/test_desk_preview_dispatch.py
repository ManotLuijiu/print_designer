"""Keep Desk overlays and PDF Forms routing independent of hook precedence."""

import sys
from types import ModuleType
from unittest.mock import Mock, patch

import pytest

from print_designer.api.desk_preview import get_html_and_style


@pytest.mark.parametrize("apps,template", [([], None), (["pdf_forms"], None), (["pdf_forms"], "Form-1")])
def test_preview_dispatch_preserves_settings_and_renderer(apps, template):
    overlays = ModuleType("print_designer.overrides.printview_watermark")
    overlays.get_html_and_style_with_watermark = Mock(return_value={"html": "overlays"})
    forms = ModuleType("pdf_forms.api.print_format")
    forms._get_form_template_id = Mock(return_value=template)
    forms.get_html_and_style = Mock(return_value={"html": "pdf form"})
    settings = {"watermark_settings": "Original on First Page", "page_number_display": "Show"}
    with patch("frappe.get_installed_apps", return_value=apps), patch.dict(
        sys.modules, {overlays.__name__: overlays, forms.__name__: forms}
    ):
        result = get_html_and_style(
            doc={"doctype": "Quotation", "name": "TEST"},
            print_format="Quotation - AWS Solution",
            settings=settings,
            prompt_data={"test": True},
        )
    renderer = forms.get_html_and_style if template else overlays.get_html_and_style_with_watermark
    other = overlays.get_html_and_style_with_watermark if template else forms.get_html_and_style
    renderer.assert_called_once()
    other.assert_not_called()
    assert renderer.call_args.kwargs["settings"] is settings
    assert result["html"] == ("pdf form" if template else "overlays")


def test_print_permission_failure_is_not_swallowed():
    overlays = ModuleType("print_designer.overrides.printview_watermark")
    overlays.get_html_and_style_with_watermark = Mock(side_effect=PermissionError("denied"))
    with patch("frappe.get_installed_apps", return_value=[]), patch.dict(
        sys.modules, {overlays.__name__: overlays}
    ), pytest.raises(PermissionError):
        get_html_and_style(doc={"doctype": "Quotation", "name": "TEST"})
