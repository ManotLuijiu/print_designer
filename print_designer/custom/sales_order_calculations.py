# Sales Order Server-Side Calculations for Thailand WHT and Retention
# Following ERPNext pattern like grand_total calculation
# Called during validate() method - NO client scripts needed
# Consolidated from thai_wht_events.py to remove redundancy

import frappe
from frappe import _
from frappe.utils import flt, cint


def sales_order_calculate_thailand_amounts(doc, method=None):
    """
    Calculate Thailand amounts for Sales Order DocType ONLY.
    
    This function is specifically designed for Sales Order and handles:
    - Company default WHT/retention rates integration
    - Thai business logic based on Company configuration
    - Preview WHT calculations
    - Customer notification of WHT deductions
    
    Called from Sales Order validate() method - runs server-side before save.
    """
    # DEBUG: Log function entry
    frappe.logger().info(f"🔍 Sales Order Calc: sales_order_calculate_thailand_amounts called for {doc.doctype} {getattr(doc, 'name', 'new')}")
    print(f"\n🔍 SALES ORDER CALC STARTED for {doc.doctype} {getattr(doc, 'name', 'new')}")
    print(f"  - pd_custom_subject_to_wht = {getattr(doc, 'pd_custom_subject_to_wht', 'NOT_SET')}")
    print(f"  - pd_custom_withholding_tax_amount = {getattr(doc, 'pd_custom_withholding_tax_amount', 'NOT_SET')}")
    print(f"  - pd_custom_net_total_after_wht = {getattr(doc, 'pd_custom_net_total_after_wht', 'NOT_SET')}")
    print(f"  - pd_custom_payment_amount = {getattr(doc, 'pd_custom_payment_amount', 'NOT_SET')}")
    
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
    apply_company_defaults_for_sales_order(doc)
    
    # Calculate withholding tax amounts
    calculate_withholding_tax_amounts_for_sales_order(doc)
    
    # Calculate WHT preview (using preview system)
    calculate_wht_preview_for_sales_order(doc)
    
    # Calculate retention amounts if applicable
    calculate_retention_amounts_for_sales_order(doc)
    
    # Calculate final payment amounts
    calculate_final_payment_amounts_for_sales_order(doc)
    
    # DEBUG: Log final state
    frappe.logger().info(f"🔍 Sales Order Calc: AFTER - pd_custom_subject_to_wht = {getattr(doc, 'pd_custom_subject_to_wht', 'NOT_SET')}")
    frappe.logger().info(f"🔍 Sales Order Calc: Final amounts - pd_custom_net_total_after_wht = {getattr(doc, 'pd_custom_net_total_after_wht', 'NOT_SET')}")
    print(f"🔍 Sales Order Calc: AFTER - pd_custom_subject_to_wht = {getattr(doc, 'pd_custom_subject_to_wht', 'NOT_SET')}")
    print(f"🔍 Sales Order Calc: Final amounts - pd_custom_net_total_after_wht = {getattr(doc, 'pd_custom_net_total_after_wht', 'NOT_SET')}")


def apply_company_defaults_for_sales_order(doc):
    """
    Apply Company default values to Sales Order when fields are not specified.
    """
    try:
        # Get Company configuration
        company_doc = frappe.get_cached_doc("Company", doc.company)
        
        # Populate fields for client-side depends_on conditions
        doc.thailand_service_business = company_doc.get('thailand_service_business', 0)
        doc.construction_service = company_doc.get('construction_service', 0)
        
        # Apply default WHT rate if pd_custom_withholding_tax_pct is not specified
        if not doc.get('pd_custom_withholding_tax_pct') and company_doc.get('default_wht_rate'):
            doc.pd_custom_withholding_tax_pct = flt(company_doc.default_wht_rate)
        
        # Apply default retention rate if pd_custom_retention_pct is not specified  
        if not doc.get('pd_custom_retention_pct') and company_doc.get('default_retention_rate'):
            doc.pd_custom_retention_pct = flt(company_doc.default_retention_rate)
            
        # NOTE: Removed auto-enablement of pd_custom_subject_to_retention
        # Field visibility is controlled by depends_on condition: "eval:doc.company && doc.construction_service"
        # Users must manually enable retention when needed
                
    except Exception as e:
        frappe.log_error(f"Error applying Company defaults to Sales Order {doc.name}: {str(e)}")


def calculate_withholding_tax_amounts_for_sales_order(doc):
    """Calculate withholding tax amounts based on pd_custom_withholding_tax_pct percentage"""
    try:
        # Only calculate WHT if user has enabled pd_custom_subject_to_wht
        if doc.get('pd_custom_subject_to_wht') and doc.pd_custom_withholding_tax_pct and doc.net_total:
            wht_rate = flt(doc.pd_custom_withholding_tax_pct)  # Already in percentage
            current_net_total = flt(doc.net_total)
            
            # Calculate what the WHT amount SHOULD be based on current net_total
            expected_wht_amount = flt((current_net_total * wht_rate) / 100, 2)
            current_wht_amount = flt(doc.get('pd_custom_withholding_tax_amount', 0))
            
            # Check if current amount is significantly different from expected (more than 0.01 difference)
            amount_mismatch = abs(current_wht_amount - expected_wht_amount) > 0.01
            
            # Calculate if:
            # 1. No amount is set yet (new document), OR
            # 2. Current amount doesn't match what it should be based on net_total (after refresh/item changes)
            if not current_wht_amount or amount_mismatch:
                doc.pd_custom_withholding_tax_amount = expected_wht_amount
                
                if amount_mismatch and current_wht_amount > 0:
                    print(f"  - RECALCULATED pd_custom_withholding_tax_amount = {doc.pd_custom_withholding_tax_amount} (was {current_wht_amount}, expected {expected_wht_amount} for net_total {current_net_total})")
                    frappe.logger().info(f"Sales Order Calc: Recalculated WHT due to mismatch - was {current_wht_amount}, now {expected_wht_amount}")
                else:
                    print(f"  - CALCULATED pd_custom_withholding_tax_amount = {doc.pd_custom_withholding_tax_amount} (net_total {current_net_total} * rate {wht_rate}%)")
                    frappe.logger().info(f"Sales Order Calc: Calculated pd_custom_withholding_tax_amount = {doc.pd_custom_withholding_tax_amount}")
            else:
                print(f"  - PRESERVED pd_custom_withholding_tax_amount = {doc.pd_custom_withholding_tax_amount} (matches expected {expected_wht_amount})")
                frappe.logger().info(f"Sales Order Calc: Preserved WHT amount = {doc.pd_custom_withholding_tax_amount} (correct for net_total {current_net_total})")
        else:
            # Clear amount if conditions not met
            doc.pd_custom_withholding_tax_amount = 0
            
    except Exception as e:
        frappe.log_error(f"Error calculating withholding tax amounts for Sales Order {doc.name}: {str(e)}")
        # Don't fail validation, just clear WHT fields
        doc.pd_custom_withholding_tax_amount = 0


def calculate_wht_preview_for_sales_order(doc):
    """
    Calculate WHT preview for Sales Order documents
    Uses existing pd_custom_withholding_tax_amount field (no longer using estimated_wht_amount)
    """
    try:
        # Add informational message if WHT applies (using existing calculated amount)
        if doc.get('pd_custom_subject_to_wht') and doc.get('pd_custom_withholding_tax_amount'):
            wht_amount = flt(doc.pd_custom_withholding_tax_amount, 2)
            net_amount = flt(doc.pd_custom_net_total_after_wht, 2)
            
            if wht_amount > 0:
                # Use realtime notification (bottom-right corner) instead of modal popup
                frappe.publish_realtime(
                    event="show_alert",
                    message={
                        "message": _(f"WHT Preview: ฿{wht_amount:,.2f} withholding tax calculated. Net payment: ฿{net_amount:,.2f}"),
                        "indicator": "blue"
                    },
                    user=frappe.session.user
                )
        
    except Exception as e:
        # Log error but don't fail validation
        frappe.log_error(
            f"Error displaying WHT preview for Sales Order {doc.name}: {str(e)}",
            "Sales Order WHT Preview Error"
        )


def calculate_retention_amounts_for_sales_order(doc):
    """Calculate retention amounts when pd_custom_subject_to_retention is enabled"""
    try:
        if doc.get('pd_custom_subject_to_retention') and doc.get('pd_custom_retention_pct') and doc.net_total:
            retention_rate = flt(doc.pd_custom_retention_pct)
            base_amount = flt(doc.net_total)
            
            # Calculate retention amount
            doc.pd_custom_retention_amount = flt((base_amount * retention_rate) / 100, 2)
        else:
            doc.pd_custom_retention_amount = 0
            
    except Exception as e:
        frappe.log_error(f"Error calculating retention amounts for Sales Order {doc.name}: {str(e)}")
        doc.pd_custom_retention_amount = 0


def calculate_final_payment_amounts_for_sales_order(doc):
    """Calculate final payment amounts after WHT and retention deductions"""
    try:
        # Start with grand total (includes VAT)
        grand_total = flt(doc.grand_total)
        
        # DEBUG: Print initial values
        print(f"🔍 Sales Order Payment Calc START:")
        print(f"  - grand_total = {grand_total}")
        print(f"  - pd_custom_net_total_after_wht (before) = {getattr(doc, 'pd_custom_net_total_after_wht', 'NOT_SET')}")
        print(f"  - pd_custom_payment_amount (before) = {getattr(doc, 'pd_custom_payment_amount', 'NOT_SET')}")
        
        # Get deduction amounts - use correct field name: pd_custom_withholding_tax_amount (not estimated_wht_amount)
        wht_amount = flt(getattr(doc, 'pd_custom_withholding_tax_amount', 0))
        retention_amount = flt(getattr(doc, 'pd_custom_retention_amount', 0))
        
        print(f"  - pd_custom_withholding_tax_amount = {wht_amount}")
        print(f"  - pd_custom_retention_amount = {retention_amount}")
        
        # Calculate what pd_custom_net_total_after_wht SHOULD be based on current grand_total and wht_amount
        expected_net_total_after_wht = flt(grand_total - wht_amount, 2)
        current_net_total_after_wht = flt(doc.get('pd_custom_net_total_after_wht', 0))
        
        # Check if current amount is significantly different from expected
        amount_mismatch = abs(current_net_total_after_wht - expected_net_total_after_wht) > 0.01
        
        # Calculate if:
        # 1. No amount is set yet (new document), OR
        # 2. Current amount doesn't match what it should be based on grand_total and wht_amount
        if not current_net_total_after_wht or amount_mismatch:
            doc.pd_custom_net_total_after_wht = expected_net_total_after_wht
            
            if amount_mismatch and current_net_total_after_wht > 0:
                print(f"  - RECALCULATED pd_custom_net_total_after_wht = {doc.pd_custom_net_total_after_wht} (was {current_net_total_after_wht}, expected {expected_net_total_after_wht})")
                frappe.logger().info(f"Sales Order Calc: Recalculated pd_custom_net_total_after_wht due to mismatch - was {current_net_total_after_wht}, now {expected_net_total_after_wht}")
            else:
                print(f"  - CALCULATED pd_custom_net_total_after_wht = {doc.pd_custom_net_total_after_wht} (grand_total {grand_total} - wht_amount {wht_amount})")
                frappe.logger().info(f"Sales Order Calc: Calculated pd_custom_net_total_after_wht = {doc.pd_custom_net_total_after_wht}")
        else:
            print(f"  - PRESERVED pd_custom_net_total_after_wht = {doc.pd_custom_net_total_after_wht} (matches expected {expected_net_total_after_wht})")
            frappe.logger().info(f"Sales Order Calc: Preserved pd_custom_net_total_after_wht = {doc.pd_custom_net_total_after_wht} (correct for grand_total {grand_total})")
        
        # Calculate payment amount based on retention status
        print(f"  - pd_custom_subject_to_retention = {doc.get('pd_custom_subject_to_retention')}")
        
        if doc.get('pd_custom_subject_to_retention') and retention_amount > 0:
            # pd_custom_net_after_wht_retention = grand_total - pd_custom_withholding_tax_amount - pd_custom_retention_amount
            doc.pd_custom_net_after_wht_retention = flt(grand_total - wht_amount - retention_amount, 2)
            print(f"  - RETENTION ACTIVE: pd_custom_net_after_wht_retention = {doc.pd_custom_net_after_wht_retention} (grand_total {grand_total} - wht {wht_amount} - retention {retention_amount})")
            
            # pd_custom_payment_amount = pd_custom_net_after_wht_retention
            doc.pd_custom_payment_amount = doc.pd_custom_net_after_wht_retention
            print(f"  - pd_custom_payment_amount = {doc.pd_custom_payment_amount} (with retention)")
        else:
            # No retention: pd_custom_payment_amount = pd_custom_net_total_after_wht
            doc.pd_custom_net_after_wht_retention = 0
            doc.pd_custom_payment_amount = doc.pd_custom_net_total_after_wht
            print(f"  - NO RETENTION: pd_custom_payment_amount = {doc.pd_custom_payment_amount} (equals pd_custom_net_total_after_wht)")
        
        # Ensure payment amount is not negative
        if doc.pd_custom_payment_amount < 0:
            print(f"  - WARNING: Payment amount was negative ({doc.pd_custom_payment_amount}), setting to 0")
            doc.pd_custom_payment_amount = 0
            frappe.msgprint(
                _("Warning: Total deductions exceed sales order amount. Payment amount set to zero."),
                alert=True, indicator="orange"
            )
        
        # Convert amounts to words (Thai language support)
        convert_amounts_to_words_for_sales_order(doc)
        
        # DEBUG: Print final summary
        print(f"🔍 Sales Order Payment Calc END:")
        print(f"  - FINAL pd_custom_net_total_after_wht = {doc.pd_custom_net_total_after_wht}")
        print(f"  - FINAL pd_custom_payment_amount = {doc.pd_custom_payment_amount}")
        print(f"  - FINAL pd_custom_net_after_wht_retention = {getattr(doc, 'pd_custom_net_after_wht_retention', 0)}")
        print("=" * 50)
            
    except Exception as e:
        frappe.log_error(f"Error calculating final payment amounts for Sales Order {doc.name}: {str(e)}")
        # Fallback to grand total
        doc.pd_custom_net_total_after_wht = flt(doc.grand_total)
        doc.pd_custom_payment_amount = flt(doc.grand_total)
        doc.pd_custom_net_after_wht_retention = 0


def convert_amounts_to_words_for_sales_order(doc):
    """
    Convert calculated amounts to words for display in Thai documents.
    Updates the 'in_words' fields for pd_custom_net_total_after_wht and custom_net_total_after_wht_and_retention.
    """
    try:
        from frappe.utils import money_in_words
        
        # Convert pd_custom_net_total_after_wht to words
        if doc.pd_custom_net_total_after_wht and hasattr(doc, 'pd_custom_net_total_after_wht_words'):
            try:
                doc.pd_custom_net_total_after_wht_words = money_in_words(doc.pd_custom_net_total_after_wht)
                print(f"🔍 Sales Order Calc: pd_custom_net_total_after_wht_words = {doc.pd_custom_net_total_after_wht_words}")
            except Exception as e:
                doc.pd_custom_net_total_after_wht_words = ""
                print(f"🔍 Sales Order Calc: Error converting pd_custom_net_total_after_wht to words: {str(e)}")
        
        # Convert pd_custom_net_after_wht_retention to words (if retention applies)
        if (doc.get('pd_custom_subject_to_retention') and 
            doc.get('pd_custom_net_after_wht_retention') and 
            hasattr(doc, 'pd_custom_net_after_wht_retention_words')):
            try:
                doc.pd_custom_net_after_wht_retention_words = money_in_words(doc.pd_custom_net_after_wht_retention)
                print(f"🔍 Sales Order Calc: pd_custom_net_after_wht_retention_words = {doc.pd_custom_net_after_wht_retention_words}")
            except Exception as e:
                doc.pd_custom_net_after_wht_retention_words = ""
                print(f"🔍 Sales Order Calc: Error converting pd_custom_net_after_wht_retention to words: {str(e)}")
        else:
            # Clear retention in_words field if not applicable
            if hasattr(doc, 'pd_custom_net_after_wht_retention_words'):
                doc.pd_custom_net_after_wht_retention_words = ""
                print(f"🔍 Sales Order Calc: Cleared pd_custom_net_after_wht_retention_words (no retention)")
                
    except Exception as e:
        frappe.log_error(f"Error converting amounts to words for Sales Order {doc.name}: {str(e)}")
        # Clear the in_words fields on error
        if hasattr(doc, 'pd_custom_net_total_after_wht_words'):
            doc.pd_custom_net_total_after_wht_words = ""
        if hasattr(doc, 'pd_custom_net_after_wht_retention_words'):
            doc.pd_custom_net_after_wht_retention_words = ""
        print(f"🔍 Sales Order Calc: Error in convert_amounts_to_words_for_sales_order: {str(e)}")


# Note: This function is the main entry point called from hooks.py
# sales_order_calculate_thailand_amounts (defined at line 11) is the correct function


# ==================================================
# CONSOLIDATED WHT PREVIEW SYSTEM
# ==================================================
# Moved from thai_wht_events.py to consolidate calculation logic


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
            'pd_custom_subject_to_wht': getattr(customer_doc, 'pd_custom_subject_to_wht', False),
            'pd_custom_wht_income_type': getattr(customer_doc, 'pd_custom_wht_income_type', 'service_fees'),
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