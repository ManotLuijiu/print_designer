# Quotation Server-Side Calculations for Thailand WHT and Retention
# Following ERPNext pattern like grand_total calculation
# Called during validate() method - NO client scripts needed

import frappe
from frappe import _
from frappe.utils import flt


def quotation_calculate_thailand_amounts(doc, method=None):
    """
    Calculate Thailand amounts for Quotation DocType ONLY.
    
    This function is specifically designed for Quotation and handles:
    - Company default WHT/retention rates integration
    - Thai business logic based on Company configuration
    - Custom field calculations (custom_withholding_tax_amount, custom_retention_amount)
    - Final payment amount calculations (net_total_after_wht)
    
    Called from Quotation validate() method - runs server-side before save.
    Uses Company default values when Quotation fields are not specified.
    """
    # DEBUG: Log function entry
    frappe.logger().info(f"🔍 Quotation Calc: quotation_calculate_thailand_amounts called for {doc.doctype} {getattr(doc, 'name', 'new')}")
    frappe.logger().info(f"🔍 Quotation Calc: BEFORE - subject_to_wht = {getattr(doc, 'subject_to_wht', 'NOT_SET')}")
    print(f"🔍 Quotation Calc: quotation_calculate_thailand_amounts called for {doc.doctype} {getattr(doc, 'name', 'new')}")
    print(f"🔍 Quotation Calc: BEFORE - subject_to_wht = {getattr(doc, 'subject_to_wht', 'NOT_SET')}")
    
    # Ensure this function only processes Quotation DocType
    if doc.doctype != "Quotation":
        frappe.logger().info(f"🔍 Quotation Calc: Not a Quotation ({doc.doctype}), skipping")
        print(f"🔍 Quotation Calc: Not a Quotation ({doc.doctype}), skipping")
        return
        
    if not doc.company:
        frappe.logger().info(f"🔍 Quotation Calc: No company set, skipping")
        print(f"🔍 Quotation Calc: No company set, skipping")
        return
    
    # Apply Company defaults if Quotation fields are not specified
    apply_company_defaults(doc)
    
    # Calculate withholding tax amounts
    calculate_withholding_tax_amounts(doc)
    
    # Calculate retention amounts  
    calculate_retention_amounts(doc)
    
    # Calculate final payment amounts
    calculate_final_payment_amounts(doc)
    
    # DEBUG: Log final state
    frappe.logger().info(f"🔍 Quotation Calc: AFTER - subject_to_wht = {getattr(doc, 'subject_to_wht', 'NOT_SET')}")
    frappe.logger().info(f"🔍 Quotation Calc: Final amounts - net_total_after_wht = {getattr(doc, 'net_total_after_wht', 'NOT_SET')}")
    print(f"🔍 Quotation Calc: AFTER - subject_to_wht = {getattr(doc, 'subject_to_wht', 'NOT_SET')}")
    print(f"🔍 Quotation Calc: Final amounts - net_total_after_wht = {getattr(doc, 'net_total_after_wht', 'NOT_SET')}")


def apply_company_defaults(doc):
    """
    Apply Company default values to Quotation when fields are not specified.
    Uses Company.default_wht_rate and Company.default_retention_rate as fallbacks.
    """
    try:
        # Get Company configuration
        company_doc = frappe.get_cached_doc("Company", doc.company)
        
        # Apply default WHT rate if custom_withholding_tax is not specified
        if not doc.get('custom_withholding_tax') and company_doc.get('default_wht_rate'):
            doc.custom_withholding_tax = flt(company_doc.default_wht_rate)
        
        # Apply default retention rate if custom_retention is not specified  
        if not doc.get('custom_retention') and company_doc.get('default_retention_rate'):
            doc.custom_retention = flt(company_doc.default_retention_rate)
            
        # Note: subject_to_wht should be manually controlled by user
        # Field visibility is controlled by depends_on condition in Custom Field
        # User decides whether Quotation contains services subject to WHT
                
        # Enable custom_subject_to_retention based on Company construction_service or default_retention_rate
        if (company_doc.get('construction_service') or company_doc.get('default_retention_rate')) and not doc.get('custom_subject_to_retention'):
            # Only auto-enable if retention rate is available (either custom or default)
            if doc.get('custom_retention') or company_doc.get('default_retention_rate'):
                doc.custom_subject_to_retention = 1
                
    except Exception as e:
        frappe.log_error(f"Error applying Company defaults to Quotation {doc.name}: {str(e)}")
        # Don't fail validation - just continue without defaults


def calculate_withholding_tax_amounts(doc):
    """Calculate withholding tax amounts based on custom_withholding_tax percentage"""
    try:
        # Only calculate WHT if user has enabled subject_to_wht
        if doc.get('subject_to_wht') and doc.custom_withholding_tax and doc.net_total:
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


# Note: This function is the main entry point called from hooks.py
# quotation_calculate_thailand_amounts (defined at line 10) is the correct function