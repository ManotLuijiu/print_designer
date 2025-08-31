#!/usr/bin/env python3
"""
Install Payment Entry Retention Fields

Creates custom fields in Payment Entry to handle retention calculations during payment processing.
This integrates with the construction service retention system from Sales Invoices.

Key Features:
1. Retention Summary Section - Shows retention details from invoices being paid
2. Per-Invoice Retention Tracking - Tracks retention for each invoice reference
3. Automatic Calculations - Calculates net payment after retention deduction
4. Retention Liability Tracking - Creates retention liability records for future release

Usage:
bench execute print_designer.commands.install_payment_entry_retention_fields.install_payment_entry_retention_fields
"""

import frappe
import click
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def _cleanup_legacy_fields():
    """Clean up legacy retention fields without pd_custom_ prefix."""
    click.echo("🧹 Cleaning up legacy retention fields...")
    
    legacy_fields = {
        "Payment Entry": [
            "retention_summary_section", "has_retention", "retention_column_break", 
            "total_retention_amount", "net_payment_after_retention", "retention_account", 
            "retention_details_section", "retention_details_column_break", "retention_note",
            "thai_tax_section", "has_thai_taxes", "total_wht_amount", "total_vat_undue_amount",
            "thai_tax_accounts_section", "wht_account", "output_vat_undue_account",
            "thai_tax_column_break", "output_vat_account", "retention_liability_account"
        ],
        "Payment Entry Reference": [
            "has_retention", "retention_amount", "retention_percentage",
            "wht_amount", "wht_percentage", "vat_undue_amount", "net_payable_amount"
        ]
    }
    
    total_cleaned = 0
    for doctype, fieldnames in legacy_fields.items():
        for fieldname in fieldnames:
            try:
                custom_fields = frappe.get_all("Custom Field",
                    filters={"dt": doctype, "fieldname": fieldname},
                    fields=["name"]
                )
                
                for field in custom_fields:
                    frappe.delete_doc("Custom Field", field.name, ignore_permissions=True)
                    total_cleaned += 1
                    click.echo(f"   🗑️ Removed legacy field: {doctype}.{fieldname}")
                    
            except Exception as e:
                # Continue cleanup even if some fields fail
                pass
    
    if total_cleaned > 0:
        click.echo(f"✅ Cleaned up {total_cleaned} legacy retention fields")
        frappe.clear_cache()
    else:
        click.echo("ℹ️ No legacy retention fields found to clean up")


@click.command()
def install_payment_entry_retention_fields():
    """Install custom fields for Payment Entry retention system."""
    click.echo("🏗️ Installing Payment Entry Retention Fields...")
    
    try:
        # Clean up legacy fields first to prevent conflicts
        _cleanup_legacy_fields()
        
        # Then install the new pd_custom_ prefixed fields
        # Define custom fields for Payment Entry
        custom_fields = {
            "Payment Entry": [
                # Retention Summary Section (after total_allocated_amount)
                {
                    "fieldname": "pd_custom_retention_summary_section",
                    "label": "Retention Summary",
                    "fieldtype": "Section Break",
                    "insert_after": "total_allocated_amount",
                    "collapsible": 0,
                    "description": "Summary of Thai tax amounts (retention, WHT, VAT) for invoices"
                },
                {
                    "fieldname": "pd_custom_has_retention",
                    "label": "Has Retention",
                    "fieldtype": "Check",
                    "insert_after": "pd_custom_retention_summary_section",
                    "read_only": 1,
                    "default": 0,
                    "description": "Automatically checked when payment includes invoices with retention"
                },
                {
                    "fieldname": "pd_custom_retention_column_break",
                    "label": "",
                    "fieldtype": "Column Break",
                    "insert_after": "pd_custom_has_retention"
                },
                {
                    "fieldname": "pd_custom_total_retention_amount",
                    "label": "Total Retention Amount",
                    "fieldtype": "Currency",
                    "insert_after": "pd_custom_retention_column_break",
                    "read_only": 1,
                    "options": "party_account_currency",
                    "precision": 2,
                    "description": "Total retention amount across all invoices in this payment"
                },
                {
                    "fieldname": "pd_custom_retention_details_section",
                    "label": "Retention Details",
                    "fieldtype": "Section Break", 
                    "insert_after": "pd_custom_total_retention_amount",
                    "collapsible": 1
                },
                {
                    "fieldname": "pd_custom_net_payment_after_retention",
                    "label": "Net Payment After Retention",
                    "fieldtype": "Currency",
                    "insert_after": "pd_custom_retention_details_section",
                    "read_only": 1,
                    "options": "party_account_currency", 
                    "precision": 2,
                    "description": "Actual amount to be paid after deducting retention"
                },
                {
                    "fieldname": "pd_custom_retention_account",
                    "label": "Retention Account", 
                    "fieldtype": "Link",
                    "options": "Account",
                    "insert_after": "pd_custom_net_payment_after_retention",
                    "description": "Asset account for booking retention amounts held (Dr. Construction Retention)"
                },
                {
                    "fieldname": "pd_custom_retention_details_column_break",
                    "label": "",
                    "fieldtype": "Column Break",
                    "insert_after": "pd_custom_retention_account"
                },
                {
                    "fieldname": "pd_custom_retention_note",
                    "label": "Thai Tax Note",
                    "fieldtype": "Small Text",
                    "insert_after": "pd_custom_retention_details_column_break",
                    "description": "Notes about Thai tax calculations (VAT + WHT + Retention)"
                },
                # Thai Tax Extension Fields
                {
                    "fieldname": "pd_custom_thai_tax_section",
                    "label": "Thai Tax System",
                    "fieldtype": "Section Break",
                    "insert_after": "pd_custom_retention_note",
                    "collapsible": 1,
                    "description": "Thai tax processing (VAT + WHT + Retention)"
                },
                {
                    "fieldname": "pd_custom_has_thai_taxes",
                    "label": "Has Thai Taxes",
                    "fieldtype": "Check",
                    "insert_after": "pd_custom_thai_tax_section",
                    "read_only": 1,
                    "default": 0,
                    "description": "Payment includes Thai tax components (VAT/WHT/Retention)"
                },
                {
                    "fieldname": "pd_custom_total_wht_amount",
                    "label": "Total WHT Amount",
                    "fieldtype": "Currency",
                    "insert_after": "pd_custom_has_thai_taxes",
                    "read_only": 1,
                    "options": "party_account_currency",
                    "precision": 2,
                    "description": "Total withholding tax amount (tax credit)"
                },
                {
                    "fieldname": "pd_custom_total_vat_undue_amount",
                    "label": "Total VAT Undue Amount",
                    "fieldtype": "Currency",
                    "insert_after": "pd_custom_total_wht_amount",
                    "read_only": 1,
                    "options": "party_account_currency",
                    "precision": 2,
                    "description": "Total Output VAT Undue to be converted"
                },
                {
                    "fieldname": "pd_custom_thai_tax_accounts_section",
                    "label": "Thai Tax Accounts",
                    "fieldtype": "Section Break",
                    "insert_after": "pd_custom_total_vat_undue_amount",
                    "collapsible": 1
                },
                {
                    "fieldname": "pd_custom_wht_account",
                    "label": "WHT Account",
                    "fieldtype": "Link",
                    "options": "Account",
                    "insert_after": "pd_custom_thai_tax_accounts_section",
                    "depends_on": "eval:doc.pd_custom_total_wht_amount > 0",
                    "description": "Asset account for WHT tax credit (Dr. WHT - Assets)"
                },
                {
                    "fieldname": "pd_custom_output_vat_undue_account",
                    "label": "Output VAT Undue Account",
                    "fieldtype": "Link",
                    "options": "Account",
                    "insert_after": "pd_custom_wht_account",
                    "depends_on": "eval:doc.pd_custom_total_vat_undue_amount > 0",
                    "description": "Liability account for Output VAT Undue (Dr. to clear)"
                },
                {
                    "fieldname": "pd_custom_thai_tax_column_break",
                    "fieldtype": "Column Break",
                    "insert_after": "pd_custom_output_vat_undue_account"
                },
                {
                    "fieldname": "pd_custom_output_vat_account",
                    "label": "Output VAT Account",
                    "fieldtype": "Link",
                    "options": "Account",
                    "insert_after": "pd_custom_thai_tax_column_break",
                    "depends_on": "eval:doc.pd_custom_total_vat_undue_amount > 0",
                    "description": "Liability account for Output VAT Due (Cr. to register)"
                }
            ],
            
            "Payment Entry Reference": [
                # Thai Tax fields for individual invoice references
                {
                    "fieldname": "pd_custom_has_retention",
                    "label": "Has Retention",
                    "fieldtype": "Check", 
                    "insert_after": "allocated_amount",
                    "read_only": 1,
                    "default": 0,
                    "description": "This invoice has retention amount"
                },
                {
                    "fieldname": "pd_custom_retention_amount",
                    "label": "Retention Amount",
                    "fieldtype": "Currency",
                    "insert_after": "pd_custom_has_retention",
                    "read_only": 1,
                    "precision": 2,
                    "description": "Retention amount for this specific invoice"
                },
                {
                    "fieldname": "pd_custom_retention_percentage",
                    "label": "Retention %",
                    "fieldtype": "Percent",
                    "insert_after": "pd_custom_retention_amount", 
                    "read_only": 1,
                    "precision": 2,
                    "description": "Retention percentage from original invoice"
                },
                {
                    "fieldname": "pd_custom_wht_amount",
                    "label": "WHT Amount",
                    "fieldtype": "Currency",
                    "insert_after": "pd_custom_retention_percentage",
                    "read_only": 1,
                    "precision": 2,
                    "description": "Withholding tax amount for this specific invoice"
                },
                {
                    "fieldname": "pd_custom_wht_percentage",
                    "label": "WHT %",
                    "fieldtype": "Percent",
                    "insert_after": "pd_custom_wht_amount",
                    "read_only": 1,
                    "precision": 2,
                    "description": "Withholding tax percentage from original invoice"
                },
                {
                    "fieldname": "pd_custom_vat_undue_amount",
                    "label": "VAT Undue Amount",
                    "fieldtype": "Currency",
                    "insert_after": "pd_custom_wht_percentage",
                    "read_only": 1,
                    "precision": 2,
                    "description": "Output VAT Undue amount for this specific invoice"
                },
                {
                    "fieldname": "pd_custom_net_payable_amount",
                    "label": "Net Payable Amount", 
                    "fieldtype": "Currency",
                    "insert_after": "pd_custom_vat_undue_amount",
                    "read_only": 1,
                    "precision": 2,
                    "description": "Amount payable after deducting retention and WHT"
                }
            ]
        }
        
        # Install the custom fields
        click.echo("📝 Creating custom fields...")
        create_custom_fields(custom_fields, update=True)
        
        click.echo("✅ Thai Tax System (Payment Entry) fields installed successfully!")
        click.echo("   📋 Payment Entry Fields Added:")
        click.echo("   - pd_custom_retention_summary_section: Retention summary display")
        click.echo("   - pd_custom_has_retention: Flag for retention presence")
        click.echo("   - pd_custom_total_retention_amount: Sum of all retention amounts")  
        click.echo("   - pd_custom_net_payment_after_retention: Actual payable amount")
        click.echo("   - pd_custom_retention_account: Account for retention asset")
        click.echo("   - pd_custom_has_thai_taxes: Thai tax system flag")
        click.echo("   - pd_custom_total_wht_amount: Total WHT (tax credit)")
        click.echo("   - pd_custom_total_vat_undue_amount: Total VAT Undue conversion")
        click.echo("   - pd_custom_wht_account: WHT asset account")
        click.echo("   - pd_custom_output_vat_undue_account: VAT Undue liability account")
        click.echo("   - pd_custom_output_vat_account: VAT Due liability account")
        click.echo("   - pd_custom_retention_note: Thai tax calculation details")
        
        click.echo("   📋 Payment Entry Reference Fields Added:")
        click.echo("   - pd_custom_has_retention: Per-invoice retention flag")
        click.echo("   - pd_custom_retention_amount: Per-invoice retention amount")
        click.echo("   - pd_custom_retention_percentage: Per-invoice retention rate")
        click.echo("   - pd_custom_wht_amount: Per-invoice WHT amount")
        click.echo("   - pd_custom_wht_percentage: Per-invoice WHT rate")
        click.echo("   - pd_custom_vat_undue_amount: Per-invoice VAT Undue amount")
        click.echo("   - pd_custom_net_payable_amount: Per-invoice net payable (after retention & WHT)")
        
        # Set up default retention accounts for companies with construction service
        _setup_retention_accounts()
        
        frappe.db.commit()
        click.echo("🎯 Payment Entry retention system installation completed!")
        
    except Exception as e:
        click.echo(f"❌ Installation failed: {str(e)}")
        frappe.log_error(
            message=f"Failed to install Payment Entry retention fields: {str(e)}",
            title="Payment Entry Retention Fields Installation Failed"
        )
        frappe.db.rollback()
        raise


def _setup_retention_accounts():
    """Setup default retention accounts for construction companies."""
    
    try:
        click.echo("\n🏦 Setting up retention accounts...")
        
        # Get companies with construction service enabled
        construction_companies = frappe.get_all("Company",
            filters={"construction_service": 1},
            fields=["name", "default_retention_account", "abbr"]
        )
        
        for company in construction_companies:
            if company.default_retention_account:
                click.echo(f"   ✅ {company.name}: Using existing account {company.default_retention_account}")
            else:
                # Try to find or suggest retention account
                retention_account = _find_retention_account(company)
                if retention_account:
                    frappe.db.set_value("Company", company.name, "default_retention_account", retention_account)
                    click.echo(f"   ✅ {company.name}: Set default retention account to {retention_account}")
                else:
                    click.echo(f"   ⚠️ {company.name}: No retention account found - please set manually")
        
    except Exception as e:
        click.echo(f"   ⚠️ Warning: Could not setup retention accounts: {str(e)}")


def _find_retention_account(company):
    """Find suitable retention account for a company."""
    
    try:
        # Look for existing retention accounts (Asset/Receivable type for asset we hold)
        retention_accounts = frappe.get_all("Account",
            filters={
                "company": company.name,
                "account_name": ["like", "%retention%"],
                "account_type": ["in", ["Asset", "Receivable"]],
                "is_group": 0
            },
            fields=["name", "account_name"]
        )
        
        if retention_accounts:
            return retention_accounts[0].name
            
        # Look for construction-related asset accounts
        construction_accounts = frappe.get_all("Account",
            filters={
                "company": company.name,
                "account_name": ["like", "%construction%"],
                "account_type": ["in", ["Asset", "Receivable"]], 
                "is_group": 0
            },
            fields=["name", "account_name"]
        )
        
        if construction_accounts:
            return construction_accounts[0].name
        
        # Default to Accounts Receivable (since retention is an asset)
        default_receivable = frappe.get_all("Account",
            filters={
                "company": company.name,
                "account_name": "Accounts Receivable",
                "is_group": 0
            },
            fields=["name"]
        )
        
        if default_receivable:
            return default_receivable[0].name
            
        return None
        
    except Exception as e:
        click.echo(f"   ⚠️ Error finding retention account for {company.name}: {str(e)}")
        return None


@click.command() 
def check_payment_entry_retention_fields():
    """Check if Payment Entry retention fields are properly installed."""
    click.echo("🔍 Checking Payment Entry Retention Fields...")
    
    # Check Payment Entry fields (Thai Tax System)
    pe_meta = frappe.get_meta("Payment Entry")
    pe_fields = ["pd_custom_retention_summary_section", "pd_custom_has_retention", "pd_custom_retention_column_break",
                 "pd_custom_total_retention_amount", "pd_custom_retention_details_section", "pd_custom_net_payment_after_retention", 
                 "pd_custom_retention_account", "pd_custom_retention_details_column_break", "pd_custom_retention_note", 
                 "pd_custom_thai_tax_section", "pd_custom_has_thai_taxes", "pd_custom_total_wht_amount", 
                 "pd_custom_total_vat_undue_amount", "pd_custom_thai_tax_accounts_section", "pd_custom_wht_account", 
                 "pd_custom_output_vat_undue_account", "pd_custom_thai_tax_column_break", "pd_custom_output_vat_account"]
    
    click.echo("📋 Payment Entry Fields:")
    all_pe_fields_exist = True
    for fieldname in pe_fields:
        field = pe_meta.get_field(fieldname)
        if field:
            click.echo(f"   ✅ {fieldname}: {field.label} ({field.fieldtype})")
        else:
            click.echo(f"   ❌ {fieldname}: Missing")
            all_pe_fields_exist = False
    
    # Check Payment Entry Reference fields (Thai Tax System)
    per_meta = frappe.get_meta("Payment Entry Reference")
    per_fields = ["pd_custom_has_retention", "pd_custom_retention_amount", "pd_custom_retention_percentage", 
                  "pd_custom_wht_amount", "pd_custom_wht_percentage", "pd_custom_vat_undue_amount", "pd_custom_net_payable_amount"]
    
    click.echo("\n📋 Payment Entry Reference Fields:")
    all_per_fields_exist = True
    for fieldname in per_fields:
        field = per_meta.get_field(fieldname)
        if field:
            click.echo(f"   ✅ {fieldname}: {field.label} ({field.fieldtype})")
        else:
            click.echo(f"   ❌ {fieldname}: Missing") 
            all_per_fields_exist = False
    
    # Overall status
    overall_status = all_pe_fields_exist and all_per_fields_exist
    status_icon = "✅" if overall_status else "❌"
    click.echo(f"\n🎯 Overall Status: {status_icon} {'PASSED' if overall_status else 'FAILED'}")
    
    return overall_status


def install_payment_entry_retention_fields_direct():
    """Direct function call version for bench execute."""
    return install_payment_entry_retention_fields.callback()


def check_payment_entry_retention_fields_direct():
    """Direct function call version for bench execute."""
    return check_payment_entry_retention_fields.callback()


@click.command()
def uninstall_payment_entry_thai_tax_fields():
    """Uninstall Thai Tax System custom fields from Payment Entry."""
    click.echo("🗑️ Uninstalling Thai Tax System (Payment Entry) fields...")
    
    try:
        # List of all Thai tax fields to remove (both old and new naming conventions)
        thai_tax_fields = {
            "Payment Entry": [
                # New pd_custom_ prefixed fields
                "pd_custom_retention_summary_section", "pd_custom_has_retention", "pd_custom_total_retention_amount",
                "pd_custom_net_payment_after_retention", "pd_custom_retention_account", "pd_custom_retention_details_section",
                "pd_custom_retention_details_column_break", "pd_custom_retention_note", "pd_custom_thai_tax_section",
                "pd_custom_has_thai_taxes", "pd_custom_total_wht_amount", "pd_custom_total_vat_undue_amount", 
                "pd_custom_thai_tax_accounts_section", "pd_custom_wht_account", "pd_custom_output_vat_undue_account",
                "pd_custom_thai_tax_column_break", "pd_custom_output_vat_account",
                # Legacy fields (for cleanup) - missing retention_column_break added
                "retention_summary_section", "has_retention", "retention_column_break", "total_retention_amount",
                "net_payment_after_retention", "retention_account", "retention_details_section",
                "retention_details_column_break", "retention_note", "thai_tax_section",
                "has_thai_taxes", "total_wht_amount", "total_vat_undue_amount", 
                "thai_tax_accounts_section", "wht_account", "output_vat_undue_account",
                "thai_tax_column_break", "output_vat_account"
            ],
            "Payment Entry Reference": [
                # New pd_custom_ prefixed fields
                "pd_custom_has_retention", "pd_custom_retention_amount", "pd_custom_retention_percentage", 
                "pd_custom_wht_amount", "pd_custom_wht_percentage", "pd_custom_vat_undue_amount", "pd_custom_net_payable_amount",
                # Legacy fields (for cleanup)
                "has_retention", "retention_amount", "retention_percentage", 
                "wht_amount", "wht_percentage", "vat_undue_amount", "net_payable_amount"
            ]
        }
        
        # Delete custom fields
        for doctype, fieldnames in thai_tax_fields.items():
            deleted_count = 0
            for fieldname in fieldnames:
                try:
                    # Find and delete the custom field
                    custom_fields = frappe.get_all("Custom Field",
                        filters={"dt": doctype, "fieldname": fieldname},
                        fields=["name"]
                    )
                    
                    for field in custom_fields:
                        frappe.delete_doc("Custom Field", field.name, ignore_permissions=True)
                        deleted_count += 1
                        
                except Exception as e:
                    click.echo(f"   ⚠️ Could not delete {fieldname}: {str(e)}")
            
            if deleted_count > 0:
                click.echo(f"   🗑️ {doctype}: {deleted_count} fields removed")
                frappe.clear_cache(doctype=doctype)
        
        frappe.db.commit()
        click.echo("✅ Thai Tax System custom fields uninstalled successfully!")
        
    except Exception as e:
        click.echo(f"❌ Uninstallation failed: {str(e)}")
        frappe.log_error(
            message=f"Failed to uninstall Thai Tax System fields: {str(e)}",
            title="Thai Tax System Uninstallation Failed"
        )
        frappe.db.rollback()
        raise


def uninstall_payment_entry_thai_tax_fields_direct():
    """Direct function call version for bench execute."""
    return uninstall_payment_entry_thai_tax_fields.callback()


@click.command()
def cleanup_legacy_retention_fields():
    """Standalone command to clean up legacy retention fields without pd_custom_ prefix."""
    click.echo("🧹 Cleaning up legacy Payment Entry retention fields...")
    
    try:
        _cleanup_legacy_fields()
        frappe.db.commit()
        click.echo("✅ Legacy field cleanup completed successfully!")
        
    except Exception as e:
        click.echo(f"❌ Legacy field cleanup failed: {str(e)}")
        frappe.log_error(
            message=f"Failed to cleanup legacy retention fields: {str(e)}",
            title="Legacy Field Cleanup Failed"
        )
        frappe.db.rollback()
        raise


def cleanup_legacy_retention_fields_direct():
    """Direct function call version for bench execute."""
    return cleanup_legacy_retention_fields.callback()


if __name__ == "__main__":
    install_payment_entry_retention_fields()