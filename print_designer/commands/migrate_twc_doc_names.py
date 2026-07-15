"""
Migrate Tax Withholding Category doc names from English to Thai.

1. Delete orphan "Services 3%" TWC (legacy record, no category_name, no Thai WHT Income Type link)
2. Rename all TWCs: English doc name → category_name (Thai)

category_name is already unique across all TWCs (rate + PND form differentiates them).

Frappe rename_doc() handles all cascade updates automatically:
- Thai WHT Income Type.tax_withholding_category (reverse link)
- All Link field values on Item, Customer, Supplier, Payment Entry, etc.
- tabCustom Field options, tabProperty Setter, etc.

Usage:
    bench execute print_designer.commands.migrate_twc_doc_names.migrate_twc_doc_names
"""

import frappe


def delete_orphan_twc():
    """Delete orphan 'Services 3%' TWC (legacy record, no links)."""
    orphan_name = "Services 3%"
    if frappe.db.exists("Tax Withholding Category", orphan_name):
        frappe.delete_doc("Tax Withholding Category", orphan_name)
        print(f"  Deleted orphan TWC: {orphan_name}")


def migrate_twc_doc_names():
    """
    One-time migration: rename TWC records to use category_name (Thai).
    """
    if not frappe.db.exists("DocType", "Tax Withholding Category"):
        print("Tax Withholding Category DocType not found")
        return

    # Step 1: Delete orphan
    print("Step 1: Deleting orphan TWC...")
    delete_orphan_twc()
    frappe.db.commit()

    # Step 2: Rename TWCs
    twcs = frappe.get_all(
        "Tax Withholding Category",
        fields=["name", "category_name"]
    )

    renamed = skipped = failed = 0
    for twc in twcs:
        if not twc.category_name:
            skipped += 1
            print(f"  Skipped (no category_name): {twc.name}")
            continue

        if twc.name == twc.category_name:
            skipped += 1
            continue

        try:
            frappe.rename_doc("Tax Withholding Category", twc.name, twc.category_name, force=True)
            renamed += 1
            print(f"  Renamed: {twc.name} → {twc.category_name}")
        except Exception as e:
            failed += 1
            print(f"  Failed: {twc.name} → {twc.category_name}: {e}")

    frappe.db.commit()
    print(f"\nMigration complete:")
    print(f"  Renamed: {renamed}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed: {failed}")
