"""
Check if the custom field exists
"""

import frappe

@frappe.whitelist()
def check_custom_field():
    """Check if the add_comment_info field exists"""
    
    try:
        field_exists = frappe.db.get_value(
            'Custom Field', 
            {'dt': 'Print Format', 'fieldname': 'add_comment_info'}, 
            'name'
        )
        
        return {
            "status": "success",
            "field_exists": bool(field_exists),
            "field_name": field_exists,
            "message": f"Custom field 'add_comment_info' {'exists' if field_exists else 'does not exist'}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking custom field: {str(e)}"
        }

@frappe.whitelist()
def create_custom_field():
    """Create the missing custom field"""
    
    try:
        # Check if field already exists
        field_exists = frappe.db.get_value(
            'Custom Field', 
            {'dt': 'Print Format', 'fieldname': 'add_comment_info'}, 
            'name'
        )
        
        if field_exists:
            return {
                "status": "info",
                "message": f"Custom field already exists: {field_exists}"
            }
        
        # Create the custom field
        from frappe.custom.doctype.custom_field.custom_field import create_custom_field
        
        field_dict = {
            "dt": "Print Format",
            "fieldname": "add_comment_info",
            "fieldtype": "Check",
            "label": "Add Comment",
            "description": "Add printed as comment in document activity",
            "insert_after": "disabled"
        }
        
        create_custom_field("Print Format", field_dict)
        
        return {
            "status": "success",
            "message": "Custom field 'add_comment_info' created successfully"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error creating custom field: {str(e)}"
        }