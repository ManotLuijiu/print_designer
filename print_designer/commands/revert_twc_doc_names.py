"""
Rollback: Revert Tax Withholding Category doc names from Thai to English.

Usage:
    bench execute print_designer.commands.revert_twc_doc_names.revert_twc_doc_names
"""

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def _build_english_name(income_category, rate, recipient_type, form_type):
    """Rebuild English TWC name (reverse of build_twc_name logic)."""
    name_map = {
        "Rental Income": "Rental",
        "Rental Income (Ship Lease)": "Rental Ship Lease",
        "Professional Services": "Professional Services",
        "Services Income": "Services",
        "Prize & Awards": "Prizes Awards",
        "Entertainment Income": "Entertainment",
        "Advertising Income": "Advertising",
        "Service Fees": "Service Fees",
        "Transport Fees": "Transport",
        "Sales Promotion Income": "Sales Promotion",
        "Commission & Royalties": "Commission Royalties",
        "Interest Income": "Interest",
        "Bond Interest": "Bond Interest",
        "Dividend Income": "Dividend",
        "Ship Rental": "Ship Rental",
        "Contracting Services": "Contracting",
        "Foreign Contractor Fees": "Foreign Contractor",
        "Insurance Premiums": "Insurance Premiums",
        "Agricultural Trading Income": "Agricultural",
    }
    short_name = name_map.get(income_category, income_category)
    recipient_suffix = "Individual" if recipient_type == "Individual" else "Corporate"
    return f"WHT {rate:.0f}% {short_name} - {recipient_suffix} ({form_type})"


def revert_twc_autoname():
    """Revert autoname back to Prompt."""
    make_property_setter(
        "Tax Withholding Category",
        "",
        "autoname",
        "Prompt",
        "Data",
    )
    frappe.db.commit()
    print("Reverted Tax Withholding Category autoname to Prompt")


def revert_twc_doc_names():
    """
    Revert TWC doc names from Thai back to English.
    Requires: autoname must be "Prompt" first (so we can set English names manually).
    """
    # Revert autoname first so we can rename
    revert_twc_autoname()

    # Get all TWCs with their English name info
    # We need to reconstruct English names — get from Thai WHT Income Type reverse lookup
    twcs = frappe.get_all(
        "Tax Withholding Category",
        fields=["name", "pd_custom_thai_wht_income_type"]
    )

    # Get Thai WHT Income Type data for reverse lookup
    thai_wht_map = {
        r.name: r
        for r in frappe.get_all(
            "Thai WHT Income Type",
            fields=["name", "form_type", "recipient_type", "income_category", "tax_rate"]
        )
    }

    renamed = skipped = failed = 0
    for twc in twcs:
        thai_wht = thai_wht_map.get(twc.pd_custom_thai_wht_income_type) if twc.pd_custom_thai_wht_income_type else None
        if not thai_wht:
            skipped += 1
            continue

        english_name = _build_english_name(
            thai_wht.income_category,
            thai_wht.tax_rate,
            thai_wht.recipient_type,
            thai_wht.form_type,
        )

        if twc.name == english_name:
            skipped += 1
            continue

        try:
            frappe.rename_doc("Tax Withholding Category", twc.name, english_name, force=True)
            renamed += 1
            print(f"  Reverted: {twc.name} → {english_name}")
        except Exception as e:
            failed += 1
            print(f"  Failed: {twc.name} → {english_name}: {e}")

    frappe.db.commit()
    print(f"\nRollback complete:")
    print(f"  Reverted: {renamed}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed: {failed}")
