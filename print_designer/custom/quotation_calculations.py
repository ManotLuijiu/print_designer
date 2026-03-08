# Quotation Server-Side Calculations for Thailand WHT and Retention
# Following ERPNext pattern like grand_total calculation
# Called during validate() method - NO client scripts needed
# Consolidated from thai_wht_events.py to remove redundancy

import frappe
from frappe import _
from frappe.utils import flt, cint


def quotation_calculate_thailand_amounts(doc, method=None):
    """
    Calculate Thailand amounts for Quotation DocType ONLY.
    
    This function is specifically designed for Quotation and handles:
    - Company default WHT/retention rates integration
    - Thai business logic based on Company configuration
    - Custom field calculations (pd_custom_withholding_tax_amount, pd_custom_retention_amount)
    - Final payment amount calculations (pd_custom_net_total_after_wht)
    
    Called from Quotation validate() method - runs server-side before save.
    Uses Company default values when Quotation fields are not specified.
    """
    # DEBUG: Log function entry
    frappe.logger().info(f"🔍 Quotation Calc: quotation_calculate_thailand_amounts called for {doc.doctype} {getattr(doc, 'name', 'new')}")
    frappe.logger().info(f"🔍 Quotation Calc: BEFORE - pd_custom_subject_to_wht = {getattr(doc, 'pd_custom_subject_to_wht', 'NOT_SET')}")
    print(f"🔍 Quotation Calc: quotation_calculate_thailand_amounts called for {doc.doctype} {getattr(doc, 'name', 'new')}")
    print(f"🔍 Quotation Calc: BEFORE - pd_custom_subject_to_wht = {getattr(doc, 'pd_custom_subject_to_wht', 'NOT_SET')}")
    
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
    frappe.logger().info(f"🔍 Quotation Calc: AFTER - pd_custom_subject_to_wht = {getattr(doc, 'pd_custom_subject_to_wht', 'NOT_SET')}")
    frappe.logger().info(f"🔍 Quotation Calc: Final amounts - pd_custom_net_total_after_wht = {getattr(doc, 'pd_custom_net_total_after_wht', 'NOT_SET')}")
    print(f"🔍 Quotation Calc: AFTER - pd_custom_subject_to_wht = {getattr(doc, 'pd_custom_subject_to_wht', 'NOT_SET')}")
    print(f"🔍 Quotation Calc: Final amounts - pd_custom_net_total_after_wht = {getattr(doc, 'pd_custom_net_total_after_wht', 'NOT_SET')}")


def apply_company_defaults(doc):
    """
    Apply Company default values to Quotation when fields are not specified.
    Uses Company.default_wht_rate and Company.default_retention_rate as fallbacks.
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
            
        # Note: pd_custom_subject_to_wht should be manually controlled by user
        # Field visibility is controlled by depends_on condition in Custom Field
        # User decides whether Quotation contains services subject to WHT
                
        # NOTE: Removed auto-enablement of pd_custom_subject_to_retention
        # Field visibility is controlled by depends_on condition: "eval:doc.company && doc.construction_service"
        # Users must manually enable retention when needed
                
    except Exception as e:
        frappe.log_error(f"Error applying Company defaults to Quotation {doc.name}: {str(e)}")
        # Don't fail validation - just continue without defaults


def calculate_withholding_tax_amounts(doc):
    """Calculate withholding tax amounts based on pd_custom_withholding_tax_pct percentage"""
    try:
        # Only calculate WHT if user has enabled pd_custom_subject_to_wht
        if doc.get('pd_custom_subject_to_wht') and doc.pd_custom_withholding_tax_pct and doc.net_total:
            wht_rate = flt(doc.pd_custom_withholding_tax_pct)  # Already in percentage
            base_amount = flt(doc.net_total)
            
            # Calculate WHT amount
            doc.pd_custom_withholding_tax_amount = flt((base_amount * wht_rate) / 100, 2)
        else:
            doc.pd_custom_withholding_tax_amount = 0
            
    except Exception as e:
        frappe.log_error(f"Error calculating withholding tax amounts for Quotation {doc.name}: {str(e)}")
        # Don't fail validation, just clear WHT fields
        doc.pd_custom_withholding_tax_amount = 0


def calculate_retention_amounts(doc):
    """Calculate retention amounts when pd_custom_subject_to_retention is enabled"""
    try:
        if doc.pd_custom_subject_to_retention and doc.pd_custom_retention_pct and doc.net_total:
            retention_rate = flt(doc.pd_custom_retention_pct)  # Already in percentage
            base_amount = flt(doc.net_total)
            
            # Calculate retention amount: pd_custom_retention_amount = net_total * pd_custom_retention_pct
            doc.pd_custom_retention_amount = flt((base_amount * retention_rate) / 100, 2)
        else:
            doc.pd_custom_retention_amount = 0
            
    except Exception as e:
        frappe.log_error(f"Error calculating retention amounts for Quotation {doc.name}: {str(e)}")
        # Don't fail validation, just clear retention fields
        doc.pd_custom_retention_amount = 0


def calculate_final_payment_amounts(doc):
    """Calculate final payment amounts after WHT and retention deductions"""
    try:
        # Start with grand total (includes VAT)
        grand_total = flt(doc.grand_total)
        
        # Get deduction amounts
        wht_amount = flt(doc.pd_custom_withholding_tax_amount)
        retention_amount = flt(doc.pd_custom_retention_amount)
        
        # Calculate pd_custom_net_total_after_wht: grand_total - pd_custom_withholding_tax_amount
        doc.pd_custom_net_total_after_wht = flt(grand_total - wht_amount, 2)
        
        # Calculate payment amount based on retention status
        if doc.pd_custom_subject_to_retention and retention_amount > 0:
            # 5.2 pd_custom_net_after_wht_retention = grand_total - pd_custom_withholding_tax_amount - pd_custom_retention_amount
            doc.pd_custom_net_after_wht_retention = flt(grand_total - wht_amount - retention_amount, 2)
            
            # 5.3 pd_custom_payment_amount = pd_custom_net_after_wht_retention
            doc.pd_custom_payment_amount = doc.pd_custom_net_after_wht_retention
        else:
            # No retention: pd_custom_payment_amount = pd_custom_net_total_after_wht
            doc.pd_custom_net_after_wht_retention = 0
            doc.pd_custom_payment_amount = doc.pd_custom_net_total_after_wht
        
        # Ensure payment amount is not negative
        if doc.pd_custom_payment_amount < 0:
            doc.pd_custom_payment_amount = 0
            frappe.msgprint(
                _("Warning: Total deductions exceed quotation amount. Payment amount set to zero."),
                alert=True, indicator="orange"
            )
        
        # Convert amounts to words (Thai language support)
        convert_amounts_to_words(doc)
            
    except Exception as e:
        frappe.log_error(f"Error calculating final payment amounts for Quotation {doc.name}: {str(e)}")
        # Fallback to grand total
        doc.pd_custom_net_total_after_wht = flt(doc.grand_total)
        doc.pd_custom_payment_amount = flt(doc.grand_total)
        doc.pd_custom_net_after_wht_retention = 0


def validate_thailand_calculations(doc):
    """
    Validate Thailand-specific calculations and constraints.
    Called after calculations are complete.
    """
    # Validate retention constraints
    if doc.pd_custom_retention_amount and doc.pd_custom_retention_amount > doc.net_total:
        frappe.throw(_("Retention amount cannot exceed net total"))
    
    # Validate withholding tax constraints  
    if doc.pd_custom_withholding_tax_amount and doc.pd_custom_withholding_tax_amount > doc.net_total:
        frappe.throw(_("Withholding tax amount cannot exceed net total"))
    
    # Validate total deductions don't exceed quotation amount
    total_deductions = flt(doc.pd_custom_retention_amount) + flt(doc.pd_custom_withholding_tax_amount)
    if total_deductions > doc.grand_total:
        frappe.throw(
            _("Total deductions ({0}) cannot exceed quotation grand total ({1})").format(
                total_deductions, doc.grand_total
            )
        )


def convert_amounts_to_words(doc):
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
                print(f"🔍 Quotation Calc: pd_custom_net_total_after_wht_words = {doc.pd_custom_net_total_after_wht_words}")
            except Exception as e:
                doc.pd_custom_net_total_after_wht_words = ""
                print(f"🔍 Quotation Calc: Error converting pd_custom_net_total_after_wht to words: {str(e)}")
        
        # Convert pd_custom_net_after_wht_retention to words (if retention applies)
        if (doc.pd_custom_subject_to_retention and 
            doc.pd_custom_net_after_wht_retention and 
            hasattr(doc, 'pd_custom_net_after_wht_retention_words')):
            try:
                doc.pd_custom_net_after_wht_retention_words = money_in_words(doc.pd_custom_net_after_wht_retention)
                print(f"🔍 Quotation Calc: pd_custom_net_after_wht_retention_words = {doc.pd_custom_net_after_wht_retention_words}")
            except Exception as e:
                doc.pd_custom_net_after_wht_retention_words = ""
                print(f"🔍 Quotation Calc: Error converting pd_custom_net_after_wht_retention to words: {str(e)}")
        else:
            # Clear retention in_words field if not applicable
            if hasattr(doc, 'pd_custom_net_after_wht_retention_words'):
                doc.pd_custom_net_after_wht_retention_words = ""
                print(f"🔍 Quotation Calc: Cleared pd_custom_net_after_wht_retention_words (no retention)")
                
    except Exception as e:
        frappe.log_error(f"Error converting amounts to words for Quotation {doc.name}: {str(e)}")
        # Clear the in_words fields on error
        if hasattr(doc, 'pd_custom_net_total_after_wht_words'):
            doc.pd_custom_net_total_after_wht_words = ""
        if hasattr(doc, 'pd_custom_net_after_wht_retention_words'):
            doc.pd_custom_net_after_wht_retention_words = ""
        print(f"🔍 Quotation Calc: Error in convert_amounts_to_words: {str(e)}")


# Note: This function is the main entry point called from hooks.py
# quotation_calculate_thailand_amounts (defined at line 10) is the correct function


# ==================================================
# CONSOLIDATED WHT PREVIEW SYSTEM
# ==================================================
# Moved from thai_wht_events.py to consolidate calculation logic

def calculate_wht_preview_for_quotation(doc, method=None):
    """
    Calculate WHT preview for Quotation documents
    Uses existing pd_custom_withholding_tax_amount field (no longer using estimated_wht_amount)
    """
    try:
        if doc.doctype != "Quotation":
            return
        
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
            f"Error displaying WHT preview for Quotation {doc.name}: {str(e)}",
            "Quotation WHT Preview Error"
        )


@frappe.whitelist()
def get_customer_wht_info_for_quotation(customer):
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
        frappe.log_error(f"Error getting customer WHT info for Quotation {customer}: {str(e)}")
        return {}


def handle_customer_wht_config_change_for_quotation(customer_name):
    """
    Handle customer WHT configuration changes for open quotations
    Consolidated from thai_wht_events.py
    """
    try:
        # Find open quotations for this customer
        open_quotations = frappe.get_all("Quotation", 
            filters={"customer": customer_name, "docstatus": 0},
            fields=["name"]
        )
        
        if not open_quotations:
            return 0
            
        updated_count = 0
        for quotation_info in open_quotations:
            try:
                quotation_doc = frappe.get_doc("Quotation", quotation_info['name'])
                
                # Recalculate both custom and preview WHT
                quotation_calculate_thailand_amounts(quotation_doc)
                calculate_wht_preview_for_quotation(quotation_doc)
                
                # Save without triggering validation loops
                quotation_doc.flags.ignore_validate = True
                quotation_doc.save()
                updated_count += 1
                
            except Exception as e:
                frappe.log_error(
                    f"Error updating WHT for Quotation {quotation_info['name']}: {str(e)}",
                    "Customer WHT Config Update Error"
                )
        
        return updated_count
        
    except Exception as e:
        frappe.log_error(
            f"Error handling customer WHT config change for quotations: {str(e)}",
            "Customer WHT Config Error"
        )
        return 0