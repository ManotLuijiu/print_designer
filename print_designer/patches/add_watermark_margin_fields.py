"""
Patch to add watermark margin fields to Print Settings
Run with: bench --site <site> execute print_designer.patches.add_watermark_margin_fields.execute
"""

import frappe


def execute():
    """Add watermark margin fields to Print Settings"""

    if not frappe.db.exists("DocType", "Print Settings"):
        frappe.log_error("Print Settings DocType not found")
        return

    fields_to_add = [
        {
            "dt": "Print Settings",
            "fieldname": "watermark_margin_top",
            "label": "Watermark Margin Top",
            "fieldtype": "Data",
            "default": "10mm",
            "insert_after": "watermark_position",
            "depends_on": "eval:doc.watermark_settings != 'None'",
            "description": "Margin from top (e.g., 10mm, 20px)",
        },
        {
            "dt": "Print Settings",
            "fieldname": "watermark_margin_bottom",
            "label": "Watermark Margin Bottom",
            "fieldtype": "Data",
            "default": "10mm",
            "insert_after": "watermark_margin_top",
            "depends_on": "eval:doc.watermark_settings != 'None'",
            "description": "Margin from bottom (e.g., 10mm, 20px)",
        },
        {
            "dt": "Print Settings",
            "fieldname": "watermark_margin_left",
            "label": "Watermark Margin Left",
            "fieldtype": "Data",
            "default": "10mm",
            "insert_after": "watermark_margin_bottom",
            "depends_on": "eval:doc.watermark_settings != 'None'",
            "description": "Margin from left (e.g., 10mm, 20px)",
        },
        {
            "dt": "Print Settings",
            "fieldname": "watermark_margin_right",
            "label": "Watermark Margin Right",
            "fieldtype": "Data",
            "default": "10mm",
            "insert_after": "watermark_margin_left",
            "depends_on": "eval:doc.watermark_settings != 'None'",
            "description": "Margin from right (e.g., 10mm, 20px)",
        },
    ]

    for field_def in fields_to_add:
        fieldname = field_def["fieldname"]

        # Check if field already exists
        if frappe.db.exists("Custom Field", {"dt": "Print Settings", "fieldname": fieldname}):
            print(f"Field {fieldname} already exists, skipping")
            continue

        # Create the custom field
        try:
            cf = frappe.get_doc(
                {
                    "doctype": "Custom Field",
                    "dt": field_def["dt"],
                    "fieldname": field_def["fieldname"],
                    "label": field_def["label"],
                    "fieldtype": field_def["fieldtype"],
                    "default": field_def.get("default"),
                    "insert_after": field_def["insert_after"],
                    "depends_on": field_def.get("depends_on"),
                    "description": field_def.get("description"),
                }
            )
            cf.insert(ignore_permissions=True)
            print(f"✅ Created field: {fieldname}")
        except Exception as e:
            print(f"❌ Error creating field {fieldname}: {e}")

    # Clear cache to reflect changes
    frappe.clear_cache()
    print("✅ Patch complete - cleared cache")
