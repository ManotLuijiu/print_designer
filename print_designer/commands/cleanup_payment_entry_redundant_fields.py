#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cleanup Script to Remove Redundant Payment Entry Fields

This script removes redundant fields from Payment Entry that were replaced
with standard ERPNext party fields.

Run with: bench execute print_designer.commands.cleanup_payment_entry_redundant_fields.execute
"""

import frappe
from frappe import _


def execute():
    """Remove redundant fields from Payment Entry"""
    print("🧹 Starting cleanup of redundant Payment Entry fields...")

    # List of redundant fields to remove
    redundant_fields = [
        "pd_custom_supplier",  # Redundant with standard 'party' field
        "pd_custom_supplier_name",  # Redundant with standard 'party_name' field
        "pd_custom_get_invoices_from_purchase_billing",  # Unnecessary button with no implementation
    ]

    removed_count = 0

    for field in redundant_fields:
        if frappe.db.exists("Custom Field", {"dt": "Payment Entry", "fieldname": field}):
            try:
                frappe.delete_doc("Custom Field", f"Payment Entry-{field}", force=1)
                print(f"   ✅ Removed field: {field}")
                removed_count += 1
            except Exception as e:
                print(f"   ❌ Error removing {field}: {str(e)}")
        else:
            print(f"   ℹ️  Field {field} not found (already removed)")

    # Clear cache to ensure changes are reflected
    frappe.clear_cache()

    print(f"\n✅ Cleanup completed. Removed {removed_count} redundant fields.")
    print("\n📝 Summary of changes:")
    print("   - Removed pd_custom_supplier (use standard 'party' field instead)")
    print("   - Removed pd_custom_supplier_name (use standard 'party_name' field instead)")
    print("   - Removed pd_custom_get_invoices_from_purchase_billing button")
    print("\n💡 The Thai Tax Compliance tab now uses ERPNext's standard party fields.")

    return {
        "success": True,
        "removed_fields": removed_count,
        "message": f"Removed {removed_count} redundant fields from Payment Entry"
    }


def check_redundant_fields():
    """Check if redundant fields still exist in Payment Entry"""
    redundant_fields = [
        "pd_custom_supplier",
        "pd_custom_supplier_name",
        "pd_custom_get_invoices_from_purchase_billing",
    ]

    existing_redundant = []

    for field in redundant_fields:
        if frappe.db.exists("Custom Field", {"dt": "Payment Entry", "fieldname": field}):
            existing_redundant.append(field)

    if existing_redundant:
        print(f"⚠️  Found {len(existing_redundant)} redundant fields that should be removed:")
        for field in existing_redundant:
            print(f"   - {field}")
        return False
    else:
        print("✅ No redundant fields found. Payment Entry is clean.")
        return True


if __name__ == "__main__":
    execute()