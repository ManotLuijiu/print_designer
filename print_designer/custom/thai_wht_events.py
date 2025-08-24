"""
Thai WHT Preview Event Handlers
===============================

Document event handlers for calculating Thai Withholding Tax preview
on Quotation, Sales Order, and Sales Invoice documents.

These handlers integrate with the WHT preview calculation system
without affecting ERPNext's payment-time WHT functionality.
"""

import frappe
from frappe import _
from frappe.utils import flt
from .thai_wht_preview import (
    calculate_thai_wht_preview,
    should_calculate_wht_preview
)


# ==================================================
# DOCUMENT EVENT HANDLERS
# ==================================================

def calculate_wht_preview_on_validate(doc, method=None):
    """
    Calculate WHT preview when sales documents are validated
    
    Called for: Quotation, Sales Order, Sales Invoice
    Event: validate
    """
    try:
        # Only calculate for supported document types
        if doc.doctype not in ['Quotation', 'Sales Order', 'Sales Invoice']:
            return
        
        # DEBUG: Log validation entry
        frappe.logger().info(f"🔍 WHT Events: calculate_wht_preview_on_validate called for {doc.doctype} {getattr(doc, 'name', 'new')}")
        frappe.logger().info(f"🔍 WHT Events: BEFORE - subject_to_wht = {getattr(doc, 'subject_to_wht', 'NOT_SET')}")
        print(f"🔍 WHT Events: calculate_wht_preview_on_validate called for {doc.doctype} {getattr(doc, 'name', 'new')}")
        print(f"🔍 WHT Events: BEFORE - subject_to_wht = {getattr(doc, 'subject_to_wht', 'NOT_SET')}")
        
        # Calculate WHT preview
        wht_preview = calculate_thai_wht_preview(doc)
        
        # DEBUG: Log what preview system returned
        frappe.logger().info(f"🔍 WHT Events: Preview system returned: {wht_preview}")
        
        # Update document fields
        for field, value in wht_preview.items():
            if hasattr(doc, field):
                old_value = getattr(doc, field, 'NOT_SET')
                setattr(doc, field, value)
                if field == 'subject_to_wht' and old_value != value:
                    frappe.logger().info(f"🔍 WHT Events: CHANGED {field}: {old_value} → {value}")
        
        # DEBUG: Log final state
        frappe.logger().info(f"🔍 WHT Events: AFTER - subject_to_wht = {getattr(doc, 'subject_to_wht', 'NOT_SET')}")
        print(f"🔍 WHT Events: AFTER - subject_to_wht = {getattr(doc, 'subject_to_wht', 'NOT_SET')}")
        
        # Add informational message if WHT applies
        if wht_preview.get('subject_to_wht'):
            wht_amount = wht_preview.get('estimated_wht_amount', 0)
            net_amount = wht_preview.get('net_payment_amount', 0)
            
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
            f"Error calculating WHT preview for {doc.doctype} {doc.name}: {str(e)}",
            "Thai WHT Preview Error"
        )


def calculate_wht_preview_on_customer_change(doc, method=None):
    """
    Recalculate WHT preview when customer is changed
    
    Called for: Quotation, Sales Order, Sales Invoice
    Event: validate (when customer changes)
    """
    try:
        # Check if customer field changed
        if hasattr(doc, '_doc_before_save') and doc._doc_before_save:
            old_customer = doc._doc_before_save.get('customer')
            new_customer = doc.customer
            
            # If customer changed, recalculate WHT
            if old_customer != new_customer:
                calculate_wht_preview_on_validate(doc, method)
        
    except Exception as e:
        frappe.log_error(
            f"Error on customer change WHT preview for {doc.doctype} {doc.name}: {str(e)}",
            "Thai WHT Preview Error"
        )


def update_wht_preview_on_amount_change(doc, method=None):
    """
    Update WHT preview when document amounts change
    
    Called for: Quotation, Sales Order, Sales Invoice
    Event: validate (when amounts change)
    """
    try:
        # Check if amounts changed
        if hasattr(doc, '_doc_before_save') and doc._doc_before_save:
            old_grand_total = doc._doc_before_save.get('grand_total', 0)
            old_net_total = doc._doc_before_save.get('net_total', 0)
            
            new_grand_total = flt(doc.grand_total, 2)
            new_net_total = flt(doc.net_total, 2)
            
            # If amounts changed significantly, recalculate
            if (abs(old_grand_total - new_grand_total) > 0.01 or 
                abs(old_net_total - new_net_total) > 0.01):
                calculate_wht_preview_on_validate(doc, method)
        
    except Exception as e:
        frappe.log_error(
            f"Error on amount change WHT preview for {doc.doctype} {doc.name}: {str(e)}",
            "Thai WHT Preview Error"
        )


# ==================================================
# SALES INVOICE SPECIFIC HANDLERS
# ==================================================

def sales_invoice_wht_preview_handler(doc, method=None):
    """
    Comprehensive WHT preview handler for Sales Invoice
    Handles validation, submission, and cancellation
    """
    try:
        if method in ['validate', 'on_update', 'before_save']:
            # Calculate WHT preview on validation/update
            calculate_wht_preview_on_validate(doc, method)
            
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
                doc.net_payment_amount = flt(doc.grand_total, 2)
        
    except Exception as e:
        frappe.log_error(
            f"Error in Sales Invoice WHT preview handler for {doc.name}: {str(e)}",
            "Thai WHT Preview Error"
        )


# ==================================================
# CUSTOMER CONFIGURATION HANDLERS
# ==================================================

def customer_wht_config_changed(doc, method=None):
    """
    Handle changes to customer WHT configuration
    Update related open sales documents
    """
    try:
        if method not in ['on_update', 'validate']:
            return
        
        # Check if WHT-related fields changed
        wht_fields = [
            'subject_to_wht', 'wht_income_type', 'custom_wht_rate', 'is_juristic_person'
        ]
        
        field_changed = False
        if hasattr(doc, '_doc_before_save') and doc._doc_before_save:
            for field in wht_fields:
                old_value = doc._doc_before_save.get(field)
                new_value = getattr(doc, field, None)
                if old_value != new_value:
                    field_changed = True
                    break
        
        if not field_changed:
            return
        
        # Find open sales documents for this customer
        open_docs = []
        
        # Get open quotations
        quotations = frappe.get_all("Quotation", 
            filters={"customer": doc.name, "docstatus": 0},
            fields=["name", "doctype"]
        )
        open_docs.extend(quotations)
        
        # Get open sales orders
        sales_orders = frappe.get_all("Sales Order",
            filters={"customer": doc.name, "docstatus": 0},
            fields=["name", "doctype"]
        )
        open_docs.extend(sales_orders)
        
        # Get draft sales invoices
        sales_invoices = frappe.get_all("Sales Invoice",
            filters={"customer": doc.name, "docstatus": 0},
            fields=["name", "doctype"]
        )
        open_docs.extend(sales_invoices)
        
        if open_docs:
            # Update WHT preview for open documents
            updated_count = 0
            for doc_info in open_docs:
                try:
                    sales_doc = frappe.get_doc(doc_info['doctype'], doc_info['name'])
                    
                    # Recalculate WHT preview
                    wht_preview = calculate_thai_wht_preview(sales_doc)
                    
                    # Update fields
                    for field, value in wht_preview.items():
                        if hasattr(sales_doc, field):
                            setattr(sales_doc, field, value)
                    
                    # Save without triggering validation loops
                    sales_doc.flags.ignore_validate = True
                    sales_doc.save()
                    updated_count += 1
                    
                except Exception as e:
                    frappe.log_error(
                        f"Error updating WHT preview for {doc_info['doctype']} {doc_info['name']}: {str(e)}",
                        "Customer WHT Config Update Error"
                    )
            
            if updated_count > 0:
                frappe.msgprint(
                    _(f"Updated WHT preview for {updated_count} open sales documents"),
                    title=_("WHT Configuration Updated"),
                    indicator="green"
                )
        
    except Exception as e:
        frappe.log_error(
            f"Error handling customer WHT config change for {doc.name}: {str(e)}",
            "Customer WHT Config Error"
        )


# ==================================================
# UTILITY FUNCTIONS
# ==================================================

def refresh_wht_preview_for_document(doctype, docname):
    """
    Manually refresh WHT preview for a specific document
    Useful for testing and manual recalculation
    """
    try:
        doc = frappe.get_doc(doctype, docname)
        
        if doctype not in ['Quotation', 'Sales Order', 'Sales Invoice']:
            frappe.throw(_("WHT preview is only supported for Quotation, Sales Order, and Sales Invoice"))
        
        # Calculate fresh WHT preview
        wht_preview = calculate_thai_wht_preview(doc)
        
        # Update document fields
        for field, value in wht_preview.items():
            if hasattr(doc, field):
                setattr(doc, field, value)
        
        # Save the document
        doc.save()
        
        frappe.msgprint(
            _(f"WHT preview refreshed for {doctype} {docname}"),
            title=_("WHT Preview Updated"),
            indicator="green"
        )
        
        return wht_preview
        
    except Exception as e:
        frappe.throw(_(f"Error refreshing WHT preview: {str(e)}"))


def bulk_refresh_wht_preview(customer=None, company=None):
    """
    Bulk refresh WHT preview for multiple documents
    """
    try:
        filters = {"docstatus": 0}  # Only draft documents
        
        if customer:
            filters["customer"] = customer
        if company:
            filters["company"] = company
        
        updated_count = 0
        
        # Process each document type
        for doctype in ['Quotation', 'Sales Order', 'Sales Invoice']:
            docs = frappe.get_all(doctype, filters=filters, fields=["name"])
            
            for doc_info in docs:
                try:
                    doc = frappe.get_doc(doctype, doc_info['name'])
                    
                    # Skip if no customer
                    if not doc.customer:
                        continue
                    
                    # Calculate WHT preview
                    wht_preview = calculate_thai_wht_preview(doc)
                    
                    # Update fields
                    for field, value in wht_preview.items():
                        if hasattr(doc, field):
                            setattr(doc, field, value)
                    
                    # Save without validation loops
                    doc.flags.ignore_validate = True
                    doc.save()
                    updated_count += 1
                    
                except Exception as e:
                    frappe.log_error(
                        f"Error in bulk WHT refresh for {doctype} {doc_info['name']}: {str(e)}",
                        "Bulk WHT Refresh Error"
                    )
        
        frappe.msgprint(
            _(f"Bulk WHT preview refresh complete. Updated {updated_count} documents."),
            title=_("Bulk Update Complete"),
            indicator="green"
        )
        
        return updated_count
        
    except Exception as e:
        frappe.throw(_(f"Error in bulk WHT refresh: {str(e)}"))


# ==================================================
# CLIENT-SIDE HELPER FUNCTIONS
# ==================================================

@frappe.whitelist()
def get_customer_wht_info(customer):
    """
    Get WHT configuration for a customer (for client-side use)
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
        frappe.log_error(f"Error getting customer WHT info for {customer}: {str(e)}")
        return {}


@frappe.whitelist()
def preview_wht_calculation_api(customer, grand_total, net_total=None, income_type=None):
    """
    API endpoint for previewing WHT calculation
    Used by client-side scripts for real-time updates
    """
    try:
        # Create temporary document for calculation
        temp_doc = frappe._dict({
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
                'net_payment_amount': flt(grand_total - wht_amount, 2)
            })
        
        return wht_preview
        
    except Exception as e:
        frappe.log_error(f"Error in WHT preview API: {str(e)}")
        return {"error": str(e)}