# Sales Invoice Server-Side Calculations for Thailand WHT and Retention
# Following ERPNext pattern like grand_total calculation
# Called during validate() method - NO client scripts needed
# Consolidated from thai_wht_events.py to remove redundancy

import frappe
from frappe import _
from frappe.utils import flt, cint


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


# ==================================================
# CONSOLIDATED WHT PREVIEW SYSTEM
# ==================================================
# Moved from thai_wht_events.py to consolidate calculation logic

def calculate_wht_preview_for_sales_invoice(doc, method=None):
    """
    Calculate WHT preview for Sales Invoice documents
    Consolidated from thai_wht_events.py system
    """
    try:
        if doc.doctype != "Sales Invoice":
            return
        
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


def sales_invoice_comprehensive_wht_handler(doc, method=None):
    """
    Comprehensive WHT handler for Sales Invoice lifecycle events
    Consolidated from thai_wht_events.py
    """
    try:
        if method in ['validate', 'on_update', 'before_save']:
            # Calculate both custom and preview WHT on validation/update
            sales_invoice_calculate_thailand_amounts(doc, method)
            calculate_wht_preview_for_sales_invoice(doc, method)
            
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
                
                # Recalculate both custom and preview WHT
                sales_invoice_calculate_thailand_amounts(invoice_doc)
                calculate_wht_preview_for_sales_invoice(invoice_doc)
                
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
        calculate_wht_preview_for_sales_invoice(doc)
        
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