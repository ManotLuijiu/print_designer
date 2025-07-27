# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe


@frappe.whitelist()
def get_print_settings_to_show(doctype, docname):
    """
    Override frappe.printing.page.print.print.get_print_settings_to_show
    to include Print Designer watermark fields while preserving ERPNext's functionality.
    
    This function returns relevant Print Settings fields for the print sidebar,
    including both ERPNext's standard fields and Print Designer's watermark fields.
    """
    
    # Get the document
    doc = frappe.get_doc(doctype, docname)
    print_settings = frappe.get_single("Print Settings")
    
    # Start with an empty list of fields to return
    fields_to_show = []
    
    # Get fields from document's get_print_settings method if it exists (ERPNext logic)
    if hasattr(doc, "get_print_settings"):
        erpnext_fields = doc.get_print_settings() or []
        
        # Add ERPNext fields to our list
        for fieldname in erpnext_fields:
            df = print_settings.meta.get_field(fieldname)
            if df:
                df.default = print_settings.get(fieldname)
                fields_to_show.append(df)
    
    # Always add Print Designer watermark fields to the sidebar
    watermark_fields = [
        "watermark_settings",
        "watermark_font_size", 
        "watermark_position",
        "watermark_font_family"
    ]
    
    # Add watermark fields to the sidebar
    for fieldname in watermark_fields:
        df = print_settings.meta.get_field(fieldname)
        if df:
            df.default = print_settings.get(fieldname)
            fields_to_show.append(df)
    
    # Log for debugging purposes
    frappe.logger().debug(f"Print Settings fields for {doctype}: {[f.fieldname for f in fields_to_show]}")
    
    return fields_to_show