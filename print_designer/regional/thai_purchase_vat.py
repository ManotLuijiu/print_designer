# Copyright (c) 2026, Digisoft ERP Co., Ltd. and contributors
# For license information, please see license.txt

"""
Thai Purchase VAT Management
Handles both:
- Thai Purchase VAT (all purchases except credit services)
- Input VAT Undue (credit service purchases only)
"""

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, cint, add_months, format_date
from datetime import datetime, date


def check_if_service_purchase(doc):
    """Check if Purchase Invoice contains service items based on item type or group"""
    if not doc.items:
        return False

    for item in doc.items:
        # Check if item has service flag
        if hasattr(item, 'is_service_item') and item.is_service_item:
            return True

        # Check item group for service indicator
        if item.item_code:
            item_doc = frappe.get_cached_value("Item", item.item_code, ["is_stock_item", "item_group"], as_dict=True)
            if item_doc:
                # Non-stock items are typically services
                if not item_doc.is_stock_item:
                    return True
                # Check if item group contains service keywords
                if item_doc.item_group and any(keyword in item_doc.item_group.lower() for keyword in ['service', 'consulting', 'maintenance']):
                    return True

    return False


class InputVATUndue(Document):
    """Input VAT Undue - for credit service purchases only"""
    pass


class DGSPurchaseVAT:
    """Helper class for Purchase VAT operations"""
    
    @staticmethod
    def is_credit_service_purchase(doc):
        """Check if this is a credit service purchase that needs Input VAT Undue"""
        return check_if_service_purchase(doc) and not doc.is_paid
    
    @staticmethod
    def get_input_vat_undue_account(company):
        """Get Input VAT Undue account from Company settings"""
        return frappe.get_value("Company", company, "default_input_vat_undue_account")
    
    @staticmethod
    def get_input_vat_account(company):
        """Get Input VAT account from Company settings"""
        return frappe.get_value("Company", company, "default_input_vat_account")


# =============================================================================
# CREATE VAT RECORDS
# =============================================================================

def create_purchase_vat_records(doc, method):
    """
    Create appropriate VAT record on Purchase Invoice submit.
    
    - Credit service purchases + Tax Invoice received → Input VAT Undue
    - Credit service purchases + NO Tax Invoice → Skip (create at Payment Entry)
    - All other purchases → Thai Purchase VAT
    """
    if doc.doctype != "Purchase Invoice" or doc.docstatus != 1:
        return

    # Only create for invoices with VAT
    if doc.base_total_taxes_and_charges <= 0:
        return

    # Check if credit service purchase
    is_credit_service = check_if_service_purchase(doc) and not doc.is_paid
    has_tax_invoice = getattr(doc, 'pd_custom_tax_invoice_received', 0)
    
    if is_credit_service:
        if has_tax_invoice:
            # Tax Invoice received - create Input VAT Undue now
            _create_input_vat_undue(doc)
        else:
            # No Tax Invoice yet - skip for now, will create at Payment Entry
            return
    else:
        # Non-service purchase - create Thai Purchase VAT
        _create_thai_purchase_vat(doc)


def _create_input_vat_undue(doc):
    """Create Input VAT Undue record for credit service purchases"""
    # Check if already exists
    existing = frappe.db.exists("Input VAT Undue", {"purchase_invoice": doc.name})
    if existing:
        return

    # Get Input VAT Undue account from Company
    input_vat_undue_account = frappe.get_value("Company", doc.company, "default_input_vat_undue_account")
    if not input_vat_undue_account:
        frappe.msgprint(
            msg="Input VAT Undue account not set in Company settings. Please configure it.",
            title="Missing Account",
            indicator="orange"
        )
        return

    vat_record = frappe.new_doc("Input VAT Undue")
    vat_record.purchase_invoice = doc.name
    vat_record.supplier = doc.supplier
    vat_record.supplier_name = doc.supplier_name
    vat_record.posting_date = doc.posting_date
    
    # Tax invoice info (empty for credit - will be filled at Payment Entry)
    vat_record.bill_no = doc.bill_no
    if hasattr(doc, 'dgs_custom_bill_series'):
        vat_record.bill_series = doc.dgs_custom_bill_series
    
    # Amounts
    vat_record.base_amount = doc.base_net_total or doc.base_grand_total_export or 0
    vat_record.vat_amount = doc.base_total_taxes_and_charges or 0
    vat_record.total_amount = doc.base_grand_total or 0
    
    # Supplier info
    if hasattr(doc, 'tax_id') and doc.tax_id:
        vat_record.supplier_tax_id = doc.tax_id
    elif doc.supplier:
        supplier_doc = frappe.get_doc("Supplier", doc.supplier)
        vat_record.supplier_tax_id = supplier_doc.tax_id or ""
        vat_record.supplier_branch = getattr(supplier_doc, 'pd_custom_branch_code', '00000') or '00000'
    
    # Company info
    vat_record.company = doc.company
    
    # VAT period
    if doc.posting_date:
        posting_date = getdate(doc.posting_date)
        vat_record.vat_month = str(posting_date.month)
        vat_record.vat_year = str(posting_date.year)
    
    vat_record.status = "Undue"
    vat_record.flags.ignore_permissions = True
    
    try:
        vat_record.insert()
        frappe.db.commit()
        
        frappe.msgprint(
            f"Input VAT Undue record created: {vat_record.name}",
            title="Input VAT Undue Created",
            indicator="green"
        )
    except Exception as e:
        frappe.log_error(f"Error creating Input VAT Undue: {str(e)}", "VAT Creation Error")


def _create_thai_purchase_vat(doc):
    """Create Thai Purchase VAT record for non-credit-service purchases"""
    # Check if already exists
    existing = frappe.db.exists("Thai Purchase VAT", {"purchase_invoice": doc.name})
    if existing:
        return
    thai_purchase_vat = frappe.new_doc("Thai Purchase VAT")
    thai_purchase_vat.purchase_invoice = doc.name
    thai_purchase_vat.purchase_for_company = doc.company or frappe.defaults.get_user_default("Company")
    thai_purchase_vat.purchase_for_branch = "00000"
    # Core invoice info
    thai_purchase_vat.supplier = doc.supplier
    thai_purchase_vat.supplier_name = doc.supplier_name
    thai_purchase_vat.bill_date = doc.bill_date or doc.posting_date
    thai_purchase_vat.bill_no = doc.bill_no
    thai_purchase_vat.posting_date = doc.posting_date
    # Tax invoice details (from PE or PI) - check both custom fields and new doctype fields
    tax_invoice_no = (getattr(doc, 'pd_custom_tax_invoice_number', None) or 
                      getattr(doc, 'tax_invoice_number', None) or 
                      doc.bill_no)
    thai_purchase_vat.tax_invoice_number = tax_invoice_no
    tax_invoice_dt = (getattr(doc, 'pd_custom_tax_invoice_date', None) or 
                      getattr(doc, 'tax_invoice_date', None) or 
                      doc.bill_date)
    thai_purchase_vat.tax_invoice_date = tax_invoice_dt
    # Tax base amount
    tax_base = (getattr(doc, 'pd_custom_tax_base_amount', None) or 
                getattr(doc, 'tax_base_amount', None) or 
                doc.base_net_total or 0)
    thai_purchase_vat.tax_base_amount = tax_base
    # Amounts
    thai_purchase_vat.base_amount = doc.base_net_total or doc.base_grand_total_export or 0
    thai_purchase_vat.vat_amount = doc.base_total_taxes_and_charges or 0
    thai_purchase_vat.total_amount = doc.base_grand_total or 0
    # Supplier info
    if doc.supplier:
        try:
            supplier_doc = frappe.get_doc("Supplier", doc.supplier)
            thai_purchase_vat.supplier_name = supplier_doc.supplier_name or doc.supplier_name
            thai_purchase_vat.supplier_tax_id = getattr(supplier_doc, 'tax_id', None) or ""
            thai_purchase_vat.supplier_branch = getattr(supplier_doc, 'pd_custom_branch_code', None) or "00000"
        except:
            thai_purchase_vat.supplier_name = doc.supplier_name
            thai_purchase_vat.supplier_tax_id = getattr(doc, 'tax_id', None) or ""
            thai_purchase_vat.supplier_branch = "00000"
    # Bill series
    if hasattr(doc, 'dgs_custom_bill_series'):
        thai_purchase_vat.bill_series = doc.dgs_custom_bill_series
    # VAT period
    if doc.bill_date:
        bill_date = getdate(doc.bill_date)
        thai_purchase_vat.vat_month = str(bill_date.month)
        thai_purchase_vat.vat_year = str(bill_date.year)
    elif doc.posting_date:
        posting_date = getdate(doc.posting_date)
        thai_purchase_vat.vat_month = str(posting_date.month)
        thai_purchase_vat.vat_year = str(posting_date.year)
    thai_purchase_vat.workflow_state = "Draft"
    thai_purchase_vat.flags.ignore_permissions = True
    try:
        thai_purchase_vat.insert()
        frappe.db.commit()
        frappe.msgprint(
            f"Thai Purchase VAT record created: {thai_purchase_vat.name}",
            title="VAT Record Created",
            indicator="green"
        )
    except Exception as e:
        frappe.log_error(f"Error creating Thai Purchase VAT: {str(e)}", "VAT Creation Error")


def handle_purchase_invoice_cancellation(doc, method):
    """Handle Purchase Invoice cancellation - update related VAT records"""
    if doc.doctype != "Purchase Invoice" or doc.docstatus != 2:
        return

    # Update Input VAT Undue if exists
    input_vat_undue = frappe.db.get_value(
        "Input VAT Undue",
        {"purchase_invoice": doc.name},
        "name"
    )
    if input_vat_undue:
        frappe.db.set_value("Input VAT Undue", input_vat_undue, "status", "Cancelled")
        frappe.db.commit()

    # Update Thai Purchase VAT if exists
    dgs_vat = frappe.db.get_value(
        "Thai Purchase VAT",
        {"purchase_invoice": doc.name},
        "name"
    )
    if dgs_vat:
        frappe.db.set_value("Thai Purchase VAT", dgs_vat, "workflow_state", "Cancelled")
        frappe.db.commit()


# =============================================================================
# UPDATE VAT FROM PAYMENT ENTRY
# =============================================================================

def update_vat_from_payment_entry(doc, method):
    """
    Update VAT records when Payment Entry is submitted with Tax Invoice.
    Called on Payment Entry SAVE (validate) to update records.
    """
    if doc.doctype != "Payment Entry":
        return

    # Only process if payment has tax invoice details
    has_tax_invoice = hasattr(doc, 'pd_custom_tax_invoice_number') and doc.pd_custom_tax_invoice_number
    if not has_tax_invoice:
        return

    for ref in doc.references:
        if ref.reference_doctype == "Purchase Invoice":
            # Update Input VAT Undue record if exists
            input_vat_undue_name = frappe.db.get_value(
                "Input VAT Undue",
                {"purchase_invoice": ref.reference_name},
                "name"
            )
            
            if input_vat_undue_name:
                try:
                    input_vat_undue = frappe.get_doc("Input VAT Undue", input_vat_undue_name)
                    
                    # Update with tax invoice details from Payment Entry
                    if hasattr(doc, 'pd_custom_tax_invoice_number'):
                        input_vat_undue.tax_invoice_number = doc.pd_custom_tax_invoice_number
                    if hasattr(doc, 'pd_custom_tax_invoice_date'):
                        input_vat_undue.tax_invoice_date = doc.pd_custom_tax_invoice_date
                    if hasattr(doc, 'pd_custom_tax_base_amount'):
                        input_vat_undue.base_amount = doc.pd_custom_tax_base_amount
                    
                    # Calculate VAT amount based on base amount
                    if input_vat_undue.base_amount and input_vat_undue.base_amount > 0:
                        input_vat_undue.vat_amount = input_vat_undue.base_amount * 0.07
                        input_vat_undue.total_amount = input_vat_undue.base_amount + input_vat_undue.vat_amount
                    
                    input_vat_undue.status = "Converted to Input VAT"
                    input_vat_undue.flags.ignore_permissions = True
                    input_vat_undue.save()
                    frappe.db.commit()
                    
                    frappe.msgprint(
                        f"Input VAT Undue {input_vat_undue.name} updated with Tax Invoice details",
                        title="VAT Updated",
                        indicator="green"
                    )
                    
                    # Also create Thai Purchase VAT record
                    _create_thai_purchase_vat_from_pe(doc, input_vat_undue)
                except Exception as e:
                    frappe.log_error(f"Error updating Input VAT Undue: {str(e)}", "VAT Update Error")


def _create_thai_purchase_vat_from_pe(doc, input_vat_undue):
    """
    Create Thai Purchase VAT record from Payment Entry after Input VAT Undue conversion.
    Called when PE is saved with tax invoice details for credit service purchases.
    """
    # Check if Thai Purchase VAT already exists for this PE
    existing = frappe.db.exists("Thai Purchase VAT", {"payment_entry": doc.name})
    if existing:
        return

    try:
        thai_vat = frappe.new_doc("Thai Purchase VAT")
        
        # Company details
        thai_vat.purchase_for_company = doc.company
        company_doc = frappe.get_doc("Company", doc.company)
        thai_vat.purchase_for_branch = getattr(company_doc, 'branch', '') or '00000'
        
        # Purchase Invoice details
        thai_vat.purchase_invoice = getattr(input_vat_undue, 'purchase_invoice', '')
        thai_vat.supplier = getattr(input_vat_undue, 'supplier', '')
        thai_vat.supplier_name = getattr(input_vat_undue, 'supplier_name', '')
        thai_vat.posting_date = getattr(input_vat_undue, 'posting_date', doc.posting_date)
        thai_vat.bill_date = doc.posting_date
        
        # Tax Invoice details
        thai_vat.bill_no = getattr(input_vat_undue, 'bill_no', '')
        thai_vat.tax_invoice_number = getattr(doc, 'pd_custom_tax_invoice_number', '')
        thai_vat.tax_invoice_date = getattr(doc, 'pd_custom_tax_invoice_date', '')
        thai_vat.tax_base_amount = getattr(doc, 'pd_custom_tax_base_amount', 0)
        thai_vat.bill_series = getattr(input_vat_undue, 'bill_series', '')
        
        # Supplier info
        thai_vat.supplier_tax_id = getattr(input_vat_undue, 'supplier_tax_id', '')
        thai_vat.supplier_branch = getattr(input_vat_undue, 'supplier_branch', '')
        
        # Payment Entry link
        thai_vat.payment_entry = doc.name
        
        # VAT period
        posting_date = getdate(doc.posting_date)
        thai_vat.vat_month = str(posting_date.month)
        thai_vat.vat_year = str(posting_date.year)
        
        # Amounts
        thai_vat.base_amount = getattr(input_vat_undue, 'base_amount', 0)
        thai_vat.vat_amount = getattr(input_vat_undue, 'vat_amount', 0)
        thai_vat.total_amount = getattr(input_vat_undue, 'total_amount', 0)
        
        thai_vat.flags.ignore_permissions = True
        thai_vat.insert()
        frappe.db.commit()
        
        frappe.msgprint(
            f"Thai Purchase VAT record created: {thai_vat.name}",
            title="Thai Purchase VAT Created",
            indicator="green"
        )
    except Exception as e:
        frappe.log_error(f"Error creating Thai Purchase VAT: {str(e)}", "Thai Purchase VAT Creation Error")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

@frappe.whitelist()
def get_thai_vat_summary(vat_month=None, vat_year=None):
    """Get summary of all Thai Purchase VAT records with optional filtering"""
    filters = {}
    
    if vat_month:
        filters["vat_month"] = vat_month
    if vat_year:
        filters["vat_year"] = vat_year
    
    dgs_vat_records = frappe.get_all(
        "Thai Purchase VAT",
        filters=filters,
        fields=["name", "purchase_invoice", "supplier", "base_amount", "vat_amount", "total_amount", "vat_month", "vat_year", "workflow_state"]
    )
    
    input_vat_records = frappe.get_all(
        "Input VAT Undue",
        filters=filters,
        fields=["name", "purchase_invoice", "supplier", "base_amount", "vat_amount", "total_amount", "vat_month", "vat_year", "status"]
    )
    
    total_base = sum([r.base_amount or 0 for r in dgs_vat_records]) + sum([r.base_amount or 0 for r in input_vat_records])
    total_vat = sum([r.vat_amount or 0 for r in dgs_vat_records]) + sum([r.vat_amount or 0 for r in input_vat_records])
    
    return {
        "dgs_vat_records": dgs_vat_records,
        "input_vat_records": input_vat_records,
        "total_base_amount": total_base,
        "total_vat_amount": total_vat,
        "total_records": len(dgs_vat_records) + len(input_vat_records)
    }


@frappe.whitelist()
def get_vat_months_years():
    """Get available VAT months and years for filtering"""
    dgs_months = frappe.get_all(
        "Thai Purchase VAT",
        fields=["vat_month", "vat_year"]
    )
    
    input_months = frappe.get_all(
        "Input VAT Undue",
        fields=["vat_month", "vat_year"]
    )
    
    all_months = dgs_months + input_months
    
    # Get unique month/year combinations
    unique = {}
    for m in all_months:
        if m.vat_month and m.vat_year:
            key = f"{m.vat_year}-{m.vat_month.zfill(2)}"
            unique[key] = {"vat_month": m.vat_month, "vat_year": m.vat_year}
    
    sorted_keys = sorted(unique.keys(), reverse=True)
    return [unique[k] for k in sorted_keys]
