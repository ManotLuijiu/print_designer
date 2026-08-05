#!/usr/bin/env python3
# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# For license information, please see license.txt

"""
Print Format Custom Fields for Print Designer
============================================
Handles installation, verification, and removal of Print Format doctype
custom fields:
- Page Orientation (per-format override of Print Settings orientation)
- Watermark per Page (per-format override of Print Settings watermark)

CLI commands:
- bench --site <site> install-print-format-fields
- bench --site <site> uninstall-print-format-fields
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install_print_format_fields():
    """
    Install custom fields for Print Format DocType.
    Adds Page Orientation and Watermark per Page to 3rd column after pdf_generator.
    """
    try:
        custom_fields = {
            "Print Format": [
                {
                    "fieldname": "orientation_col_break",
                    "fieldtype": "Column Break",
                    "insert_after": "pdf_generator",
                },
                {
                    "label": "Page Orientation",
                    "fieldname": "page_orientation",
                    "fieldtype": "Select",
                    "options": "Portrait\nLandscape",
                    "default": "Portrait",
                    "insert_after": "orientation_col_break",
                    "description": "Override page orientation for this print format",
                },
                {
                    "label": "Watermark per Page",
                    "fieldname": "watermark_settings",
                    "fieldtype": "Select",
                    "options": "None\nOriginal on First Page\nCopy on All Pages\nOriginal,Copy on Sequence",
                    "default": "None",
                    "insert_after": "page_orientation",
                    "description": "Control watermark display per page",
                },
            ]
        }

        print("\nInstalling Print Format orientation/watermark fields...")
        create_custom_fields(custom_fields, update=True)
        print("   Done: Page Orientation and Watermark per Page installed")

        # Apply Property Setters
        _apply_property_setters()

        frappe.db.commit()
        return True

    except Exception as e:
        print(f"   Error: {str(e)}")
        frappe.log_error("Print Format Fields Installation Error", str(e))
        return False


def _apply_property_setters():
    """Create property setters for Print Format DocType."""
    try:
        # Set pdf_generator default to chrome
        frappe.make_property_setter(
            {
                "doctype": "Print Format",
                "fieldname": "pdf_generator",
                "property": "default",
                "value": "chrome",
                "property_type": "Select",
            },
            validate_fields_for_doctype=False,
        )
        print("   Done: pdf_generator default = chrome")

    except Exception as e:
        print(f"   Warning: Property setter error (may already exist): {str(e)}")


def uninstall_print_format_fields():
    """
    Remove custom fields from Print Format DocType.
    """
    try:
        print("\nRemoving Print Format custom fields...")
        fields_to_remove = [
            "page_orientation",
            "watermark_settings",
            "orientation_col_break",
            # Cleanup from previous wrong install
            "pdf_settings_section",
            "pdf_settings_col_break",
            "pdf_settings_col_break_02",
            "pdf_page_size",
            "pdf_custom_width",
            "pdf_custom_height",
        ]
        for fieldname in fields_to_remove:
            if frappe.db.exists("Custom Field", {"dt": "Print Format", "fieldname": fieldname}):
                frappe.delete_doc("Custom Field", {"dt": "Print Format", "fieldname": fieldname})
                print(f"   Removed: {fieldname}")

        frappe.db.commit()
        print("   Done: Print Format custom fields removed")
        return True

    except Exception as e:
        print(f"   Error: {str(e)}")
        frappe.log_error("Print Format Fields Uninstall Error", str(e))
        return False


def check_print_format_fields():
    """Check status of Print Format custom fields."""
    required_fields = ["page_orientation", "watermark_settings"]
    missing = []
    installed = []

    for fieldname in required_fields:
        if frappe.db.exists("Custom Field", {"dt": "Print Format", "fieldname": fieldname}):
            installed.append(f"Print Format.{fieldname}")
        else:
            missing.append(f"Print Format.{fieldname}")

    if missing:
        print(f"Missing: {', '.join(missing)}")
        return False
    print("All required Print Format custom fields are installed")
    return True


# CLI execution
if __name__ == "__main__":
    import sys

    site = "digisoft-erp.bunchee.online"
    frappe.init(site=site)
    frappe.connect()

    action = sys.argv[1] if len(sys.argv) > 1 else "install"

    if action == "install":
        install_print_format_fields()
    elif action == "uninstall":
        uninstall_print_format_fields()
    elif action == "check":
        check_print_format_fields()
    else:
        print(f"Unknown action: {action}")
        print("Usage: python install_print_format_fields.py [install|uninstall|check]")

    frappe.destroy()
