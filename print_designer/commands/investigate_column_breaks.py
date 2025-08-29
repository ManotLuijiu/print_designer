#!/usr/bin/env python3
import frappe

def investigate_all_column_breaks():
    """Investigate all Column Break fields in Sales Invoice"""
    
    print("🔍 Investigating all Column Break fields in Sales Invoice...")
    print("=" * 80)
    
    # Get all fields (DocField and Custom Field) that are Column Breaks
    all_column_breaks = []
    
    # Get DocField Column Breaks
    doc_column_breaks = frappe.get_all('DocField',
        filters={
            'parent': 'Sales Invoice',
            'fieldtype': 'Column Break'
        },
        fields=['fieldname', 'label', 'idx'],
        order_by='idx'
    )
    
    for field in doc_column_breaks:
        all_column_breaks.append({
            'fieldname': field['fieldname'],
            'label': field['label'] or '(no label)',
            'idx': field['idx'],
            'source': 'DocField (Standard)',
            'has_proper_name': not (field['fieldname'].startswith('col_break') or field['fieldname'].startswith('column_break'))
        })
    
    # Get Custom Field Column Breaks
    custom_column_breaks = frappe.get_all('Custom Field',
        filters={
            'dt': 'Sales Invoice',
            'fieldtype': 'Column Break'
        },
        fields=['fieldname', 'label', 'idx', 'insert_after'],
        order_by='idx'
    )
    
    for field in custom_column_breaks:
        all_column_breaks.append({
            'fieldname': field['fieldname'],
            'label': field['label'] or '(no label)',
            'idx': field['idx'],
            'insert_after': field['insert_after'],
            'source': 'Custom Field',
            'has_proper_name': not (field['fieldname'].startswith('col_break') or field['fieldname'].startswith('column_break'))
        })
    
    # Sort by index
    all_column_breaks.sort(key=lambda x: x['idx'])
    
    print(f"📋 All Column Break fields in Sales Invoice ({len(all_column_breaks)} total):")
    print(f"{'#':>3} | {'idx':>3} | {'Fieldname':30} | {'Label':25} | {'Source':15} | {'Proper Name?':12}")
    print("-" * 100)
    
    problematic_fields = []
    
    for i, field in enumerate(all_column_breaks, 1):
        proper_name_status = "✅ Yes" if field['has_proper_name'] else "❌ No"
        
        if not field['has_proper_name'] or field['label'] == '(no label)':
            problematic_fields.append(field)
        
        print(f"{i:3d} | {field['idx']:3d} | {field['fieldname']:30} | {field['label']:25} | {field['source']:15} | {proper_name_status:12}")
    
    # Now find the specific field after connections_tab
    print(f"\n🎯 Looking for Column Break after connections_tab...")
    
    # Find connections_tab index
    connections_tab = frappe.get_value('DocField', {
        'parent': 'Sales Invoice',
        'fieldname': 'connections_tab'
    })
    
    if connections_tab:
        connections_doc = frappe.get_doc('DocField', connections_tab)
        connections_idx = connections_doc.idx
        
        print(f"   connections_tab found at index: {connections_idx}")
        
        # Find Column Breaks that come after connections_tab
        fields_after_connections = []
        for field in all_column_breaks:
            if field['idx'] > connections_idx:
                fields_after_connections.append(field)
        
        if fields_after_connections:
            print(f"\n📋 Column Breaks after connections_tab:")
            for field in fields_after_connections:
                status = "🚨 PROBLEMATIC" if field in problematic_fields else "✅ OK"
                insert_info = f" | after: {field.get('insert_after', 'N/A')}" if 'insert_after' in field else ""
                print(f"   - {field['fieldname']:30} | {field['label']:25} | {status}{insert_info}")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   Total Column Breaks: {len(all_column_breaks)}")
    print(f"   Problematic fields: {len(problematic_fields)}")
    
    if problematic_fields:
        print(f"\n🚨 PROBLEMATIC FIELDS FOUND:")
        for field in problematic_fields:
            issues = []
            if not field['has_proper_name']:
                issues.append("generic fieldname")
            if field['label'] == '(no label)':
                issues.append("no label")
            
            print(f"   - {field['fieldname']:30} | Issues: {', '.join(issues)} | Source: {field['source']}")
    
    return {
        'total_column_breaks': len(all_column_breaks),
        'problematic_fields': problematic_fields,
        'fields_after_connections': fields_after_connections if 'fields_after_connections' in locals() else []
    }

def propose_fix_plan():
    """Analyze the situation and propose a fix plan"""
    
    print("\n" + "="*80)
    print("🔧 PROPOSING FIX PLAN")
    print("="*80)
    
    analysis = investigate_all_column_breaks()
    
    if not analysis['problematic_fields']:
        print("✅ No problematic Column Break fields found - no action needed")
        return
    
    print(f"\n📋 RECOMMENDED ACTIONS:")
    
    for i, field in enumerate(analysis['problematic_fields'], 1):
        print(f"\n{i}. Fix field: {field['fieldname']}")
        
        if field['fieldname'] == 'wht_preview_column_break':
            print(f"   🎯 This appears to be the field mentioned by the user")
            print(f"   Recommended action: Rename to 'wht_amounts_column_break'")
            print(f"   Add label: 'WHT Amounts'")
            print(f"   Ensure proper positioning in Thai WHT section")
        
        elif not field['has_proper_name']:
            print(f"   Issue: Generic fieldname")
            print(f"   Recommended action: Rename to descriptive name")
        
        if field['label'] == '(no label)':
            print(f"   Issue: No label")
            print(f"   Recommended action: Add appropriate label")
    
    print(f"\n🎯 PRIORITY ACTION:")
    print(f"   Based on user request: Rename the unlabeled Column Break after connections_tab")
    print(f"   Target: Change to 'wht_amounts_column_break' with label 'WHT Amounts'")
    
    return analysis