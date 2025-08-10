"""
Install Thailand Withholding Tax Fields for Service Businesses

Creates custom fields for Thailand withholding tax calculation and accounting.
Follows the same pattern as install_retention_fields.py for consistency.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install_thailand_wht_fields():
    """Install custom fields for Thailand withholding tax system."""
    
    # Use the main installation function from thailand_wht_fields.py to avoid duplication
    from print_designer.thailand_wht_fields import install_thailand_wht_fields as main_install_function
    
    print("Installing Thailand Withholding Tax Fields for Service Businesses...")
    
    try:
        # Call the main installation function
        success = main_install_function()
        
        if success:
            # Set up default accounts if needed
            print("\n🔧 Setting up default withholding tax accounts...")
            _setup_default_wht_accounts()
            print("✅ Thailand withholding tax fields installation completed!")
        else:
            print("❌ Thailand withholding tax fields installation failed!")
            
    except Exception as e:
        print(f"❌ Error installing Thailand withholding tax fields: {str(e)}")
        frappe.db.rollback()
        raise


def _setup_default_wht_accounts():
    """Setup default withholding tax accounts for companies with Thailand service business enabled."""
    
    try:
        # Get all companies with Thailand service business enabled
        thailand_companies = frappe.get_all("Company", 
            filters={"thailand_service_business": 1},
            fields=["name", "default_currency", "abbr"]
        )
        
        for company in thailand_companies:
            # Check if default WHT account is already set
            if frappe.db.get_value("Company", company.name, "default_wht_account"):
                print(f"   ✓ Company {company.name} already has default WHT account")
                continue
                
            # Try to find existing withholding tax account
            wht_account = _find_or_create_wht_account(company)
            
            if wht_account:
                # Set as default for the company
                frappe.db.set_value("Company", company.name, "default_wht_account", wht_account)
                print(f"   ✓ Set default WHT account for {company.name}: {wht_account}")
                
    except Exception as e:
        print(f"   ⚠️  Warning: Could not setup default WHT accounts: {str(e)}")


def _find_or_create_wht_account(company):
    """Find existing or suggest withholding tax account for a company."""
    
    try:
        company_abbr = company.get("abbr", "")
        
        # Try to find existing withholding tax accounts
        existing_accounts = frappe.get_all("Account",
            filters={
                "company": company.name,
                "account_name": ["like", "%withhold%"],
                "is_group": 0
            },
            fields=["name", "account_name"]
        )
        
        if existing_accounts:
            # Use the first matching account
            account_name = existing_accounts[0].name
            print(f"   ✓ Found existing WHT account for {company.name}: {account_name}")
            return account_name
            
        # Try alternative search terms
        alt_accounts = frappe.get_all("Account",
            filters={
                "company": company.name,
                "account_name": ["like", "%tax%asset%"],
                "is_group": 0
            },
            fields=["name", "account_name"]
        )
        
        if alt_accounts:
            account_name = alt_accounts[0].name
            print(f"   ✓ Found suitable tax asset account for {company.name}: {account_name}")
            return account_name
            
        print(f"   ⚠️  No suitable WHT account found for {company.name}. Please create manually.")
        return None
        
    except Exception as e:
        print(f"   ⚠️  Error finding WHT account for {company.name}: {str(e)}")
        return None


def check_thailand_wht_fields():
    """Check if Thailand withholding tax fields are properly installed."""
    
    print("Checking Thailand Withholding Tax Fields Installation...")
    
    # Check Company fields
    company_business_field = frappe.get_meta("Company").get_field("thailand_service_business")
    if company_business_field:
        print("✅ Company.thailand_service_business field found")
    else:
        print("❌ Company.thailand_service_business field missing")
    
    company_account_field = frappe.get_meta("Company").get_field("default_wht_account")
    if company_account_field:
        print("✅ Company.default_wht_account field found")
    else:
        print("❌ Company.default_wht_account field missing")
    
    # Check Sales Invoice fields
    si_meta = frappe.get_meta("Sales Invoice")
    
    si_wht_field = si_meta.get_field("subject_to_wht")
    if si_wht_field:
        print("✅ Sales Invoice.subject_to_wht field found")
    else:
        print("❌ Sales Invoice.subject_to_wht field missing")
    
    si_amount_field = si_meta.get_field("estimated_wht_amount")
    if si_amount_field:
        print("✅ Sales Invoice.estimated_wht_amount field found")
    else:
        print("❌ Sales Invoice.estimated_wht_amount field missing")
    
    # Check new Sales Invoice fields we added
    si_net_total_field = si_meta.get_field("net_total_after_wht")
    if si_net_total_field:
        print("✅ Sales Invoice.net_total_after_wht field found")
    else:
        print("❌ Sales Invoice.net_total_after_wht field missing")
    
    si_words_field = si_meta.get_field("net_total_after_wht_in_words")
    if si_words_field:
        print("✅ Sales Invoice.net_total_after_wht_in_words field found")
    else:
        print("❌ Sales Invoice.net_total_after_wht_in_words field missing")
    
    # Check Payment Entry fields
    pe_meta = frappe.get_meta("Payment Entry")
    
    pe_apply_field = pe_meta.get_field("apply_wht")
    if pe_apply_field:
        print("✅ Payment Entry.apply_wht field found")
    else:
        print("❌ Payment Entry.apply_wht field missing")
    
    pe_amount_field = pe_meta.get_field("wht_amount")
    if pe_amount_field:
        print("✅ Payment Entry.wht_amount field found")
    else:
        print("❌ Payment Entry.wht_amount field missing")
    
    pe_account_field = pe_meta.get_field("wht_account")
    if pe_account_field:
        print("✅ Payment Entry.wht_account field found")
    else:
        print("❌ Payment Entry.wht_account field missing")
    
    # Return overall status
    all_fields_exist = all([
        company_business_field, company_account_field,
        si_wht_field, si_amount_field, si_net_total_field, si_words_field,
        pe_apply_field, pe_amount_field, pe_account_field
    ])
    
    if all_fields_exist:
        print("✅ All Thailand withholding tax fields are properly installed")
    else:
        print("❌ Some Thailand withholding tax fields are missing")
    
    return all_fields_exist


if __name__ == "__main__":
    install_thailand_wht_fields()