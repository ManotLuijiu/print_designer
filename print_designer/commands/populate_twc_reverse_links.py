"""
Populate pd_custom_thai_wht_income_type on Tax Withholding Category
by reading tax_withholding_category from Thai WHT Income Type.
"""

import frappe


def populate_twc_reverse_links():
    """Populate TWC.pd_custom_thai_wht_income_type from TWI.tax_withholding_category."""
    if not frappe.db.exists("DocType", "Thai WHT Income Type"):
        print("Thai WHT Income Type DocType not found")
        return

    if not frappe.db.exists("Custom Field", "Tax Withholding Category-pd_custom_thai_wht_income_type"):
        print("pd_custom_thai_wht_income_type field not installed yet")
        return

    twi_list = frappe.get_all(
        "Thai WHT Income Type",
        fields=["name", "tax_withholding_category"]
    )

    updated = 0
    for twi in twi_list:
        if twi.tax_withholding_category:
            frappe.db.set_value(
                "Tax Withholding Category",
                twi.tax_withholding_category,
                "pd_custom_thai_wht_income_type",
                twi.name
            )
            updated += 1

    frappe.db.commit()
    print(f"Populated pd_custom_thai_wht_income_type on {updated} TWC records")


if __name__ != "__main__":
    populate_twc_reverse_links()
