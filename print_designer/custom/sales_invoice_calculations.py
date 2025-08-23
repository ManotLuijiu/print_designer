# Sales Invoice Server-Side Calculations for Thailand WHT and Retention
# Following ERPNext pattern like grand_total calculation
# Called during validate() method - NO client scripts needed

import frappe
from frappe import _
from frappe.utils import flt


def calculate_thailand_amounts(doc):
    """
    Calculate Thailand withholding tax and retention amounts during Sales Invoice validation.
    This follows the same pattern as ERPNext's calculate_taxes_and_totals() method.
    
    Called from Sales Invoice validate() method - runs server-side before save.
    """
    if not doc.company:
        return
    
    # Calculate retention amounts
    calculate_retention_amounts(doc)
    
    # Calculate withholding tax amounts  
    calculate_withholding_tax_amounts(doc)
    
    # Calculate final payment amount
    calculate_final_payment_amount(doc)


def calculate_retention_amounts(doc):
    """Calculate retention amounts based on Company Retention Settings"""
    try:
        from print_designer.print_designer.doctype.company_retention_settings.company_retention_settings import CompanyRetentionSettings
        
        settings = CompanyRetentionSettings.get_retention_settings(doc.company)
        
        if not settings.get('construction_service_enabled'):
            # Clear retention fields if not enabled
            doc.custom_retention = 0
            doc.custom_retention_amount = 0
            return
        
        # Auto-calculate retention rate if enabled and not manually set
        if settings.get('auto_calculate_retention') and not doc.custom_retention:
            doc.custom_retention = flt(settings.get('default_retention_rate', 5.0))
        
        # Calculate retention amount based on net total
        if doc.custom_retention and doc.base_net_total:
            retention_rate = flt(doc.custom_retention)
            max_rate = flt(settings.get('maximum_retention_rate', 10.0))
            
            # Validate retention rate doesn't exceed maximum
            if retention_rate > max_rate:
                frappe.msgprint(
                    _("Retention rate {0}% exceeds maximum allowed rate {1}%").format(retention_rate, max_rate),
                    alert=True, indicator="orange"
                )
                retention_rate = max_rate
                doc.custom_retention = retention_rate
            
            # Calculate retention amount
            doc.custom_retention_amount = flt((doc.base_net_total * retention_rate) / 100, 2)
        else:
            doc.custom_retention_amount = 0
            
    except Exception as e:
        frappe.log_error(f"Error calculating retention amounts for {doc.name}: {str(e)}")
        # Don't fail validation, just clear retention fields
        doc.custom_retention = 0
        doc.custom_retention_amount = 0


def calculate_withholding_tax_amounts(doc):
    """Calculate withholding tax amounts based on company settings"""
    try:
        # Check if company has Thailand service business enabled - use document-level caching to prevent excessive API calls
        if not hasattr(doc, '_thailand_service_business_cached'):
            doc._thailand_service_business_cached = frappe.get_cached_value("Company", doc.company, "thailand_service_business") or 0
        thailand_service = doc._thailand_service_business_cached
        
        if not thailand_service:
            # Clear WHT fields if Thailand service not enabled
            doc.subject_to_wht = 0
            doc.estimated_wht_amount = 0
            doc.custom_withholding_tax = 0
            doc.custom_withholding_tax_amount = 0
            return
        
        # Get default WHT rate from company - use document-level caching to prevent excessive API calls
        if not hasattr(doc, '_default_wht_rate_cached'):
            doc._default_wht_rate_cached = frappe.get_cached_value("Company", doc.company, "default_wht_rate") or 3.0
        default_wht_rate = doc._default_wht_rate_cached
        
        # If subject to WHT, calculate estimated amount
        if doc.subject_to_wht and doc.base_net_total:
            doc.estimated_wht_amount = flt((doc.base_net_total * default_wht_rate) / 100, 2)
        else:
            doc.estimated_wht_amount = 0
        
        # Calculate actual withholding tax if enabled
        if doc.custom_withholding_tax and doc.base_net_total:
            # Use default rate or calculate based on items
            wht_rate = default_wht_rate
            doc.custom_withholding_tax_amount = flt((doc.base_net_total * wht_rate) / 100, 2)
        else:
            doc.custom_withholding_tax_amount = 0
            
    except Exception as e:
        frappe.log_error(f"Error calculating withholding tax amounts for {doc.name}: {str(e)}")
        # Don't fail validation, just clear WHT fields
        doc.subject_to_wht = 0
        doc.estimated_wht_amount = 0
        doc.custom_withholding_tax = 0
        doc.custom_withholding_tax_amount = 0


def calculate_final_payment_amount(doc):
    """Calculate final payment amount after all deductions"""
    try:
        # Start with grand total (includes VAT)
        base_amount = flt(doc.grand_total)
        
        # Subtract retention amount
        retention_amount = flt(doc.custom_retention_amount)
        
        # Subtract withholding tax amount  
        wht_amount = flt(doc.custom_withholding_tax_amount)
        
        # Calculate net payment amount
        doc.custom_payment_amount = flt(base_amount - retention_amount - wht_amount, 2)
        
        # Ensure payment amount is not negative
        if doc.custom_payment_amount < 0:
            doc.custom_payment_amount = 0
            frappe.msgprint(
                _("Warning: Total deductions exceed invoice amount. Payment amount set to zero."),
                alert=True, indicator="orange"
            )
            
    except Exception as e:
        frappe.log_error(f"Error calculating final payment amount for {doc.name}: {str(e)}")
        # Fallback to grand total
        doc.custom_payment_amount = flt(doc.grand_total)


def calculate_net_total_after_wht(doc):
    """Calculate net total after WHT for display purposes"""
    try:
        if doc.subject_to_wht and doc.estimated_wht_amount:
            # Net total = Grand total - Estimated WHT
            doc.net_total_after_wht = flt(doc.grand_total - doc.estimated_wht_amount, 2)
        else:
            doc.net_total_after_wht = flt(doc.grand_total)
            
        # Convert to words if Thai language support available
        if doc.net_total_after_wht and hasattr(doc, 'net_total_after_wht_in_words'):
            try:
                from frappe.utils import money_in_words
                doc.net_total_after_wht_in_words = money_in_words(doc.net_total_after_wht)
            except:
                doc.net_total_after_wht_in_words = ""
                
    except Exception as e:
        frappe.log_error(f"Error calculating net total after WHT for {doc.name}: {str(e)}")
        doc.net_total_after_wht = flt(doc.grand_total)


def validate_thailand_calculations(doc):
    """
    Validate Thailand-specific calculations and constraints.
    Called after calculations are complete.
    """
    # Validate retention constraints
    if doc.custom_retention_amount and doc.custom_retention_amount > doc.base_net_total:
        frappe.throw(_("Retention amount cannot exceed net total"))
    
    # Validate withholding tax constraints  
    if doc.custom_withholding_tax_amount and doc.custom_withholding_tax_amount > doc.base_net_total:
        frappe.throw(_("Withholding tax amount cannot exceed net total"))
    
    # Validate total deductions don't exceed invoice amount
    total_deductions = flt(doc.custom_retention_amount) + flt(doc.custom_withholding_tax_amount)
    if total_deductions > doc.grand_total:
        frappe.throw(
            _("Total deductions ({0}) cannot exceed invoice grand total ({1})").format(
                total_deductions, doc.grand_total
            )
        )


# Main entry point - called from Sales Invoice validate() method
def sales_invoice_calculate_thailand_amounts(doc, method=None):
    """
    Main calculation method called from Sales Invoice validate().
    This follows the ERPNext pattern - server-side calculation during validation.
    
    Args:
        doc: Sales Invoice document
        method: Hook method (validate)
    """
    try:
        # Only calculate for draft documents
        if doc.docstatus != 0:
            return
            
        # Skip calculations for return invoices  
        if getattr(doc, 'is_return', False):
            return
        
        # Perform all Thailand-specific calculations
        calculate_thailand_amounts(doc)
        calculate_net_total_after_wht(doc)
        
        # Validate calculations
        validate_thailand_calculations(doc)
        
    except Exception as e:
        frappe.log_error(
            f"Error in Thailand calculations for Sales Invoice {doc.name}: {str(e)}",
            "Thailand Sales Invoice Calculations"
        )
        # Re-raise validation errors, but not calculation errors
        if isinstance(e, frappe.ValidationError):
            raise