"""
Force Installation of Construction Service Field

This patch addresses a critical production issue where the construction_service field
was not being installed due to a missing emergency_fallback function in hooks.py.

The hooks.py was calling 'emergency_fallback_install_enhanced_retention_fields' 
but this function didn't exist, causing the construction_service field to never be installed.

This patch ensures the field is properly installed in production.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Force install construction service field and related enhanced retention fields."""
    
    print("🚨 CRITICAL PATCH: Force Installing Construction Service Field...")
    
    try:
        # Check if construction_service field already exists
        company_meta = frappe.get_meta("Company")
        construction_service_field = company_meta.get_field("construction_service")
        
        if construction_service_field:
            print("✅ construction_service field already exists - patch not needed")
            return
            
        print("❌ construction_service field missing - installing now...")
        
        # Define the construction service fields
        custom_fields = {
            "Company": [
                {
                    "fieldname": "construction_service",
                    "label": "Enable Construction Service",
                    "fieldtype": "Check",
                    "insert_after": "country",
                    "description": "Enable construction service features including retention calculations",
                    "default": 0,
                },
                {
                    "fieldname": "default_retention_rate",
                    "fieldtype": "Percent",
                    "label": "Default Retention Rate (%)",
                    "insert_after": "construction_service",
                    "depends_on": "eval:doc.construction_service",
                    "description": "Default retention rate for construction projects (e.g., 5% for most projects)",
                    "default": 5.0,
                    "precision": 2,
                },
                {
                    "fieldname": "default_retention_account",
                    "fieldtype": "Link",
                    "label": "Default Retention Account",
                    "options": "Account",
                    "insert_after": "default_retention_rate",
                    "depends_on": "eval:doc.construction_service",
                    "description": "Default account for retention liability (e.g., Construction Retention Payable)",
                }
            ]
        }
        
        # Install the custom fields with version tracking disabled to avoid formatting errors
        frappe.flags.ignore_version = True
        create_custom_fields(custom_fields, update=True)
        frappe.flags.ignore_version = False
        
        print("✅ Construction service fields installed successfully!")
        print("   - Company: construction_service (checkbox)")  
        print("   - Company: default_retention_rate (percentage)")
        print("   - Company: default_retention_account (link to Account)")
        
        # Commit the changes
        frappe.db.commit()
        
        # Clear cache to ensure fields are visible
        frappe.clear_cache()
        frappe.clear_cache(doctype="Company")
        
        print("✅ PATCH COMPLETED: Construction service field is now available!")
        print("   You should now see the 'Enable Construction Service' checkbox in Company settings")
        
    except Exception as e:
        print(f"❌ PATCH FAILED: {str(e)}")
        frappe.log_error(
            message=f"Failed to install construction service field: {str(e)}",
            title="Construction Service Field Installation Failed"
        )
        frappe.db.rollback()
        raise


if __name__ == "__main__":
    execute()