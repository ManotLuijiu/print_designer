#!/usr/bin/env python3
import frappe

def find_all_wht_section_fields():
    """Find all wht_section fields across all DocTypes"""
    
    print("🔍 Searching for all wht_section fields in the database...")
    print("=" * 70)
    
    # Search in Custom Field table
    custom_fields = frappe.get_all('Custom Field',
        filters={'fieldname': 'wht_section'},
        fields=['name', 'dt', 'fieldname', 'fieldtype', 'label', 'insert_after', 'module'],
        order_by='dt'
    )
    
    # Search in DocField table (standard fields)
    doc_fields = frappe.get_all('DocField',
        filters={'fieldname': 'wht_section'},
        fields=['name', 'parent', 'fieldname', 'fieldtype', 'label'],
        order_by='parent'
    )
    
    print(f"📊 Search Results:")
    print(f"   Custom Fields: {len(custom_fields)}")
    print(f"   DocFields (Standard): {len(doc_fields)}")
    
    if custom_fields:
        print(f"\n📋 Custom Fields with wht_section:")
        for i, field in enumerate(custom_fields, 1):
            print(f"   {i}. {field['dt']} → {field['fieldname']}")
            print(f"      Label: '{field['label']}'")
            print(f"      Type: {field['fieldtype']}")
            print(f"      Module: {field['module'] or 'None'}")
            print(f"      Record: {field['name']}")
            print()
    
    if doc_fields:
        print(f"📋 Standard DocFields with wht_section:")
        for i, field in enumerate(doc_fields, 1):
            print(f"   {i}. {field['parent']} → {field['fieldname']}")
            print(f"      Label: '{field['label']}'")
            print(f"      Type: {field['fieldtype']}")
            print(f"      Record: {field['name']}")
            print()
    
    return custom_fields, doc_fields

def delete_all_wht_section_fields():
    """Delete all wht_section fields from database"""
    
    print("🗑️  Deleting all wht_section fields...")
    print("=" * 50)
    
    custom_fields, doc_fields = find_all_wht_section_fields()
    
    if not custom_fields and not doc_fields:
        print("✅ No wht_section fields found to delete")
        return True
    
    try:
        # Delete Custom Fields
        deleted_custom = 0
        for field in custom_fields:
            try:
                print(f"   Deleting Custom Field: {field['dt']}-{field['fieldname']}")
                frappe.delete_doc('Custom Field', field['name'], ignore_permissions=True)
                deleted_custom += 1
                print(f"     ✅ Deleted: {field['name']}")
            except Exception as e:
                print(f"     ❌ Error deleting {field['name']}: {str(e)}")
        
        # Delete DocFields (if any - should not be deleted as they're standard fields)
        if doc_fields:
            print(f"\n⚠️  Found {len(doc_fields)} Standard DocFields with wht_section:")
            print("   These are standard ERPNext fields and will NOT be deleted")
            for field in doc_fields:
                print(f"   - {field['parent']}-{field['fieldname']} (keeping)")
        
        # Commit changes
        frappe.db.commit()
        
        print(f"\n📊 Deletion Summary:")
        print(f"   ✅ Custom Fields deleted: {deleted_custom}")
        print(f"   ⚠️  Standard Fields kept: {len(doc_fields)}")
        
        # Clear cache
        print(f"\n🧹 Clearing DocType caches...")
        affected_doctypes = set()
        for field in custom_fields:
            affected_doctypes.add(field['dt'])
        
        for doctype in affected_doctypes:
            frappe.clear_cache(doctype=doctype)
            print(f"   ✅ Cleared cache for {doctype}")
        
        print(f"\n✅ All wht_section fields cleanup completed!")
        return True
        
    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error during deletion: {str(e)}")
        return False

def verify_complete_removal():
    """Verify that all wht_section fields have been removed"""
    
    print("\n🔍 Verifying complete removal of wht_section fields...")
    print("-" * 50)
    
    # Check Custom Fields again
    remaining_custom = frappe.get_all('Custom Field',
        filters={'fieldname': 'wht_section'},
        fields=['name', 'dt', 'fieldname']
    )
    
    # Check DocFields again  
    remaining_doc = frappe.get_all('DocField',
        filters={'fieldname': 'wht_section'},
        fields=['name', 'parent', 'fieldname']
    )
    
    if not remaining_custom and not remaining_doc:
        print("✅ VERIFICATION SUCCESSFUL: All wht_section fields have been removed")
        return True
    else:
        print(f"❌ VERIFICATION FAILED:")
        if remaining_custom:
            print(f"   {len(remaining_custom)} Custom Fields still exist:")
            for field in remaining_custom:
                print(f"   - {field['dt']}-{field['fieldname']}")
        if remaining_doc:
            print(f"   {len(remaining_doc)} DocFields still exist:")
            for field in remaining_doc:
                print(f"   - {field['parent']}-{field['fieldname']}")
        return False

def complete_cleanup():
    """Complete cleanup process for all wht_section fields"""
    
    print("🧹 Complete Cleanup: Removing all wht_section fields from tipsiricons.bunchee.online")
    print("=" * 80)
    
    # Step 1: Find all fields
    custom_fields, doc_fields = find_all_wht_section_fields()
    
    if not custom_fields and not doc_fields:
        print("✅ No wht_section fields found - cleanup not needed")
        return True
    
    # Step 2: Delete all fields
    if delete_all_wht_section_fields():
        # Step 3: Verify removal
        if verify_complete_removal():
            print("\n🎉 CLEANUP COMPLETED SUCCESSFULLY!")
            print("   All wht_section fields have been removed from tipsiricons.bunchee.online")
            return True
        else:
            print("\n⚠️  CLEANUP INCOMPLETE - some fields remain")
            return False
    else:
        print("\n❌ CLEANUP FAILED - deletion errors occurred")
        return False