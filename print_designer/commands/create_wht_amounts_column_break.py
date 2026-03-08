#!/usr/bin/env python3
import frappe

def create_wht_amounts_column_break():
    """Create pd_custom_wht_amounts_cb field after connections_tab"""
    
    print("🔧 Creating pd_custom_wht_amounts_cb field after connections_tab...")
    
    try:
        # First check if field already exists
        existing_field = frappe.get_value('Custom Field', {
            'dt': 'Sales Invoice',
            'fieldname': 'pd_custom_wht_amounts_cb'
        })
        
        if existing_field:
            print(f"❌ Field pd_custom_wht_amounts_cb already exists: {existing_field}")
            return False
        
        # Create the custom field
        custom_field = frappe.new_doc("Custom Field")
        custom_field.dt = "Sales Invoice"
        custom_field.fieldname = "pd_custom_wht_amounts_cb"
        custom_field.fieldtype = "Column Break"
        custom_field.label = "WHT Amounts"
        custom_field.insert_after = "connections_tab"
        
        # Save the field
        custom_field.insert(ignore_permissions=True)
        frappe.db.commit()
        
        print("✅ Successfully created pd_custom_wht_amounts_cb field!")
        print(f"   Fieldname: pd_custom_wht_amounts_cb")
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
    
    print("\n🔍 Verifying pd_custom_wht_amounts_cb field creation...")
    
    # Check if field exists
    field_name = frappe.get_value('Custom Field', {
        'dt': 'Sales Invoice',
        'fieldname': 'pd_custom_wht_amounts_cb'
    })
    
    if not field_name:
        print("❌ Field pd_custom_wht_amounts_cb not found")
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
    
    print("🎯 Creating pd_custom_wht_amounts_cb field for Sales Invoice")
    print("=" * 60)
    
    # Create the field
    if create_wht_amounts_column_break():
        # Verify creation
        return verify_field_creation()
    else:
        return False