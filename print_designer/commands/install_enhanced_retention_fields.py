"""
Install Enhanced Retention Fields for Construction Services

Creates custom fields for retention calculation including default retention rate.
Follows the same pattern as install_thailand_wht_fields.py for consistency.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install_enhanced_retention_fields():
    """Install enhanced custom fields for retention calculation system with default rate."""
    
    print("Installing Enhanced Retention Fields for Construction Services...")
    
    # Define custom fields
    custom_fields = {
        "Company": [
            {
                "fieldname": "construction_service",
                "label": "Enable Construction Service",
                "fieldtype": "Check",
                "insert_after": "country",
                "description": "Enable construction service features including retention calculations",
                "default": 0,
            },
            {
                "fieldname": "default_retention_rate",
                "fieldtype": "Percent",
                "label": "Default Retention Rate (%)",
                "insert_after": "construction_service",
                "depends_on": "eval:doc.construction_service",
                "description": "Default retention rate for construction projects (e.g., 5% for most projects)",
                "default": 5.0,
                "precision": 2,
            },
            {
                "fieldname": "default_retention_account",
                "fieldtype": "Link",
                "label": "Default Retention Account",
                "options": "Account",
                "insert_after": "default_retention_rate",
                "depends_on": "eval:doc.construction_service",
                "description": "Default account for retention liability (e.g., Construction Retention Payable)",
            }
        ],
        "Sales Invoice": [
            {
                "fieldname": "retention_section",
                "label": "Retention Details",
                "fieldtype": "Section Break",
                "insert_after": "taxes_and_charges",
                "depends_on": "eval:doc.company && doc.construction_service",
                "collapsible": 1,
            },
            {
                "fieldname": "custom_retention",
                "label": "Retention %",
                "fieldtype": "Percent",
                "insert_after": "retention_section",
                "description": "Retention percentage to be withheld from payment",
                "depends_on": "eval:doc.company && doc.construction_service",
                "precision": 2,
            },
            {
                "fieldname": "custom_retention_amount",
                "label": "Retention Amount",
                "fieldtype": "Currency",
                "insert_after": "custom_retention",
                "description": "Calculated retention amount",
                "read_only": 1,
                "depends_on": "eval:doc.company && doc.construction_service",
                "options": "Company:company:default_currency",
            },
        ],
    }
    
    try:
        # Create custom fields
        create_custom_fields(custom_fields, update=True)
        
        print("✅ Enhanced custom fields created successfully!")
        print("   - Company: construction_service (checkbox)")
        print("   - Company: default_retention_rate (percentage)")
        print("   - Company: default_retention_account (link to Account)")
        print("   - Sales Invoice: custom_retention (percentage)")
        print("   - Sales Invoice: custom_retention_amount (currency)")
        
        # Update existing companies with default retention rate
        _set_default_retention_rates()
        
        # Setup default retention accounts
        _setup_default_retention_accounts()
        
        frappe.db.commit()
        print("✅ Enhanced retention fields installation completed!")
        
    except Exception as e:
        print(f"❌ Error installing enhanced retention fields: {str(e)}")
        frappe.db.rollback()
        raise


def _set_default_retention_rates():
    """Set default retention rates for companies with construction service enabled."""
    
    try:
        # Get all companies with construction service enabled
        construction_companies = frappe.get_all("Company", 
            filters={"construction_service": 1},
            fields=["name"]
        )
        
        for company in construction_companies:
            # Check if default retention rate is already set
            current_rate = frappe.db.get_value("Company", company.name, "default_retention_rate")
            if not current_rate:
                # Set default rate to 5%
                frappe.db.set_value("Company", company.name, "default_retention_rate", 5.0)
                print(f"   ✓ Set default retention rate for {company.name}: 5.0%")
            else:
                print(f"   ✓ Company {company.name} already has retention rate: {current_rate}%")
                
    except Exception as e:
        print(f"   ⚠️  Warning: Could not set default retention rates: {str(e)}")


def _setup_default_retention_accounts():
    """Setup default retention accounts for companies with construction service enabled."""
    
    try:
        # Get all companies with construction service enabled
        construction_companies = frappe.get_all("Company", 
            filters={"construction_service": 1},
            fields=["name", "default_currency", "abbr"]
        )
        
        for company in construction_companies:
            # Check if default retention account is already set
            if frappe.db.get_value("Company", company.name, "default_retention_account"):
                print(f"   ✓ Company {company.name} already has default retention account")
                continue
                
            # Try to find existing retention account
            retention_account = _find_or_create_retention_account(company)
            
            if retention_account:
                # Set as default for the company
                frappe.db.set_value("Company", company.name, "default_retention_account", retention_account)
                print(f"   ✓ Set default retention account for {company.name}: {retention_account}")
                
    except Exception as e:
        print(f"   ⚠️  Warning: Could not setup default retention accounts: {str(e)}")


def _find_or_create_retention_account(company):
    """Find existing or suggest retention account for a company."""
    
    try:
        company_abbr = company.get("abbr", "")
        
        # Try to find existing retention accounts
        existing_accounts = frappe.get_all("Account",
            filters={
                "company": company.name,
                "account_name": ["like", "%retention%"],
                "is_group": 0
            },
            fields=["name", "account_name"]
        )
        
        if existing_accounts:
            # Use the first matching account
            account_name = existing_accounts[0].name
            print(f"   ✓ Found existing retention account for {company.name}: {account_name}")
            return account_name
            
        # Try alternative search terms
        alt_accounts = frappe.get_all("Account",
            filters={
                "company": company.name,
                "account_name": ["like", "%payable%"],
                "is_group": 0
            },
            fields=["name", "account_name"]
        )
        
        # Look for construction or contractor payable accounts
        for account in alt_accounts:
            account_name_lower = account.account_name.lower()
            if any(term in account_name_lower for term in ["construction", "contractor", "subcontractor"]):
                print(f"   ✓ Found suitable payable account for {company.name}: {account.name}")
                return account.name
        
        # If no specific accounts found, suggest using general accounts payable
        if alt_accounts:
            account_name = alt_accounts[0].name
            print(f"   ✓ Found general payable account for {company.name}: {account_name}")
            return account_name
            
        print(f"   ⚠️  No suitable retention account found for {company.name}. Please create manually.")
        return None
        
    except Exception as e:
        print(f"   ⚠️  Error finding retention account for {company.name}: {str(e)}")
        return None


def check_enhanced_retention_fields():
    """Check if enhanced retention fields are properly installed."""
    
    print("Checking Enhanced Retention Fields Installation...")
    
    # Check Company fields
    company_field = frappe.get_meta("Company").get_field("construction_service")
    if company_field:
        print("✅ Company.construction_service field found")
    else:
        print("❌ Company.construction_service field missing")
    
    retention_rate_field = frappe.get_meta("Company").get_field("default_retention_rate")
    if retention_rate_field:
        print("✅ Company.default_retention_rate field found")
    else:
        print("❌ Company.default_retention_rate field missing")
    
    retention_account_field = frappe.get_meta("Company").get_field("default_retention_account")
    if retention_account_field:
        print("✅ Company.default_retention_account field found")
    else:
        print("❌ Company.default_retention_account field missing")
    
    # Check Sales Invoice fields
    si_meta = frappe.get_meta("Sales Invoice")
    
    retention_field = si_meta.get_field("custom_retention")
    if retention_field:
        print("✅ Sales Invoice.custom_retention field found")
    else:
        print("❌ Sales Invoice.custom_retention field missing")
    
    retention_amount_field = si_meta.get_field("custom_retention_amount")
    if retention_amount_field:
        print("✅ Sales Invoice.custom_retention_amount field found")
    else:
        print("❌ Sales Invoice.custom_retention_amount field missing")
    
    return bool(company_field and retention_rate_field and retention_account_field and retention_field and retention_amount_field)


if __name__ == "__main__":
    install_enhanced_retention_fields()