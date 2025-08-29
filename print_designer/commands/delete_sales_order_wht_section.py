#!/usr/bin/env python3
import frappe

def find_wht_section_in_sales_order():
    """Find wht_section field in Sales Order database"""
    
    print("🔍 Searching for wht_section field in Sales Order...")
    print("=" * 60)
    
    # Search in Custom Field table
    custom_field = frappe.get_value('Custom Field', {
        'dt': 'Sales Order',
        'fieldname': 'wht_section'
    })
    
    if custom_field:
        print(f"✅ Found wht_section in Custom Field: {custom_field}")
        field_doc = frappe.get_doc('Custom Field', custom_field)
        print(f"   Fieldname: {field_doc.fieldname}")
        print(f"   Fieldtype: {field_doc.fieldtype}")
        print(f"   Label: {field_doc.label or '(no label)'}")
        print(f"   Insert After: {field_doc.insert_after}")
        print(f"   Index: {field_doc.idx}")
        return {'type': 'Custom Field', 'name': custom_field, 'doc': field_doc}
    
    # Search in DocField table (standard fields)
    doc_field = frappe.get_value('DocField', {
        'parent': 'Sales Order',
        'fieldname': 'wht_section'
    })
    
    if doc_field:
        print(f"❌ Found wht_section in DocField: {doc_field}")
        print("   Cannot delete standard DocField - this is part of core ERPNext")
        field_doc = frappe.get_doc('DocField', doc_field)
        return {'type': 'DocField', 'name': doc_field, 'doc': field_doc}
    
    print("❌ wht_section field not found in Sales Order")
    return None

def delete_wht_section_field():
    """Delete the wht_section field from Sales Order"""
    
    field_info = find_wht_section_in_sales_order()
    
    if not field_info:
        print("No wht_section field found to delete")
        return False
    
    if field_info['type'] == 'DocField':
        print("❌ Cannot delete standard DocField - this would affect core ERPNext functionality")
        return False
    
    try:
        print(f"\n🗑️  Deleting Custom Field: {field_info['name']}")
        
        # Delete the custom field
        frappe.delete_doc('Custom Field', field_info['name'], ignore_permissions=True)
        frappe.db.commit()
        
        print("✅ wht_section field deleted successfully!")
        
        # Clear cache
        frappe.clear_cache(doctype='Sales Order')
        print("✅ Cache cleared for Sales Order")
        
        return True
        
    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error deleting wht_section field: {str(e)}")
        return False

def verify_deletion():
    """Verify that wht_section was deleted"""
    
    print("\n🔍 Verifying deletion...")
    
    # Check Custom Field
    custom_field = frappe.get_value('Custom Field', {
        'dt': 'Sales Order',
        'fieldname': 'wht_section'
    })
    
    if custom_field:
        print(f"❌ wht_section still exists in Custom Field: {custom_field}")
        return False
    
    # Check DocField (shouldn't exist either)
    doc_field = frappe.get_value('DocField', {
        'parent': 'Sales Order',
        'fieldname': 'wht_section'
    })
    
    if doc_field:
        print(f"⚠️  wht_section still exists as DocField: {doc_field} (this is expected if it's a standard field)")
        return True  # This is OK for standard fields
    
    print("✅ wht_section field successfully removed from Sales Order")
    return True

def delete_and_verify():
    """Complete process: find, delete, and verify"""
    
    print("🎯 Deleting wht_section from Sales Order in tipsiricons.bunchee.online")
    print("=" * 70)
    
    # Step 1: Find the field
    if not find_wht_section_in_sales_order():
        return
    
    # Step 2: Delete the field
    if delete_wht_section_field():
        # Step 3: Verify deletion
        verify_deletion()
    else:
        print("❌ Deletion failed or was not possible")