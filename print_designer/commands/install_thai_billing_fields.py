#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Install Thai Billing Link Field for Payment Entry
Adds a link field to Payment Entry to connect it to Thai Billing documents
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Main installation function for Thai Billing link field"""
    print("Installing Thai Billing link field for Payment Entry...")
    create_thai_billing_fields()
    frappe.clear_cache()
    print("Thai Billing link field installed successfully for Payment Entry")


def create_thai_billing_fields():
    """Create Thai Billing link field in Payment Entry"""

    # Check if Thai Billing DocType exists
    if not frappe.db.exists("DocType", "Thai Billing"):
        print("Thai Billing DocType not found - skipping field installation")
        return

    custom_fields = {
        "Payment Entry": [
            {
                "fieldname": "custom_thai_billing",
                "fieldtype": "Link",
                "label": "Thai Billing",
                "options": "Thai Billing",
                "insert_after": "party_name",
                "description": "Reference to the Thai Billing document this payment is for",
                "hidden": 0,
                "read_only": 0,
                "in_standard_filter": 1,
                "no_copy": 0,
                "print_hide": 0,
            },
        ]
    }

    create_custom_fields(custom_fields, update=True)
    print("Created Thai Billing link field in Payment Entry")


def check_thai_billing_fields():
    """Check if Thai Billing link field exists in Payment Entry"""

    field_exists = frappe.db.exists(
        "Custom Field",
        {"dt": "Payment Entry", "fieldname": "custom_thai_billing"}
    )

    if field_exists:
        print("Thai Billing link field exists in Payment Entry")
        return True
    else:
        print("Thai Billing link field is missing from Payment Entry")
        return False


def uninstall_thai_billing_fields():
    """Remove Thai Billing link field from Payment Entry (for uninstall)"""

    if frappe.db.exists("Custom Field", {"dt": "Payment Entry", "fieldname": "custom_thai_billing"}):
        frappe.db.delete("Custom Field", {"dt": "Payment Entry", "fieldname": "custom_thai_billing"})
        frappe.clear_cache()
        print("Removed Thai Billing link field from Payment Entry")
    else:
        print("Thai Billing link field not found - nothing to remove")


if __name__ == "__main__":
    execute()
