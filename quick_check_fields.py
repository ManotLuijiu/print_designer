#!/usr/bin/env python3
"""
Quick Check - What fields actually exist in Company DocType
"""

import frappe

def quick_check():
    """Quick check of Company custom fields"""
    
    print("🔍 QUICK CHECK: Company Custom Fields")
    print("=" * 50)
    
    # Get ALL custom fields for Company
    all_fields = frappe.db.sql("""
        SELECT 
            fieldname, label, fieldtype, insert_after, idx, hidden, print_hide
        FROM `tabCustom Field` 
        WHERE dt = 'Company'
        ORDER BY idx ASC
    """, as_dict=True)
    
    print(f"📊 Total custom fields found: {len(all_fields)}")
    print()
    
    # Check for signature-related fields specifically
    signature_keywords = ["signature", "stamp", "seal", "stamps_signatures"]
    signature_fields = [f for f in all_fields if any(keyword in f.fieldname.lower() for keyword in signature_keywords)]
    
    if signature_fields:
        print(f"🖼️  Found {len(signature_fields)} signature-related fields:")
        for field in signature_fields:
            hidden_status = " (HIDDEN)" if field.hidden else ""
            print_hide_status = " (PRINT_HIDE)" if field.print_hide else ""
            print(f"   • {field.fieldname} - {field.label} ({field.fieldtype}){hidden_status}{print_hide_status}")
            print(f"     Insert after: {field.insert_after}, Index: {field.idx}")
        print()
    else:
        print("❌ NO signature-related fields found!")
        print()
    
    # Check for the specific tab
    tab_field = next((f for f in all_fields if f.fieldname == "stamps_signatures_tab"), None)
    if tab_field:
        print(f"📑 Stamps & Signatures tab: FOUND (index {tab_field.idx})")
        
        # Find fields that come after this tab
        fields_after_tab = [f for f in all_fields if f.idx > tab_field.idx and any(keyword in f.fieldname.lower() for keyword in signature_keywords)]
        print(f"   Fields after tab: {len(fields_after_tab)}")
        for field in fields_after_tab:
            print(f"      → {field.fieldname} ({field.fieldtype})")
    else:
        print("❌ Stamps & Signatures tab: NOT FOUND")
    
    print()
    
    # Show some context - fields around where our tab should be
    print("📋 All fields (showing context):")
    for field in all_fields:
        marker = "👉" if any(keyword in field.fieldname.lower() for keyword in signature_keywords) else "  "
        print(f"{marker} {field.idx:3d}: {field.fieldname} ({field.fieldtype}) -> {field.insert_after}")
    
    return signature_fields, tab_field

if __name__ == "__main__":
    quick_check()