#!/usr/bin/env python3
# Copyright (c) 2026, AWS Solution Ltd. and contributors
# For license information, please see license.txt
"""
Migrate existing Input VAT records to populate new fields.

This script:
1. Sets vat_type = "General" on existing Thai Purchase VAT records (that don't already have it)
2. Sets source_doctype = "Purchase Invoice" on existing Input VAT Undue records
3. Reports what was migrated

Run with:
    bench --site <site> execute print_designer.commands.migrate_input_vat_records.main
"""

import frappe


def main():
    frappe.init(sites_path="/home/frappe/frappe-bench/sites")
    site = frappe.utils.get_site_name(frappe.request.hostname) if frappe.request else None
    if not site:
        site = "inpac-pharma-v16.bunchee.online"
    frappe.init(site)
    frappe.connect()

    print("=" * 60)
    print("Input VAT Records Migration")
    print("=" * 60)

    migrated_tpv = 0
    migrated_iuv = 0

    # 1. Thai Purchase VAT — set vat_type = "General" where missing
    tpvs = frappe.db.sql(
        """
        SELECT name, purchase_invoice, vat_type
        FROM `tabThai Purchase VAT`
        WHERE (vat_type IS NULL OR vat_type = '')
        """,
        as_dict=True,
    )

    for tpv in tpvs:
        frappe.db.set_value(
            "Thai Purchase VAT", tpv.name, "vat_type", "General"
        )
        migrated_tpv += 1
        print(f"  [TPV] {tpv.name} | PI: {tpv.purchase_invoice} → vat_type = General")

    if migrated_tpv:
        frappe.db.commit()
        print(f"\nMigrated {migrated_tpv} Thai Purchase VAT records")

    # 2. Input VAT Undue — set source_doctype = "Purchase Invoice" where missing
    iuvs = frappe.db.sql(
        """
        SELECT name, purchase_invoice, source_doctype
        FROM `tabInput VAT Undue`
        WHERE (source_doctype IS NULL OR source_doctype = '')
        """,
        as_dict=True,
    )

    for iuv in iuvs:
        frappe.db.set_value(
            "Input VAT Undue", iuv.name, "source_doctype", "Purchase Invoice"
        )
        migrated_iuv += 1
        print(f"  [IUV] {iuv.name} | PI: {iuv.purchase_invoice} → source_doctype = Purchase Invoice")

    if migrated_iuv:
        frappe.db.commit()
        print(f"\nMigrated {migrated_iuv} Input VAT Undue records")

    # Summary
    total_tpv = frappe.db.count("Thai Purchase VAT")
    total_iuv = frappe.db.count("Input VAT Undue")

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Thai Purchase VAT total records: {total_tpv}")
    print(f"  Thai Purchase VAT migrated:   {migrated_tpv}")
    print(f"  Input VAT Undue total records: {total_iuv}")
    print(f"  Input VAT Undue migrated:      {migrated_iuv}")
    print("=" * 60)

    frappe.destroy()


if __name__ == "__main__":
    main()
