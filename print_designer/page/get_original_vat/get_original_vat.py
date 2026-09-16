# Copyright (c) 2026, AWS Solution Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import fmt_money


def get_context(context):
    """Render Get Original VAT page."""
    context.brand_html = "Get Original VAT"
    context.title = "Get Original VAT - Input VAT Undue"

    # Get pending records
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
        """,
        as_dict=True,
    )

    # Get converted count
    converted_count = frappe.db.count(
        "Input VAT Undue",
        {"status": "Converted to Input VAT"},
    )

    total_pending = len(pending)
    total_pending_vat = sum(r.vat_amount or 0 for r in pending)

    context.pending_records = pending
    context.total_pending = total_pending
    context.total_pending_vat = fmt_money(total_pending_vat, currency="THB")
    context.converted_count = converted_count

    # Stats by source type
    source_stats = {}
    for r in pending:
        src = r.source_doctype or "Purchase Invoice"
        if src not in source_stats:
            source_stats[src] = {"count": 0, "vat": 0}
        source_stats[src]["count"] += 1
        source_stats[src]["vat"] += r.vat_amount or 0
    context.source_stats = source_stats
