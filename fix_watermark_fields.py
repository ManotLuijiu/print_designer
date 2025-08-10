#!/usr/bin/env python3
"""
Emergency fix for watermark fields installation
This script installs the watermark_text field for Stock Entry and other DocTypes
"""

import sys
import os

# Add the frappe-bench path so we can import frappe
sys.path.insert(0, '/home/frappe/frappe-bench')

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def fix_watermark_fields():
    """Install watermark fields directly"""
    
    # Initialize frappe for the site
    frappe.init('tipsiricons.bunchee.online')
    frappe.connect()
    
    try:
        # Import watermark fields definition
        from print_designer.watermark_fields import get_watermark_custom_fields
        
        # Get all watermark fields
        custom_fields = get_watermark_custom_fields()
        
        print(f"Installing watermark fields for {len(custom_fields)} DocTypes...")
        
        # Install the custom fields
        create_custom_fields(custom_fields, update=True)
        
        # Commit the changes
        frappe.db.commit()
        
        print("✅ Watermark fields installed successfully!")
        print("✅ Stock Entry watermark_text field should now be available")
        
        # Verify Stock Entry field was created
        if frappe.db.sql("SHOW COLUMNS FROM `tabStock Entry` LIKE 'watermark_text'"):
            print("✅ Confirmed: watermark_text column exists in Stock Entry table")
        else:
            print("❌ Warning: watermark_text column not found in Stock Entry table")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        frappe.db.rollback()
        return False
    
    finally:
        frappe.destroy()
    
    return True

if __name__ == "__main__":
    success = fix_watermark_fields()
    sys.exit(0 if success else 1)