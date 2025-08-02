import frappe

def check_supplier_fields():
    # Get all custom fields for Supplier
    custom_fields = frappe.db.sql("""
        SELECT fieldname, label, fieldtype, idx 
        FROM `tabCustom Field` 
        WHERE dt = 'Supplier' 
        ORDER BY idx
    """, as_dict=True)
    
    print(f"Found {len(custom_fields)} custom fields in Supplier DocType:")
    print("=" * 60)
    
    branch_code_fields = []
    
    for field in custom_fields:
        print(f"Field: {field.fieldname}")
        print(f"  Label: {field.label}")
        print(f"  Type: {field.fieldtype}")
        print(f"  Index: {field.idx}")
        print("-" * 40)
        
        # Check if this is a branch code field
        if 'branch' in field.fieldname.lower() and 'code' in field.fieldname.lower():
            branch_code_fields.append(field)
        elif 'branch' in field.label.lower() and 'code' in field.label.lower():
            branch_code_fields.append(field)
    
    print(f"\nBranch Code related fields: {len(branch_code_fields)}")
    for field in branch_code_fields:
        print(f"  - {field.fieldname}: {field.label}")

check_supplier_fields()