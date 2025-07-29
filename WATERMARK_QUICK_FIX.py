#!/usr/bin/env python3
"""
Quick fix script for watermark per page not showing issue
Run this script to install the essential watermark_settings field
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def fix_watermark_sidebar():
    """Fix the missing watermark per page sidebar issue"""
    
    print("🔧 Starting watermark sidebar fix...")
    
    # Initialize frappe
    try:
        frappe.init(site="erpnext-dev-server.bunchee.online")
        frappe.connect()
        print("✅ Connected to site")
    except Exception as e:
        print(f"❌ Failed to connect to site: {e}")
        return False
    
    # Step 1: Remove conflicting fields
    print("\n📋 Step 1: Checking for conflicting fields...")
    try:
        conflicting_fields = frappe.get_all("Custom Field", 
            filters={
                "dt": "Print Settings", 
                "fieldname": ["in", ["watermark_font_size", "watermark_position", "watermark_font_family"]]
            },
            fields=["name", "fieldname", "fieldtype"]
        )
        
        for field in conflicting_fields:
            if field.fieldtype == "Data" and field.fieldname == "watermark_font_size":
                print(f"🗑️  Removing conflicting field: {field.fieldname} ({field.fieldtype})")
                frappe.delete_doc("Custom Field", field.name)
        
        print(f"✅ Checked {len(conflicting_fields)} existing fields")
    except Exception as e:
        print(f"⚠️  Warning: Could not check conflicting fields: {e}")
    
    # Step 2: Install essential fields
    print("\n📋 Step 2: Installing essential watermark fields...")
    
    essential_fields = {
        "Print Settings": [
            {
                "fieldname": "watermark_settings_section",
                "fieldtype": "Section Break",
                "label": "Watermark Settings",
                "insert_after": "print_taxes_with_zero_amount",
                "collapsible": 1,
            },
            {
                "fieldname": "watermark_settings",
                "fieldtype": "Select",
                "label": "Watermark per Page",
                "options": "None\\nOriginal on First Page\\nCopy on All Pages\\nOriginal,Copy on Sequence",
                "default": "None",
                "insert_after": "watermark_settings_section",
                "description": "Control watermark display: None=no watermarks, Original on First Page=first page shows 'Original', Copy on All Pages=all pages show 'Copy', Original,Copy on Sequence=pages alternate between 'Original' and 'Copy'",
            },
            {
                "fieldname": "watermark_font_size",
                "fieldtype": "Int",
                "label": "Watermark Font Size (px)",
                "default": 24,
                "insert_after": "watermark_settings",
                "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
            },
            {
                "fieldname": "watermark_position",
                "fieldtype": "Select",
                "label": "Watermark Position", 
                "options": "Top Left\\nTop Center\\nTop Right\\nMiddle Left\\nMiddle Center\\nMiddle Right\\nBottom Left\\nBottom Center\\nBottom Right",
                "default": "Top Right",
                "insert_after": "watermark_font_size",
                "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
            },
            {
                "fieldname": "watermark_font_family",
                "fieldtype": "Select",
                "label": "Watermark Font Family",
                "options": "Arial\\nHelvetica\\nTimes New Roman\\nCourier New\\nVerdana\\nGeorgia\\nTahoma\\nCalibri\\nSarabun",
                "default": "Sarabun", 
                "insert_after": "watermark_position",
                "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
            },
        ]
    }
    
    try:
        create_custom_fields(essential_fields, update=True)
        print("✅ Custom fields installed successfully")
    except Exception as e:
        print(f"❌ Failed to install custom fields: {e}")
        return False
    
    # Step 3: Set default values
    print("\n📋 Step 3: Setting default values...")
    try:
        print_settings = frappe.get_single('Print Settings')
        
        # Set defaults if not already set
        defaults = {
            'watermark_settings': 'None',
            'watermark_font_size': 24,
            'watermark_position': 'Top Right', 
            'watermark_font_family': 'Sarabun'
        }
        
        updated = False
        for field, default_value in defaults.items():
            if not print_settings.get(field):
                print_settings.set(field, default_value)
                updated = True
                print(f"  📝 Set {field} = {default_value}")
        
        if updated:
            print_settings.save()
            print("✅ Default values set and saved")
        else:
            print("✅ Default values already configured")
            
    except Exception as e:
        print(f"❌ Failed to set default values: {e}")
        return False
    
    # Step 4: Commit changes
    print("\n📋 Step 4: Committing changes...")
    try:
        frappe.db.commit()
        print("✅ Changes committed to database")
    except Exception as e:
        print(f"❌ Failed to commit changes: {e}")
        return False
    
    # Step 5: Verify installation
    print("\n📋 Step 5: Verifying installation...")
    try:
        # Check if field exists
        field_exists = frappe.db.exists("Custom Field", {"dt": "Print Settings", "fieldname": "watermark_settings"})
        if field_exists:
            print("✅ watermark_settings field exists in database")
            
            # Check if Print Settings has the field
            print_settings = frappe.get_single('Print Settings')
            if hasattr(print_settings, 'watermark_settings'):
                print(f"✅ Print Settings has watermark_settings = '{print_settings.watermark_settings}'")
            else:
                print("⚠️  Print Settings loaded but field not accessible")
                
        else:
            print("❌ watermark_settings field not found in database")
            return False
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    
    print("\n🎉 Watermark sidebar fix completed successfully!")
    print("\n📋 Next steps:")
    print("1. Go to any document in ERPNext")
    print("2. Click 'Print' button")
    print("3. Look for 'Watermark per Page' in the right sidebar")
    print("4. You should see options: None, Original on First Page, Copy on All Pages, Original,Copy on Sequence")
    
    return True

if __name__ == "__main__":
    try:
        success = fix_watermark_sidebar()
        if not success:
            print("\n❌ Fix failed. Please check the errors above.")
            exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)