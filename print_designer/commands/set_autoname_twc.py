"""
Set autoname on Tax Withholding Category to use category_name field (Thai).

This makes new records auto-use Thai doc names like "ค่าบริการ 3% (ภงด.53)".
Run after bench migrate.

Usage:
    bench execute print_designer.commands.set_autoname_twc.set_autoname_twc
"""

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def set_autoname_twc():
    """Set autoname on Tax Withholding Category to field:category_name."""
    if not frappe.db.exists("DocType", "Tax Withholding Category"):
        print("Tax Withholding Category DocType not found")
        return

    current_autoname = frappe.db.get_value("DocType", "Tax Withholding Category", "autoname")
    if current_autoname == "field:category_name":
        print("Autoname already set to field:category_name")
        return

    make_property_setter(
        "Tax Withholding Category",
        "",
        "autoname",
        "field:category_name",
        "Data",
    )
    frappe.db.commit()
    print("✅ Set autoname to field:category_name on Tax Withholding Category")
