"""
Payment Entry Thai Tax Population Module

This module provides API methods to fetch Thai tax details from Sales Invoices
for populating Payment Entry references with retention, WHT, and VAT information.
"""

import frappe

@frappe.whitelist()
def get_invoice_thai_tax_details(invoice_type, invoice_name):
    """
    Get Thai tax details from Sales Invoice for Payment Entry population
    
    Args:
        invoice_type (str): Document type (should be 'Sales Invoice')
        invoice_name (str): Name of the Sales Invoice
        
    Returns:
        dict: Thai tax details including retention, WHT, and VAT amounts
    """
    if invoice_type != 'Sales Invoice':
        return {}
    
    try:
        # Get the Sales Invoice document
        invoice_doc = frappe.get_doc('Sales Invoice', invoice_name)
        
        # Extract Thai tax fields from the invoice
        thai_tax_details = {
            'pd_custom_has_retention': invoice_doc.get('pd_custom_has_retention', 0),
            'pd_custom_retention_amount': invoice_doc.get('pd_custom_retention_amount', 0),
            'pd_custom_retention_percentage': invoice_doc.get('pd_custom_retention_percentage', 0),
            'pd_custom_wht_amount': invoice_doc.get('pd_custom_wht_amount', 0),
            'pd_custom_wht_percentage': invoice_doc.get('pd_custom_wht_percentage', 0),
            'pd_custom_vat_undue_amount': invoice_doc.get('pd_custom_vat_undue_amount', 0),
            
            # Additional fields that might be useful
            'pd_custom_has_thai_taxes': invoice_doc.get('pd_custom_has_thai_taxes', 0),
            'pd_custom_wht_certificate_number': invoice_doc.get('pd_custom_wht_certificate_number', ''),
            'pd_custom_wht_certificate_date': invoice_doc.get('pd_custom_wht_certificate_date', ''),
        }
        
        return thai_tax_details
        
    except frappe.DoesNotExistError:
        frappe.throw(f"Sales Invoice {invoice_name} does not exist")
    except Exception as e:
        frappe.log_error(f"Error fetching Thai tax details for {invoice_name}: {str(e)}")
        return {}

@frappe.whitelist()
def get_invoice_net_payable_amount(invoice_type, invoice_name, allocated_amount):
    """
    Calculate net payable amount after deducting Thai taxes
    
    Args:
        invoice_type (str): Document type (should be 'Sales Invoice')
        invoice_name (str): Name of the Sales Invoice
        allocated_amount (float): Amount being allocated in payment
        
    Returns:
        dict: Calculated net payable amount and breakdown
    """
    if invoice_type != 'Sales Invoice':
        return {'net_payable': allocated_amount}
    
    try:
        # Get Thai tax details
        thai_tax_details = get_invoice_thai_tax_details(invoice_type, invoice_name)
        
        # Convert allocated_amount to float
        allocated_amount = float(allocated_amount or 0)
        
        # Calculate deductions
        retention_amount = float(thai_tax_details.get('pd_custom_retention_amount', 0))
        wht_amount = float(thai_tax_details.get('pd_custom_wht_amount', 0))
        
        # Calculate net payable
        net_payable = allocated_amount - retention_amount - wht_amount
        
        return {
            'net_payable': net_payable,
            'allocated_amount': allocated_amount,
            'retention_amount': retention_amount,
            'wht_amount': wht_amount,
            'total_deductions': retention_amount + wht_amount
        }
        
    except Exception as e:
        frappe.log_error(f"Error calculating net payable for {invoice_name}: {str(e)}")
        return {'net_payable': allocated_amount}

@frappe.whitelist()
def validate_thai_tax_amounts(invoice_type, invoice_name):
    """
    Validate Thai tax amounts in Sales Invoice
    
    Args:
        invoice_type (str): Document type (should be 'Sales Invoice')
        invoice_name (str): Name of the Sales Invoice
        
    Returns:
        dict: Validation results and any warnings
    """
    if invoice_type != 'Sales Invoice':
        return {'valid': True, 'warnings': []}
    
    try:
        invoice_doc = frappe.get_doc('Sales Invoice', invoice_name)
        warnings = []
        
        # Get amounts
        grand_total = float(invoice_doc.get('grand_total', 0))
        retention_amount = float(invoice_doc.get('pd_custom_retention_amount', 0))
        wht_amount = float(invoice_doc.get('pd_custom_wht_amount', 0))
        
        # Validate retention amount doesn't exceed grand total
        if retention_amount > grand_total:
            warnings.append(f"Retention amount ({retention_amount}) exceeds grand total ({grand_total})")
        
        # Validate WHT amount doesn't exceed grand total
        if wht_amount > grand_total:
            warnings.append(f"WHT amount ({wht_amount}) exceeds grand total ({grand_total})")
        
        # Validate total deductions don't exceed grand total
        total_deductions = retention_amount + wht_amount
        if total_deductions > grand_total:
            warnings.append(f"Total deductions ({total_deductions}) exceed grand total ({grand_total})")
        
        return {
            'valid': len(warnings) == 0,
            'warnings': warnings,
            'grand_total': grand_total,
            'retention_amount': retention_amount,
            'wht_amount': wht_amount,
            'total_deductions': total_deductions,
            'net_amount': grand_total - total_deductions
        }
        
    except Exception as e:
        frappe.log_error(f"Error validating Thai tax amounts for {invoice_name}: {str(e)}")
        return {'valid': False, 'warnings': [f"Error during validation: {str(e)}"]}