"""
Sales Order Thailand Calculations Module

Handles Thailand-specific calculations for Sales Order DocType:
- Withholding Tax (WHT) calculations
- Retention calculations
- Net total after WHT
"""

import frappe
from frappe import _
from frappe.utils import flt, money_in_words


def sales_order_calculate_thailand_amounts(doc, method=None):
    """
    Calculate Thailand amounts for Sales Order DocType ONLY.
    
    This function is specifically designed for Sales Order and handles:
    - Company default WHT/retention rates integration
    - Thai business logic based on Company configuration
    - Custom field calculations (custom_withholding_tax_amount, custom_retention_amount)
    - Final payment amount calculations (net_total_after_wht)
    
    Called from Sales Order validate() method - runs server-side before save.
    Uses Company default values when Sales Order fields are not specified.
    """
    # DEBUG: Log function entry
    frappe.logger().info(f"🔍 Sales Order Calc: sales_order_calculate_thailand_amounts called for {doc.doctype} {getattr(doc, 'name', 'new')}")
    frappe.logger().info(f"🔍 Sales Order Calc: BEFORE - subject_to_wht = {getattr(doc, 'subject_to_wht', 'NOT_SET')}")
    print(f"🔍 Sales Order Calc: sales_order_calculate_thailand_amounts called for {doc.doctype} {getattr(doc, 'name', 'new')}")
    print(f"🔍 Sales Order Calc: BEFORE - subject_to_wht = {getattr(doc, 'subject_to_wht', 'NOT_SET')}")
    
    # Ensure this function only processes Sales Order DocType
    if doc.doctype != "Sales Order":
        frappe.logger().info(f"🔍 Sales Order Calc: Not a Sales Order ({doc.doctype}), skipping")
        print(f"🔍 Sales Order Calc: Not a Sales Order ({doc.doctype}), skipping")
        return
        
    if not doc.company:
        frappe.logger().info(f"🔍 Sales Order Calc: No company set, skipping")
        print(f"🔍 Sales Order Calc: No company set, skipping")
        return
    
    # Apply Company defaults if Sales Order fields are not specified
    apply_company_defaults(doc)
    
    # Calculate withholding tax amounts
    calculate_withholding_tax_amounts(doc)
    
    # Calculate retention amounts  
    calculate_retention_amounts(doc)
    
    # Calculate final payment amounts
    calculate_final_payment_amounts(doc)
    
    # DEBUG: Log final state
    frappe.logger().info(f"🔍 Sales Order Calc: AFTER - subject_to_wht = {getattr(doc, 'subject_to_wht', 'NOT_SET')}")
    frappe.logger().info(f"🔍 Sales Order Calc: Final amounts - net_total_after_wht = {getattr(doc, 'net_total_after_wht', 'NOT_SET')}")
    print(f"🔍 Sales Order Calc: AFTER - subject_to_wht = {getattr(doc, 'subject_to_wht', 'NOT_SET')}")
    print(f"🔍 Sales Order Calc: Final amounts - net_total_after_wht = {getattr(doc, 'net_total_after_wht', 'NOT_SET')}")


def apply_company_defaults(doc):
    """
    Apply Company default settings to Sales Order when not specified.
    Uses Company-level settings as defaults for Thai business calculations.
    """
    try:
        # Get Company settings
        company_doc = frappe.get_cached_doc("Company", doc.company)
        
        # Apply Thai business defaults
        if hasattr(company_doc, 'thai_business') and company_doc.thai_business:
            # Set subject_to_wht if not already set
            if not getattr(doc, 'subject_to_wht', None):
                doc.subject_to_wht = 1
                frappe.logger().info(f"🔍 Sales Order Calc: Applied Thai business default - subject_to_wht = 1")
                print(f"🔍 Sales Order Calc: Applied Thai business default - subject_to_wht = 1")
        
        # Apply WHT rate if subject to WHT and rate not specified
        if getattr(doc, 'subject_to_wht', None):
            if not getattr(doc, 'withholding_tax_rate', None):
                default_rate = getattr(company_doc, 'default_wht_rate', 3.0)
                doc.withholding_tax_rate = default_rate
                frappe.logger().info(f"🔍 Sales Order Calc: Applied Company default WHT rate: {default_rate}%")
                print(f"🔍 Sales Order Calc: Applied Company default WHT rate: {default_rate}%")
        
        # Apply retention settings if not specified
        if hasattr(company_doc, 'enable_retention') and company_doc.enable_retention:
            if not hasattr(doc, 'subject_to_retention') or doc.subject_to_retention is None:
                doc.subject_to_retention = 1
                
            if getattr(doc, 'subject_to_retention', None):
                if not getattr(doc, 'retention_percentage', None):
                    default_retention = getattr(company_doc, 'default_retention_percentage', 5.0)
                    doc.retention_percentage = default_retention
                    frappe.logger().info(f"🔍 Sales Order Calc: Applied Company default retention: {default_retention}%")
                    print(f"🔍 Sales Order Calc: Applied Company default retention: {default_retention}%")
                
    except Exception as e:
        frappe.logger().error(f"🔍 Sales Order Calc: Error applying company defaults: {str(e)}")
        print(f"🔍 Sales Order Calc: Error applying company defaults: {str(e)}")


def calculate_withholding_tax_amounts(doc):
    """
    Calculate withholding tax amounts for Sales Order.
    Sets custom_withholding_tax_amount based on net total and WHT rate.
    """
    try:
        if getattr(doc, 'subject_to_wht', None):
            # Use net_total as the base amount (before tax)
            base_amount = flt(doc.net_total)
            wht_rate = flt(getattr(doc, 'withholding_tax_rate', 3.0))
            
            # Calculate WHT amount (always based on net_total)
            wht_amount = base_amount * (wht_rate / 100)
            doc.custom_withholding_tax_amount = wht_amount
            
            frappe.logger().info(f"🔍 Sales Order Calc: WHT Calculation - Base: {base_amount}, Rate: {wht_rate}%, Amount: {wht_amount}")
            print(f"🔍 Sales Order Calc: WHT Calculation - Base: {base_amount}, Rate: {wht_rate}%, Amount: {wht_amount}")
        else:
            doc.custom_withholding_tax_amount = 0
            frappe.logger().info(f"🔍 Sales Order Calc: Not subject to WHT, setting amount to 0")
            print(f"🔍 Sales Order Calc: Not subject to WHT, setting amount to 0")
            
    except Exception as e:
        frappe.logger().error(f"🔍 Sales Order Calc: Error calculating WHT: {str(e)}")
        print(f"🔍 Sales Order Calc: Error calculating WHT: {str(e)}")
        doc.custom_withholding_tax_amount = 0


def calculate_retention_amounts(doc):
    """
    Calculate retention amounts for Sales Order.
    Sets custom_retention_amount based on grand total and retention percentage.
    """
    try:
        if getattr(doc, 'subject_to_retention', None):
            # Use grand_total as the base for retention (includes VAT)
            base_amount = flt(doc.grand_total)
            retention_rate = flt(getattr(doc, 'retention_percentage', 5.0))
            
            # Calculate retention amount
            retention_amount = base_amount * (retention_rate / 100)
            doc.custom_retention_amount = retention_amount
            
            frappe.logger().info(f"🔍 Sales Order Calc: Retention Calculation - Base: {base_amount}, Rate: {retention_rate}%, Amount: {retention_amount}")
            print(f"🔍 Sales Order Calc: Retention Calculation - Base: {base_amount}, Rate: {retention_rate}%, Amount: {retention_amount}")
        else:
            doc.custom_retention_amount = 0
            frappe.logger().info(f"🔍 Sales Order Calc: Not subject to retention, setting amount to 0")
            print(f"🔍 Sales Order Calc: Not subject to retention, setting amount to 0")
            
    except Exception as e:
        frappe.logger().error(f"🔍 Sales Order Calc: Error calculating retention: {str(e)}")
        print(f"🔍 Sales Order Calc: Error calculating retention: {str(e)}")
        doc.custom_retention_amount = 0


def calculate_final_payment_amounts(doc):
    """
    Calculate final payment amounts after WHT and retention deductions for Sales Order.
    Sets net_total_after_wht which represents the amount to be paid.
    
    Formula: net_total_after_wht = grand_total - custom_withholding_tax_amount - custom_retention_amount
    """
    try:
        # Start with grand total (includes VAT)
        grand_total = flt(doc.grand_total)
        
        # Deduct WHT (if applicable)
        wht_amount = flt(getattr(doc, 'custom_withholding_tax_amount', 0))
        
        # Deduct retention (if applicable)
        retention_amount = flt(getattr(doc, 'custom_retention_amount', 0))
        
        # Calculate net total after deductions
        net_total_after_wht = grand_total - wht_amount - retention_amount
        doc.net_total_after_wht = net_total_after_wht
        
        frappe.logger().info(f"🔍 Sales Order Calc: Final Payment Calculation:")
        frappe.logger().info(f"  Grand Total: {grand_total}")
        frappe.logger().info(f"  - WHT: {wht_amount}")
        frappe.logger().info(f"  - Retention: {retention_amount}")
        frappe.logger().info(f"  = Net After WHT: {net_total_after_wht}")
        
        print(f"🔍 Sales Order Calc: Final Payment Calculation:")
        print(f"  Grand Total: {grand_total}")
        print(f"  - WHT: {wht_amount}")
        print(f"  - Retention: {retention_amount}")
        print(f"  = Net After WHT: {net_total_after_wht}")
        
        # Convert amounts to words (Thai format)
        convert_amounts_to_words(doc)
        
    except Exception as e:
        frappe.logger().error(f"🔍 Sales Order Calc: Error calculating final payment: {str(e)}")
        print(f"🔍 Sales Order Calc: Error calculating final payment: {str(e)}")
        doc.net_total_after_wht = doc.grand_total


def validate_thailand_calculations(doc):
    """
    Validate that all Thailand calculations are correct and fields are properly set.
    This function can be called to verify the integrity of calculations.
    """
    errors = []
    warnings = []
    
    # Check if required fields exist
    required_fields = [
        'subject_to_wht',
        'withholding_tax_rate',
        'custom_withholding_tax_amount',
        'subject_to_retention',
        'retention_percentage', 
        'custom_retention_amount',
        'net_total_after_wht'
    ]
    
    for field in required_fields:
        if not hasattr(doc, field):
            errors.append(f"Missing required field: {field}")
    
    # Validate calculations if fields exist
    if hasattr(doc, 'subject_to_wht') and doc.subject_to_wht:
        # Verify WHT calculation
        expected_wht = flt(doc.net_total) * (flt(doc.withholding_tax_rate) / 100)
        actual_wht = flt(doc.custom_withholding_tax_amount)
        
        if abs(expected_wht - actual_wht) > 0.01:  # Allow small rounding differences
            warnings.append(f"WHT calculation mismatch: Expected {expected_wht:.2f}, got {actual_wht:.2f}")
    
    if hasattr(doc, 'subject_to_retention') and doc.subject_to_retention:
        # Verify retention calculation
        expected_retention = flt(doc.grand_total) * (flt(doc.retention_percentage) / 100)
        actual_retention = flt(doc.custom_retention_amount)
        
        if abs(expected_retention - actual_retention) > 0.01:
            warnings.append(f"Retention calculation mismatch: Expected {expected_retention:.2f}, got {actual_retention:.2f}")
    
    # Verify final payment calculation
    if hasattr(doc, 'net_total_after_wht'):
        expected_net = flt(doc.grand_total) - flt(getattr(doc, 'custom_withholding_tax_amount', 0)) - flt(getattr(doc, 'custom_retention_amount', 0))
        actual_net = flt(doc.net_total_after_wht)
        
        if abs(expected_net - actual_net) > 0.01:
            warnings.append(f"Net payment calculation mismatch: Expected {expected_net:.2f}, got {actual_net:.2f}")
    
    return errors, warnings


def convert_amounts_to_words(doc):
    """
    Convert numeric amounts to words (Thai format) for printing on documents.
    Sets the in_words fields for various amounts.
    """
    try:
        # Get currency
        currency = doc.currency or frappe.get_cached_value("Company", doc.company, "default_currency")
        
        # Convert grand total to words
        if hasattr(doc, 'grand_total') and doc.grand_total:
            doc.grand_total_in_words = money_in_words(doc.grand_total, currency)
        
        # Convert net total after WHT to words
        if hasattr(doc, 'net_total_after_wht') and doc.net_total_after_wht:
            doc.net_total_after_wht_in_words = money_in_words(doc.net_total_after_wht, currency)
        
        # Convert WHT amount to words
        if hasattr(doc, 'custom_withholding_tax_amount') and doc.custom_withholding_tax_amount:
            doc.custom_withholding_tax_amount_in_words = money_in_words(doc.custom_withholding_tax_amount, currency)
        
        # Convert retention amount to words  
        if hasattr(doc, 'custom_retention_amount') and doc.custom_retention_amount:
            doc.custom_retention_amount_in_words = money_in_words(doc.custom_retention_amount, currency)
            
    except Exception as e:
        frappe.logger().error(f"🔍 Sales Order Calc: Error converting amounts to words: {str(e)}")
        print(f"🔍 Sales Order Calc: Error converting amounts to words: {str(e)}")