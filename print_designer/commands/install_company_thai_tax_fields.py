"""
Install Company Thai Tax Fields

Creates all Thai tax-related custom fields for Company doctype in the correct order.
This handles the missing WHT fields and adds the new VAT account fields.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install_company_thai_tax_fields():
    """Install all Thai tax-related custom fields for Company doctype."""

    print("Installing Company Thai Tax Fields...")

    # Define custom fields for Company in the correct insertion order
    custom_fields = {
        "Company": [
            # Thai Compliance Tab
            {
                "fieldname": "accounts_thai_tab",
                "fieldtype": "Tab Break",
                "label": "Thai Compliance",
                "insert_after": "asset_received_but_not_billed",
            },
            {
                "fieldname": "thai_accounting_section",
                "fieldtype": "Section Break",
                "label": "Thai Accounting Settings",
                "insert_after": "accounts_thai_tab",
            },
            {
                "fieldname": "thai_accounting_column_left",
                "fieldtype": "Column Break",
                "insert_after": "thai_accounting_section",
            },
            {
                "fieldname": "enable_thai_accounting_translation",
                "fieldtype": "Check",
                "label": "Enable Thai Chart of Accounts Translation",
                "insert_after": "thai_accounting_column_left",
                "default": 0,
                "description": "Show Thai account names in Chart of Accounts tree view",
            },
            {
                "fieldname": "auto_populate_thai_accounts",
                "fieldtype": "Button",
                "label": "Auto-populate Thai Account Names",
                "insert_after": "enable_thai_accounting_translation",
                "description": "Automatically translate common account names to Thai",
            },
            {
                "fieldname": "thai_accounting_column_right",
                "fieldtype": "Column Break",
                "insert_after": "auto_populate_thai_accounts",
            },
            # Thailand Service Business (base field)
            {
                "fieldname": "thailand_service_business",
                "fieldtype": "Check",
                "label": "Thailand Service Business",
                "insert_after": "thai_accounting_column_right",
                "description": "Enable Thailand withholding tax features for service businesses",
                "default": "0",
            },
            # WHT Rate field
            {
                "fieldname": "default_wht_rate",
                "fieldtype": "Percent",
                "label": "Default WHT Rate (%)",
                "insert_after": "thailand_service_business",
                "depends_on": "eval:doc.thailand_service_business",
                "description": "Default withholding tax rate for services (e.g., 3% for most services)",
                "default": "3",
                "precision": 2,
            },
            # WHT Account field
            {
                "fieldname": "default_wht_account",
                "fieldtype": "Link",
                "label": "Default Withholding Tax Assets Account",
                "options": "Account",
                "insert_after": "default_wht_rate",
                "depends_on": "eval:doc.thailand_service_business",
                "description": "Default account for withholding tax asset (e.g., Withholding Tax Assets)",
            },
            # Output VAT Undue Account field
            {
                "fieldname": "default_output_vat_undue_account",
                "fieldtype": "Link",
                "label": "Default Output VAT Undue Account",
                "options": "Account",
                "insert_after": "default_wht_account",
                "description": "Default account for Output VAT undue (e.g., Output VAT Undue)",
            },
            # Output VAT Output Account field
            {
                "fieldname": "default_output_vat_account",
                "fieldtype": "Link",
                "label": "Default Output VAT Account",
                "options": "Account",
                "insert_after": "default_output_vat_undue_account",
                "description": "Default account for Output VAT (e.g., Output VAT)",
            },
            # Input VAT Undue Account field
            {
                "fieldname": "default_input_vat_undue_account",
                "fieldtype": "Link",
                "label": "Default Input VAT Undue Account",
                "options": "Account",
                "insert_after": "parent_company",
                "description": "Default account for Input VAT undue (e.g., Input VAT Undue)",
            },
            # Input VAT Account field
            {
                "fieldname": "default_input_vat_account",
                "fieldtype": "Link",
                "label": "Default Input VAT Account",
                "options": "Account",
                "insert_after": "default_input_vat_undue_account",
                "description": "Default account for Input VAT (e.g., Input VAT)",
            },
            # WHT Debt Account field
            {
                "fieldname": "default_wht_debt_account",
                "fieldtype": "Link",
                "label": "Default Withholding Tax Debt Account",
                "options": "Account",
                "insert_after": "default_input_vat_account",
                "description": "Default account for withholding tax debt (e.g., Withholding Tax Debt)",
            },
        ]
    }

    try:
        # Create custom fields
        create_custom_fields(custom_fields, update=True)

        print("✅ Company Thai tax fields created successfully!")
        print("   - Company: thailand_service_business (checkbox)")
        print("   - Company: default_wht_rate (percentage)")
        print("   - Company: default_wht_account (link to Account)")
        print("   - Company: default_output_vat_undue_account (link to Account)")
        print("   - Company: default_output_vat_account (link to Account)")

        # Setup default accounts for companies
        # _setup_default_accounts()  # Commented out - Chart of Accounts is dynamic per user

        frappe.db.commit()
        print("✅ Company Thai tax fields installation completed!")

    except Exception as e:
        print(f"❌ Error installing Company Thai tax fields: {str(e)}")
        frappe.db.rollback()
        raise


def _setup_default_accounts():  # Commented out - Chart of Accounts is dynamic per user
    """Setup default accounts for companies with Thai tax features enabled."""

    try:
        # Get all companies with Thailand service business enabled
        thai_companies = frappe.get_all(
            "Company",
            filters={"thailand_service_business": 1},
            fields=["name", "default_currency", "abbr"],
        )

        for company in thai_companies:
            print(f"   Setting up accounts for {company.name}...")

            # Setup WHT account if not already set
            if not frappe.db.get_value("Company", company.name, "default_wht_account"):
                wht_account = _find_or_suggest_wht_account(company)
                if wht_account:
                    frappe.db.set_value(
                        "Company", company.name, "default_wht_account", wht_account
                    )
                    print(f"   ✓ Set default WHT account: {wht_account}")

            # Setup VAT accounts if not already set
            vat_accounts = _find_vat_accounts(company)

            if vat_accounts.get("vat_undue") and not frappe.db.get_value(
                "Company", company.name, "default_output_vat_undue_account"
            ):
                frappe.db.set_value(
                    "Company",
                    company.name,
                    "default_output_vat_undue_account",
                    vat_accounts["vat_undue"],
                )
                print(f"   ✓ Set default output VAT undue account: {vat_accounts['vat_undue']}")

            if vat_accounts.get("vat_output") and not frappe.db.get_value(
                "Company", company.name, "default_output_vat_account"
            ):
                frappe.db.set_value(
                    "Company",
                    company.name,
                    "default_output_vat_account",
                    vat_accounts["vat_output"],
                )
                print(f"   ✓ Set default output VAT account: {vat_accounts['vat_output']}")

    except Exception as e:
        print(f"   ⚠️  Warning: Could not setup default accounts: {str(e)}")


def _find_or_suggest_wht_account(company):  # Commented out - Chart of Accounts is dynamic per user
    """Find existing or suggest WHT account for a company."""

    try:
        # Try to find existing WHT accounts
        wht_accounts = frappe.get_all(
            "Account",
            filters={
                "company": company.name,
                "account_name": ["like", "%withholding%"],
                "is_group": 0,
            },
            fields=["name", "account_name"],
        )

        if wht_accounts:
            print(f"   ✓ Found existing WHT account: {wht_accounts[0].name}")
            return wht_accounts[0].name

        # Try alternative search terms
        alt_accounts = frappe.get_all(
            "Account",
            filters={"company": company.name, "account_name": ["like", "%tax%"], "is_group": 0},
            fields=["name", "account_name"],
        )

        for account in alt_accounts:
            if "asset" in account.account_name.lower() and "tax" in account.account_name.lower():
                print(f"   ✓ Found suitable tax asset account: {account.name}")
                return account.name

        print(f"   ⚠️  No suitable WHT account found for {company.name}. Please create manually.")
        return None

    except Exception as e:
        print(f"   ⚠️  Error finding WHT account for {company.name}: {str(e)}")
        return None


def _find_vat_accounts(company):  # Commented out - Chart of Accounts is dynamic per user
    """Find existing VAT accounts for a company."""

    try:
        # Try to find existing VAT accounts
        vat_accounts = frappe.get_all(
            "Account",
            filters={"company": company.name, "account_name": ["like", "%VAT%"], "is_group": 0},
            fields=["name", "account_name"],
        )

        result = {"vat_undue": None, "vat_output": None}

        for account in vat_accounts:
            account_name_lower = account.account_name.lower()

            # Look for VAT undue accounts
            if "undue" in account_name_lower and "output" in account_name_lower:
                result["vat_undue"] = account.name
                print(f"   ✓ Found VAT undue account: {account.name}")

            # Look for output VAT accounts
            elif (
                "output" in account_name_lower
                and "vat" in account_name_lower
                and "undue" not in account_name_lower
            ):
                result["vat_output"] = account.name
                print(f"   ✓ Found output VAT account: {account.name}")

        return result

    except Exception as e:
        print(f"   ⚠️  Error finding VAT accounts for {company.name}: {str(e)}")
        return {"vat_undue": None, "vat_output": None}


def remove_company_thai_tax_fields():
    """Remove all Thai tax-related custom fields from Company doctype during uninstallation."""

    print("Removing Company Thai Tax Fields...")

    # List of all Company Thai tax fields to remove (including translation fields)
    fields_to_remove = [
        # Thai Accounting Translation Fields
        "accounts_thai_tab",
        "thai_accounting_section",
        "thai_accounting_column_left",
        "enable_thai_accounting_translation",
        "auto_populate_thai_accounts",
        "thai_accounting_column_right",
        # WHT and VAT Fields
        "thailand_service_business",
        "default_wht_rate",
        "default_wht_account",
        "default_output_vat_undue_account",
        "default_output_vat_account",
        "default_input_vat_undue_account",
        "default_input_vat_account",
        "default_wht_debt_account",
    ]

    try:
        removed_count = 0
        for field_name in fields_to_remove:
            try:
                # Check if custom field exists
                custom_field_name = f"Company-{field_name}"
                if frappe.db.exists("Custom Field", custom_field_name):
                    frappe.delete_doc("Custom Field", custom_field_name)
                    print(f"✅ Removed Company.{field_name}")
                    removed_count += 1
                else:
                    print(f"⏭️ Company.{field_name} not found (already removed)")
            except Exception as e:
                print(f"❌ Error removing Company.{field_name}: {str(e)}")

        frappe.db.commit()
        print(f"✅ Successfully removed {removed_count} Company Thai tax fields")

    except Exception as e:
        print(f"❌ Error removing Company Thai tax fields: {str(e)}")
        frappe.db.rollback()
        raise


def check_company_thai_tax_fields():
    """Check if Company Thai tax fields are properly installed."""

    print("Checking Company Thai Tax Fields Installation...")

    # company_meta = frappe.get_meta("Company")  # Not needed - using frappe.db.exists instead

    # Check each field (including translation fields)
    fields_to_check = [
        # Thai Accounting Translation Fields
        "accounts_thai_tab",
        "thai_accounting_section",
        "thai_accounting_column_left",
        "enable_thai_accounting_translation",
        "auto_populate_thai_accounts",
        "thai_accounting_column_right",
        # WHT and VAT Fields
        "thailand_service_business",
        "default_wht_rate",
        "default_wht_account",
        "default_output_vat_undue_account",
        "default_output_vat_account",
        "default_input_vat_undue_account",
        "default_input_vat_account",
        "default_wht_debt_account",
    ]

    all_fields_exist = True

    for field_name in fields_to_check:
        if frappe.db.exists("Custom Field", f"Company-{field_name}"):
            print(f"✅ Company.{field_name} - Installed")
        else:
            print(f"❌ Company.{field_name} - Missing")
            all_fields_exist = False

    return all_fields_exist


def emergency_fallback_install_company_thai_tax_fields():
    """Emergency fallback to install Company Thai tax fields if they don't exist."""

    print("🚨 Running Emergency Fallback: Company Thai Tax Fields Installation...")

    try:
        company_meta = frappe.get_meta("Company")

        # Check if any key fields are missing
        missing_fields = []
        key_fields = [
            "thailand_service_business",
            "default_wht_rate",
            "default_wht_account",
            "default_output_vat_undue_account",
            "default_output_vat_account",
        ]

        for field_name in key_fields:
            if not company_meta.get_field(field_name):
                missing_fields.append(field_name)

        if missing_fields:
            print(f"❌ Missing fields: {', '.join(missing_fields)} - installing now...")
            install_company_thai_tax_fields()
        else:
            print("✅ All Company Thai tax fields already exist")

    except Exception as e:
        print(f"🚨 Emergency fallback error: {str(e)}")
        print("   Attempting full installation...")
        try:
            install_company_thai_tax_fields()
        except Exception as install_error:
            print(f"❌ Failed to install Company Thai tax fields: {str(install_error)}")
            raise


if __name__ == "__main__":
    install_company_thai_tax_fields()
