#!/usr/bin/env python3
"""
Install Delivery Note Custom Fields for QR Approval System
This script ensures all required custom fields are properly installed
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from print_designer.print_designer.custom_fields import DELIVERY_NOTE_CUSTOM_FIELDS

def install_delivery_note_fields():
    """Install all delivery note custom fields for QR approval system"""
    
    print("Installing Delivery Note custom fields...")
    
    try:
        # Create custom fields using Frappe's built-in method
        create_custom_fields(DELIVERY_NOTE_CUSTOM_FIELDS)
        
        frappe.db.commit()
        print("✅ All Delivery Note custom fields installed successfully!")
        
        # Verify installation
        verify_fields()
        
        return {"success": True, "message": "Delivery Note custom fields installed successfully"}
        
    except Exception as e:
        print(f"❌ Error installing custom fields: {str(e)}")
        frappe.log_error(f"Error installing delivery note fields: {str(e)}")
        return {"success": False, "error": str(e)}

def verify_fields():
    """Verify that all required fields are installed"""
    
    required_fields = [
        "customer_approval_status",
        "customer_signature", 
        "customer_approved_by",
        "customer_approved_on",
        "approval_qr_code"
    ]
    
    print("\nVerifying field installation...")
    
    for fieldname in required_fields:
        exists = frappe.db.exists("Custom Field", {
            "dt": "Delivery Note",
            "fieldname": fieldname
        })
        
        if exists:
            print(f"✅ {fieldname} - Installed")
        else:
            print(f"❌ {fieldname} - Missing")
    
    print("\nField verification complete!")

def remove_delivery_note_fields():
    """Remove all delivery note custom fields (for cleanup if needed)"""
    
    print("Removing Delivery Note custom fields...")
    
    try:
        all_fields = []
        for doctype_fields in DELIVERY_NOTE_CUSTOM_FIELDS.values():
            for field in doctype_fields:
                all_fields.append(field["fieldname"])
        
        for fieldname in all_fields:
            if frappe.db.exists("Custom Field", {"dt": "Delivery Note", "fieldname": fieldname}):
                frappe.delete_doc("Custom Field", 
                    frappe.db.get_value("Custom Field", {"dt": "Delivery Note", "fieldname": fieldname}))
                print(f"Removed field: {fieldname}")
        
        frappe.db.commit()
        print("✅ All Delivery Note custom fields removed successfully!")
        
        return {"success": True, "message": "Delivery Note custom fields removed successfully"}
        
    except Exception as e:
        print(f"❌ Error removing custom fields: {str(e)}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    install_delivery_note_fields()