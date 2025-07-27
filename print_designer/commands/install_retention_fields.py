"""
Install Retention Fields for Construction Services

Creates custom fields for retention calculation when construction service is enabled.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install_retention_fields():
    """Install custom fields for retention calculation system."""
    
    print("Installing Retention Fields for Construction Services...")
    
    # Define custom fields
    custom_fields = {
        "Company": [
            {
                "fieldname": "construction_service",
                "label": "Enable Construction Service",
                "fieldtype": "Check",
                "insert_after": "country",
                "description": "Enable construction service features including retention calculations",
                "default": 0,
            }
        ],
        "Sales Invoice": [
            {
                "fieldname": "retention_section",
                "label": "Retention Details",
                "fieldtype": "Section Break",
                "insert_after": "taxes_and_charges",
                "depends_on": "eval:doc.company && frappe.db.get_value('Company', doc.company, 'construction_service')",
                "collapsible": 1,
            },
            {
                "fieldname": "custom_retention",
                "label": "Retention %",
                "fieldtype": "Percent",
                "insert_after": "retention_section",
                "description": "Retention percentage to be withheld from payment",
                "depends_on": "eval:doc.company && frappe.db.get_value('Company', doc.company, 'construction_service')",
                "precision": 2,
            },
            {
                "fieldname": "custom_retention_amount",
                "label": "Retention Amount",
                "fieldtype": "Currency",
                "insert_after": "custom_retention",
                "description": "Calculated retention amount",
                "read_only": 1,
                "depends_on": "eval:doc.company && frappe.db.get_value('Company', doc.company, 'construction_service')",
                "options": "Company:company:default_currency",
            },
        ],
    }
    
    try:
        # Create custom fields
        create_custom_fields(custom_fields, update=True)
        
        print("✅ Custom fields created successfully!")
        print("   - Company: construction_service (checkbox)")
        print("   - Sales Invoice: custom_retention (percentage)")
        print("   - Sales Invoice: custom_retention_amount (currency)")
        
        # Set up user defaults mechanism
        print("\n🔧 Setting up conditional field visibility...")
        
        frappe.db.commit()
        print("✅ Retention fields installation completed!")
        
    except Exception as e:
        print(f"❌ Error installing retention fields: {str(e)}")
        frappe.db.rollback()
        raise


def check_retention_fields():
    """Check if retention fields are properly installed."""
    
    print("Checking Retention Fields Installation...")
    
    # Check Company field
    company_field = frappe.get_meta("Company").get_field("construction_service")
    if company_field:
        print("✅ Company.construction_service field found")
    else:
        print("❌ Company.construction_service field missing")
    
    # Check Sales Invoice fields
    si_meta = frappe.get_meta("Sales Invoice")
    
    retention_field = si_meta.get_field("custom_retention")
    if retention_field:
        print("✅ Sales Invoice.custom_retention field found")
    else:
        print("❌ Sales Invoice.custom_retention field missing")
    
    retention_amount_field = si_meta.get_field("custom_retention_amount")
    if retention_amount_field:
        print("✅ Sales Invoice.custom_retention_amount field found")
    else:
        print("❌ Sales Invoice.custom_retention_amount field missing")
    
    return bool(company_field and retention_field and retention_amount_field)


if __name__ == "__main__":
    install_retention_fields()