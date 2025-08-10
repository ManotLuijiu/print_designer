#!/usr/bin/env python3
"""
Check Company Custom Fields and Their Positioning
"""

import frappe

def check_company_fields():
    """Check all custom fields in Company DocType and their positioning"""
    
    print("🔍 Analyzing Company DocType Custom Fields")
    print("=" * 60)
    
    # Get all custom fields for Company
    company_fields = frappe.get_all(
        "Custom Field",
        filters={"dt": "Company"},
        fields=["fieldname", "label", "fieldtype", "insert_after", "idx"],
        order_by="idx asc"
    )
    
    print(f"\n📋 Found {len(company_fields)} custom fields in Company DocType:")
    print("-" * 60)
    
    signature_related = []
    tab_breaks = []
    sections = []
    
    for field in company_fields:
        field_type_icon = {
            "Tab Break": "📑",
            "Section Break": "📄", 
            "Column Break": "📋",
            "Attach Image": "🖼️",
            "Data": "📝",
            "Link": "🔗",
            "Check": "☑️"
        }.get(field.fieldtype, "📄")
        
        print(f"{field_type_icon} {field.fieldname}")
        print(f"   Label: {field.label}")
        print(f"   Type: {field.fieldtype}")
        print(f"   Insert After: {field.insert_after}")
        print(f"   Index: {field.idx}")
        print()
        
        # Categorize fields
        if field.fieldtype == "Tab Break":
            tab_breaks.append(field)
        elif field.fieldtype == "Section Break":
            sections.append(field)
        elif any(keyword in field.fieldname for keyword in ["signature", "stamp", "seal"]):
            signature_related.append(field)
    
    print("\n📑 Tab Breaks Found:")
    for tab in tab_breaks:
        print(f"   - {tab.fieldname} ({tab.label}) - Insert After: {tab.insert_after}")
    
    print("\n📄 Section Breaks Found:")  
    for section in sections:
        print(f"   - {section.fieldname} ({section.label}) - Insert After: {section.insert_after}")
    
    print("\n🖼️ Signature/Stamp Fields Found:")
    for sig_field in signature_related:
        print(f"   - {sig_field.fieldname} ({sig_field.label}) - Insert After: {sig_field.insert_after}")
    
    # Check the specific issue
    stamps_tab = next((t for t in tab_breaks if t.fieldname == "stamps_signatures_tab"), None)
    if stamps_tab:
        print(f"\n✅ Stamps & Signatures tab exists: {stamps_tab.label}")
        
        # Find fields that should be after this tab
        fields_after_tab = [f for f in signature_related if f.insert_after and (
            f.insert_after == "stamps_signatures_tab" or
            f.insert_after in [sf.fieldname for sf in signature_related] or
            f.insert_after in [s.fieldname for s in sections if s.insert_after == "stamps_signatures_tab"]
        )]
        
        print(f"   Fields positioned after this tab: {len(fields_after_tab)}")
        for field in fields_after_tab:
            print(f"      - {field.fieldname} -> {field.insert_after}")
    else:
        print("\n❌ Stamps & Signatures tab not found!")
    
    return {
        "total_fields": len(company_fields),
        "signature_fields": signature_related,
        "tab_breaks": tab_breaks,
        "sections": sections,
        "stamps_tab": stamps_tab
    }

def analyze_field_positioning():
    """Analyze the logical flow of field positioning"""
    
    print("\n🔄 Analyzing Field Positioning Logic")
    print("=" * 60)
    
    # Expected sequence from signature_fields.py
    expected_sequence = [
        "stamps_signatures_tab",          # Tab Break
        "company_signatures_section",     # Section Break  
        "authorized_signature_1",         # Attach Image
        "authorized_signature_2",         # Attach Image
        "ceo_signature",                 # Attach Image
        "company_stamps_section",        # Section Break
        "company_stamp_1",               # Attach Image
        "company_stamp_2",               # Attach Image
        "official_seal"                  # Attach Image
    ]
    
    # Check if each field exists and its positioning
    for i, fieldname in enumerate(expected_sequence):
        field_doc = frappe.db.get_value(
            "Custom Field",
            {"dt": "Company", "fieldname": fieldname},
            ["name", "label", "fieldtype", "insert_after", "idx"],
            as_dict=True
        )
        
        if field_doc:
            expected_insert_after = expected_sequence[i-1] if i > 0 else "default_in_transit_warehouse"
            actual_insert_after = field_doc.insert_after
            
            status = "✅" if actual_insert_after == expected_insert_after else "⚠️"
            print(f"{status} {fieldname}")
            print(f"   Expected after: {expected_insert_after}")
            print(f"   Actually after: {actual_insert_after}")
            print(f"   Type: {field_doc.fieldtype}")
            print()
        else:
            print(f"❌ {fieldname} - MISSING")
            print()

def run_analysis():
    """Run the complete analysis"""
    try:
        data = check_company_fields()
        analyze_field_positioning()
        
        print("\n📊 Summary:")
        print(f"   Total Custom Fields: {data['total_fields']}")
        print(f"   Signature/Stamp Fields: {len(data['signature_fields'])}")
        print(f"   Tab Breaks: {len(data['tab_breaks'])}")
        print(f"   Section Breaks: {len(data['sections'])}")
        print(f"   Stamps Tab Exists: {'✅' if data['stamps_tab'] else '❌'}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_analysis()