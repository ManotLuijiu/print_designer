#!/usr/bin/env python3

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def add_wht_rate_field():
    """Add the default WHT rate field to Company DocType"""
    
    # Check if field already exists
    if frappe.db.exists("Custom Field", {"dt": "Company", "fieldname": "default_wht_rate"}):
        print("✅ Company default_wht_rate field already exists")
        return True
    
    # Define the field
    wht_rate_field = {
        "Company": [
            {
                "fieldname": "default_wht_rate",
                "fieldtype": "Percent",
                "label": "Default WHT Rate (%)",
                "insert_after": "thailand_service_business",
                "depends_on": "eval:doc.thailand_service_business",
                "description": "Default withholding tax rate for services (e.g., 3% for most services)",
                "default": 3.0,
                "precision": 2,
            }
        ]
    }
    
    try:
        create_custom_fields(wht_rate_field, update=False)
        frappe.db.commit()
        print("✅ Company default_wht_rate field added successfully!")
        return True
    except Exception as e:
        print(f"❌ Error adding WHT rate field: {str(e)}")
        return False

if __name__ == "__main__":
    add_wht_rate_field()