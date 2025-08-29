#!/usr/bin/env python3
import frappe

def find_connections_tab_column_break():
    """Find the unlabeled Column Break after connections_tab"""
    
    print("🔍 Investigating Sales Invoice field structure around connections_tab...")
    print("=" * 80)
    
    # Get all Sales Invoice fields (both DocField and Custom Field) sorted by index
    all_fields = []
    
    # Get DocFields (standard fields) - note: DocField doesn't have insert_after
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
            'insert_after': 'N/A (DocField)',
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
    
    # Find connections_tab and the fields around it
    connections_tab_idx = None
    for i, field in enumerate(all_fields):
        if field['fieldname'] == 'connections_tab':
            connections_tab_idx = i
            break
    
    if connections_tab_idx is None:
        print("❌ connections_tab not found!")
        return None
    
    print(f"📋 Fields around connections_tab (showing 10 fields before and after):")
    print(f"{'#':>3} | {'idx':>3} | {'Fieldname':40} | {'Type':15} | {'Label':30} | {'Source':12}")
    print("-" * 120)
    
    start_idx = max(0, connections_tab_idx - 5)
    end_idx = min(len(all_fields), connections_tab_idx + 15)
    
    target_field = None
    
    for i in range(start_idx, end_idx):
        field = all_fields[i]
        marker = "👉" if i == connections_tab_idx else "  "
        
        # Look for Column Break fields that come after connections_tab and have no label
        if (i > connections_tab_idx and 
            field['fieldtype'] == 'Column Break' and 
            (not field['label'] or field['label'] == '(no label)')):
            marker = "🎯"  # Target field
            if target_field is None:  # Take the first one
                target_field = field
        
        print(f"{marker} {i+1:2d} | {field['idx']:3d} | {field['fieldname']:40} | {field['fieldtype']:15} | {field['label']:30} | {field['source']:12}")
    
    if target_field:
        print(f"\n🎯 FOUND TARGET: Unlabeled Column Break after connections_tab")
        print(f"   Fieldname: {target_field['fieldname']}")
        print(f"   Index: {target_field['idx']}")
        print(f"   Source: {target_field['source']}")
        print(f"   Insert After: {target_field['insert_after']}")
        
        return target_field
    else:
        print(f"\n❌ No unlabeled Column Break found after connections_tab")
        return None

def rename_column_break_to_wht_amounts():
    """Rename the unlabeled Column Break to wht_amounts_column_break"""
    
    print("🔧 Renaming unlabeled Column Break to wht_amounts_column_break...")
    
    target_field = find_connections_tab_column_break()
    
    if not target_field:
        return False
    
    try:
        if target_field['source'] == 'Custom Field':
            # Get the Custom Field document
            custom_field_name = frappe.get_value('Custom Field', {
                'dt': 'Sales Invoice',
                'fieldname': target_field['fieldname']
            })
            
            if custom_field_name:
                # Update the fieldname
                frappe.db.set_value('Custom Field', custom_field_name, {
                    'fieldname': 'wht_amounts_column_break',
                    'label': 'WHT Amounts'
                })
                
                print(f"✅ Successfully renamed {target_field['fieldname']} to wht_amounts_column_break")
                
        elif target_field['source'] == 'DocField':
            print(f"❌ Cannot rename DocField {target_field['fieldname']} - it's a standard field")
            return False
        
        # Commit changes
        frappe.db.commit()
        
        # Clear cache
        frappe.clear_cache(doctype='Sales Invoice')
        
        print("✅ Column Break renamed successfully!")
        return True
        
    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error renaming Column Break: {str(e)}")
        return False