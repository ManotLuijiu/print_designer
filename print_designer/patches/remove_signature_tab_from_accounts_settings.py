import frappe


def execute():
    """Remove Signature tab from Accounts Settings"""
    
    # List of custom fields to remove
    signature_fields = [
        "signature_tab",
        "signature_settings_section", 
        "enable_signature_in_print",
        "default_signature_user",
        "signature_management_section",
        "signature_management_html"
    ]
    
    # Remove custom fields from Accounts Settings
    for field in signature_fields:
        try:
            custom_field_name = frappe.db.get_value("Custom Field", {"dt": "Accounts Settings", "fieldname": field}, "name")
            if custom_field_name:
                frappe.delete_doc("Custom Field", custom_field_name)
                print(f"✅ Removed custom field: {field}")
        except Exception as e:
            print(f"Warning: Could not remove field {field}: {e}")
    
    # Remove client script for Accounts Settings signature functionality
    try:
        client_scripts = frappe.get_all("Client Script", {"dt": "Accounts Settings"}, ["name"])
        for script in client_scripts:
            script_doc = frappe.get_doc("Client Script", script.name)
            if "signature" in script_doc.script.lower():
                frappe.delete_doc("Client Script", script.name)
                print(f"✅ Removed client script: {script.name}")
    except Exception as e:
        print(f"Warning: Could not remove client script: {e}")
    
    frappe.db.commit()
    print("✅ Signature tab removed from Accounts Settings")