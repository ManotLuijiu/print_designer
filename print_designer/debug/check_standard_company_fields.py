import frappe

def check_standard_company_fields():
    """Check the standard Company DocType fields to understand the original structure"""
    
    try:
        # Get the Company DocType meta
        meta = frappe.get_meta("Company")
        
        print("🔍 Standard Company DocType Fields (relevant sections):")
        
        # Look for fields around default_in_transit_warehouse
        found_transit = False
        fields_after_transit = []
        
        for field in meta.fields:
            if field.fieldname == "default_in_transit_warehouse":
                found_transit = True
                print(f"\n📍 FOUND: {field.fieldname} = '{field.label}' [{field.fieldtype}]")
                continue
                
            if found_transit:
                fields_after_transit.append(field)
                print(f"  ➡️  {field.fieldname}: '{field.label}' [{field.fieldtype}]")
                
                # Stop after a few fields or when we hit a section break
                if field.fieldtype == "Section Break" or len(fields_after_transit) > 5:
                    break
        
        # Look specifically for operating cost account
        print("\n🎯 Searching for 'operating cost' related fields:")
        for field in meta.fields:
            if field.label and "operating" in field.label.lower():
                print(f"  - {field.fieldname}: '{field.label}' [{field.fieldtype}]")
                
        # Check if it might be in a different name
        print("\n🔍 Searching for 'cost' related fields:")
        for field in meta.fields:
            if field.label and "cost" in field.label.lower():
                print(f"  - {field.fieldname}: '{field.label}' [{field.fieldtype}]")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking standard fields: {e}")
        return False