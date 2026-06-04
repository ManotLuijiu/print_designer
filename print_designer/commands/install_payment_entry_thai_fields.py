#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Install Thai Tax Compliance Fields for Payment Entry
Adds Thai-specific tax fields for withholding tax and VAT compliance
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe import _


def execute():
    """Main installation function for Payment Entry Thai tax fields"""
    print("Installing Thai Tax Compliance fields for Payment Entry...")

    create_payment_entry_thai_fields()

    # Clear cache to ensure changes are reflected
    frappe.clear_cache()
    print("✅ Thai Tax Compliance fields installed successfully for Payment Entry")


def create_payment_entry_thai_fields():
    """Create Thai tax compliance fields in Payment Entry matching fixtures order"""

    custom_fields = {
        "Payment Entry": [
            # Thai Compliance Tab - placed after title field
            {
                "fieldname": "pd_custom_thai_compliance_tab",
                "fieldtype": "Tab Break",
                "label": "Thai Tax Compliance",
                "insert_after": "title",
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
            },
            {
                "fieldname": "pd_custom_vat_section",
                "fieldtype": "Section Break",
                "label": "Value Added Tax",
                "insert_after": "pd_custom_thai_compliance_tab",
            },
            # Column 1 - Removed button and redundant fields
            {
                "fieldname": "pd_custom_thai_tax_column_1",
                "fieldtype": "Column Break",
                "insert_after": "pd_custom_vat_section",
                "width": "50%",
            },
            {
                "fieldname": "pd_custom_tax_invoice_number",
                "fieldtype": "Data",
                "label": "Tax Invoice Number",
                "insert_after": "pd_custom_thai_tax_column_1",
                "translatable": 0,
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
                "read_only": 0,  # Ensure it's editable
            },
            {
                "fieldname": "pd_custom_tax_invoice_date",
                "fieldtype": "Date",
                "label": "Tax Invoice Date",
                "insert_after": "pd_custom_tax_invoice_number",
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
                "read_only": 0,  # Ensure it's editable
            },
            {
                "fieldname": "pd_custom_thai_tax_column_2",
                "fieldtype": "Column Break",
                "insert_after": "pd_custom_tax_invoice_date",
                "width": "50%",
            },
            {
                "fieldname": "pd_custom_tax_base_amount",
                "fieldtype": "Currency",
                "label": "Tax Base Amount",
                "insert_after": "pd_custom_thai_tax_column_2",  # Updated - pd_custom_income_type DEPRECATED
                "options": "Company:company:default_currency",
                "read_only": 1,
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
                "bold": 1,
            },
            {
                "fieldname": "pd_custom_vat_amount",
                "fieldtype": "Currency",
                "label": "VAT Amount",
                "insert_after": "pd_custom_tax_base_amount",
                "options": "Company:company:default_currency",
                "read_only": 1,
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
                "bold": 1,
            },
            {
                "fieldname": "pd_custom_input_vat_ref",
                "fieldtype": "Link",
                "label": "Input VAT Report Ref.",
                "insert_after": "pd_custom_vat_amount",
                "options": "Thai Purchase VAT",
                "translatable": 0,
                "hidden": 0,
                "read_only": 1,
                "no_copy": 0,
                "print_hide": 0,
            },
            # Withholding Tax Section
            {
                "fieldname": "pd_custom_wht_section",
                "fieldtype": "Section Break",
                "label": "Withholding Tax",
                "insert_after": "pd_custom_input_vat_ref",
            },
            # Column 2
            {
                "fieldname": "pd_custom_thai_tax_column_3",
                "fieldtype": "Column Break",
                "insert_after": "pd_custom_wht_section",
                "width": "50%",
            },
            {
                "fieldname": "pd_custom_apply_withholding_tax",
                "fieldtype": "Check",
                "label": "Apply Withholding Tax",
                "insert_after": "pd_custom_thai_tax_column_3",
                "default": "0",
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
            },
            # Receive WHT
            {
                "fieldname": "pd_custom_wht_certificate_no",
                "fieldtype": "Data",
                "label": "Certificate Number",
                "insert_after": "pd_custom_apply_withholding_tax",
                "depends_on": "eval:doc.payment_type=='Receive'",
                "description": "WHT Certificate Number received from customer",
                "translatable": 0,
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
            },
            # Link to Receive WHT Register (for Receive scenario)
            {
                "fieldname": "pd_custom_receive_wht_register",
                "fieldtype": "Link",
                "label": "Receive WHT Register",
                "insert_after": "pd_custom_wht_certificate_no",
                "depends_on": "eval:doc.payment_type=='Receive'",
                "options": "Receive WHT Register",
                "translatable": 0,
                "hidden": 0,
                "read_only": 1,
                "no_copy": 0,
                "print_hide": 0,
                "description": "Link to Receive WHT Register when customer provides WHT certificate",
            },
            {
                "fieldname": "pd_custom_wht_certificate_date",
                "fieldtype": "Date",
                "label": "WHT Certificate Date",
                "insert_after": "pd_custom_receive_wht_register",
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
            },
            {
                "fieldname": "pd_custom_withholding_tax_rate",
                "fieldtype": "Percent",
                "label": "Withholding Tax Rate (%)",
                "insert_after": "pd_custom_wht_certificate_date",
                "default": "0",
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
            },
            # Column 3
            {
                "fieldname": "pd_custom_thai_tax_column_4",
                "fieldtype": "Column Break",
                "insert_after": "pd_custom_withholding_tax_rate",
                "width": "50%",
            },
            {
                "fieldname": "pd_custom_withholding_tax_amount",
                "fieldtype": "Currency",
                "label": "Withholding Tax Amount",
                "insert_after": "pd_custom_thai_tax_column_4",
                "options": "Company:company:default_currency",
                "read_only": 1,
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
                "bold": 1,
            },
            {
                "fieldname": "pd_custom_net_payment_amount",
                "fieldtype": "Currency",
                "label": "Net Payment Amount",
                "insert_after": "pd_custom_withholding_tax_amount",
                "options": "Company:company:default_currency",
                "read_only": 1,
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
                "bold": 1,
            },
            # CRITICAL: Mirror Fields for Regional GL Function (regional/payment_entry.py)
            # These fields match the exact field names the regional function expects
            {
                "fieldname": "withholding_tax_amount",
                "fieldtype": "Currency",
                "label": "Withholding Tax Amount (System)",
                "options": "Company:company:default_currency",
                "insert_after": "pd_custom_net_payment_amount",
                "description": "Mirror field for regional GL function",
                "hidden": 1,  # Hidden as it's synced from pd_custom_withholding_tax_amount
                "read_only": 1,
                "no_copy": 1,
                "print_hide": 1,
            },
            {
                "fieldname": "tax_base_amount",
                "fieldtype": "Currency",
                "label": "Tax Base Amount (System)",
                "options": "Company:company:default_currency",
                "insert_after": "withholding_tax_amount",
                "description": "Mirror field for regional GL function",
                "hidden": 1,  # Hidden as it's synced from pd_custom_tax_base_amount
                "read_only": 1,
                "no_copy": 1,
                "print_hide": 1,
            },
            {
                "fieldname": "apply_withholding_tax",
                "fieldtype": "Check",
                "label": "Apply Withholding Tax (System)",
                "insert_after": "tax_base_amount",
                "description": "Mirror field for regional GL function",
                "hidden": 1,  # Hidden as it's synced from pd_custom_apply_withholding_tax
                "read_only": 1,
                "no_copy": 1,
                "print_hide": 1,
            },
            # CRITICAL: Account Configuration Fields for Thai Tax GL Entries
            # These fields are required by regional/payment_entry.py for GL entries
            {
                "fieldname": "pd_custom_wht_account",
                "fieldtype": "Link",
                "label": "Withholding Tax Account",
                "options": "Account",
                "insert_after": "apply_withholding_tax",
                "description": "Account for withholding tax GL entries",
                "hidden": 1,  # Hidden as it's populated from Company defaults
                "no_copy": 0,
                "print_hide": 1,
            },
            {
                "fieldname": "pd_custom_retention_account",
                "fieldtype": "Link",
                "label": "Retention Account",
                "options": "Account",
                "insert_after": "pd_custom_wht_account",
                "description": "Account for retention GL entries",
                "hidden": 1,  # Hidden as it's populated from Company defaults
                "no_copy": 0,
                "print_hide": 1,
            },
            {
                "fieldname": "pd_custom_output_vat_undue_account",
                "fieldtype": "Link",
                "label": "Output VAT Undue Account",
                "options": "Account",
                "insert_after": "pd_custom_retention_account",
                "description": "Account for output VAT undue GL entries",
                "hidden": 1,  # Hidden as it's populated from Company defaults
                "no_copy": 0,
                "print_hide": 1,
            },
            {
                "fieldname": "pd_custom_output_vat_account",
                "fieldtype": "Link",
                "label": "Output VAT Account",
                "options": "Account",
                "insert_after": "pd_custom_output_vat_undue_account",
                "description": "Account for output VAT GL entries",
                "hidden": 1,  # Hidden as it's populated from Company defaults
                "print_hide": 1,
            },
        ]
    }

    # Create the custom fields
    create_custom_fields(custom_fields, update=True)

    print("✅ Created Thai Tax Compliance fields in Payment Entry")


def check_fields_exist():
    """Check if Thai tax compliance fields already exist in Payment Entry"""

    required_fields = [
        "pd_custom_thai_compliance_tab",
        "pd_custom_tax_base_amount",
        "pd_custom_tax_invoice_number",
        # Removed pd_custom_supplier - using standard party field
        "pd_custom_tax_invoice_date",
        # Removed pd_custom_supplier_name - using standard party_name field
        "pd_custom_income_type",
        "pd_custom_wht_certificate",
        "pd_custom_wht_certificate_no",
        "pd_custom_wht_certificate_date",
        "pd_custom_withholding_tax_amount",
        "pd_custom_withholding_tax_rate",
        "pd_custom_net_payment_amount",
        "pd_custom_apply_withholding_tax",
        # Removed pd_custom_get_invoices_from_purchase_billing - not needed
        # CRITICAL: Mirror fields that regional GL function expects
        "withholding_tax_amount",
        "tax_base_amount",
        "apply_withholding_tax",
        # CRITICAL: Account configuration fields for GL entries
        "pd_custom_wht_account",
        "pd_custom_retention_account",
        "pd_custom_output_vat_undue_account",
        "pd_custom_output_vat_account",
    ]

    existing_fields = []
    missing_fields = []

    for field in required_fields:
        if frappe.db.exists("Custom Field", {"dt": "Payment Entry", "fieldname": field}):
            existing_fields.append(field)
        else:
            missing_fields.append(field)

    print("\n📋 Payment Entry Thai Tax Compliance Fields Status:")
    print(f"✅ Existing fields: {len(existing_fields)}/{len(required_fields)}")

    if missing_fields:
        print(f"❌ Missing fields ({len(missing_fields)}):")
        for field in missing_fields:
            print(f"   - {field}")

    return len(missing_fields) == 0


def remove_thai_fields():
    """Remove Thai tax compliance fields from Payment Entry (for uninstall)"""

    fields_to_remove = [
        "pd_custom_thai_compliance_tab",
        "pd_custom_thai_tax_column_1",
        "pd_custom_thai_tax_column_2",
        "pd_custom_tax_base_amount",
        "pd_custom_tax_invoice_number",
        # Removed pd_custom_supplier - will be removed from DB
        "pd_custom_tax_invoice_date",
        # Removed pd_custom_supplier_name - will be removed from DB
        "pd_custom_income_type",
        "pd_custom_wht_certificate",
        "pd_custom_wht_certificate_no",
        "pd_custom_wht_certificate_date",
        "pd_custom_withholding_tax_amount",
        "pd_custom_withholding_tax_rate",
        "pd_custom_net_payment_amount",
        "pd_custom_apply_withholding_tax",
        # Removed pd_custom_get_invoices_from_purchase_billing - will be removed from DB
        # CRITICAL: Mirror fields that regional GL function expects
        "withholding_tax_amount",
        "tax_base_amount",
        "apply_withholding_tax",
        # CRITICAL: Account configuration fields for GL entries
        "pd_custom_wht_account",
        "pd_custom_retention_account",
        "pd_custom_output_vat_undue_account",
        "pd_custom_output_vat_account",
    ]

    for field in fields_to_remove:
        frappe.db.delete("Custom Field", {"dt": "Payment Entry", "fieldname": field})

    frappe.clear_cache()
    print("✅ Removed Thai Tax Compliance fields from Payment Entry")


def populate_payment_entry_account_fields_from_company():
    """
    Populate Payment Entry account fields from Company default account settings.
    This function should be called during document creation or validation.
    """
    try:
        print("Populating Payment Entry account fields from Company defaults...")

        # Get all Payment Entries that might need account field population
        payment_entries = frappe.get_all(
            "Payment Entry",
            filters={"pd_custom_apply_withholding_tax": 1},
            fields=["name", "company"],
        )

        if not payment_entries:
            print("ℹ️  No Payment Entries with WHT found to update")
            return

        updated_count = 0
        for pe in payment_entries:
            # Get company's default account settings
            company_doc = frappe.get_doc("Company", pe.company)

            # Prepare updates
            updates = {}

            # Check and populate account fields
            if hasattr(company_doc, "default_wht_account") and company_doc.default_wht_account:
                updates["pd_custom_wht_account"] = company_doc.default_wht_account

            if (
                hasattr(company_doc, "default_retention_account")
                and company_doc.default_retention_account
            ):
                updates["pd_custom_retention_account"] = company_doc.default_retention_account

            if (
                hasattr(company_doc, "default_output_vat_undue_account")
                and company_doc.default_output_vat_undue_account
            ):
                updates["pd_custom_output_vat_undue_account"] = (
                    company_doc.default_output_vat_undue_account
                )

            if (
                hasattr(company_doc, "default_output_vat_account")
                and company_doc.default_output_vat_account
            ):
                updates["pd_custom_output_vat_account"] = company_doc.default_output_vat_account

            # Apply updates if we have any
            if updates:
                for field, value in updates.items():
                    frappe.db.set_value("Payment Entry", pe.name, field, value)
                updated_count += 1
                print(f"   ✅ Updated {pe.name} with {len(updates)} account fields")

        if updated_count > 0:
            frappe.db.commit()
            print(
                f"✅ Updated {updated_count} Payment Entries with account fields from Company defaults"
            )
        else:
            print("ℹ️  No Payment Entries needed account field updates")

    except Exception as e:
        print(f"❌ Error populating account fields: {str(e)}")
        frappe.db.rollback()


def emergency_install_missing_account_fields():
    """
    Emergency function to install missing account fields if they don't exist.
    This addresses the critical issue where Payment Entry account fields are missing.
    """
    try:
        print("🚨 Emergency: Checking for missing Payment Entry account fields...")

        # Check if the critical account fields exist
        pe_meta = frappe.get_meta("Payment Entry")
        critical_fields = [
            # Mirror fields that regional GL function expects
            "withholding_tax_amount",
            "tax_base_amount",
            "apply_withholding_tax",
            # Account configuration fields for GL entries
            "pd_custom_wht_account",
            "pd_custom_retention_account",
            "pd_custom_output_vat_undue_account",
            "pd_custom_output_vat_account",
        ]

        missing_fields = []
        for field in critical_fields:
            if not pe_meta.get_field(field):
                missing_fields.append(field)

        if missing_fields:
            print(f"❌ Missing critical account fields: {missing_fields}")
            print("🔧 Installing missing fields...")

            # Run the full installation to add missing fields
            create_payment_entry_thai_fields()

            print("✅ Missing account fields installed!")
            return True
        else:
            print("✅ All critical account fields are already installed")
            return False

    except Exception as e:
        print(f"❌ Emergency install failed: {str(e)}")
        raise


if __name__ == "__main__":
    execute()
