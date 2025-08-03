import frappe

def check_company_field_positions():
    """Check the positioning of Company fields, especially around tabs"""
    
    # Get all Custom Fields for Company DocType
    custom_fields = frappe.db.sql("""
        SELECT fieldname, label, fieldtype, insert_after, idx 
        FROM `tabCustom Field` 
        WHERE dt = 'Company' 
        ORDER BY idx, fieldname
    """, as_dict=True)
    
    print("🔍 All Company Custom Fields:")
    for field in custom_fields:
        field_type = field.fieldtype
        if field_type == "Tab Break":
            print(f"\n📋 TAB: {field.fieldname} = '{field.label}' (after: {field.insert_after}, idx: {field.idx})")
        else:
            print(f"    {field.fieldname}: '{field.label}' [{field_type}] (after: {field.insert_after}, idx: {field.idx})")
    
    # Check for the specific "Default Operating Cost Account" field
    print("\n🎯 Looking for 'Default Operating Cost Account' field...")
    
    # Check in Custom Fields
    operating_cost_custom = frappe.db.get_value(
        "Custom Field",
        {"dt": "Company", "label": "Default Operating Cost Account"},
        ["fieldname", "insert_after", "idx"],
        as_dict=True
    )
    
    if operating_cost_custom:
        print(f"  Found in Custom Fields: {operating_cost_custom}")
    else:
        print("  Not found in Custom Fields")
    
    # Also check if it's a standard field in the DocType
    doctype_fields = frappe.get_meta("Company").fields
    for field in doctype_fields:
        if "operating" in field.label.lower() and "cost" in field.label.lower():
            print(f"  Standard field: {field.fieldname} = '{field.label}' (after: {field.insert_after if hasattr(field, 'insert_after') else 'N/A'})")
    
    # Check what comes after "default_in_transit_warehouse"
    print("\n🔍 Fields positioned after 'default_in_transit_warehouse':")
    after_transit = frappe.db.sql("""
        SELECT fieldname, label, fieldtype 
        FROM `tabCustom Field` 
        WHERE dt = 'Company' AND insert_after = 'default_in_transit_warehouse'
        ORDER BY idx
    """, as_dict=True)
    
    for field in after_transit:
        print(f"  - {field.fieldname}: '{field.label}' [{field.fieldtype}]")
    
    return True