import frappe

def fix_loan_tab_position():
    """Fix the position of the Loan tab to appear in the correct location"""
    
    try:
        # Get the loan tab field
        loan_tab_name = frappe.db.get_value(
            "Custom Field",
            {"dt": "Company", "fieldname": "loan_tab"}, 
            "name"
        )
        
        if not loan_tab_name:
            print("❌ loan_tab field not found")
            return False
            
        print(f"📝 Found loan tab field: {loan_tab_name}")
        
        # Check current position
        current_position = frappe.db.get_value(
            "Custom Field",
            loan_tab_name,
            ["insert_after", "idx"],
            as_dict=True
        )
        print(f"🔍 Current position: {current_position}")
        
        # The Loan tab should appear after a more appropriate field
        # Let's check what standard fields exist in Company DocType
        meta = frappe.get_meta("Company")
        standard_fields = [f.fieldname for f in meta.fields]
        
        print("🎯 Looking for appropriate position for Loan tab...")
        
        # Common fields that should come before Loan tab
        preferred_positions = [
            "default_cash_account",
            "default_receivable_account", 
            "default_payable_account",
            "default_income_account",
            "default_expense_account",
            "cost_center",
            "credit_limit",
            "payment_terms"
        ]
        
        # Find the best position
        best_position = None
        for field in preferred_positions:
            if field in standard_fields:
                best_position = field
                print(f"  ✓ Found suitable position: after '{field}'")
                break
        
        if not best_position:
            best_position = "credit_limit"  # Fallback
            print(f"  ⚠️  Using fallback position: after '{best_position}'")
        
        # Update the loan tab position
        frappe.db.set_value("Custom Field", loan_tab_name, {
            "insert_after": best_position,
            "idx": 50  # Set a reasonable index
        })
        
        frappe.db.commit()
        print(f"✅ Updated Loan tab position to appear after '{best_position}'")
        
        # Verify the change
        updated_tab = frappe.db.get_value(
            "Custom Field",
            loan_tab_name,
            ["insert_after", "idx"],
            as_dict=True
        )
        
        print(f"🔍 Verification - Loan tab now positioned: {updated_tab}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing loan tab position: {e}")
        frappe.db.rollback()
        return False