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


def check_payment_entry_fields():
    """Check Payment Entry custom fields for Thai WHT functionality"""
    
    # Get all custom fields for Payment Entry
    custom_fields = frappe.db.sql("""
        SELECT fieldname, label, fieldtype, idx, options, depends_on
        FROM `tabCustom Field` 
        WHERE dt = 'Payment Entry' 
        ORDER BY idx
    """, as_dict=True)
    
    print(f"Found {len(custom_fields)} custom fields in Payment Entry DocType:")
    print("=" * 80)
    
    # Expected fields from the workflow document
    expected_wht_fields = [
        'apply_thai_withholding_tax',
        'income_type_selection', 
        'withholding_tax_rate',
        'custom_company_tax_id',
        'custom_party_tax_id',
        'custom_withholding_tax_details',
        'custom_total_amount_paid',
        'custom_total_tax_withheld',
        'submission_form_number',
        'submission_form_date'
    ]
    
    found_fields = []
    missing_fields = []
    
    for field in custom_fields:
        print(f"Field: {field.fieldname}")
        print(f"  Label: {field.label}")
        print(f"  Type: {field.fieldtype}")
        print(f"  Index: {field.idx}")
        if field.options:
            print(f"  Options: {field.options[:100]}...")
        if field.depends_on:
            print(f"  Depends on: {field.depends_on}")
        print("-" * 60)
        
        # Check if this is a WHT field
        field_name = field.fieldname.lower()
        if any(expected in field_name for expected in ['thai', 'withholding', 'wht', 'income_type', 'submission']):
            found_fields.append(field.fieldname)
    
    # Check which expected fields are missing
    for expected_field in expected_wht_fields:
        if expected_field not in [f.fieldname for f in custom_fields]:
            missing_fields.append(expected_field)
        
    print(f"\n🔍 Thai WHT Analysis:")
    print(f"Found WHT-related fields: {len(found_fields)}")
    for field in found_fields:
        print(f"  ✓ {field}")
        
    if missing_fields:
        print(f"\nMissing expected fields: {len(missing_fields)}")
        for field in missing_fields:
            print(f"  ❌ {field}")
    else:
        print(f"\n✅ All expected WHT fields are present!")


def check_thai_wht_detail_doctype():
    """Check if Thai Withholding Tax Detail DocType exists"""
    
    doctype_name = "Thai Withholding Tax Detail"
    
    if frappe.db.exists("DocType", doctype_name):
        print(f"✅ {doctype_name} DocType exists")
        
        # Get DocType details
        doctype_doc = frappe.get_doc("DocType", doctype_name)
        print(f"   Module: {doctype_doc.module}")
        print(f"   Is Table: {doctype_doc.istable}")
        print(f"   Fields: {len(doctype_doc.fields)}")
        
        # List fields
        print(f"\n📋 Fields in {doctype_name}:")
        for field in doctype_doc.fields:
            print(f"  - {field.fieldname}: {field.label} ({field.fieldtype})")
            
    else:
        print(f"❌ {doctype_name} DocType does not exist")


def check_print_formats():
    """Check if Thai Form 50ทวิ print formats exist"""
    
    expected_formats = [
        "Thai Form 50ทวิ - JSON Format",
        "Thai Form 50ทวิ - Official Certificate"
    ]
    
    print("🖨️  Checking Print Formats:")
    print("=" * 50)
    
    for format_name in expected_formats:
        if frappe.db.exists("Print Format", format_name):
            print(f"✅ {format_name} exists")
            
            # Get format details
            format_doc = frappe.get_doc("Print Format", format_name)
            print(f"   DocType: {format_doc.doc_type}")
            print(f"   Module: {format_doc.module}")
            print(f"   Type: {getattr(format_doc, 'print_format_type', 'Standard')}")
            
        else:
            print(f"❌ {format_name} does not exist")
        print("-" * 40)


def check_wht_report():
    """Check if WHT Certificate Register report exists"""
    
    report_name = "WHT Certificate Register"
    
    print("📊 Checking WHT Reports:")
    print("=" * 40)
    
    if frappe.db.exists("Report", report_name):
        print(f"✅ {report_name} report exists")
        
        # Get report details
        report_doc = frappe.get_doc("Report", report_name)
        print(f"   Module: {report_doc.module}")
        print(f"   Type: {report_doc.report_type}")
        print(f"   Ref DocType: {report_doc.ref_doctype}")
        
    else:
        print(f"❌ {report_name} report does not exist")