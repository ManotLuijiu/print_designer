# Copyright (c) 2026, AWS Solution Ltd. and contributors
# For license information, please see license.txt

"""
Thai Purchase VAT Management

Two-doctype architecture for Input VAT:
  - Thai Purchase VAT  = Source of Truth (original tax invoice received)
  - Input VAT Undue   = Pending (copy tax invoice — waiting for original)

Flow:
  PI submitted
    ├── Import Clearance PI  → Input VAT Undue (copy, source_doctype=Import Clearance)
    ├── Service purchase     → Input VAT Undue (copy, source_doctype=Service)
    └── Regular purchase    → Thai Purchase VAT (original, vat_type=General)
                                (only if tax invoice received immediately)

  Input VAT Undue "Got Original" ticked
    └── Creates Thai Purchase VAT (vat_type=Undue)
"""

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, cint, add_months, format_date
from datetime import datetime, date


def check_if_service_purchase(doc):
    """Check if Purchase Invoice contains service items based on item type or group."""
    if not doc.items:
        return False

    for item in doc.items:
        if hasattr(item, "is_service_item") and item.is_service_item:
            return True
        if item.item_code:
            item_doc = frappe.get_cached_value(
                "Item", item.item_code, ["is_stock_item", "item_group"], as_dict=True
            )
            if item_doc:
                if not item_doc.is_stock_item:
                    return True
                if item_doc.item_group and any(
                    keyword in item_doc.item_group.lower()
                    for keyword in ["service", "consulting", "maintenance"]
                ):
                    return True
    return False


def check_if_import_clearance_pi(doc):
    """Check if this PI is from Import Clearance (tbs_custom_po_type == 'Import')."""
    return getattr(doc, "tbs_custom_po_type", None) == "Import"


def check_has_tax_invoice(doc):
    """Check if PI has tax invoice received (immediate or via pd_custom fields)."""
    return bool(getattr(doc, "pd_custom_tax_invoice_received", 0))


# =============================================================================
# CREATE VAT RECORDS — on PI submit
# =============================================================================

def create_purchase_vat_records(doc, method):
    """
    Create Input VAT record on Purchase Invoice submit.

    Routing logic:
      - Import Clearance PI  → Input VAT Undue (copy, source_doctype=Import Clearance)
      - Service purchase     → Input VAT Undue (copy, source_doctype=Service)
      - Regular purchase     → Thai Purchase VAT (original, vat_type=General)
                                (only when tax invoice received immediately)

    All Import Clearance PIs land in Input VAT Undue first (copy invoice).
    User marks "Got Original" later → Thai Purchase VAT created then.
    """
    if doc.doctype != "Purchase Invoice" or doc.docstatus != 1:
        return

    if doc.base_total_taxes_and_charges <= 0:
        return

    # Route: Import Clearance PI → Input VAT Undue
    if check_if_import_clearance_pi(doc):
        _create_input_vat_undue(doc, source_doctype="Import Clearance")
        return

    # Route: Service purchase → Input VAT Undue (copy, waiting for original)
    if check_if_service_purchase(doc):
        if check_has_tax_invoice(doc):
            # Has tax invoice → create Thai Purchase VAT directly (original)
            _create_thai_purchase_vat(doc, vat_type="General")
        else:
            # No tax invoice → Input VAT Undue (copy)
            _create_input_vat_undue(doc, source_doctype="Service")
        return

    # Route: Regular purchase → Thai Purchase VAT (original, tax invoice already received)
    _create_thai_purchase_vat(doc, vat_type="General")


# =============================================================================
# INPUT VAT UNDUE
# =============================================================================

def _create_input_vat_undue(doc, source_doctype=None):
    """Create Input VAT Undue record (copy tax invoice — pending original)."""
    existing = frappe.db.exists(
        "Input VAT Undue", {"purchase_invoice": doc.name}
    )
    if existing:
        return

    vat_record = frappe.new_doc("Input VAT Undue")
    vat_record.purchase_invoice = doc.name
    vat_record.supplier = doc.supplier
    vat_record.supplier_name = doc.supplier_name
    vat_record.posting_date = doc.posting_date

    # Tax invoice info (may be empty — copy invoice)
    vat_record.tax_invoice_number = (
        getattr(doc, "pd_custom_tax_invoice_number", None)
        or getattr(doc, "tax_invoice_number", None)
        or doc.bill_no
        or ""
    )
    vat_record.tax_invoice_date = (
        getattr(doc, "pd_custom_tax_invoice_date", None)
        or getattr(doc, "tax_invoice_date", None)
        or doc.bill_date
        or None
    )
    vat_record.bill_no = doc.bill_no or ""
    if hasattr(doc, "dgs_custom_bill_series"):
        vat_record.bill_series = getattr(doc, "dgs_custom_bill_series", "") or ""

    # Amounts — use the correct tax_base_amount
    vat_record.base_amount = _get_tax_base_amount(doc)
    vat_record.vat_amount = doc.base_total_taxes_and_charges or 0
    vat_record.total_amount = doc.base_grand_total or 0

    # Supplier info
    if doc.supplier:
        try:
            supplier_doc = frappe.get_doc("Supplier", doc.supplier)
            vat_record.supplier_tax_id = getattr(supplier_doc, "tax_id", None) or ""
            vat_record.supplier_branch = (
                getattr(supplier_doc, "pd_custom_branch_code", None) or "00000"
            )
        except Exception:
            vat_record.supplier_tax_id = getattr(doc, "tax_id", None) or ""
            vat_record.supplier_branch = "00000"

    vat_record.company = doc.company

    # VAT period from posting date
    if doc.posting_date:
        posting_date = getdate(doc.posting_date)
        vat_record.vat_month = str(posting_date.month)
        vat_record.vat_year = str(posting_date.year)

    # New fields for the two-doctype flow
    vat_record.status = "Pending"
    vat_record.has_original = 0
    vat_record.source_doctype = source_doctype or "Purchase Invoice"

    # Account
    vat_record.input_vat_account = frappe.get_value(
        "Company", doc.company, "default_input_vat_undue_account"
    )

    vat_record.flags.ignore_permissions = True

    try:
        vat_record.insert()
        frappe.db.commit()
        frappe.msgprint(
            f"Input VAT Undue record created: {vat_record.name}",
            title="Input VAT Undue Created",
            indicator="green",
        )
    except Exception as e:
        frappe.log_error(
            f"Error creating Input VAT Undue: {str(e)}", "VAT Creation Error"
        )


def _get_tax_base_amount(doc):
    """Get the correct tax base amount from PI, trying multiple sources."""
    # Try pd_custom_tax_base_amount first
    val = getattr(doc, "pd_custom_tax_base_amount", None)
    if val:
        return flt(val)

    # Try tax_base_amount field
    val = getattr(doc, "tax_base_amount", None)
    if val:
        return flt(val)

    # Fallback: calculate from net total and taxes
    # VAT = base_total_taxes_and_charges; base = VAT / 0.07
    vat = flt(doc.base_total_taxes_and_charges)
    if vat and vat > 0:
        # Assume 7% standard rate
        return round(vat / 0.07, 2)

    # Last fallback: base_net_total
    return flt(doc.base_net_total) or 0


# =============================================================================
# THAI PURCHASE VAT
# =============================================================================

def _create_thai_purchase_vat(doc, vat_type="General"):
    """Create Thai Purchase VAT record (original tax invoice received)."""
    # Prevent duplicate: one record per PI
    existing = frappe.get_value(
        "Thai Purchase VAT", {"purchase_invoice": doc.name}, "name"
    )
    if existing:
        return

    thai_vat = frappe.new_doc("Thai Purchase VAT")
    thai_vat.purchase_invoice = doc.name
    thai_vat.purchase_for_company = doc.company or frappe.defaults.get_user_default(
        "Company"
    )
    thai_vat.purchase_for_branch = "00000"

    # Core invoice info
    thai_vat.supplier = doc.supplier
    thai_vat.supplier_name = doc.supplier_name
    thai_vat.bill_date = doc.bill_date or doc.posting_date
    thai_vat.bill_no = doc.bill_no or ""
    thai_vat.posting_date = doc.posting_date

    # Tax invoice details
    thai_vat.tax_invoice_number = (
        getattr(doc, "pd_custom_tax_invoice_number", None)
        or getattr(doc, "tax_invoice_number", None)
        or doc.bill_no
        or ""
    )
    thai_vat.tax_invoice_date = (
        getattr(doc, "pd_custom_tax_invoice_date", None)
        or getattr(doc, "tax_invoice_date", None)
        or doc.bill_date
        or None
    )

    # Tax base amount
    thai_vat.tax_base_amount = _get_tax_base_amount(doc)

    # Amounts
    thai_vat.base_amount = flt(doc.base_net_total) or 0
    thai_vat.vat_amount = doc.base_total_taxes_and_charges or 0
    thai_vat.total_amount = doc.base_grand_total or 0

    # Supplier info
    if doc.supplier:
        try:
            supplier_doc = frappe.get_doc("Supplier", doc.supplier)
            thai_vat.supplier_name = (
                supplier_doc.supplier_name or doc.supplier_name
            )
            thai_vat.supplier_tax_id = getattr(supplier_doc, "tax_id", None) or ""
            thai_vat.supplier_branch = (
                getattr(supplier_doc, "pd_custom_branch_code", None) or "00000"
            )
        except Exception:
            thai_vat.supplier_name = doc.supplier_name
            thai_vat.supplier_tax_id = getattr(doc, "tax_id", None) or ""
            thai_vat.supplier_branch = "00000"

    if hasattr(doc, "dgs_custom_bill_series"):
        thai_vat.bill_series = getattr(doc, "dgs_custom_bill_series", "") or ""

    # VAT period
    if doc.bill_date:
        bill_date = getdate(doc.bill_date)
        thai_vat.vat_month = str(bill_date.month)
        thai_vat.vat_year = str(bill_date.year)
    elif doc.posting_date:
        posting_date = getdate(doc.posting_date)
        thai_vat.vat_month = str(posting_date.month)
        thai_vat.vat_year = str(posting_date.year)

    # New field: vat_type
    thai_vat.vat_type = vat_type
    thai_vat.workflow_state = "Draft"

    thai_vat.flags.ignore_permissions = True

    try:
        thai_vat.insert()
        frappe.db.commit()
        frappe.msgprint(
            f"Thai Purchase VAT record created: {thai_vat.name}",
            title="VAT Record Created",
            indicator="green",
        )
    except Exception as e:
        frappe.log_error(
            f"Error creating Thai Purchase VAT: {str(e)}", "VAT Creation Error"
        )


# =============================================================================
# CANCELLATION
# =============================================================================

def handle_purchase_invoice_cancellation(doc, method):
    """Handle PI cancellation — update related Input VAT Undue / Thai Purchase VAT."""
    if doc.doctype != "Purchase Invoice" or doc.docstatus != 2:
        return

    # Update Input VAT Undue
    undue_name = frappe.get_value(
        "Input VAT Undue", {"purchase_invoice": doc.name}, "name"
    )
    if undue_name:
        frappe.db.set_value("Input VAT Undue", undue_name, "status", "Cancelled")
        frappe.db.commit()

    # Update Thai Purchase VAT
    vat_name = frappe.get_value(
        "Thai Purchase VAT", {"purchase_invoice": doc.name}, "name"
    )
    if vat_name:
        frappe.db.set_value("Thai Purchase VAT", vat_name, "workflow_state", "Cancelled")
        frappe.db.commit()


# =============================================================================
# "GOT ORIGINAL" — creates Thai Purchase VAT from Input VAT Undue
# =============================================================================

@frappe.whitelist()
def mark_original_received(input_vat_undue_name):
    """
    Called when user ticks "Got Original" on an Input VAT Undue record.

    Creates a Thai Purchase VAT record and marks the Input VAT Undue as
    "Converted to Input VAT".

    Args:
        input_vat_undue_name: name of the Input VAT Undue record
    """
    if not frappe.has_permission("Input VAT Undue", "write"):
        frappe.throw(_("No permission to update Input VAT Undue"))

    undue = frappe.get_doc("Input VAT Undue", input_vat_undue_name)

    if undue.has_original:
        frappe.msgprint(
            "Original already received — Thai Purchase VAT record already created.",
            title="Already Processed",
            indicator="orange",
        )
        return

    # Prevent duplicate: one Thai Purchase VAT per PI
    existing = frappe.get_value(
        "Thai Purchase VAT", {"purchase_invoice": undue.purchase_invoice}, "name"
    )
    if existing:
        frappe.throw(
            f"Thai Purchase VAT record already exists: {existing}",
            title="Duplicate",
        )

    # Determine vat_type from source_doctype
    vat_type = "Undue"
    if undue.source_doctype == "Import Clearance":
        vat_type = "Import"

    # Create Thai Purchase VAT from Input VAT Undue data
    thai_vat = frappe.new_doc("Thai Purchase VAT")
    thai_vat.purchase_invoice = undue.purchase_invoice
    thai_vat.purchase_for_company = undue.company
    thai_vat.purchase_for_branch = undue.supplier_branch or "00000"
    thai_vat.supplier = undue.supplier
    thai_vat.supplier_name = undue.supplier_name
    thai_vat.posting_date = undue.posting_date
    thai_vat.bill_date = undue.tax_invoice_date or undue.posting_date
    thai_vat.tax_invoice_number = undue.tax_invoice_number or undue.bill_no or ""
    thai_vat.tax_invoice_date = undue.tax_invoice_date
    thai_vat.tax_base_amount = undue.base_amount or 0
    thai_vat.bill_series = undue.bill_series or ""
    thai_vat.supplier_tax_id = undue.supplier_tax_id or ""
    thai_vat.supplier_branch = undue.supplier_branch or "00000"
    thai_vat.base_amount = undue.base_amount or 0
    thai_vat.vat_amount = undue.vat_amount or 0
    thai_vat.total_amount = undue.total_amount or 0

    # VAT period from posting date
    if undue.posting_date:
        pd = getdate(undue.posting_date)
        thai_vat.vat_month = str(pd.month)
        thai_vat.vat_year = str(pd.year)

    thai_vat.vat_type = vat_type
    thai_vat.workflow_state = "Draft"

    thai_vat.flags.ignore_permissions = True
    thai_vat.insert()

    # Update Input VAT Undue status
    undue.has_original = 1
    undue.status = "Converted to Input VAT"
    undue.converted_date = frappe.utils.nowdate()
    undue.converted_by = frappe.session.user
    undue.flags.ignore_permissions = True
    undue.save()

    frappe.db.commit()

    frappe.msgprint(
        f"Thai Purchase VAT {thai_vat.name} created from Input VAT Undue {undue.name}",
        title="Original Received",
        indicator="green",
    )

    return {"thai_purchase_vat": thai_vat.name, "input_vat_undue": undue.name}


# =============================================================================
# UTILITY
# =============================================================================

from frappe.utils import flt


@frappe.whitelist()
def get_thai_vat_summary(vat_month=None, vat_year=None):
    """Get summary of all Thai Purchase VAT records with optional filtering."""
    filters = {}
    if vat_month:
        filters["vat_month"] = vat_month
    if vat_year:
        filters["vat_year"] = vat_year

    vat_records = frappe.get_all(
        "Thai Purchase VAT",
        filters=filters,
        fields=[
            "name",
            "purchase_invoice",
            "supplier",
            "base_amount",
            "vat_amount",
            "total_amount",
            "vat_month",
            "vat_year",
            "workflow_state",
            "vat_type",
        ],
    )

    undue_records = frappe.get_all(
        "Input VAT Undue",
        filters={"status": ["!=", "Cancelled"]},
        fields=[
            "name",
            "purchase_invoice",
            "supplier",
            "base_amount",
            "vat_amount",
            "total_amount",
            "vat_month",
            "vat_year",
            "status",
            "source_doctype",
            "has_original",
        ],
    )

    total_base = sum(r.base_amount or 0 for r in vat_records)
    total_vat = sum(r.vat_amount or 0 for r in vat_records)
    pending_base = sum(r.base_amount or 0 for r in undue_records)
    pending_vat = sum(r.vat_amount or 0 for r in undue_records)

    return {
        "thai_purchase_vat_records": vat_records,
        "input_vat_undue_records": undue_records,
        "total_base_amount": total_base,
        "total_vat_amount": total_vat,
        "pending_base_amount": pending_base,
        "pending_vat_amount": pending_vat,
        "total_thai_purchase_vat_records": len(vat_records),
        "total_input_vat_undue_records": len(undue_records),
    }


@frappe.whitelist()
def get_vat_months_years():
    """Get available VAT months and years for filtering."""
    tpv_months = frappe.get_all(
        "Thai Purchase VAT", fields=["vat_month", "vat_year"]
    )
    iuv_months = frappe.get_all(
        "Input VAT Undue", fields=["vat_month", "vat_year"]
    )

    all_months = tpv_months + iuv_months
    unique = {}
    for m in all_months:
        if m.vat_month and m.vat_year:
            key = f"{m.vat_year}-{m.vat_month.zfill(2)}"
            unique[key] = {"vat_month": m.vat_month, "vat_year": m.vat_year}

    return [unique[k] for k in sorted(unique.keys(), reverse=True)]


# Keep legacy function name for backward compatibility
def update_vat_from_payment_entry(doc, method):
    """Legacy: handle PE with tax invoice to update Input VAT Undue."""
    # This function is kept for compatibility with existing hooks.
    # New flow uses mark_original_received() instead.
    pass
