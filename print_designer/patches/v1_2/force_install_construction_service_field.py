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
        
        # Install the custom fields with version tracking completely disabled to avoid formatting errors
        original_flags = {}
        flags_to_set = {
            'ignore_version': True,
            'ignore_validate': True,
            'ignore_permissions': True,
            'ignore_links': True
        }
        
        # Save original flag values and set new ones
        for flag, value in flags_to_set.items():
            original_flags[flag] = getattr(frappe.flags, flag, False)
            setattr(frappe.flags, flag, value)
        
        try:
            # Create fields one by one to better handle errors
            for doctype, fields in custom_fields.items():
                for field_config in fields:
                    # Check if field already exists
                    existing_field = frappe.get_value("Custom Field", 
                        {"dt": doctype, "fieldname": field_config["fieldname"]})
                    
                    if existing_field:
                        print(f"   Field {field_config['fieldname']} already exists - skipping")
                        continue
                    
                    # Create the custom field document
                    custom_field = frappe.new_doc("Custom Field")
                    custom_field.dt = doctype
                    
                    # Set field properties, ensuring all values are proper types
                    for key, value in field_config.items():
                        if key == 'default' and isinstance(value, (int, float)):
                            # Ensure numeric defaults are properly handled
                            custom_field.set(key, value)
                        elif isinstance(value, str) and value.strip() == '':
                            # Handle empty strings
                            custom_field.set(key, None)
                        else:
                            custom_field.set(key, value)
                    
                    # Save without version tracking
                    custom_field.insert(ignore_permissions=True)
                    print(f"   Created field: {field_config['fieldname']}")
        
        finally:
            # Restore original flag values
            for flag, original_value in original_flags.items():
                setattr(frappe.flags, flag, original_value)
        
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