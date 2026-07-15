"""
Rollback: Revert Thai WHT Income Type doc names from Thai to English.

Usage:
    bench execute print_designer.commands.revert_thai_wht_doc_names.revert_thai_wht_doc_names
"""

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def revert_thai_wht_autoname():
    """Revert autoname back to Prompt."""
    make_property_setter(
        "Thai WHT Income Type",
        "",
        "autoname",
        "Prompt",
        "Data",
    )
    frappe.db.commit()
    print("Reverted Thai WHT Income Type autoname to Prompt")


def revert_thai_wht_doc_names():
    """
    Revert Thai WHT Income Type doc names from Thai back to English.
    Requires: autoname must be "Prompt" first (so we can set English names manually).
    """
    # Revert autoname first so we can rename
    revert_thai_wht_autoname()

    records = frappe.get_all(
        "Thai WHT Income Type",
        fields=["name", "form_type", "income_category"]
    )

    renamed = skipped = failed = 0
    for rec in records:
        english_name = f"{rec.form_type}-{rec.income_category}"

        if rec.name == english_name:
            skipped += 1
            continue

        try:
            frappe.rename_doc("Thai WHT Income Type", rec.name, english_name, force=True)
            renamed += 1
            print(f"  Reverted: {rec.name} → {english_name}")
        except Exception as e:
            failed += 1
            print(f"  Failed: {rec.name} → {english_name}: {e}")

    frappe.db.commit()
    print(f"\nRollback complete:")
    print(f"  Reverted: {renamed}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed: {failed}")
