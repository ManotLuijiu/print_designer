#!/usr/bin/env python3
# Copyright (c) 2025, Hussain Nagaria and contributors
# For license information, please see license.txt

"""
Patch to remove custom_branch_code field from Supplier doctype.

This legacy field has been replaced by pd_custom_branch_code.
Data migration was handled by print_designer.patches.v1_8.migrate_branch_code_to_pd_custom
"""

import frappe


def execute():
    """Remove custom_branch_code field from Supplier doctype."""

    # Field to remove
    field_name = "custom_branch_code"
    doctype = "Supplier"

    # Check if field exists before attempting deletion
    if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field_name}):
        try:
            # Delete the custom field
            frappe.delete_doc("Custom Field", {"dt": doctype, "fieldname": field_name}, ignore_permissions=True)
            frappe.db.commit()

            print(f"✅ Removed custom field '{field_name}' from {doctype} doctype")
        except Exception as e:
            print(f"❌ Error removing custom field '{field_name}': {str(e)}")
            frappe.db.rollback()
    else:
        print(f"ℹ️  Custom field '{field_name}' not found in {doctype} doctype, skipping")
