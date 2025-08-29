#!/usr/bin/env python3
import frappe

def find_null_fieldnames():
    """Check database for Custom Fields with NULL or empty fieldnames"""
    
    print("🔍 Checking database for fields with NULL/empty fieldnames...")
    print("=" * 80)
    
    # Direct SQL query to find Custom Fields with NULL/empty fieldnames
    query = """
        SELECT name, dt, fieldname, fieldtype, label, idx, insert_after
        FROM `tabCustom Field`
        WHERE dt = 'Sales Invoice' 
        AND (fieldname IS NULL OR fieldname = '')
        ORDER BY idx
    """
    
    null_fieldname_fields = frappe.db.sql(query, as_dict=True)
    
    print(f"📋 Custom Fields with NULL/empty fieldnames ({len(null_fieldname_fields)} found):")
    
    if not null_fieldname_fields:
        print("   ✅ No Custom Fields with NULL/empty fieldnames found")
        
        # Also check for fields with very generic names that might be the issue
        print("\n🔍 Checking for Column Breaks with generic names near connections_tab...")
        
        generic_query = """
            SELECT name, dt, fieldname, fieldtype, label, idx, insert_after
            FROM `tabCustom Field`
            WHERE dt = 'Sales Invoice' 
            AND fieldtype = 'Column Break'
            AND (fieldname LIKE 'column_break%' OR fieldname LIKE 'col_break%' OR fieldname = '')
            ORDER BY idx
        """
        
        generic_fields = frappe.db.sql(generic_query, as_dict=True)
        
        for field in generic_fields:
            print(f"   - {field.name}: fieldname='{field.fieldname}', label='{field.label or '(no label)'}', idx={field.idx}")
        
        return None
    
    print(f"{'#':>3} | {'Record Name':40} | {'Fieldname':20} | {'Type':15} | {'Label':25} | {'idx':>3} | {'Insert After':20}")
    print("-" * 140)
    
    target_field = None
    
    for i, field in enumerate(null_fieldname_fields, 1):
        fieldname_display = field.fieldname or '(NULL/EMPTY)'
        label_display = field.label or '(no label)'
        
        print(f"{i:3d} | {field.name:40} | {fieldname_display:20} | {field.fieldtype:15} | {label_display:25} | {field.idx:3d} | {field.insert_after or '':20}")
        
        # Look for Column Break that might be the target
        if field.fieldtype == 'Column Break':
            target_field = field
    
    if target_field:
        print(f"\n🎯 FOUND TARGET: Column Break with NULL/empty fieldname")
        print(f"   Record name: {target_field.name}")
        print(f"   Index: {target_field.idx}")
        print(f"   Insert after: {target_field.insert_after}")
        
        return target_field
    else:
        print(f"\n❌ No Column Break fields with NULL/empty fieldnames found")
        return None

def check_connections_tab_area():
    """Check the area around connections_tab for problematic fields"""
    
    print("\n" + "="*80)
    print("🔍 DETAILED CHECK: Area around connections_tab")
    print("="*80)
    
    # Get connections_tab index
    connections_tab_info = frappe.db.sql("""
        SELECT idx FROM `tabDocField`
        WHERE parent = 'Sales Invoice' AND fieldname = 'connections_tab'
    """, as_dict=True)
    
    if not connections_tab_info:
        print("❌ connections_tab not found")
        return
    
    connections_idx = connections_tab_info[0].idx
    print(f"📍 connections_tab found at index: {connections_idx}")
    
    # Get all fields (DocField and Custom Field) around connections_tab
    range_start = connections_idx - 5
    range_end = connections_idx + 20
    
    print(f"\n📋 All fields from index {range_start} to {range_end}:")
    
    # DocFields
    doc_fields = frappe.db.sql("""
        SELECT fieldname, fieldtype, label, idx, 'DocField' as source
        FROM `tabDocField`
        WHERE parent = 'Sales Invoice' 
        AND idx BETWEEN %s AND %s
        ORDER BY idx
    """, (range_start, range_end), as_dict=True)
    
    # Custom Fields
    custom_fields = frappe.db.sql("""
        SELECT name, fieldname, fieldtype, label, idx, insert_after, 'Custom Field' as source
        FROM `tabCustom Field`
        WHERE dt = 'Sales Invoice' 
        AND idx BETWEEN %s AND %s
        ORDER BY idx
    """, (range_start, range_end), as_dict=True)
    
    # Combine and sort
    all_fields = list(doc_fields) + list(custom_fields)
    all_fields.sort(key=lambda x: x['idx'])
    
    print(f"{'idx':>3} | {'Fieldname':35} | {'Type':15} | {'Label':25} | {'Source':12}")
    print("-" * 105)
    
    blank_column_breaks = []
    
    for field in all_fields:
        fieldname_display = field.get('fieldname') or '(NULL/EMPTY)'
        label_display = field.get('label') or '(no label)'
        
        marker = "📌" if field.get('fieldname') == 'connections_tab' else "  "
        if field.get('fieldtype') == 'Column Break' and (not field.get('fieldname') or not field.get('label')):
            marker = "🎯"
            blank_column_breaks.append(field)
        
        print(f"{marker}{field['idx']:3d} | {fieldname_display:35} | {field['fieldtype']:15} | {label_display:25} | {field['source']:12}")
    
    if blank_column_breaks:
        print(f"\n🎯 BLANK COLUMN BREAKS FOUND:")
        for field in blank_column_breaks:
            print(f"   - Record: {field.get('name', 'N/A')}")
            print(f"     Fieldname: '{field.get('fieldname') or '(NULL/EMPTY)'}'")
            print(f"     Label: '{field.get('label') or '(no label)'}'") 
            print(f"     Index: {field['idx']}")
            print(f"     Insert after: '{field.get('insert_after', 'N/A')}'")
            print()
        
        return blank_column_breaks
    
    return []

def fix_blank_fieldname():
    """Fix the blank fieldname by setting it to wht_amounts_column_break"""
    
    blank_fields = check_connections_tab_area()
    
    if not blank_fields:
        print("❌ No blank Column Break fields found to fix")
        return False
    
    # Find the most likely candidate (Column Break after connections_tab with blank fieldname)
    target_field = None
    connections_idx = frappe.db.get_value('DocField', 
        {'parent': 'Sales Invoice', 'fieldname': 'connections_tab'}, 'idx')
    
    for field in blank_fields:
        if (field['fieldtype'] == 'Column Break' and 
            field['idx'] > connections_idx and 
            not field.get('fieldname')):
            target_field = field
            break
    
    if not target_field:
        print("❌ Could not identify target field to fix")
        return False
    
    print(f"🔧 FIXING: Setting fieldname for record {target_field.get('name')}")
    
    try:
        # Update the fieldname
        frappe.db.set_value('Custom Field', target_field['name'], {
            'fieldname': 'wht_amounts_column_break',
            'label': 'WHT Amounts'
        })
        
        frappe.db.commit()
        
        print(f"✅ Successfully updated:")
        print(f"   Record: {target_field['name']}")
        print(f"   Fieldname: (blank) → 'wht_amounts_column_break'")
        print(f"   Label: (blank) → 'WHT Amounts'")
        
        # Clear cache
        frappe.clear_cache(doctype='Sales Invoice')
        
        return True
        
    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error fixing fieldname: {str(e)}")
        return False