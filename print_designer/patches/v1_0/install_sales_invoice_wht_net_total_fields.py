"""
Install the missing Sales Invoice WHT net total fields.
This patch ensures Sales Invoice has the same net total fields as Quotation.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def execute():
    """Install the missing Sales Invoice WHT net total fields"""
    
    print("Installing missing Sales Invoice WHT net total fields...")
    
    # Define the fields we need to add
    fields_to_add = [
        {
            "dt": "Sales Invoice",
            "fieldname": "net_total_after_wht",
            "label": "Net Total (After WHT)",
            "fieldtype": "Currency",
            "insert_after": "wht_certificate_required",
            "description": "Net total after adding VAT (7%) and deducting WHT",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht",
            "options": "Company:company:default_currency",
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "net_total_after_wht_in_words",
            "label": "Net Total (After WHT) in Words",
            "fieldtype": "Small Text",
            "insert_after": "net_total_after_wht",
            "description": "Net total amount in Thai words",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht && doc.net_total_after_wht",
        }
    ]
    
    for field_config in fields_to_add:
        fieldname = field_config["fieldname"]
        
        # Check if field already exists
        if frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": fieldname}):
            print(f"✅ Sales Invoice.{fieldname} already exists")
            continue
            
        try:
            create_custom_field("Sales Invoice", field_config)
            print(f"✅ Created Sales Invoice.{fieldname} field")
        except Exception as e:
            print(f"❌ Error creating {fieldname}: {e}")
            # Log but don't fail the patch
            frappe.log_error(f"Failed to create Sales Invoice.{fieldname}: {str(e)}", "WHT Fields Patch")
    
    # Commit changes
    frappe.db.commit()
    print("✅ Sales Invoice WHT net total fields installation completed")