"""
Migrate Thai WHT Income Type doc names from English to Thai.

Renames: "{form_type}-{income_category}"  →  "{form_type}-{income_category_th}"
e.g., "PND3-Prize & Awards" → "PND3-รางวัล/ชิงโชค"

Frappe rename_doc() handles all cascade updates automatically:
- Tax Withholding Category.tax_withholding_category (reverse link)
- All Link field values on Item, Customer, Supplier, Payment Entry, etc.
- tabCustom Field options, tabProperty Setter, etc.

Usage:
    bench execute print_designer.commands.migrate_thai_wht_doc_names.migrate_thai_wht_doc_names
"""

import frappe


FORM_TYPE_TH = {
    "PND3": "ภงด.3",
    "PND53": "ภงด.53",
}


def migrate_thai_wht_doc_names():
    """
    One-time migration: rename Thai WHT Income Type records to use income_category_th.
    """
    if not frappe.db.exists("DocType", "Thai WHT Income Type"):
        print("Thai WHT Income Type DocType not found")
        return

    records = frappe.get_all(
        "Thai WHT Income Type",
        fields=["name", "form_type", "income_category", "income_category_th"]
    )

    renamed = skipped = failed = 0
    for rec in records:
        old_name = rec.name
        # Use Thai form type prefix (ภงด.3 / ภงด.53) instead of English (PND3 / PND53)
        form_th = FORM_TYPE_TH.get(rec.form_type, rec.form_type)
        new_name = f"{form_th}-{rec.income_category_th}"

        if old_name == new_name or old_name.startswith("ภงด."):
            skipped += 1
            continue

        try:
            frappe.rename_doc("Thai WHT Income Type", old_name, new_name, force=True)
            renamed += 1
            print(f"  Renamed: {old_name} → {new_name}")
        except Exception as e:
            failed += 1
            print(f"  Failed: {old_name} → {new_name}: {e}")

    frappe.db.commit()
    print(f"\nMigration complete:")
    print(f"  Renamed: {renamed}")
    print(f"  Skipped (already Thai): {skipped}")
    print(f"  Failed: {failed}")
