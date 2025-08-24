# Quotation Server-Side Calculations for Thailand WHT and Retention
# Following ERPNext pattern like grand_total calculation
# Called during validate() method - NO client scripts needed

import frappe
from frappe import _
from frappe.utils import flt


def calculate_thailand_amounts(doc):
    """
    Calculate Thailand withholding tax and retention amounts during Quotation validation.
    This follows the same pattern as ERPNext's calculate_taxes_and_totals() method.
    
    Called from Quotation validate() method - runs server-side before save.
    """
    if not doc.company:
        return
    
    # Calculate withholding tax amounts
    calculate_withholding_tax_amounts(doc)
    
    # Calculate retention amounts  
    calculate_retention_amounts(doc)
    
    # Calculate final payment amounts
    calculate_final_payment_amounts(doc)


def calculate_withholding_tax_amounts(doc):
    """Calculate withholding tax amounts based on custom_withholding_tax percentage"""
    try:
        # Calculate WHT amount: custom_withholding_tax_amount = net_total * custom_withholding_tax
        if doc.custom_withholding_tax and doc.net_total:
            wht_rate = flt(doc.custom_withholding_tax)  # Already in percentage
            base_amount = flt(doc.net_total)
            
            # Calculate WHT amount
            doc.custom_withholding_tax_amount = flt((base_amount * wht_rate) / 100, 2)
        else:
            doc.custom_withholding_tax_amount = 0
            
    except Exception as e:
        frappe.log_error(f"Error calculating withholding tax amounts for Quotation {doc.name}: {str(e)}")
        # Don't fail validation, just clear WHT fields
        doc.custom_withholding_tax_amount = 0


def calculate_retention_amounts(doc):
    """Calculate retention amounts when custom_subject_to_retention is enabled"""
    try:
        if doc.custom_subject_to_retention and doc.custom_retention and doc.net_total:
            retention_rate = flt(doc.custom_retention)  # Already in percentage
            base_amount = flt(doc.net_total)
            
            # Calculate retention amount: custom_retention_amount = net_total * custom_retention
            doc.custom_retention_amount = flt((base_amount * retention_rate) / 100, 2)
        else:
            doc.custom_retention_amount = 0
            
    except Exception as e:
        frappe.log_error(f"Error calculating retention amounts for Quotation {doc.name}: {str(e)}")
        # Don't fail validation, just clear retention fields
        doc.custom_retention_amount = 0


def calculate_final_payment_amounts(doc):
    """Calculate final payment amounts after WHT and retention deductions"""
    try:
        # Start with grand total (includes VAT)
        grand_total = flt(doc.grand_total)
        
        # Get deduction amounts
        wht_amount = flt(doc.custom_withholding_tax_amount)
        retention_amount = flt(doc.custom_retention_amount)
        
        # Calculate net_total_after_wht: grand_total - custom_withholding_tax_amount
        doc.net_total_after_wht = flt(grand_total - wht_amount, 2)
        
        # Calculate payment amount based on retention status
        if doc.custom_subject_to_retention and retention_amount > 0:
            # 5.2 custom_net_total_after_wht_retention = grand_total - custom_withholding_tax_amount - custom_retention_amount
            doc.custom_net_total_after_wht_retention = flt(grand_total - wht_amount - retention_amount, 2)
            
            # 5.3 custom_payment_amount = custom_net_total_after_wht_retention
            doc.custom_payment_amount = doc.custom_net_total_after_wht_retention
        else:
            # No retention: custom_payment_amount = net_total_after_wht
            doc.custom_net_total_after_wht_retention = 0
            doc.custom_payment_amount = doc.net_total_after_wht
        
        # Ensure payment amount is not negative
        if doc.custom_payment_amount < 0:
            doc.custom_payment_amount = 0
            frappe.msgprint(
                _("Warning: Total deductions exceed quotation amount. Payment amount set to zero."),
                alert=True, indicator="orange"
            )
            
    except Exception as e:
        frappe.log_error(f"Error calculating final payment amounts for Quotation {doc.name}: {str(e)}")
        # Fallback to grand total
        doc.net_total_after_wht = flt(doc.grand_total)
        doc.custom_payment_amount = flt(doc.grand_total)
        doc.custom_net_total_after_wht_retention = 0


def validate_thailand_calculations(doc):
    """
    Validate Thailand-specific calculations and constraints.
    Called after calculations are complete.
    """
    # Validate retention constraints
    if doc.custom_retention_amount and doc.custom_retention_amount > doc.net_total:
        frappe.throw(_("Retention amount cannot exceed net total"))
    
    # Validate withholding tax constraints  
    if doc.custom_withholding_tax_amount and doc.custom_withholding_tax_amount > doc.net_total:
        frappe.throw(_("Withholding tax amount cannot exceed net total"))
    
    # Validate total deductions don't exceed quotation amount
    total_deductions = flt(doc.custom_retention_amount) + flt(doc.custom_withholding_tax_amount)
    if total_deductions > doc.grand_total:
        frappe.throw(
            _("Total deductions ({0}) cannot exceed quotation grand total ({1})").format(
                total_deductions, doc.grand_total
            )
        )


# Main entry point - called from Quotation validate() method
def quotation_calculate_thailand_amounts(doc, method=None):
    """
    Main calculation method called from Quotation validate().
    This follows the ERPNext pattern - server-side calculation during validation.
    
    Args:
        doc: Quotation document
        method: Hook method (validate)
    """
    try:
        # Only calculate for draft documents
        if doc.docstatus != 0:
            return
        
        # Perform all Thailand-specific calculations
        calculate_thailand_amounts(doc)
        
        # Validate calculations
        validate_thailand_calculations(doc)
        
    except Exception as e:
        frappe.log_error(
            f"Error in Thailand calculations for Quotation {doc.name}: {str(e)}",
            "Thailand Quotation Calculations"
        )
        # Re-raise validation errors, but not calculation errors
        if isinstance(e, frappe.ValidationError):
            raise