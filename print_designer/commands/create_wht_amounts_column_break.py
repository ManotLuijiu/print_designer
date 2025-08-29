#!/usr/bin/env python3
import frappe

def create_wht_amounts_column_break():
    """Create wht_amounts_column_break field after connections_tab"""
    
    print("🔧 Creating wht_amounts_column_break field after connections_tab...")
    
    try:
        # First check if field already exists
        existing_field = frappe.get_value('Custom Field', {
            'dt': 'Sales Invoice',
            'fieldname': 'wht_amounts_column_break'
        })
        
        if existing_field:
            print(f"❌ Field wht_amounts_column_break already exists: {existing_field}")
            return False
        
        # Create the custom field
        custom_field = frappe.new_doc("Custom Field")
        custom_field.dt = "Sales Invoice"
        custom_field.fieldname = "wht_amounts_column_break"
        custom_field.fieldtype = "Column Break"
        custom_field.label = "WHT Amounts"
        custom_field.insert_after = "connections_tab"
        
        # Save the field
        custom_field.insert(ignore_permissions=True)
        frappe.db.commit()
        
        print("✅ Successfully created wht_amounts_column_break field!")
        print(f"   Fieldname: wht_amounts_column_break")
        print(f"   Label: WHT Amounts")
        print(f"   Type: Column Break")
        print(f"   Insert After: connections_tab")
        
        # Clear cache to make field visible
        frappe.clear_cache(doctype='Sales Invoice')
        
        return True
        
    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error creating field: {str(e)}")
        return False

def verify_field_creation():
    """Verify that the field was created correctly"""
    
    print("\n🔍 Verifying wht_amounts_column_break field creation...")
    
    # Check if field exists
    field_name = frappe.get_value('Custom Field', {
        'dt': 'Sales Invoice',
        'fieldname': 'wht_amounts_column_break'
    })
    
    if not field_name:
        print("❌ Field wht_amounts_column_break not found")
        return False
    
    # Get field details
    field_doc = frappe.get_doc('Custom Field', field_name)
    
    print("✅ Field verification successful!")
    print(f"   Record Name: {field_doc.name}")
    print(f"   Fieldname: {field_doc.fieldname}")
    print(f"   Label: {field_doc.label}")
    print(f"   Type: {field_doc.fieldtype}")
    print(f"   Insert After: {field_doc.insert_after}")
    print(f"   Index: {field_doc.idx}")
    
    return True

def create_and_verify():
    """Create the field and verify it was created correctly"""
    
    print("🎯 Creating wht_amounts_column_break field for Sales Invoice")
    print("=" * 60)
    
    # Create the field
    if create_wht_amounts_column_break():
        # Verify creation
        return verify_field_creation()
    else:
        return False