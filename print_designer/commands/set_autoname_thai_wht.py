"""
Set autoname on Thai WHT Income Type to use income_category_th field (Thai).

This makes new records auto-use Thai doc names like "PND3-ค่าโฆษณา".
Run after bench migrate.

Usage:
    bench execute print_designer.commands.set_autoname_thai_wht.set_autoname_thai_wht
"""

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def set_autoname_thai_wht():
    """Set autoname on Thai WHT Income Type to field:income_category_th."""
    if not frappe.db.exists("DocType", "Thai WHT Income Type"):
        print("Thai WHT Income Type DocType not found")
        return

    current_autoname = frappe.db.get_value("DocType", "Thai WHT Income Type", "autoname")
    if current_autoname == "field:income_category_th":
        print("Autoname already set to field:income_category_th")
        return

    make_property_setter(
        "Thai WHT Income Type",
        "",
        "autoname",
        "field:income_category_th",
        "Data",
    )
    frappe.db.commit()
    print("✅ Set autoname to field:income_category_th on Thai WHT Income Type")
