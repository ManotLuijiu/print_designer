"""
Migrate pd_custom_wht_income_type field from Thai WHT Income Type to Tax Withholding Category

This script updates the custom field definition in the database.
Run this to apply the field type change after updating the installation scripts.
"""

import frappe


def migrate_wht_income_type_field_options():
    """
    Update pd_custom_wht_income_type field options from Thai WHT Income Type to Tax Withholding Category
    across all doctypes that use this field.
    """
    doctypes = [
        "Payment Entry",
        "Purchase Invoice",
        "Sales Invoice",
        "Sales Order",
        "Purchase Order",
        "Quotation",
        "Item",
    ]
    
    for dt in doctypes:
        field_name = f"{dt}-pd_custom_wht_income_type"
        if frappe.db.exists("Custom Field", field_name):
            current_options = frappe.db.get_value("Custom Field", field_name, "options")
            if current_options == "Thai WHT Income Type":
                frappe.db.set_value("Custom Field", field_name, "options", "Tax Withholding Category")
                print(f"✅ Updated {dt}.pd_custom_wht_income_type: Thai WHT Income Type → Tax Withholding Category")
            else:
                print(f"⏭️ {dt}.pd_custom_wht_income_type already has options: {current_options}")
        else:
            print(f"⚠️ Field not found: {field_name}")
    
    frappe.db.commit()
    print("\n✅ Migration complete! Clear cache and test.")


def execute():
    print("Starting pd_custom_wht_income_type field migration...")
    print("Changing from: Thai WHT Income Type")
    print("Changing to: Tax Withholding Category")
    print("-" * 50)
    migrate_wht_income_type_field_options()


if __name__ == "__main__":
    execute()