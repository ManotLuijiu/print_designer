# Copyright (c) 2026, AWS Solution Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import fmt_money


def get_context(context):
    """Render Get Original VAT page (website/desk template)."""
    context.brand_html = "Get Original VAT"
    context.title = "Get Original VAT - Input VAT Undue"

    data = _get_pending_data()
    context.pending_records = data["pending_records"]
    context.total_pending = data["total_pending"]
    context.total_pending_vat = data["total_pending_vat_formatted"]
    context.converted_count = data["converted_count"]
    context.source_stats = data["source_stats"]


@frappe.whitelist()
def get_pending_records():
    """Return pending Input VAT Undue records for the desk page."""
    if not frappe.has_permission("Input VAT Undue", "read"):
        frappe.throw(frappe._("No permission to read Input VAT Undue"))

    data = _get_pending_data()
    return data


def _get_pending_data():
    """Shared data builder for get_pending_records and get_context."""
    pending = frappe.db.sql(
        """
        SELECT
            iuv.name,
            iuv.purchase_invoice,
            iuv.supplier,
            iuv.supplier_name,
            iuv.posting_date,
            iuv.base_amount,
            iuv.vat_amount,
            iuv.total_amount,
            iuv.source_doctype,
            iuv.company
        FROM `tabInput VAT Undue` iuv
        WHERE iuv.status = 'Pending'
          AND iuv.has_original = 0
        ORDER BY iuv.posting_date DESC
        LIMIT 200
        """,
        as_dict=True,
    )

    converted_count = frappe.db.count(
        "Input VAT Undue",
        {"status": "Converted to Input VAT"},
    )

    total_pending = len(pending)
    total_pending_vat = sum(r.vat_amount or 0 for r in pending)

    source_stats = {}
    for r in pending:
        src = r.source_doctype or "Purchase Invoice"
        if src not in source_stats:
            source_stats[src] = {"count": 0, "vat": 0}
        source_stats[src]["count"] += 1
        source_stats[src]["vat"] += r.vat_amount or 0

    return {
        "pending_records": pending,
        "total_pending": total_pending,
        "total_pending_vat_formatted": fmt_money(total_pending_vat, currency="THB"),
        "total_pending_vat": total_pending_vat,
        "converted_count": converted_count,
        "source_stats": source_stats,
    }


@frappe.whitelist()
def mark_bulk_received(names):
    """
    Mark multiple Input VAT Undue records as having original received.
    Creates a Thai Purchase VAT record for each.

    Args:
        names: list of Input VAT Undue record names

    Returns:
        list of results with success/failure per record
    """
    if not frappe.has_permission("Input VAT Undue", "write"):
        frappe.throw(frappe._("No permission to update Input VAT Undue"))

    if not names:
        return []

    if isinstance(names, str):
        import json
        names = json.loads(names)

    results = []
    for name in names:
        try:
            from print_designer.regional.thai_purchase_vat import mark_original_received

            result = mark_original_received(name)
            results.append({"name": name, "success": True, "result": result})
        except Exception as e:
            results.append(
                {
                    "name": name,
                    "success": False,
                    "error": str(e),
                }
            )

    return results
