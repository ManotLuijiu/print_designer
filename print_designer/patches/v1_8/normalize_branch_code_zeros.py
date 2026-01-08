#!/usr/bin/env python3
# Copyright (c) 2025, Hussain Nagaria and contributors
# For license information, please see license.txt

"""
Patch to normalize branch code values from '0' to '00000'.

Issue: Some records in production have pd_custom_branch_code = '0' instead of '00000'
This patch ensures all branch codes are properly formatted with 5 digits.

Thai Tax Compliance: '00000' is the standard head office branch code
"""

import frappe


def execute():
    """Normalize branch code values from '0' to '00000' for Customer and Supplier."""

    print("\n" + "=" * 80)
    print("NORMALIZING BRANCH CODES: '0' → '00000'")
    print("=" * 80 + "\n")

    customer_stats = normalize_branch_codes("Customer")
    supplier_stats = normalize_branch_codes("Supplier")

    print("\n" + "=" * 80)
    print("NORMALIZATION COMPLETE!")
    print(f"  Customers: {customer_stats['normalized']} records updated")
    print(f"  Suppliers: {supplier_stats['normalized']} records updated")
    print("=" * 80 + "\n")


def normalize_branch_codes(doctype):
    """
    Normalize branch code values for a specific DocType.

    Changes '0' to '00000' for Thai tax compliance.

    Args:
        doctype: "Customer" or "Supplier"

    Returns:
        dict: Normalization statistics
    """
    table_name = f"tab{doctype}"
    stats = {"normalized": 0, "skipped": 0, "errors": 0}

    print(f"📋 Normalizing {doctype} branch codes...")

    # Check if pd_custom_branch_code field exists
    try:
        frappe.db.sql(f"SELECT pd_custom_branch_code FROM `{table_name}` LIMIT 1")
    except Exception:
        print(f"   ⚠️  Field pd_custom_branch_code doesn't exist in {doctype} - skipping")
        return stats

    # Find all records with '0' instead of '00000'
    # Also handle any other single-digit or incomplete branch codes
    records_to_normalize = frappe.db.sql(f"""
        SELECT name, pd_custom_branch_code
        FROM `{table_name}`
        WHERE pd_custom_branch_code IS NOT NULL
        AND pd_custom_branch_code != ''
        AND pd_custom_branch_code != '00000'
        AND (
            pd_custom_branch_code = '0'
            OR LENGTH(pd_custom_branch_code) < 5
        )
    """, as_dict=True)

    if not records_to_normalize:
        print(f"   ✅ No records need normalization in {doctype}")
        return stats

    print(f"   🔄 Normalizing {len(records_to_normalize)} {doctype} record(s)...\n")

    for record in records_to_normalize:
        try:
            old_value = record.pd_custom_branch_code

            # Normalize to 5-digit format
            # '0' → '00000'
            # '1' → '00001'
            # '123' → '00123'
            if old_value.isdigit():
                new_value = old_value.zfill(5)  # Pad with zeros to make 5 digits
            else:
                # If not pure numeric, set to default head office code
                new_value = '00000'

            # Update the value
            frappe.db.set_value(
                doctype,
                record.name,
                "pd_custom_branch_code",
                new_value,
                update_modified=False
            )

            print(f"      ✓ {record.name}: '{old_value}' → '{new_value}'")
            stats["normalized"] += 1

        except Exception as e:
            print(f"      ✗ {record.name}: Normalization failed - {str(e)}")
            stats["errors"] += 1

    frappe.db.commit()

    print(f"\n   📊 {doctype} Summary: {stats['normalized']} normalized, {stats['errors']} errors")
    return stats
