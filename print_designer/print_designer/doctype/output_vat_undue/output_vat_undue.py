# Copyright (c) 2026, Print Designer
# For license information, please see license.txt

"""
Output VAT Undue - tracks sales where tax invoice hasn't been issued yet.
When tax invoice is issued (from SI), status changes to "Converted to Output VAT".
"""

import frappe
from frappe.model.document import Document


class OutputVATUndue(Document):
    pass


def check_if_service_sale(doc):
    """Check if Sales Invoice contains service items"""
    if not doc.items:
        return False

    for item in doc.items:
        if hasattr(item, 'is_service_item') and item.is_service_item:
            return True

        if item.item_code:
            item_doc = frappe.get_cached_value("Item", item.item_code, ["is_stock_item", "item_group"], as_dict=True)
            if item_doc:
                if not item_doc.is_stock_item:
                    return True
                if item_doc.item_group and any(keyword in item_doc.item_group.lower() for keyword in ['service', 'consulting']):
                    return True

    return False


def create_output_vat_undue_record(doc, method=None):
    """
    Create Output VAT Undue record on Sales Invoice submission.
    For credit sales (not cash/single invoice), track the output VAT as undue
    until tax invoice is issued.
    """
    if doc.doctype != "Sales Invoice" or doc.docstatus != 1:
        return

    if doc.base_total_taxes_and_charges <= 0:
        return

    # Only create for credit sales (is_pos=0) or if configured to track all
    # For now: create for all sales with VAT, update status when tax invoice issued
    
    existing = frappe.db.exists("Output VAT Undue", {"sales_invoice": doc.name})
    if existing:
        return

    output_vat_undue_account = frappe.get_value("Company", doc.company, "default_output_vat_undue_account")
    if not output_vat_undue_account:
        # Don't block, just skip creation if account not configured
        return

    vat_record = frappe.new_doc("Output VAT Undue")
    vat_record.sales_invoice = doc.name
    vat_record.customer = doc.customer
    vat_record.customer_name = doc.customer_name
    vat_record.posting_date = doc.posting_date
    vat_record.invoice_number = doc.name
    
    # Tax invoice info
    if hasattr(doc, 'pd_custom_tax_invoice_number') and doc.pd_custom_tax_invoice_number:
        vat_record.tax_invoice_number = doc.pd_custom_tax_invoice_number
        vat_record.tax_invoice_date = getattr(doc, 'pd_custom_tax_invoice_date', None)
    
    # Amounts
    vat_record.base_amount = doc.base_net_total or doc.base_grand_total_export or 0
    vat_record.vat_amount = doc.base_total_taxes_and_charges or 0
    vat_record.total_amount = doc.base_grand_total or 0
    
    # Account and status
    vat_record.output_vat_account = output_vat_undue_account
    vat_record.status = "Pending"
    
    # Customer info
    if hasattr(doc, 'tax_id') and doc.tax_id:
        vat_record.customer_tax_id = doc.tax_id
    elif doc.customer:
        customer_doc = frappe.get_doc("Customer", doc.customer)
        vat_record.customer_tax_id = customer_doc.tax_id or ""
        
        if hasattr(customer_doc, 'pd_custom_branch_code'):
            vat_record.customer_branch = customer_doc.pd_custom_branch_code or "00000"
        else:
            vat_record.customer_branch = "00000"
    
    try:
        vat_record.save()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Error creating Output VAT Undue: {str(e)}")


def update_output_vat_on_tax_invoice(doc, method=None):
    """
    Update Output VAT Undue when Sales Invoice receives tax invoice number.
    Called on validate (save) of Sales Invoice.
    """
    if doc.doctype != "Sales Invoice":
        return

    # Check if tax invoice number entered
    has_tax_invoice = hasattr(doc, 'pd_custom_tax_invoice_number') and doc.pd_custom_tax_invoice_number
    if not has_tax_invoice:
        return

    output_vat_undue = frappe.db.get_value(
        "Output VAT Undue",
        {"sales_invoice": doc.name},
        "name"
    )
    
    if output_vat_undue:
        from frappe.utils import getdate
        output_vat = frappe.get_doc("Output VAT Undue", output_vat_undue)
        output_vat.tax_invoice_number = doc.pd_custom_tax_invoice_number
        if hasattr(doc, 'pd_custom_tax_invoice_date'):
            output_vat.tax_invoice_date = doc.pd_custom_tax_invoice_date
        output_vat.status = "Converted to Output VAT"
        output_vat.converted_date = getdate()
        output_vat.converted_by = frappe.session.user
        output_vat.flags.ignore_permissions = True
        output_vat.save()
        frappe.db.commit()