#!/usr/bin/env python3
"""
Payment Entry Creation Hook

Hooks into Payment Entry creation from Sales Invoice to populate Thai tax fields
when using "Create > Payment" button from Sales Invoice.
"""

import frappe
from frappe import _


@frappe.whitelist()
def get_payment_entry_with_thai_tax(dt, dn, **kwargs):
    """
    Enhanced get_payment_entry that populates Thai tax fields.
    This overrides the default get_payment_entry for Sales Invoices.
    """
    # Import the original function
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
    
    # Filter out 'cmd' parameter that's automatically added by Frappe API calls
    filtered_kwargs = {k: v for k, v in kwargs.items() if k != 'cmd'}
    
    # Call the original function to get the Payment Entry
    pe = get_payment_entry(dt, dn, **filtered_kwargs)
    
    # If this is a Sales Invoice, populate Thai tax fields
    if dt == "Sales Invoice" and pe.references:
        for ref in pe.references:
            if ref.reference_doctype == "Sales Invoice" and ref.reference_name == dn:
                # Fetch Thai tax data from the Sales Invoice
                thai_tax_data = _get_sales_invoice_thai_tax_data(dn)
                
                if thai_tax_data:
                    # Populate Thai tax fields in the reference
                    _populate_reference_thai_tax_fields(ref, thai_tax_data)
                    
                    # Update summary fields in the Payment Entry
                    _update_payment_entry_thai_tax_summary(pe, thai_tax_data)
    
    return pe


def _get_sales_invoice_thai_tax_data(invoice_name):
    """
    Fetch Thai tax data from a Sales Invoice.
    Returns dict with Thai tax information.
    """
    try:
        # Get Thai tax fields from Sales Invoice
        invoice_data = frappe.db.get_value(
            "Sales Invoice",
            invoice_name,
            [
                "custom_subject_to_retention",
                "custom_retention_amount", 
                "custom_retention",
                "subject_to_wht",
                "grand_total",
                "net_total_after_wht",
                "custom_withholding_tax",
                "taxes_and_charges",
                "vat_treatment"
            ],
            as_dict=True
        )
        
        if not invoice_data:
            return None
        
        # Get WHT percentage directly from custom_withholding_tax field (already a percentage)
        wht_percentage = invoice_data.get("custom_withholding_tax", 0)
        
        # Calculate WHT amount from percentage and net_total_after_wht
        net_total_after_wht = invoice_data.get("net_total_after_wht", 0)
        wht_amount = 0
        if wht_percentage > 0 and net_total_after_wht > 0:
            # WHT amount = net_total_after_wht * (wht_percentage / 100)
            wht_amount = net_total_after_wht * (wht_percentage / 100)
            print(f"DEBUG WHT Calculation: Invoice {invoice_name}, WHT% = {wht_percentage}%, Net Total After WHT = {net_total_after_wht}, Calculated WHT Amount = {wht_amount}")
        else:
            print(f"DEBUG WHT Skip: Invoice {invoice_name}, WHT% = {wht_percentage}%, Net Total After WHT = {net_total_after_wht}")
        
        # Calculate VAT Undue amount from taxes_and_charges with VAT treatment context
        vat_undue_amount = _calculate_vat_undue_amount(invoice_name, invoice_data.get("taxes_and_charges", ""), invoice_data.get("vat_treatment", ""))
        
        # Convert to Payment Entry Reference field format
        thai_tax_data = {
            "has_retention": invoice_data.get("custom_subject_to_retention", 0),
            "retention_amount": invoice_data.get("custom_retention_amount", 0),
            "retention_percentage": invoice_data.get("custom_retention", 0),
            "has_wht": invoice_data.get("subject_to_wht", 0),
            "wht_amount": wht_amount,
            "wht_percentage": wht_percentage,
            "vat_undue_amount": vat_undue_amount,
            "vat_treatment": invoice_data.get("vat_treatment", "")  # Include VAT treatment info
        }
        
        return thai_tax_data
        
    except Exception as e:
        frappe.log_error(
            message=f"Error fetching Thai tax data for Sales Invoice {invoice_name}: {str(e)}",
            title="Payment Entry Thai Tax Data Fetch Error"
        )
        return None


def _calculate_vat_undue_amount(invoice_name, taxes_and_charges_template, vat_treatment=""):
    """
    Calculate VAT Undue amount from Sales Invoice taxes.
    
    In Thailand's service business, VAT occurs when payment is made.
    If taxes_and_charges template contains 'undue', 'ภาษีขายตั้งพัก', or 'ภาษีขายที่ไม่ถึงกำหนด',
    then all VAT amounts are VAT Undue amounts.
    
    Args:
        invoice_name: Sales Invoice name
        taxes_and_charges_template: Template name from taxes_and_charges field
        vat_treatment: VAT treatment status (VAT 7%, VAT 0%, VAT Exempt)
    
    Returns:
        float: Total VAT Undue amount
    """
    if not taxes_and_charges_template:
        return 0
    
    # Thai VAT Undue keywords
    vat_undue_keywords = ['undue', 'ภาษีขายตั้งพัก', 'ภาษีขายที่ไม่ถึงกำหนด']
    template_lower = taxes_and_charges_template.lower()
    
    # Check if template contains VAT Undue keywords
    is_vat_undue_template = any(keyword.lower() in template_lower for keyword in vat_undue_keywords)
    
    if not is_vat_undue_template:
        return 0
    
    # Additional validation: Check VAT treatment status
    # Only process VAT Undue if VAT is applicable (not VAT Exempt or Zero-rated)
    if vat_treatment:
        vat_treatment_lower = vat_treatment.lower()
        if "exempt" in vat_treatment_lower or "zero-rated" in vat_treatment_lower:
            return 0  # No VAT Undue for VAT Exempt or Zero-rated Export invoices
    
    try:
        # Get all tax rows from the Sales Invoice
        tax_rows = frappe.db.get_all(
            "Sales Taxes and Charges",
            filters={
                "parent": invoice_name,
                "parenttype": "Sales Invoice"
            },
            fields=["account_head", "tax_amount", "description"]
        )
        
        total_vat_undue = 0
        
        # Log VAT treatment for debugging
        if vat_treatment:
            frappe.logger().debug(f"Processing VAT Undue for {invoice_name}: VAT Treatment = {vat_treatment}")
        
        for tax in tax_rows:
            # Check if this tax row is VAT (contains VAT keywords in account or description)
            account_head = tax.get("account_head", "").lower()
            description = tax.get("description", "").lower()
            
            # VAT indicators in account head or description
            vat_indicators = ['vat', 'ภาษีขาย', 'ภาพ']
            
            is_vat_row = any(indicator in account_head or indicator in description 
                           for indicator in vat_indicators)
            
            if is_vat_row and tax.get("tax_amount"):
                total_vat_undue += tax.get("tax_amount", 0)
        
        return total_vat_undue
        
    except Exception as e:
        frappe.log_error(
            message=f"Error calculating VAT Undue for {invoice_name}: {str(e)}",
            title="VAT Undue Calculation Error"
        )
        return 0


def _populate_reference_thai_tax_fields(ref, thai_tax_data):
    """
    Populate Thai tax fields in a Payment Entry Reference row.
    """
    if not thai_tax_data:
        return
    
    # Set retention fields
    ref.pd_custom_has_retention = thai_tax_data.get("has_retention", 0)
    ref.pd_custom_retention_amount = thai_tax_data.get("retention_amount", 0)
    ref.pd_custom_retention_percentage = thai_tax_data.get("retention_percentage", 0)
    
    # Set WHT fields
    ref.pd_custom_wht_amount = thai_tax_data.get("wht_amount", 0)
    ref.pd_custom_wht_percentage = thai_tax_data.get("wht_percentage", 0)
    
    # Set VAT fields
    ref.pd_custom_vat_undue_amount = thai_tax_data.get("vat_undue_amount", 0)
    
    # Calculate net payable amount (allocated amount minus deductions)
    net_payable = ref.allocated_amount or 0
    
    if ref.pd_custom_retention_amount:
        net_payable -= ref.pd_custom_retention_amount
    
    if ref.pd_custom_wht_amount:
        net_payable -= ref.pd_custom_wht_amount
    
    ref.pd_custom_net_payable_amount = net_payable


def _update_payment_entry_thai_tax_summary(pe, thai_tax_data):
    """
    Update Payment Entry summary fields based on Thai tax data.
    """
    if not thai_tax_data:
        return
    
    # Check if Payment Entry has the Thai tax summary fields
    retention_amount = thai_tax_data.get("retention_amount", 0)
    wht_amount = thai_tax_data.get("wht_amount", 0)
    vat_undue_amount = thai_tax_data.get("vat_undue_amount", 0)
    
    has_thai_taxes = bool(retention_amount or wht_amount or vat_undue_amount)
    
    # Set summary fields if they exist
    if hasattr(pe, 'pd_custom_has_thai_taxes'):
        pe.pd_custom_has_thai_taxes = 1 if has_thai_taxes else 0
    
    if hasattr(pe, 'pd_custom_has_retention'):
        pe.pd_custom_has_retention = 1 if retention_amount > 0 else 0
    
    if hasattr(pe, 'pd_custom_total_retention_amount'):
        pe.pd_custom_total_retention_amount = retention_amount
    
    if hasattr(pe, 'pd_custom_total_wht_amount'):
        pe.pd_custom_total_wht_amount = wht_amount
    
    if hasattr(pe, 'pd_custom_total_vat_undue_amount'):
        pe.pd_custom_total_vat_undue_amount = vat_undue_amount
    
    if hasattr(pe, 'pd_custom_net_payment_after_retention'):
        pe.pd_custom_net_payment_after_retention = (pe.total_allocated_amount or 0) - retention_amount
    
    # Set default accounts from Company settings if not already set
    _populate_default_thai_tax_accounts(pe)


def _populate_default_thai_tax_accounts(pe):
    """
    Populate default Thai tax accounts from Company settings if not already set.
    This ensures the Payment Entry has proper account defaults from the company.
    """
    if not pe.company:
        return
    
    try:
        # Get company default accounts
        company_data = frappe.db.get_value(
            "Company",
            pe.company,
            [
                "default_retention_account",
                "default_wht_account", 
                "default_output_vat_undue_account",
                "default_output_vat_account"
            ],
            as_dict=True
        )
        
        if not company_data:
            return
        
        # Set retention account if blank and company has default
        if hasattr(pe, 'pd_custom_retention_account') and not getattr(pe, 'pd_custom_retention_account', None):
            if company_data.get("default_retention_account"):
                pe.pd_custom_retention_account = company_data.get("default_retention_account")
        
        # Set WHT account if blank and company has default
        if hasattr(pe, 'pd_custom_wht_account') and not getattr(pe, 'pd_custom_wht_account', None):
            if company_data.get("default_wht_account"):
                pe.pd_custom_wht_account = company_data.get("default_wht_account")
        
        # Set VAT Undue account if blank and company has default
        if hasattr(pe, 'pd_custom_output_vat_undue_account') and not getattr(pe, 'pd_custom_output_vat_undue_account', None):
            if company_data.get("default_output_vat_undue_account"):
                pe.pd_custom_output_vat_undue_account = company_data.get("default_output_vat_undue_account")
        
        # Set VAT account if blank and company has default
        if hasattr(pe, 'pd_custom_output_vat_account') and not getattr(pe, 'pd_custom_output_vat_account', None):
            if company_data.get("default_output_vat_account"):
                pe.pd_custom_output_vat_account = company_data.get("default_output_vat_account")
                
    except Exception as e:
        frappe.log_error(
            message=f"Error populating default Thai tax accounts for Payment Entry: {str(e)}",
            title="Payment Entry Default Account Population Error"
        )