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


# ─── Conditional Client Script (for non-Thai countries) ──────────────────
# Property Setters are static — they can't switch based on form values.
# To support addresses from non-Thailand countries (e.g., South Korea),
# we install a Client Script that conditionally switches labels at
# form load + on country change.
CONDITIONAL_SCRIPT_NAME = "Thai Address Field Labels (conditional)"

CONDITIONAL_SCRIPT_SOURCE = '''
frappe.ui.form.on("Address", {
    refresh(frm) {
        apply_thai_address_labels(frm);
    },
    country(frm) {
        apply_thai_address_labels(frm);
    }
});

function apply_thai_address_labels(frm) {
    const is_thailand = (frm.doc.country || "").trim() === "Thailand";
    const labels = is_thailand ? {
        city: "Sub-district",
        county: "District",
        state: "Province",
    } : {
        city: "City/Town",
        county: "County",
        state: "State/Province",
    };

    for (const [fieldname, label] of Object.entries(labels)) {
        if (!frm.fields_dict[fieldname]) {
            continue;
        }

        frm.set_df_property(fieldname, "label", label);
        frm.refresh_field(fieldname);
    }
}
'''


def install_address_field_conditional_script():
    """Install Client Script that switches labels based on country.

    For Thailand: Sub-district, District, Province.
    For other countries: City/Town, County, State/Province.

    Idempotent: skips if already installed.
    """
    existing = frappe.db.exists("Client Script", CONDITIONAL_SCRIPT_NAME)
    if existing:
        doc = frappe.get_doc("Client Script", existing)
        doc.dt = "Address"
        doc.enabled = 1
        doc.script = CONDITIONAL_SCRIPT_SOURCE
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        print("   ✓ Updated Client Script 'Thai Address Field Labels (conditional)'")
        return

    doc = frappe.new_doc("Client Script")
    doc.name = CONDITIONAL_SCRIPT_NAME
    doc.dt = "Address"
    doc.enabled = 1
    doc.script = CONDITIONAL_SCRIPT_SOURCE
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print("   ✓ Created Client Script 'Thai Address Field Labels (conditional)'")


def remove_address_field_conditional_script():
    """Remove the conditional Client Script (called from before_uninstall)."""
    if frappe.db.exists("Client Script", CONDITIONAL_SCRIPT_NAME):
        frappe.delete_doc("Client Script", CONDITIONAL_SCRIPT_NAME, ignore_permissions=True)
        print("   ✓ Removed Client Script 'Thai Address Field Labels (conditional)'")
    else:
        print("   · No Client Script to remove (skipped)")


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

    # Also install the conditional Client Script (switches labels
    # to English for non-Thailand addresses)
    install_address_field_conditional_script()


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

def remove_address_fields():
    """Remove Address field label overrides (called from before_uninstall).

    Mirror of install_address_fields() — removes the same Property
    Setters this module creates, so uninstalling Print Designer
    doesn't leave orphan label overrides on the host bench.
    Idempotent: if a Property Setter is already gone, the loop
    just skips it.
    """
    print("Removing Address field label overrides...")

    overrides = ("city", "county", "state")

    for fieldname in overrides:
        ps_name = frappe.db.get_value(
            "Property Setter",
            {
                "doc_type": "Address",
                "field_name": fieldname,
                "property": "label",
            },
            "name",
        )
        if ps_name:
            frappe.delete_doc("Property Setter", ps_name, ignore_permissions=True)
            print(f"   ✓ Removed Property Setter for Address.{fieldname}.label")
        else:
            print(f"   · No Property Setter for Address.{fieldname}.label (skipped)")

    # Also remove the conditional Client Script
    remove_address_field_conditional_script()

    frappe.clear_cache(doctype="Address")
    print("✅ Address field label overrides removed!")
