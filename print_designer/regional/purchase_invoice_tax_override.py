# Copyright (c) 2026, Print Designer
# For license information, please see license.txt

"""
Override tax account for credit service purchases.
Credit service purchases should use Input VAT Undue instead of Input VAT.
"""

import frappe


def check_if_service_purchase(doc):
    """Check if Purchase Invoice contains service items"""
    if not doc.items:
        return False

    for item in doc.items:
        # Get item properties from Item doctype (not from the child table)
        item_doc = frappe.get_cached_value(
            "Item", 
            item.item_code, 
            ["is_stock_item", "item_group", "pd_custom_is_service_item"], 
            as_dict=True
        )
        
        if item_doc:
            # Check explicit service flag first
            if item_doc.get('pd_custom_is_service_item'):
                return True
            
            # Non-stock items are typically services
            if not item_doc.get('is_stock_item'):
                return True
            
            # Check if item group contains service keywords
            item_group = item_doc.get('item_group', '')
            if item_group and any(keyword in item_group.lower() for keyword in ['service', 'consulting', 'maintenance']):
                return True

    return False


def override_service_credit_tax_account(doc, method=None):
    """
    Override tax account for credit service purchases.
    
    Triggered on: Purchase Invoice validate (on Save)
    
    Logic:
    - If credit service purchase (is_paid=0 AND service items):
      - Replace Input VAT account with Input VAT Undue from Company settings
      - Create Input VAT Undue tracking record
    - Otherwise: No change (keep template account)
    """
    if doc.doctype != "Purchase Invoice":
        return
    
    # Check if credit service purchase
    is_service = check_if_service_purchase(doc)
    is_credit = not doc.is_paid
    
    if not (is_service and is_credit):
        return  # Not credit service, no override needed
    
    # Get Input VAT Undue account from Company
    input_vat_undue_account = frappe.get_value("Company", doc.company, "default_input_vat_undue_account")
    if not input_vat_undue_account:
        frappe.msgprint(
            msg="⚠️ Input VAT Undue account not set in Company settings. Please configure it in Company → Thai Tax Settings.",
            title="Missing Account",
            indicator="orange"
        )
        return
    
    # Find and replace Input VAT accounts in taxes table
    accounts_replaced = []
    for tax in doc.taxes:
        # Check if this is a VAT account (Input VAT but not already Undue)
        if tax.account_head and "Input VAT" in tax.account_head and "Undue" not in tax.account_head:
            old_account = tax.account_head
            tax.account_head = input_vat_undue_account
            accounts_replaced.append(old_account)
    
    if accounts_replaced:
        frappe.msgprint(
            msg=f"✓ Tax account overridden to Input VAT Undue: {', '.join(accounts_replaced)}",
            title="Input VAT Undue Override",
            indicator="green"
        )
        
        # Create or update Input VAT Undue tracking record
        _create_input_vat_undue_record(doc, input_vat_undue_account)


def _create_input_vat_undue_record(doc, input_vat_undue_account):
    """Create Input VAT Undue record for tracking"""
    # Check if already exists
    existing = frappe.db.exists("Input VAT Undue", {"purchase_invoice": doc.name})
    if existing:
        return  # Already exists
    
    try:
        vat_record = frappe.new_doc("Input VAT Undue")
        vat_record.purchase_invoice = doc.name
        vat_record.supplier = doc.supplier
        vat_record.supplier_name = doc.supplier_name
        vat_record.posting_date = doc.posting_date
        vat_record.bill_no = doc.bill_no
        
        if hasattr(doc, 'dgs_custom_bill_series'):
            vat_record.bill_series = doc.dgs_custom_bill_series
        
        # Amounts
        vat_record.base_amount = doc.base_net_total or doc.base_grand_total_export or 0
        vat_record.vat_amount = doc.base_total_taxes_and_charges or 0
        vat_record.total_amount = doc.base_grand_total or 0
        
        # Account and status
        vat_record.input_vat_account = input_vat_undue_account
        vat_record.status = "Pending"
        
        # Supplier info
        if hasattr(doc, 'tax_id') and doc.tax_id:
            vat_record.supplier_tax_id = doc.tax_id
        elif doc.supplier:
            supplier_doc = frappe.get_doc("Supplier", doc.supplier)
            vat_record.supplier_tax_id = supplier_doc.tax_id or ""
            
            if hasattr(supplier_doc, 'pd_custom_branch_code'):
                vat_record.supplier_branch = supplier_doc.pd_custom_branch_code or "00000"
            else:
                vat_record.supplier_branch = "00000"
        
        vat_record.save()
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Error creating Input VAT Undue record: {str(e)}")


@frappe.whitelist()
def get_input_vat_undue_status(purchase_invoice):
    """Get Input VAT Undue status for a Purchase Invoice"""
    record = frappe.db.get_value(
        "Input VAT Undue",
        {"purchase_invoice": purchase_invoice},
        ["name", "status", "tax_invoice_number", "tax_invoice_date", "vat_amount"],
        as_dict=True
    )
    
    if record:
        return {
            "found": True,
            "name": record.name,
            "status": record.status,
            "tax_invoice_number": record.tax_invoice_number,
            "tax_invoice_date": record.tax_invoice_date,
            "vat_amount": record.vat_amount
        }
    
    return {"found": False}