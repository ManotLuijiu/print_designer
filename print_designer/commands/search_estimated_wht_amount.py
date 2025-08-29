#!/usr/bin/env python3
import frappe

def search_estimated_wht_amount_field():
    """Search for estimated_wht_amount field across all DocTypes"""
    
    print("🔍 Searching for estimated_wht_amount field...")
    print("=" * 60)
    
    # Search in Custom Field table
    custom_fields = frappe.get_all('Custom Field', 
        filters={'fieldname': 'estimated_wht_amount'}, 
        fields=['dt', 'fieldname', 'fieldtype', 'label', 'insert_after']
    )
    
    if custom_fields:
        print(f"✅ Found estimated_wht_amount in Custom Fields ({len(custom_fields)} entries):")
        for field in custom_fields:
            print(f"   - DocType: {field['dt']}")
            print(f"     Fieldname: {field['fieldname']}")
            print(f"     Type: {field['fieldtype']}")
            print(f"     Label: {field['label']}")
            print(f"     Insert After: {field['insert_after']}")
            print()
    else:
        print("❌ No estimated_wht_amount found in Custom Fields")
    
    # Search in DocField table (standard fields)
    doc_fields = frappe.get_all('DocField', 
        filters={'fieldname': 'estimated_wht_amount'}, 
        fields=['parent', 'fieldname', 'fieldtype', 'label']
    )
    
    if doc_fields:
        print(f"✅ Found estimated_wht_amount in DocFields ({len(doc_fields)} entries):")
        for field in doc_fields:
            print(f"   - DocType: {field['parent']}")
            print(f"     Fieldname: {field['fieldname']}")
            print(f"     Type: {field['fieldtype']}")
            print(f"     Label: {field['label']}")
            print()
    else:
        print("❌ No estimated_wht_amount found in DocFields")
    
    # Check if it was mentioned in any comments or documentation
    print("\n📋 Context from print_designer codebase:")
    print("Based on search results, estimated_wht_amount appears to be DEPRECATED:")
    print("- Comments indicate it's 'no longer using estimated_wht_amount'")
    print("- Replaced with 'custom_withholding_tax_amount'")
    print("- Was removed from Quotation (mentioned in QUOTATION_CUSTOM_FIELDS.md)")
    
    return custom_fields + doc_fields if custom_fields or doc_fields else []

def check_database_directly():
    """Check database directly with SQL query"""
    
    print("\n🔍 Direct database search...")
    print("-" * 40)
    
    # Direct SQL query for Custom Fields
    try:
        custom_results = frappe.db.sql("""
            SELECT dt, fieldname, fieldtype, label, insert_after 
            FROM `tabCustom Field` 
            WHERE fieldname = 'estimated_wht_amount'
        """, as_dict=True)
        
        if custom_results:
            print(f"✅ Direct SQL found {len(custom_results)} Custom Field entries:")
            for result in custom_results:
                print(f"   - {result['dt']}: {result['fieldname']} ({result['fieldtype']})")
        else:
            print("❌ Direct SQL: No Custom Fields with estimated_wht_amount")
    
    except Exception as e:
        print(f"❌ Error in Custom Field SQL query: {str(e)}")
    
    # Direct SQL query for DocFields  
    try:
        doc_results = frappe.db.sql("""
            SELECT parent, fieldname, fieldtype, label 
            FROM `tabDocField` 
            WHERE fieldname = 'estimated_wht_amount'
        """, as_dict=True)
        
        if doc_results:
            print(f"✅ Direct SQL found {len(doc_results)} DocField entries:")
            for result in doc_results:
                print(f"   - {result['parent']}: {result['fieldname']} ({result['fieldtype']})")
        else:
            print("❌ Direct SQL: No DocFields with estimated_wht_amount")
    
    except Exception as e:
        print(f"❌ Error in DocField SQL query: {str(e)}")

def complete_search():
    """Complete search for estimated_wht_amount field"""
    
    print("🎯 Complete Search for estimated_wht_amount Field")
    print("=" * 70)
    
    # Method 1: Frappe ORM search
    fields = search_estimated_wht_amount_field()
    
    # Method 2: Direct database search
    check_database_directly()
    
    print(f"\n📊 CONCLUSION:")
    if fields:
        print(f"   Field EXISTS in database with {len(fields)} entries")
        print(f"   However, print_designer code indicates it's DEPRECATED")
        print(f"   Replaced by 'custom_withholding_tax_amount'")
    else:
        print(f"   Field NOT FOUND in current database")
        print(f"   Likely was removed or never installed")
        print(f"   print_designer code shows it was deprecated")
    
    return fields