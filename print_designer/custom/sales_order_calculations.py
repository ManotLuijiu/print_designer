# Sales Order Server-Side Calculations for Thailand WHT and Retention
# Following ERPNext pattern like grand_total calculation
# Called during validate() method - NO client scripts needed
# Consolidated from thai_wht_events.py to remove redundancy

import frappe
from frappe import _
from frappe.utils import flt, cint


def sales_order_calculate_thailand_amounts(doc, method=None):
    """
    Calculate Thailand amounts for Sales Order DocType.
    
    This function handles:
    - Company default WHT/retention rates integration
    - Thai business logic based on Company configuration
    - Preview WHT calculations
    - Customer notification of WHT deductions
    
    Called from Sales Order validate() method - runs server-side before save.
    """
    # DEBUG: Log function entry
    frappe.logger().info(f"🔍 Sales Order Calc: sales_order_calculate_thailand_amounts called for {doc.doctype} {getattr(doc, 'name', 'new')}")
    print(f"🔍 Sales Order Calc: sales_order_calculate_thailand_amounts called for {doc.doctype} {getattr(doc, 'name', 'new')}")
    
    # Ensure this function only processes Sales Order DocType
    if doc.doctype != "Sales Order":
        frappe.logger().info(f"🔍 Sales Order Calc: Not a Sales Order ({doc.doctype}), skipping")
        return
        
    if not doc.company:
        frappe.logger().info(f"🔍 Sales Order Calc: No company set, skipping")
        return
    
    # Apply Company defaults if Sales Order fields are not specified
    apply_company_defaults_for_sales_order(doc)
    
    # Calculate WHT preview (using preview system)
    calculate_wht_preview_for_sales_order(doc)
    
    # Calculate retention amounts if applicable
    calculate_retention_amounts_for_sales_order(doc)
    
    # Calculate final payment amounts
    calculate_final_payment_amounts_for_sales_order(doc)
    
    # DEBUG: Log final state
    frappe.logger().info(f"🔍 Sales Order Calc: AFTER - subject_to_wht = {getattr(doc, 'subject_to_wht', 'NOT_SET')}")
    frappe.logger().info(f"🔍 Sales Order Calc: Final amounts - net_total_after_wht = {getattr(doc, 'net_total_after_wht', 'NOT_SET')}")
    print(f"🔍 Sales Order Calc: AFTER - subject_to_wht = {getattr(doc, 'subject_to_wht', 'NOT_SET')}")
    print(f"🔍 Sales Order Calc: Final amounts - net_total_after_wht = {getattr(doc, 'net_total_after_wht', 'NOT_SET')}")


def apply_company_defaults_for_sales_order(doc):
    """
    Apply Company default values to Sales Order when fields are not specified.
    """
    try:
        # Get Company configuration
        company_doc = frappe.get_cached_doc("Company", doc.company)
        
        # Apply default retention rate if custom_retention is not specified  
        if not doc.get('custom_retention') and company_doc.get('default_retention_rate'):
            doc.custom_retention = flt(company_doc.default_retention_rate)
            
        # Enable custom_subject_to_retention based on Company settings
        if (company_doc.get('construction_service') or company_doc.get('default_retention_rate')) and not doc.get('custom_subject_to_retention'):
            if doc.get('custom_retention') or company_doc.get('default_retention_rate'):
                doc.custom_subject_to_retention = 1
                
    except Exception as e:
        frappe.log_error(f"Error applying Company defaults to Sales Order {doc.name}: {str(e)}")


def calculate_wht_preview_for_sales_order(doc):
    """
    Calculate WHT preview for Sales Order documents
    Consolidated from thai_wht_events.py system
    """
    try:
        # Import preview calculation from thai_wht_preview module
        from .thai_wht_preview import calculate_thai_wht_preview
        
        # Calculate WHT preview
        wht_preview = calculate_thai_wht_preview(doc)
        
        # Update document fields with preview values
        for field, value in wht_preview.items():
            if hasattr(doc, field):
                old_value = getattr(doc, field, None)
                setattr(doc, field, value)
                
                # Log important changes
                if field == 'subject_to_wht' and old_value != value:
                    frappe.logger().info(f"Sales Order WHT Preview: {field} changed from {old_value} to {value}")
        
        # Add informational message if WHT applies
        if wht_preview.get('subject_to_wht'):
            wht_amount = wht_preview.get('estimated_wht_amount', 0)
            net_amount = wht_preview.get('net_total_after_wht', 0)
            
            if wht_amount > 0:
                frappe.msgprint(
                    _(f"WHT Preview: ฿{flt(wht_amount, 2):,.2f} withholding tax estimated. "
                      f"Net payment: ฿{flt(net_amount, 2):,.2f}"),
                    title=_("Withholding Tax Preview"),
                    indicator="blue"
                )
        
    except Exception as e:
        # Log error but don't fail validation
        frappe.log_error(
            f"Error calculating WHT preview for Sales Order {doc.name}: {str(e)}",
            "Sales Order WHT Preview Error"
        )


def calculate_retention_amounts_for_sales_order(doc):
    """Calculate retention amounts when custom_subject_to_retention is enabled"""
    try:
        if doc.get('custom_subject_to_retention') and doc.get('custom_retention') and doc.net_total:
            retention_rate = flt(doc.custom_retention)
            base_amount = flt(doc.net_total)
            
            # Calculate retention amount
            doc.custom_retention_amount = flt((base_amount * retention_rate) / 100, 2)
        else:
            doc.custom_retention_amount = 0
            
    except Exception as e:
        frappe.log_error(f"Error calculating retention amounts for Sales Order {doc.name}: {str(e)}")
        doc.custom_retention_amount = 0


def calculate_final_payment_amounts_for_sales_order(doc):
    """Calculate final payment amounts after WHT and retention deductions"""
    try:
        # Start with grand total (includes VAT)
        grand_total = flt(doc.grand_total)
        
        # Get deduction amounts
        wht_amount = flt(getattr(doc, 'estimated_wht_amount', 0))
        retention_amount = flt(getattr(doc, 'custom_retention_amount', 0))
        
        # Calculate net_total_after_wht: grand_total - estimated_wht_amount
        doc.net_total_after_wht = flt(grand_total - wht_amount, 2)
        
        # Calculate payment amount based on retention status
        if doc.get('custom_subject_to_retention') and retention_amount > 0:
            # custom_net_total_after_wht_retention = grand_total - estimated_wht_amount - custom_retention_amount
            doc.custom_net_total_after_wht_retention = flt(grand_total - wht_amount - retention_amount, 2)
            
            # custom_payment_amount = custom_net_total_after_wht_retention
            doc.custom_payment_amount = doc.custom_net_total_after_wht_retention
        else:
            # No retention: custom_payment_amount = net_total_after_wht
            doc.custom_net_total_after_wht_retention = 0
            doc.custom_payment_amount = doc.net_total_after_wht
        
        # Ensure payment amount is not negative
        if doc.custom_payment_amount < 0:
            doc.custom_payment_amount = 0
            frappe.msgprint(
                _("Warning: Total deductions exceed sales order amount. Payment amount set to zero."),
                alert=True, indicator="orange"
            )
        
        # Convert amounts to words (Thai language support)
        convert_amounts_to_words_for_sales_order(doc)
            
    except Exception as e:
        frappe.log_error(f"Error calculating final payment amounts for Sales Order {doc.name}: {str(e)}")
        # Fallback to grand total
        doc.net_total_after_wht = flt(doc.grand_total)
        doc.custom_payment_amount = flt(doc.grand_total)
        doc.custom_net_total_after_wht_retention = 0


def convert_amounts_to_words_for_sales_order(doc):
    """
    Convert calculated amounts to words for display in Thai documents.
    """
    try:
        from frappe.utils import money_in_words
        
        # Convert net_total_after_wht to words
        if doc.net_total_after_wht and hasattr(doc, 'net_total_after_wht_in_words'):
            try:
                doc.net_total_after_wht_in_words = money_in_words(doc.net_total_after_wht)
            except Exception as e:
                doc.net_total_after_wht_in_words = ""
        
        # Convert custom_net_total_after_wht_retention to words (if retention applies)
        if (doc.get('custom_subject_to_retention') and 
            doc.get('custom_net_total_after_wht_retention') and 
            hasattr(doc, 'custom_net_total_after_wht_and_retention_in_words')):
            try:
                doc.custom_net_total_after_wht_and_retention_in_words = money_in_words(doc.custom_net_total_after_wht_retention)
            except Exception as e:
                doc.custom_net_total_after_wht_and_retention_in_words = ""
        else:
            # Clear retention in_words field if not applicable
            if hasattr(doc, 'custom_net_total_after_wht_and_retention_in_words'):
                doc.custom_net_total_after_wht_and_retention_in_words = ""
                
    except Exception as e:
        frappe.log_error(f"Error converting amounts to words for Sales Order {doc.name}: {str(e)}")
        # Clear the in_words fields on error
        if hasattr(doc, 'net_total_after_wht_in_words'):
            doc.net_total_after_wht_in_words = ""
        if hasattr(doc, 'custom_net_total_after_wht_and_retention_in_words'):
            doc.custom_net_total_after_wht_and_retention_in_words = ""


# ==================================================
# CUSTOMER CONFIGURATION HANDLERS
# ==================================================

@frappe.whitelist()
def get_customer_wht_info_for_sales_order(customer):
    """
    Get WHT configuration for a customer (consolidated from thai_wht_events.py)
    """
    if not customer:
        return {}
    
    try:
        customer_doc = frappe.get_cached_doc("Customer", customer)
        
        return {
            'subject_to_wht': getattr(customer_doc, 'subject_to_wht', False),
            'wht_income_type': getattr(customer_doc, 'wht_income_type', 'service_fees'),
            'custom_wht_rate': getattr(customer_doc, 'custom_wht_rate', 0),
            'is_juristic_person': getattr(customer_doc, 'is_juristic_person', True),
            'tax_id': getattr(customer_doc, 'tax_id', '')
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting customer WHT info for Sales Order {customer}: {str(e)}")
        return {}


def handle_customer_wht_config_change_for_sales_order(customer_name):
    """
    Handle customer WHT configuration changes for open sales orders
    Consolidated from thai_wht_events.py
    """
    try:
        # Find open sales orders for this customer
        open_sales_orders = frappe.get_all("Sales Order", 
            filters={"customer": customer_name, "docstatus": 0},
            fields=["name"]
        )
        
        if not open_sales_orders:
            return 0
            
        updated_count = 0
        for so_info in open_sales_orders:
            try:
                so_doc = frappe.get_doc("Sales Order", so_info['name'])
                
                # Recalculate WHT and amounts
                sales_order_calculate_thailand_amounts(so_doc)
                
                # Save without triggering validation loops
                so_doc.flags.ignore_validate = True
                so_doc.save()
                updated_count += 1
                
            except Exception as e:
                frappe.log_error(
                    f"Error updating WHT for Sales Order {so_info['name']}: {str(e)}",
                    "Customer WHT Config Update Error"
                )
        
        return updated_count
        
    except Exception as e:
        frappe.log_error(
            f"Error handling customer WHT config change for sales orders: {str(e)}",
            "Customer WHT Config Error"
        )
        return 0