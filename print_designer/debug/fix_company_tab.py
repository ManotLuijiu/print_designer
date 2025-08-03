import frappe

def fix_company_tab_position():
    """Fix the position of the Company stamps_signatures_tab"""
    
    try:
        # Get the current tab field
        tab_name = frappe.db.get_value(
            "Custom Field",
            {"dt": "Company", "fieldname": "stamps_signatures_tab"}, 
            "name"
        )
        
        if not tab_name:
            print("❌ stamps_signatures_tab field not found")
            return False
            
        print(f"📝 Found tab field: {tab_name}")
        
        # Update the tab position to be after dashboard_tab
        frappe.db.set_value("Custom Field", tab_name, {
            "insert_after": "dashboard_tab",
            "idx": 200  # Set a high index to ensure it appears after dashboard
        })
        
        frappe.db.commit()
        print("✅ Updated tab position to appear after Dashboard tab")
        
        # Verify the change
        updated_tab = frappe.db.get_value(
            "Custom Field",
            tab_name,
            ["insert_after", "idx"],
            as_dict=True
        )
        
        print(f"🔍 Verification - Tab now positioned: {updated_tab}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing tab position: {e}")
        frappe.db.rollback()
        return False