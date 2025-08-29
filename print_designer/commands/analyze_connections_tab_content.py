#!/usr/bin/env python3
import frappe

def analyze_connections_tab_content():
    """Analyze all fields inside the connections_tab section"""
    
    print("🔍 Analyzing fields INSIDE connections_tab section...")
    print("=" * 80)
    
    # Get all fields (DocField and Custom Field) sorted by index
    all_fields = []
    
    # Get DocFields (standard fields)
    doc_fields = frappe.get_all('DocField',
        filters={'parent': 'Sales Invoice'},
        fields=['fieldname', 'fieldtype', 'label', 'idx'],
        order_by='idx'
    )
    
    for field in doc_fields:
        all_fields.append({
            'fieldname': field['fieldname'],
            'fieldtype': field['fieldtype'],
            'label': field['label'] or '(no label)',
            'idx': field['idx'],
            'source': 'DocField'
        })
    
    # Get Custom Fields
    custom_fields = frappe.get_all('Custom Field',
        filters={'dt': 'Sales Invoice'},
        fields=['fieldname', 'fieldtype', 'label', 'idx', 'insert_after'],
        order_by='idx'
    )
    
    for field in custom_fields:
        all_fields.append({
            'fieldname': field['fieldname'],
            'fieldtype': field['fieldtype'],
            'label': field['label'] or '(no label)',
            'idx': field['idx'],
            'insert_after': field.get('insert_after', ''),
            'source': 'Custom Field'
        })
    
    # Sort all fields by index
    all_fields.sort(key=lambda x: x['idx'])
    
    # Find connections_tab
    connections_tab_idx = None
    for i, field in enumerate(all_fields):
        if field['fieldname'] == 'connections_tab':
            connections_tab_idx = i
            break
    
    if connections_tab_idx is None:
        print("❌ connections_tab not found!")
        return None
    
    # Find the next Tab Break after connections_tab
    next_tab_idx = None
    for i in range(connections_tab_idx + 1, len(all_fields)):
        if all_fields[i]['fieldtype'] == 'Tab Break':
            next_tab_idx = i
            break
    
    # Get all fields between connections_tab and next tab (or end of list)
    end_idx = next_tab_idx if next_tab_idx else len(all_fields)
    connections_tab_fields = all_fields[connections_tab_idx:end_idx]
    
    print(f"📋 All fields in connections_tab section ({len(connections_tab_fields)} total):")
    print(f"{'#':>3} | {'idx':>3} | {'Fieldname':40} | {'Type':15} | {'Label':30} | {'Source':12}")
    print("-" * 120)
    
    column_breaks_in_tab = []
    
    for i, field in enumerate(connections_tab_fields):
        marker = "📌" if field['fieldname'] == 'connections_tab' else "  "
        
        if field['fieldtype'] == 'Column Break':
            marker = "🎯"  # Mark Column Breaks
            column_breaks_in_tab.append({
                'position': i,
                'field': field
            })
        
        print(f"{marker} {i+1:2d} | {field['idx']:3d} | {field['fieldname']:40} | {field['fieldtype']:15} | {field['label']:30} | {field['source']:12}")
    
    print(f"\n🎯 COLUMN BREAKS inside connections_tab:")
    
    if not column_breaks_in_tab:
        print("   ❌ No Column Break fields found inside connections_tab")
        return None
    
    for i, cb in enumerate(column_breaks_in_tab, 1):
        field = cb['field']
        position_desc = f"Position {cb['position']}/{len(connections_tab_fields)}"
        
        if i == 1:
            expected_name = "wht_amounts_column_break"
            status = "✅ CORRECT" if field['fieldname'] == expected_name else f"❌ SHOULD BE: {expected_name}"
        elif i == 2:
            expected_name = "wht_preview_column_break"  
            status = "✅ CORRECT" if field['fieldname'] == expected_name else f"❌ SHOULD BE: {expected_name}"
        else:
            status = "⚠️  UNEXPECTED"
        
        print(f"   {i}. {field['fieldname']:30} | {field['label']:25} | {position_desc:15} | {status}")
    
    # Identify what needs to be fixed
    print(f"\n🔧 ACTIONS NEEDED:")
    
    needs_fixing = []
    
    for i, cb in enumerate(column_breaks_in_tab, 1):
        field = cb['field']
        
        if i == 1 and field['fieldname'] != 'wht_amounts_column_break':
            needs_fixing.append({
                'current_name': field['fieldname'],
                'correct_name': 'wht_amounts_column_break',
                'action': 'rename',
                'field_info': field
            })
        
        if field['label'] == '(no label)':
            label_action = {
                'current_name': field['fieldname'],
                'action': 'add_label',
                'field_info': field
            }
            if field['fieldname'] == 'wht_amounts_column_break' or (i == 1):
                label_action['correct_label'] = 'WHT Amounts'
            elif field['fieldname'] == 'wht_preview_column_break' or (i == 2):
                label_action['correct_label'] = 'WHT Preview'
            
            needs_fixing.append(label_action)
    
    if needs_fixing:
        for action in needs_fixing:
            if action['action'] == 'rename':
                print(f"   ✏️  Rename: {action['current_name']} → {action['correct_name']}")
            elif action['action'] == 'add_label':
                print(f"   🏷️  Add label: {action['current_name']} → \"{action['correct_label']}\"")
    else:
        print("   ✅ No actions needed - structure is correct!")
    
    return {
        'connections_tab_fields': connections_tab_fields,
        'column_breaks': column_breaks_in_tab,
        'needs_fixing': needs_fixing
    }