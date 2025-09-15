"""
Payment Entry Thai Tax Population Module

This module provides API methods to fetch Thai tax details from Sales Invoices
for populating Payment Entry references with retention, WHT, and VAT information.
"""

import frappe

def _calculate_vat_undue_from_taxes(invoice_doc):
    """
    Calculate VAT Undue amount from Sales Invoice taxes.

    Based on Thai service business rules where VAT occurs when payment is made.
    """
    try:
        taxes_and_charges_template = invoice_doc.get("taxes_and_charges", "")
        vat_treatment = invoice_doc.get("vat_treatment", "")

        print(f"DEBUG VAT: Calculating VAT Undue for {invoice_doc.name}")
        print(f"  - taxes_and_charges: '{taxes_and_charges_template}'")
        print(f"  - vat_treatment: '{vat_treatment}'")

        if not taxes_and_charges_template:
            print("  - No taxes template, returning 0")
            return 0

        # Thai VAT Undue keywords
        vat_undue_keywords = ['undue', 'ภาษีขายตั้งพัก', 'ภาษีขายที่ไม่ถึงกำหนด']
        template_lower = taxes_and_charges_template.lower()

        # Check if template contains VAT Undue keywords
        is_vat_undue_template = any(keyword.lower() in template_lower for keyword in vat_undue_keywords)

        print(f"  - is_vat_undue_template: {is_vat_undue_template}")

        if not is_vat_undue_template:
            print("  - Not VAT Undue template, returning 0")
            return 0

        # Additional validation: Check VAT treatment status
        if vat_treatment:
            vat_treatment_lower = vat_treatment.lower()
            if "exempt" in vat_treatment_lower or "zero-rated" in vat_treatment_lower:
                print("  - VAT Exempt or Zero-rated, returning 0")
                return 0

        # Get all tax rows from the Sales Invoice
        total_vat_undue = 0

        if hasattr(invoice_doc, 'taxes') and invoice_doc.taxes:
            print(f"  - Processing {len(invoice_doc.taxes)} tax rows")

            for tax in invoice_doc.taxes:
                # Check if this tax row is VAT
                account_head = (tax.get("account_head") or "").lower()
                description = (tax.get("description") or "").lower()

                # VAT indicators
                vat_indicators = ['vat', 'ภาษีขาย', 'ภาพ']

                is_vat_row = any(indicator in account_head or indicator in description
                               for indicator in vat_indicators)

                if is_vat_row and tax.get("tax_amount"):
                    vat_amount = float(tax.get("tax_amount", 0))
                    total_vat_undue += vat_amount
                    print(f"  - Found VAT row: {account_head} = ฿{vat_amount}")

        print(f"  - Total VAT Undue calculated: ฿{total_vat_undue}")
        return total_vat_undue

    except Exception as e:
        frappe.log_error(f"Error calculating VAT Undue for {invoice_doc.name}: {str(e)}")
        print(f"  - Error calculating VAT Undue: {str(e)}")
        return 0

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
        
        print(f"DEBUG API: Fetching Thai tax data for {invoice_name}")

        # Extract Thai tax fields from the invoice using correct field names
        thai_tax_details = {
            # Retention fields (map to correct Sales Invoice field names)
            'retention': invoice_doc.get('custom_retention', 0),  # percentage
            'retention_amount': invoice_doc.get('custom_retention_amount', 0),
            'has_retention': 1 if invoice_doc.get('custom_subject_to_retention', 0) else 0,

            # WHT fields (map to correct Sales Invoice field names)
            'wht': invoice_doc.get('custom_withholding_tax', 0),  # percentage
            'wht_amount': invoice_doc.get('custom_withholding_tax_amount', 0),
            'has_wht': 1 if invoice_doc.get('subject_to_wht', 0) else 0,

            # Additional WHT fields for Payment Entry population
            'wht_description': invoice_doc.get('wht_description', ''),
            'wht_income_type': invoice_doc.get('wht_income_type', ''),

            # VAT fields
            'vat_undue': _calculate_vat_undue_from_taxes(invoice_doc),
            'vat_treatment': invoice_doc.get('vat_treatment', ''),

            # Net amounts
            'net_total_after_wht': invoice_doc.get('net_total_after_wht', 0),
            'net_total_after_wht_in_words': invoice_doc.get('net_total_after_wht_in_words', ''),
            'grand_total': invoice_doc.get('grand_total', 0),
            'base_net_total': invoice_doc.get('base_net_total', 0),  # Amount excluding taxes
        }

        print(f"DEBUG API: Thai tax data extracted for {invoice_name}:")
        print(f"  - has_retention: {thai_tax_details['has_retention']}")
        print(f"  - retention_amount: {thai_tax_details['retention_amount']}")
        print(f"  - has_wht: {thai_tax_details['has_wht']}")
        print(f"  - wht_amount: {thai_tax_details['wht_amount']}")
        print(f"  - wht_description: {thai_tax_details['wht_description']}")
        print(f"  - wht_income_type: {thai_tax_details['wht_income_type']}")
        print(f"  - net_total_after_wht: {thai_tax_details['net_total_after_wht']}")
        print(f"  - net_total_after_wht_in_words: {thai_tax_details['net_total_after_wht_in_words']}")
        print(f"  - vat_undue: {thai_tax_details['vat_undue']}")
        print(f"  - base_net_total: {thai_tax_details['base_net_total']}")
        
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
        
        # Calculate deductions using corrected field names
        retention_amount = float(thai_tax_details.get('retention_amount', 0))
        wht_amount = float(thai_tax_details.get('wht_amount', 0))
        
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
        
        # Get amounts using correct field names
        grand_total = float(invoice_doc.get('grand_total', 0))
        retention_amount = float(invoice_doc.get('custom_retention_amount', 0))
        wht_amount = float(invoice_doc.get('custom_withholding_tax_amount', 0))
        
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