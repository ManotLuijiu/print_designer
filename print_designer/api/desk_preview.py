"""Desk preview entry point independent of competing core RPC overrides."""

import frappe


@frappe.whitelist()
def get_html_and_style(
    doc,
    name=None,
    print_format=None,
    no_letterhead=None,
    letterhead=None,
    trigger_print=False,
    style=None,
    settings=None,
    prompt_data=None,
):
    args = dict(
        doc=doc,
        name=name,
        print_format=print_format,
        no_letterhead=no_letterhead,
        letterhead=letterhead,
        trigger_print=trigger_print,
        style=style,
        settings=settings,
    )
    # PDF Forms can associate a template by reverse lookup as well as by the
    # Print Format field. Preserve both cases, including its permission checks.
    if "pdf_forms" in frappe.get_installed_apps():
        from pdf_forms.api.print_format import (
            _get_form_template_id,
            get_html_and_style as get_form_preview,
        )

        if _get_form_template_id(print_format):
            return get_form_preview(**args, prompt_data=prompt_data)

    from print_designer.overrides.printview_watermark import (
        get_html_and_style_with_watermark,
    )

    # The renderer calls Frappe's original implementation, which validates
    # document print permission before returning any HTML.
    return get_html_and_style_with_watermark(**args)
