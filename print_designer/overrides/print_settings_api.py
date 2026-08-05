# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

"""
Print Settings Sidebar API for Print Designer
============================================
Overrides Frappe's get_print_settings_to_show to add Print Designer
watermark fields to the print preview sidebar.

Target file: print_designer/overrides/print_settings_api.py
Registered in hooks.py line 519:
    "frappe.printing.page.print.print.get_print_settings_to_show":
        "print_designer.overrides.print_settings_api.get_print_settings_to_show"

Called from Frappe core print.js setup_additional_settings() (line ~236).
"""

import frappe


@frappe.whitelist()
def get_print_settings_to_show(doctype, docname):
    """
    Override frappe.printing.page.print.print.get_print_settings_to_show
    to include Print Designer watermark fields while preserving ERPNext's functionality.

    Returns relevant Print Settings fields for the print sidebar,
    including both ERPNext's standard fields and Print Designer's watermark fields.
    """
    # ============ DEBUG (temporary — remove after confirming) ============
    import sys

    print("\n" + "=" * 70, file=sys.stderr)
    print("[PD-PRINT-SETTINGS] >>> get_print_settings_to_show CALLED!", file=sys.stderr)
    print(f"[PD-PRINT-SETTINGS] doctype={doctype}", file=sys.stderr)
    print(f"[PD-PRINT-SETTINGS] docname={docname}", file=sys.stderr)
    print("=" * 70 + "\n", file=sys.stderr)
    # ====================================================================

    # Get the document
    doc = frappe.get_doc(doctype, docname)
    print_settings = frappe.get_single("Print Settings")

    # Start with an empty list of fields to return
    fields_to_show = []

    # Get fields from document's get_print_settings method if it exists (ERPNext logic)
    if hasattr(doc, "get_print_settings"):
        erpnext_fields = doc.get_print_settings() or []
        print(f"[PD-PRINT-SETTINGS] ERPNext returned fields: {erpnext_fields}", file=sys.stderr)

        # Add ERPNext fields to our list
        for fieldname in erpnext_fields:
            df = print_settings.meta.get_field(fieldname)
            if df:
                df.default = print_settings.get(fieldname)
                fields_to_show.append(df)
                print(
                    f"[PD-PRINT-SETTINGS]   + ERPNext field: {fieldname} (label: {df.label})",
                    file=sys.stderr,
                )
    else:
        print("[PD-PRINT-SETTINGS] doc has no get_print_settings method", file=sys.stderr)

    # ===========================================================================
    # 1. COPY SETTINGS (before watermark)
    # Only show if "Show Copy Controls in Toolbar" is enabled in Print Settings
    # ===========================================================================
    if print_settings.get("show_copy_controls_in_toolbar"):
        copy_fields = [
            "enable_multiple_copies",
            "default_copy_count",
            "pdf_page_size",
            "page_orientation",
            "pdf_generator",  # PDF generator after page orientation (3-column layout)
            "default_original_label",
            "default_copy_label",
        ]
        print(f"[PD-PRINT-SETTINGS] Copy fields to add: {copy_fields}", file=sys.stderr)
        label_overrides = {
            "default_copy_count": "Copy Count",
            "default_original_label": "Original Label",
            "default_copy_label": "Copy Label",
        }
        read_only_fields = {"default_original_label", "default_copy_label"}
        for fieldname in copy_fields:
            df = print_settings.meta.get_field(fieldname)
            if df:
                df.default = print_settings.get(fieldname)
                if fieldname in label_overrides:
                    df.label = label_overrides[fieldname]
                if fieldname in read_only_fields:
                    df.read_only = 1
                    df.description = "Driven by Watermark per Page"
                fields_to_show.append(df)
                print(
                    f"[PD-PRINT-SETTINGS]   + copy field: {fieldname} (label: {df.label})",
                    file=sys.stderr,
                )
            else:
                print(
                    f"[PD-PRINT-SETTINGS]   X copy field '{fieldname}' NOT FOUND",
                    file=sys.stderr,
                )
    else:
        print(
            "[PD-PRINT-SETTINGS]   Skip copy fields (show_copy_controls_in_toolbar is disabled)",
            file=sys.stderr,
        )

    # ===========================================================================
    # 2. WATERMARK SETTINGS
    # Order: watermark_settings -> position -> font_family -> font_size -> margins
    # ===========================================================================
    watermark_fields = [
        "watermark_settings_section",
        "watermark_settings",
        "watermark_position",
        "watermark_font_family",
        "watermark_font_size",
        # NOTE: watermark_col_break is internal - not included
        "watermark_top",
        "watermark_right",
        "watermark_bottom",
        "watermark_left",
    ]
    print(
        f"[PD-PRINT-SETTINGS] Watermark fields to add: {watermark_fields}",
        file=sys.stderr,
    )

    # Add watermark fields to the sidebar
    for fieldname in watermark_fields:
        df = print_settings.meta.get_field(fieldname)
        if df:
            # Skip Section Break and Column Break - not renderable as controls
            if df.fieldtype in ("Section Break", "Column Break"):
                print(
                    f"[PD-PRINT-SETTINGS]   - skip {fieldname} (fieldtype: {df.fieldtype}) - not renderable",
                    file=sys.stderr,
                )
                continue
            df.default = print_settings.get(fieldname)
            fields_to_show.append(df)
            print(
                f"[PD-PRINT-SETTINGS]   + watermark field: {fieldname} "
                f"(label: {df.label}, insert_after: {getattr(df, 'insert_after', 'N/A')})",
                file=sys.stderr,
            )
        else:
            print(
                f"[PD-PRINT-SETTINGS]   X watermark field '{fieldname}' NOT FOUND in Print Settings meta",
                file=sys.stderr,
            )

    # ===========================================================================
    # 3. PAGE NUMBER SETTINGS (after watermark)
    # ===========================================================================
    page_number_fields = [
        "page_number_section",
        "page_number_display",
        "page_number_position",
        "page_number_font_family",
        "page_number_font_size",
        "page_number_font_color",
        "page_number_border",
        "page_number_top",
        "page_number_right",
        "page_number_bottom",
        "page_number_left",
    ]
    print(
        f"[PD-PRINT-SETTINGS] Page Number fields to add: {page_number_fields}",
        file=sys.stderr,
    )
    for fieldname in page_number_fields:
        df = print_settings.meta.get_field(fieldname)
        if df:
            # Skip Section Break and Column Break - not renderable as controls
            if df.fieldtype in ("Section Break", "Column Break"):
                print(f"[PD-PRINT-SETTINGS]   - skip {fieldname} ({df.fieldtype})", file=sys.stderr)
                continue
            stored_value = print_settings.get(fieldname)
            if stored_value is not None and stored_value != "":
                df.default = stored_value
            fields_to_show.append(df)
            print(
                f"[PD-PRINT-SETTINGS]   + page_number field: {fieldname} (label: {df.label}, default: {df.default})",
                file=sys.stderr,
            )
        else:
            print(
                f"[PD-PRINT-SETTINGS]   X page_number field '{fieldname}' NOT FOUND",
                file=sys.stderr,
            )

    print(
        f"[PD-PRINT-SETTINGS] FINAL returning {len(fields_to_show)} fields: "
        f"{[(f.fieldname, f.label) for f in fields_to_show]}",
        file=sys.stderr,
    )
    print("=" * 70 + "\n", file=sys.stderr)

    return fields_to_show
