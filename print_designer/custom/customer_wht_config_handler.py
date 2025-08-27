# Customer WHT Configuration Handler
# Consolidated from thai_wht_events.py to remove redundancy
# Handles Customer WHT configuration changes and updates related documents

import frappe
from frappe import _
from frappe.utils import flt


def handle_customer_wht_config_changes(doc, method=None):
    """
    Handle changes to customer WHT configuration
    Update related open sales documents
    Consolidated from thai_wht_events.py
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
        
        # Update related documents
        total_updated = 0
        
        # Update Quotations
        from .quotation_calculations import handle_customer_wht_config_change_for_quotation
        quotation_count = handle_customer_wht_config_change_for_quotation(doc.name)
        total_updated += quotation_count
        
        # Update Sales Orders
        from .sales_order_calculations import handle_customer_wht_config_change_for_sales_order
        sales_order_count = handle_customer_wht_config_change_for_sales_order(doc.name)
        total_updated += sales_order_count
        
        # Update Sales Invoices
        from .sales_invoice_calculations import handle_customer_wht_config_change_for_sales_invoice
        sales_invoice_count = handle_customer_wht_config_change_for_sales_invoice(doc.name)
        total_updated += sales_invoice_count
        
        if total_updated > 0:
            frappe.msgprint(
                _(f"Updated WHT configuration for {total_updated} open sales documents "
                  f"(Quotations: {quotation_count}, Sales Orders: {sales_order_count}, Sales Invoices: {sales_invoice_count})"),
                title=_("WHT Configuration Updated"),
                indicator="green"
            )
        
    except Exception as e:
        frappe.log_error(
            f"Error handling customer WHT config change for {doc.name}: {str(e)}",
            "Customer WHT Config Handler Error"
        )


@frappe.whitelist()
def bulk_refresh_customer_wht_config(customer=None, company=None):
    """
    Bulk refresh WHT configuration for multiple customers
    """
    try:
        filters = {}
        
        if customer:
            filters["name"] = customer
        if company:
            # This would need a custom field to filter by company
            # For now, we'll update all customers
            pass
        
        customers = frappe.get_all("Customer", filters=filters, fields=["name"])
        
        total_updated = 0
        
        for customer_info in customers:
            try:
                customer_doc = frappe.get_doc("Customer", customer_info['name'])
                
                # Trigger the update manually
                handle_customer_wht_config_changes(customer_doc, method='validate')
                
            except Exception as e:
                frappe.log_error(
                    f"Error in bulk refresh for Customer {customer_info['name']}: {str(e)}",
                    "Bulk Customer WHT Config Error"
                )
        
        frappe.msgprint(
            _(f"Bulk customer WHT configuration refresh complete. Updated {total_updated} documents."),
            title=_("Bulk Update Complete"),
            indicator="green"
        )
        
        return total_updated
        
    except Exception as e:
        frappe.throw(_(f"Error in bulk customer WHT refresh: {str(e)}"))


@frappe.whitelist()
def get_customer_wht_summary(customer):
    """
    Get summary of customer WHT configuration and related documents
    """
    try:
        customer_doc = frappe.get_cached_doc("Customer", customer)
        
        # Get customer WHT config
        wht_config = {
            'subject_to_wht': getattr(customer_doc, 'subject_to_wht', False),
            'wht_income_type': getattr(customer_doc, 'wht_income_type', 'service_fees'),
            'custom_wht_rate': getattr(customer_doc, 'custom_wht_rate', 0),
            'is_juristic_person': getattr(customer_doc, 'is_juristic_person', True),
            'tax_id': getattr(customer_doc, 'tax_id', '')
        }
        
        # Get count of open documents
        open_quotations = frappe.db.count("Quotation", {
            "customer": customer, 
            "docstatus": 0
        })
        
        open_sales_orders = frappe.db.count("Sales Order", {
            "customer": customer, 
            "docstatus": 0
        })
        
        draft_invoices = frappe.db.count("Sales Invoice", {
            "customer": customer, 
            "docstatus": 0
        })
        
        return {
            "wht_config": wht_config,
            "open_documents": {
                "quotations": open_quotations,
                "sales_orders": open_sales_orders,
                "sales_invoices": draft_invoices,
                "total": open_quotations + open_sales_orders + draft_invoices
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting customer WHT summary for {customer}: {str(e)}")
        return {"error": str(e)}