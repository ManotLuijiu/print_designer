"""Hide company currency taxes fields in Purchase Order via Property Setter."""

import frappe


def execute():
    """Set print_hide=1 on company currency taxes fields to avoid duplicate label display."""

    # Fields to hide (company currency)
    fields_to_hide = [
        "base_taxes_and_charges_added",
        "base_taxes_and_charges_deducted",
        "base_total_taxes_and_charges",
    ]

    doctype = "Purchase Order"

    for fieldname in fields_to_hide:
        existing = frappe.db.exists(
            "Property Setter",
            {"doc_type": doctype, "field_name": fieldname, "property": "print_hide"}
        )

        if existing:
            frappe.db.set_value("Property Setter", existing, "value", "1")
            print(f"Updated: {doctype}.{fieldname} print_hide = 1")
        else:
            prop = frappe.new_doc("Property Setter")
            prop.doctype_or_field = "DocField"
            prop.doc_type = doctype
            prop.field_name = fieldname
            prop.property = "print_hide"
            prop.property_type = "Check"
            prop.value = "1"
            prop.insert()
            print(f"Created: {doctype}.{fieldname} print_hide = 1")

    frappe.clear_cache(doctype=doctype)
    print("\n✅ Purchase Order taxes fields updated successfully")
    print("   Hidden: base_taxes_and_charges_added, base_taxes_and_charges_deducted, base_total_taxes_and_charges")
    print("   Only document currency fields will show: taxes_and_charges_added, taxes_and_charges_deducted, total_taxes_and_charges")


def uninstall():
    """Remove property setters (cleanup on app uninstall)."""
    doctype = "Purchase Order"

    fields_to_unhide = [
        "base_taxes_and_charges_added",
        "base_taxes_and_charges_deducted",
        "base_total_taxes_and_charges",
    ]

    for fieldname in fields_to_unhide:
        existing = frappe.db.exists(
            "Property Setter",
            {"doc_type": doctype, "field_name": fieldname, "property": "print_hide"}
        )
        if existing:
            frappe.delete_doc("Property Setter", existing, force=True)
            print(f"Removed: {doctype}.{fieldname} print_hide setter")

    frappe.clear_cache(doctype=doctype)
    print("\n✅ Property setters removed")