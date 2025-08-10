import frappe

def check_company_tabs():
    """Check what tabs exist for Company DocType"""
    
    # Query all tab break fields for Company
    tabs = frappe.db.sql("""
        SELECT fieldname, label, insert_after, idx 
        FROM `tabCustom Field` 
        WHERE dt = 'Company' AND fieldtype = 'Tab Break' 
        ORDER BY idx
    """, as_dict=True)
    
    print("🔍 Company Tab Break Fields:")
    for tab in tabs:
        print(f"  - {tab.fieldname}: '{tab.label}' (after: {tab.insert_after}, idx: {tab.idx})")
    
    # Also check for the specific stamps_signatures_tab field
    stamps_tab = frappe.db.get_value(
        "Custom Field",
        {"dt": "Company", "fieldname": "stamps_signatures_tab"},
        ["name", "label", "insert_after", "idx"],
        as_dict=True
    )
    
    print(f"\n🎯 stamps_signatures_tab field:")
    if stamps_tab:
        print(f"  - Found: {stamps_tab}")
    else:
        print("  - Not found")
    
    # Check if the tab has the correct insert_after value
    if stamps_tab and stamps_tab.get('insert_after') != 'dashboard_tab':
        print(f"  ⚠️  Tab position issue: insert_after is '{stamps_tab.get('insert_after')}' but should be 'dashboard_tab'")
    
    return stamps_tab