"""
Address Field Label Override for Thai Localization

Overrides default Address doctype field labels to use clearer English terms.
Frappe handles Thai translation automatically via the translation system.

Labels:
  - city    → Sub-district (ตำบล/แขวง)
  - county  → District (อำเภอ/เขต)
  - state   → Province (จังหวัด)
"""

import frappe


def _set_property_setter(doctype, fieldname, property_name, value, property_type):
    """
    Helper to create or update a Property Setter.
    Checks if exists, updates if present, creates if new.
    """
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter

    existing = frappe.db.exists(
        "Property Setter",
        {
            "doc_type": doctype,
            "field_name": fieldname,
            "property": property_name,
        },
    )

    if existing:
        frappe.db.set_value("Property Setter", existing, "value", value)
        print(f"   ✓ Updated {doctype}.{fieldname}.{property_name} = '{value}'")
    else:
        make_property_setter(
            doctype=doctype,
            fieldname=fieldname,
            property=property_name,
            value=value,
            property_type=property_type,
            for_doctype=False,
        )
        print(f"   ✓ Created {doctype}.{fieldname}.{property_name} = '{value}'")


def install_address_fields():
    """
    Install Address doctype field label overrides for Thai localization.

    Maps standard Address fields to Thai-appropriate English labels:
    - city    → Sub-district
    - county  → District
    - state   → Province

    These labels make it clear what Thai administrative level each field represents.
    """
    print("Installing Address field label overrides...")

    overrides = [
        ("city", "Sub-district"),
        ("county", "District"),
        ("state", "Province"),
    ]

    for fieldname, label in overrides:
        _set_property_setter("Address", fieldname, "label", label, "Data")

    frappe.clear_cache(doctype="Address")
    print("✅ Address field label overrides installed!")


def check_address_fields():
    """
    Verify Address field label overrides are installed correctly.
    """
    print("Checking Address field label overrides...")

    overrides = [
        ("city", "Sub-district"),
        ("county", "District"),
        ("state", "Province"),
    ]

    all_present = True
    for fieldname, expected_label in overrides:
        ps = frappe.db.get_value(
            "Property Setter",
            {
                "doc_type": "Address",
                "field_name": fieldname,
                "property": "label",
            },
            ["name", "value"],
            as_dict=True,
        )

        if ps:
            status = "✓" if ps.value == expected_label else "✗"
            print(f"   {status} {fieldname}: '{ps.value}' (expected: '{expected_label}')")
            if ps.value != expected_label:
                all_present = False
        else:
            print(f"   ✗ {fieldname}: Not installed")
            all_present = False

    if all_present:
        print("✅ All Address field label overrides are correctly installed!")
        return True
    else:
        print("❌ Some Address field label overrides need attention.")
        return False