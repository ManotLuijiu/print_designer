#!/usr/bin/env python3
import frappe

def search_payment_entry_wht_section():
    """Search for wht_section field in Payment Entry"""
    
    print("🔍 Searching for wht_section in Payment Entry...")
    print("=" * 60)
    
    # Search in Custom Field table
    custom_field = frappe.get_value('Custom Field', {
        'dt': 'Payment Entry',
        'fieldname': 'wht_section'
    })
    
    if custom_field:
        print(f"✅ Found wht_section in Custom Field: {custom_field}")
        field_doc = frappe.get_doc('Custom Field', custom_field)
        print(f"   Fieldname: {field_doc.fieldname}")
        print(f"   Fieldtype: {field_doc.fieldtype}")
        print(f"   Label: {field_doc.label}")
        print(f"   Insert After: {field_doc.insert_after}")
        print(f"   Index: {field_doc.idx}")
        print(f"   Module: {field_doc.module}")
        return {'type': 'Custom Field', 'doc': field_doc}
    else:
        print("❌ wht_section field not found in Payment Entry Custom Fields")
    
    # Search in DocField table (standard fields)
    doc_field = frappe.get_value('DocField', {
        'parent': 'Payment Entry',
        'fieldname': 'wht_section'
    })
    
    if doc_field:
        print(f"✅ Found wht_section in DocField: {doc_field}")
        field_doc = frappe.get_doc('DocField', doc_field)
        print(f"   Fieldname: {field_doc.fieldname}")
        print(f"   Fieldtype: {field_doc.fieldtype}")
        print(f"   Label: {field_doc.label}")
        print(f"   Module: {field_doc.module}")
        return {'type': 'DocField', 'doc': field_doc}
    else:
        print("❌ wht_section field not found in Payment Entry DocFields")
    
    # Check all Payment Entry custom fields for reference
    print("\n📋 All Payment Entry custom fields:")
    all_custom_fields = frappe.get_all('Custom Field',
        filters={'dt': 'Payment Entry'},
        fields=['fieldname', 'fieldtype', 'label', 'insert_after'],
        order_by='idx'
    )
    
    if all_custom_fields:
        print(f"Found {len(all_custom_fields)} custom fields in Payment Entry:")
        for i, field in enumerate(all_custom_fields, 1):
            print(f"   {i:2d}. {field['fieldname']:30} | {field['fieldtype']:15} | {field['label'] or '(no label)':25}")
    else:
        print("   No custom fields found in Payment Entry")
    
    return None

def search_across_all_doctypes():
    """Search for wht_section across all DocTypes"""
    
    print("\n🔍 Searching wht_section across ALL DocTypes...")
    print("-" * 50)
    
    # Search Custom Fields
    custom_fields = frappe.get_all('Custom Field',
        filters={'fieldname': 'wht_section'},
        fields=['dt', 'fieldname', 'fieldtype', 'label', 'insert_after']
    )
    
    if custom_fields:
        print(f"✅ Found wht_section in {len(custom_fields)} Custom Fields:")
        for field in custom_fields:
            print(f"   - {field['dt']}: {field['fieldname']} ({field['fieldtype']}) - '{field['label']}'")
    else:
        print("❌ No wht_section found in any Custom Fields")
    
    # Search DocFields
    doc_fields = frappe.get_all('DocField',
        filters={'fieldname': 'wht_section'},
        fields=['parent', 'fieldname', 'fieldtype', 'label']
    )
    
    if doc_fields:
        print(f"✅ Found wht_section in {len(doc_fields)} DocFields:")
        for field in doc_fields:
            print(f"   - {field['parent']}: {field['fieldname']} ({field['fieldtype']}) - '{field['label']}'")
    else:
        print("❌ No wht_section found in any DocFields")

def complete_search():
    """Complete search for wht_section in Payment Entry"""
    
    print("🎯 Complete Search: wht_section in Payment Entry")
    print("=" * 60)
    
    # Search Payment Entry specifically
    result = search_payment_entry_wht_section()
    
    # Search across all DocTypes for reference
    search_across_all_doctypes()
    
    print(f"\n📊 CONCLUSION:")
    if result:
        print(f"   wht_section EXISTS in Payment Entry")
        print(f"   Type: {result['type']}")
        if result['type'] == 'Custom Field':
            print(f"   Source: Likely installed by custom field installation")
            print(f"   Module: {result['doc'].module or 'Unknown'}")
    else:
        print(f"   wht_section NOT FOUND in Payment Entry")
        print(f"   May not exist or may have different name")
    
    return result