# Sales Invoice Server-Side Calculations for Thailand WHT and Retention
# Following ERPNext pattern like grand_total calculation
# Called during validate() method - NO client scripts needed
# Consolidated from thai_wht_events.py to remove redundancy

import frappe
from frappe import _
from frappe.utils import flt, cint


def sales_invoice_calculate_thailand_amounts(doc, method=None):
    """
    Calculate Thailand amounts for Sales Invoice DocType ONLY.

    This function is specifically designed for Sales Invoice and handles:
    - Company default WHT/retention rates integration
    - Thai business logic based on Company configuration
    - Preview WHT calculations
    - Customer notification of WHT deductions

    Called from Sales Invoice validate() method - runs server-side before save.
    """
    # DEBUG: Log function entry
    frappe.logger().info(f"🔍 Sales Invoice Calc: sales_invoice_calculate_thailand_amounts called for {doc.doctype} {getattr(doc, 'name', 'new')}")
    print(f"🔍 Sales Invoice Calc: sales_invoice_calculate_thailand_amounts called for {doc.doctype} {getattr(doc, 'name', 'new')}")

    # Ensure this function only processes Sales Invoice DocType
    if doc.doctype != "Sales Invoice":
        frappe.logger().info(f"🔍 Sales Invoice Calc: Not a Sales Invoice ({doc.doctype}), skipping")
        return

    if not doc.company:
        frappe.logger().info(f"🔍 Sales Invoice Calc: No company set, skipping")
        return

    # Apply Company defaults if Sales Invoice fields are not specified
    apply_company_defaults_for_sales_invoice(doc)
    
    # Calculate withholding tax amounts
    calculate_withholding_tax_amounts_for_sales_invoice(doc)
    
    # Calculate WHT preview (using preview system)
    calculate_wht_preview_for_sales_invoice(doc)
    
    # Calculate retention amounts if applicable
    calculate_retention_amounts_for_sales_invoice(doc)
    
    # Calculate final payment amounts
    calculate_final_payment_amounts_for_sales_invoice(doc)
    
    # DEBUG: Log final state
    frappe.logger().info(f"🔍 Sales Invoice Calc: AFTER - subject_to_wht = {getattr(doc, 'subject_to_wht', 'NOT_SET')}")
    frappe.logger().info(f"🔍 Sales Invoice Calc: Final amounts - net_total_after_wht = {getattr(doc, 'net_total_after_wht', 'NOT_SET')}")
    print(f"🔍 Sales Invoice Calc: AFTER - subject_to_wht = {getattr(doc, 'subject_to_wht', 'NOT_SET')}")
    print(f"🔍 Sales Invoice Calc: Final amounts - net_total_after_wht = {getattr(doc, 'net_total_after_wht', 'NOT_SET')}")


def apply_company_defaults_for_sales_invoice(doc):
    """
    Apply Company default values to Sales Invoice when fields are not specified.
    """
    try:
        # Get Company configuration
        company_doc = frappe.get_cached_doc("Company", doc.company)
        
        # Populate fields for client-side depends_on conditions
        doc.thailand_service_business = company_doc.get('thailand_service_business', 0)
        doc.construction_service = company_doc.get('construction_service', 0)
        
        # Apply default WHT rate if custom_withholding_tax is not specified
        if not doc.get('custom_withholding_tax') and company_doc.get('default_wht_rate'):
            doc.custom_withholding_tax = flt(company_doc.default_wht_rate)
        
        # Apply default retention rate if custom_retention is not specified  
        if not doc.get('custom_retention') and company_doc.get('default_retention_rate'):
            doc.custom_retention = flt(company_doc.default_retention_rate)
            
        # NOTE: Removed auto-enablement of custom_subject_to_retention
        # Field visibility is controlled by depends_on condition: "eval:doc.company && doc.construction_service"
        # Users must manually enable retention when needed
                
    except Exception as e:
        frappe.log_error(f"Error applying Company defaults to Sales Invoice {doc.name}: {str(e)}")


def calculate_withholding_tax_amounts_for_sales_invoice(doc):
    """Calculate withholding tax amounts based on custom_withholding_tax percentage"""
    try:
        # Only calculate WHT if user has enabled subject_to_wht
        if doc.get('subject_to_wht') and doc.custom_withholding_tax and doc.net_total:
            wht_rate = flt(doc.custom_withholding_tax)  # Already in percentage
            current_net_total = flt(doc.net_total)
            
            # Calculate what the WHT amount SHOULD be based on current net_total
            expected_wht_amount = flt((current_net_total * wht_rate) / 100, 2)
            current_wht_amount = flt(doc.get('custom_withholding_tax_amount', 0))
            
            # Check if current amount is significantly different from expected (more than 0.01 difference)
            amount_mismatch = abs(current_wht_amount - expected_wht_amount) > 0.01
            
            # Calculate if:
            # 1. No amount is set yet (new document), OR
            # 2. Current amount doesn't match what it should be based on net_total (after refresh/item changes)
            if not current_wht_amount or amount_mismatch:
                doc.custom_withholding_tax_amount = expected_wht_amount
                
                if amount_mismatch and current_wht_amount > 0:
                    print(f"  - RECALCULATED custom_withholding_tax_amount = {expected_wht_amount} (expected {expected_wht_amount} vs current {current_wht_amount})")
                    frappe.logger().info(f"Sales Invoice Calc: Recalculated due to amount mismatch: expected {expected_wht_amount} vs current {current_wht_amount}")
                else:
                    print(f"  - CALCULATED custom_withholding_tax_amount = {expected_wht_amount} (net_total {current_net_total} * rate {wht_rate}%)")
                    frappe.logger().info(f"Sales Invoice Calc: Calculated custom_withholding_tax_amount = {expected_wht_amount}")
            else:
                print(f"  - PRESERVED custom_withholding_tax_amount = {current_wht_amount} (already correct value)")
                frappe.logger().info(f"Sales Invoice Calc: Preserved custom_withholding_tax_amount = {current_wht_amount}")
        else:
            # Clear amount if conditions not met
            doc.custom_withholding_tax_amount = 0
            
    except Exception as e:
        frappe.log_error(f"Error calculating withholding tax amounts for Sales Invoice {doc.name}: {str(e)}")
        # Don't fail validation, just clear WHT fields
        doc.custom_withholding_tax_amount = 0


def calculate_wht_preview_for_sales_invoice(doc):
    """
    Calculate WHT preview for Sales Invoice documents
    Uses existing custom_withholding_tax_amount field (no longer using estimated_wht_amount)
    """
    try:
        # Add informational message if WHT applies (using existing calculated amount)
        if doc.get('subject_to_wht') and doc.get('custom_withholding_tax_amount'):
            wht_amount = flt(doc.custom_withholding_tax_amount, 2)
            net_amount = flt(doc.net_total_after_wht, 2)
            
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
            f"Error displaying WHT preview for Sales Invoice {doc.name}: {str(e)}",
            "Sales Invoice WHT Preview Error"
        )


def calculate_retention_amounts_for_sales_invoice(doc):
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
        frappe.log_error(f"Error calculating retention amounts for Sales Invoice {doc.name}: {str(e)}")
        doc.custom_retention_amount = 0


def calculate_final_payment_amounts_for_sales_invoice(doc):
    """Calculate final payment amounts after WHT and retention deductions"""
    try:
        # Start with grand total (includes VAT)
        grand_total = flt(doc.grand_total)
        
        # Get deduction amounts - use correct field name: custom_withholding_tax_amount (not estimated_wht_amount)
        wht_amount = flt(getattr(doc, 'custom_withholding_tax_amount', 0))
        retention_amount = flt(getattr(doc, 'custom_retention_amount', 0))
        
        # Calculate what net_total_after_wht SHOULD be based on current grand_total and wht_amount
        expected_net_total_after_wht = flt(grand_total - wht_amount, 2)
        current_net_total_after_wht = flt(doc.get('net_total_after_wht', 0))
        
        # Check if current amount is significantly different from expected
        amount_mismatch = abs(current_net_total_after_wht - expected_net_total_after_wht) > 0.01
        
        # Calculate if:
        # 1. No amount is set yet (new document), OR  
        # 2. Current amount doesn't match what it should be based on grand_total and wht_amount
        if not current_net_total_after_wht or amount_mismatch:
            doc.net_total_after_wht = expected_net_total_after_wht
            
            if amount_mismatch and current_net_total_after_wht > 0:
                frappe.logger().info(f"Sales Invoice Calc: Recalculated net_total_after_wht due to amount mismatch: expected {expected_net_total_after_wht} vs current {current_net_total_after_wht}")
            else:
                frappe.logger().info(f"Sales Invoice Calc: Calculated net_total_after_wht = {expected_net_total_after_wht}")
        else:
            frappe.logger().info(f"Sales Invoice Calc: Preserved net_total_after_wht = {current_net_total_after_wht}")
        
        # Calculate payment amount based on retention status
        if doc.get('custom_subject_to_retention') and retention_amount > 0:
            # custom_net_total_after_wht_retention = grand_total - custom_withholding_tax_amount - custom_retention_amount
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
                _("Warning: Total deductions exceed sales invoice amount. Payment amount set to zero."),
                alert=True, indicator="orange"
            )
        
        # Convert amounts to words (Thai language support)
        convert_amounts_to_words_for_sales_invoice(doc)
            
    except Exception as e:
        frappe.log_error(f"Error calculating final payment amounts for Sales Invoice {doc.name}: {str(e)}")
        # Fallback to grand total
        doc.net_total_after_wht = flt(doc.grand_total)
        doc.custom_payment_amount = flt(doc.grand_total)
        doc.custom_net_total_after_wht_retention = 0


def convert_amounts_to_words_for_sales_invoice(doc):
    """
    Convert calculated amounts to words for display in Thai documents.
    Updates the 'in_words' fields for net_total_after_wht and custom_net_total_after_wht_and_retention.
    """
    try:
        from frappe.utils import money_in_words
        
        # Convert net_total_after_wht to words
        if doc.net_total_after_wht and hasattr(doc, 'net_total_after_wht_in_words'):
            try:
                doc.net_total_after_wht_in_words = money_in_words(doc.net_total_after_wht)
                print(f"🔍 Sales Invoice Calc: net_total_after_wht_in_words = {doc.net_total_after_wht_in_words}")
            except Exception as e:
                doc.net_total_after_wht_in_words = ""
                print(f"🔍 Sales Invoice Calc: Error converting net_total_after_wht to words: {str(e)}")
        
        # Convert custom_net_total_after_wht_retention to words (if retention applies)
        if (doc.get('custom_subject_to_retention') and 
            doc.get('custom_net_total_after_wht_retention') and 
            hasattr(doc, 'custom_net_total_after_wht_retention_in_words')):
            try:
                doc.custom_net_total_after_wht_retention_in_words = money_in_words(doc.custom_net_total_after_wht_retention)
                print(f"🔍 Sales Invoice Calc: custom_net_total_after_wht_retention_in_words = {doc.custom_net_total_after_wht_retention_in_words}")
            except Exception as e:
                doc.custom_net_total_after_wht_retention_in_words = ""
                print(f"🔍 Sales Invoice Calc: Error converting custom_net_total_after_wht_retention to words: {str(e)}")
        else:
            # Clear retention in_words field if not applicable
            if hasattr(doc, 'custom_net_total_after_wht_retention_in_words'):
                doc.custom_net_total_after_wht_retention_in_words = ""
                print(f"🔍 Sales Invoice Calc: Cleared custom_net_total_after_wht_retention_in_words (no retention)")
                
    except Exception as e:
        frappe.log_error(f"Error converting amounts to words for Sales Invoice {doc.name}: {str(e)}")
        # Clear the in_words fields on error
        if hasattr(doc, 'net_total_after_wht_in_words'):
            doc.net_total_after_wht_in_words = ""
        if hasattr(doc, 'custom_net_total_after_wht_retention_in_words'):
            doc.custom_net_total_after_wht_retention_in_words = ""
        print(f"🔍 Sales Invoice Calc: Error in convert_amounts_to_words_for_sales_invoice: {str(e)}")


def validate_thailand_calculations_for_sales_invoice(doc):
    """
    Validate Thailand-specific calculations and constraints for Sales Invoice.
    Called after calculations are complete.
    """
    # Validate retention constraints
    if doc.get('custom_retention_amount') and doc.custom_retention_amount > doc.net_total:
        frappe.throw(_("Retention amount cannot exceed net total"))
    
    # Validate withholding tax constraints  
    if doc.get('custom_withholding_tax_amount') and doc.custom_withholding_tax_amount > doc.net_total:
        frappe.throw(_("Withholding tax amount cannot exceed net total"))
    
    # Validate total deductions don't exceed sales invoice amount
    total_deductions = flt(doc.get('custom_retention_amount', 0)) + flt(doc.get('custom_withholding_tax_amount', 0))
    if total_deductions > doc.grand_total:
        frappe.throw(
            _("Total deductions ({0}) cannot exceed sales invoice grand total ({1})").format(
                total_deductions, doc.grand_total
            )
        )


# Note: This function is the main entry point called from hooks.py
# sales_invoice_calculate_thailand_amounts (defined at line 11) is the correct function


# ==================================================
# CONSOLIDATED WHT PREVIEW SYSTEM
# ==================================================
# Moved from thai_wht_events.py to consolidate calculation logic

def sales_invoice_comprehensive_wht_handler(doc, method=None):
    """
    Comprehensive WHT handler for Sales Invoice lifecycle events
    Consolidated from thai_wht_events.py
    """
    try:
        if method in ['validate', 'on_update', 'before_save']:
            # Calculate both custom and preview WHT on validation/update
            sales_invoice_calculate_thailand_amounts(doc, method)
            
        elif method == 'on_submit':
            # Add submission note about WHT
            if getattr(doc, 'subject_to_wht', False):
                wht_amount = getattr(doc, 'custom_withholding_tax_amount', 0)
                if wht_amount > 0:
                    frappe.msgprint(
                        _(f"Sales Invoice submitted with WHT amount: ฿{flt(wht_amount, 2):,.2f}. "
                          f"Actual WHT will be processed during payment."),
                        title=_("WHT Information"),
                        indicator="blue"
                    )
        
        elif method == 'on_cancel':
            # Clear WHT fields on cancellation
            if hasattr(doc, 'subject_to_wht'):
                doc.subject_to_wht = 0
                if hasattr(doc, 'custom_withholding_tax_amount'):
                    doc.custom_withholding_tax_amount = 0
                doc.net_total_after_wht = flt(doc.grand_total, 2)
        
    except Exception as e:
        frappe.log_error(
            f"Error in Sales Invoice comprehensive WHT handler for {doc.name}: {str(e)}",
            "Sales Invoice WHT Handler Error"
        )


# ==================================================
# CUSTOMER CONFIGURATION HANDLERS
# ==================================================

@frappe.whitelist()
def get_customer_wht_info_for_sales_invoice(customer):
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
        frappe.log_error(f"Error getting customer WHT info for Sales Invoice {customer}: {str(e)}")
        return {}


def handle_customer_wht_config_change_for_sales_invoice(customer_name):
    """
    Handle customer WHT configuration changes for draft sales invoices
    Consolidated from thai_wht_events.py
    """
    try:
        # Find draft sales invoices for this customer
        draft_invoices = frappe.get_all("Sales Invoice", 
            filters={"customer": customer_name, "docstatus": 0},
            fields=["name"]
        )
        
        if not draft_invoices:
            return 0
            
        updated_count = 0
        for invoice_info in draft_invoices:
            try:
                invoice_doc = frappe.get_doc("Sales Invoice", invoice_info['name'])
                
                # Recalculate WHT and amounts
                sales_invoice_calculate_thailand_amounts(invoice_doc)
                
                # Save without triggering validation loops
                invoice_doc.flags.ignore_validate = True
                invoice_doc.save()
                updated_count += 1
                
            except Exception as e:
                frappe.log_error(
                    f"Error updating WHT for Sales Invoice {invoice_info['name']}: {str(e)}",
                    "Customer WHT Config Update Error"
                )
        
        return updated_count
        
    except Exception as e:
        frappe.log_error(
            f"Error handling customer WHT config change for sales invoices: {str(e)}",
            "Customer WHT Config Error"
        )
        return 0


# ==================================================
# UTILITY FUNCTIONS FOR API INTEGRATION
# ==================================================

@frappe.whitelist()
def refresh_wht_preview_for_sales_invoice(docname):
    """
    Manually refresh WHT preview for a specific Sales Invoice
    Consolidated from thai_wht_events.py
    """
    try:
        doc = frappe.get_doc("Sales Invoice", docname)
        
        # Calculate fresh WHT preview and custom calculations
        sales_invoice_calculate_thailand_amounts(doc)
        
        # Save the document
        doc.save()
        
        frappe.msgprint(
            _(f"WHT preview refreshed for Sales Invoice {docname}"),
            title=_("WHT Preview Updated"),
            indicator="green"
        )
        
        return {
            "success": True,
            "net_total_after_wht": doc.net_total_after_wht,
            "custom_withholding_tax_amount": getattr(doc, 'custom_withholding_tax_amount', 0),
            "custom_payment_amount": getattr(doc, 'custom_payment_amount', 0)
        }
        
    except Exception as e:
        frappe.throw(_(f"Error refreshing WHT preview: {str(e)}"))


@frappe.whitelist()
def preview_wht_calculation_for_sales_invoice(customer, grand_total, net_total=None, income_type=None):
    """
    API endpoint for previewing WHT calculation for Sales Invoice
    Simplified version without thai_wht_preview module dependency
    """
    try:
        if not customer:
            return {"error": "Customer is required"}
            
        # Get customer WHT info
        customer_doc = frappe.get_cached_doc("Customer", customer)
        
        # Basic preview calculation
        preview_result = {
            'subject_to_wht': getattr(customer_doc, 'subject_to_wht', False),
            'custom_withholding_tax_amount': 0,
            'net_total_after_wht': flt(grand_total, 2)
        }
        
        # If customer is subject to WHT, calculate basic amount
        if preview_result['subject_to_wht']:
            wht_rate = getattr(customer_doc, 'custom_wht_rate', 0)
            if wht_rate > 0:
                base_amount = flt(net_total) if net_total else flt(grand_total)
                wht_amount = flt((base_amount * wht_rate) / 100, 2)
                
                preview_result.update({
                    'custom_withholding_tax_amount': wht_amount,
                    'net_total_after_wht': flt(grand_total - wht_amount, 2),
                    'wht_income_type': getattr(customer_doc, 'wht_income_type', 'service_fees')
                })
        
        return preview_result

    except Exception as e:
        frappe.log_error(f"Error in Sales Invoice WHT preview API: {str(e)}")
        return {"error": str(e)}


def before_validate_sales_invoice(doc, method=None):
    """
    Before validate hook for Sales Invoice.

    Sets the ignore_validate_update_after_submit flag to prevent
    UpdateAfterSubmitError when ERPNext's set_total_in_words() recalculates
    in_words/base_in_words fields during the submit validation cycle.

    The error occurs because:
    1. During submit, Frappe runs validate() again
    2. ERPNext's set_total_in_words() recalculates in_words
    3. If the recalculated value differs (e.g., currency format changes),
       Frappe throws UpdateAfterSubmitError

    This hook runs BEFORE validate(), so the flag is set before the
    recalculation happens.

    Only set the flag when document is being submitted (docstatus changing to 1).
    """
    # Only set flag when submitting (docstatus will be 1 during submit action)
    if doc.docstatus == 1:
        doc.flags.ignore_validate_update_after_submit = True
        print(f"🔍 Sales Invoice before_validate: Set ignore_validate_update_after_submit flag for {doc.name} (submitting)")