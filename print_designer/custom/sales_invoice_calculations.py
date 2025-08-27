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
        
        # Apply default retention rate if custom_retention is not specified  
        if not doc.get('custom_retention') and company_doc.get('default_retention_rate'):
            doc.custom_retention = flt(company_doc.default_retention_rate)
            
        # Enable custom_subject_to_retention based on Company settings
        if (company_doc.get('construction_service') or company_doc.get('default_retention_rate')) and not doc.get('custom_subject_to_retention'):
            if doc.get('custom_retention') or company_doc.get('default_retention_rate'):
                doc.custom_subject_to_retention = 1
                
    except Exception as e:
        frappe.log_error(f"Error applying Company defaults to Sales Invoice {doc.name}: {str(e)}")


def calculate_wht_preview_for_sales_invoice(doc):
    """
    Calculate WHT preview for Sales Invoice documents
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
                    frappe.logger().info(f"Sales Invoice WHT Preview: {field} changed from {old_value} to {value}")
        
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
            f"Error calculating WHT preview for Sales Invoice {doc.name}: {str(e)}",
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
            hasattr(doc, 'custom_net_total_after_wht_and_retention_in_words')):
            try:
                doc.custom_net_total_after_wht_and_retention_in_words = money_in_words(doc.custom_net_total_after_wht_retention)
                print(f"🔍 Sales Invoice Calc: custom_net_total_after_wht_and_retention_in_words = {doc.custom_net_total_after_wht_and_retention_in_words}")
            except Exception as e:
                doc.custom_net_total_after_wht_and_retention_in_words = ""
                print(f"🔍 Sales Invoice Calc: Error converting custom_net_total_after_wht_retention to words: {str(e)}")
        else:
            # Clear retention in_words field if not applicable
            if hasattr(doc, 'custom_net_total_after_wht_and_retention_in_words'):
                doc.custom_net_total_after_wht_and_retention_in_words = ""
                print(f"🔍 Sales Invoice Calc: Cleared custom_net_total_after_wht_and_retention_in_words (no retention)")
                
    except Exception as e:
        frappe.log_error(f"Error converting amounts to words for Sales Invoice {doc.name}: {str(e)}")
        # Clear the in_words fields on error
        if hasattr(doc, 'net_total_after_wht_in_words'):
            doc.net_total_after_wht_in_words = ""
        if hasattr(doc, 'custom_net_total_after_wht_and_retention_in_words'):
            doc.custom_net_total_after_wht_and_retention_in_words = ""
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
    if doc.get('estimated_wht_amount') and doc.estimated_wht_amount > doc.net_total:
        frappe.throw(_("Withholding tax amount cannot exceed net total"))
    
    # Validate total deductions don't exceed sales invoice amount
    total_deductions = flt(doc.get('custom_retention_amount', 0)) + flt(doc.get('estimated_wht_amount', 0))
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
                wht_amount = getattr(doc, 'estimated_wht_amount', 0)
                if wht_amount > 0:
                    frappe.msgprint(
                        _(f"Sales Invoice submitted with WHT preview: ฿{flt(wht_amount, 2):,.2f}. "
                          f"Actual WHT will be calculated during payment processing."),
                        title=_("WHT Preview Information"),
                        indicator="blue"
                    )
        
        elif method == 'on_cancel':
            # Clear WHT preview fields on cancellation
            if hasattr(doc, 'subject_to_wht'):
                doc.subject_to_wht = 0
                doc.estimated_wht_rate = 0
                doc.estimated_wht_amount = 0
                doc.wht_base_amount = 0
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
            "estimated_wht_amount": getattr(doc, 'estimated_wht_amount', 0),
            "custom_payment_amount": getattr(doc, 'custom_payment_amount', 0)
        }
        
    except Exception as e:
        frappe.throw(_(f"Error refreshing WHT preview: {str(e)}"))


@frappe.whitelist()
def preview_wht_calculation_for_sales_invoice(customer, grand_total, net_total=None, income_type=None):
    """
    API endpoint for previewing WHT calculation for Sales Invoice
    Consolidated from thai_wht_events.py
    """
    try:
        # Create temporary document for calculation
        temp_doc = frappe._dict({
            'doctype': 'Sales Invoice',
            'customer': customer,
            'grand_total': flt(grand_total),
            'net_total': flt(net_total) if net_total else flt(grand_total),
            'company': frappe.defaults.get_user_default('Company') or frappe.get_all("Company", limit=1)[0].name
        })
        
        # Calculate WHT preview
        from .thai_wht_preview import calculate_thai_wht_preview
        wht_preview = calculate_thai_wht_preview(temp_doc)
        
        # Override income type if provided
        if income_type and wht_preview.get('subject_to_wht'):
            from .thai_wht_preview import get_applicable_wht_rate, get_customer_wht_config, get_wht_description
            
            customer_config = get_customer_wht_config(customer)
            customer_config['income_type'] = income_type
            
            wht_rate = get_applicable_wht_rate(temp_doc, customer_config)
            base_amount = wht_preview.get('wht_base_amount', 0)
            wht_amount = (base_amount * wht_rate) / 100
            
            wht_preview.update({
                'wht_income_type': income_type,
                'wht_description': get_wht_description(income_type),
                'estimated_wht_rate': wht_rate,
                'estimated_wht_amount': flt(wht_amount, 2),
                'net_total_after_wht': flt(grand_total - wht_amount, 2)
            })
        
        return wht_preview
        
    except Exception as e:
        frappe.log_error(f"Error in Sales Invoice WHT preview API: {str(e)}")
        return {"error": str(e)}