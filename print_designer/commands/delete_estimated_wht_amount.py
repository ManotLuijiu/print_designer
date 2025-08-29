#!/usr/bin/env python3
import frappe

def delete_estimated_wht_amount():
    """Delete the deprecated estimated_wht_amount field from database"""
    
    print("🗑️  Deleting deprecated estimated_wht_amount field...")
    print("=" * 60)
    
    try:
        # Find the Custom Field
        custom_field = frappe.get_value('Custom Field', {
            'dt': 'Sales Invoice',
            'fieldname': 'estimated_wht_amount'
        })
        
        if custom_field:
            print(f"✅ Found field: {custom_field}")
            
            # Get field details before deletion
            field_doc = frappe.get_doc('Custom Field', custom_field)
            print(f"   DocType: {field_doc.dt}")
            print(f"   Fieldname: {field_doc.fieldname}")
            print(f"   Label: {field_doc.label}")
            print(f"   Type: {field_doc.fieldtype}")
            print(f"   Insert After: {field_doc.insert_after}")
            
            # Delete the field
            frappe.delete_doc('Custom Field', custom_field, ignore_permissions=True)
            frappe.db.commit()
            
            print("✅ estimated_wht_amount field deleted successfully!")
            
            # Clear cache
            frappe.clear_cache(doctype='Sales Invoice')
            print("✅ Sales Invoice cache cleared")
            
            return True
            
        else:
            print("❌ estimated_wht_amount field not found")
            return False
            
    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error deleting field: {str(e)}")
        return False

def verify_deletion():
    """Verify the field was deleted"""
    
    print("\n🔍 Verifying deletion...")
    
    custom_field = frappe.get_value('Custom Field', {
        'dt': 'Sales Invoice',
        'fieldname': 'estimated_wht_amount'
    })
    
    if custom_field:
        print(f"❌ Field still exists: {custom_field}")
        return False
    else:
        print("✅ Field successfully deleted from database")
        return True

def delete_and_verify():
    """Delete field and verify"""
    
    print("🎯 Deleting deprecated estimated_wht_amount field")
    print("=" * 50)
    
    if delete_estimated_wht_amount():
        verify_deletion()
    else:
        print("❌ Deletion failed")