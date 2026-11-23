"""Shared filters and permission checks for the submitted sales VAT registers."""

import frappe
from frappe import _
from frappe.utils import getdate


def get_register_rows(doctype, filters, fields, *, due=False):
    filters = frappe._dict(filters or {})
    if not filters.company:
        return []

    start = getdate(filters.from_date) if filters.from_date else None
    end = getdate(filters.to_date) if filters.to_date else None
    if start and end and start > end:
        frappe.throw(_("From Date must be on or before To Date."))

    invoice_filters = {"company": filters.company, "docstatus": 1}
    if filters.invoice_name:
        invoice_filters["name"] = filters.invoice_name
    invoices = frappe.get_list(
        "Sales Invoice", filters=invoice_filters, pluck="name", limit_page_length=0
    )
    if not invoices:
        return []

    ledger_filters = {"sales_invoice": ["in", invoices]}
    if due:
        ledger_filters["vat_type"] = "VAT Due"
        if filters.payment_entry_reference:
            ledger_filters["payment_entry_reference"] = filters.payment_entry_reference
    rows = frappe.get_list(
        doctype, filters=ledger_filters, fields=fields, limit_page_length=0
    )

    result = []
    for row in rows:
        date = row.posting_date
        if due:
            date = row.tax_invoice_date or row.vat_conversion_date or date
        if start or end:
            if not date:
                continue
            date = getdate(date)
            if (start and date < start) or (end and date > end):
                continue
        row.report_date = date
        result.append(row)
    return sorted(result, key=lambda row: (str(row.report_date or ""), row.name))


def make_columns(definitions):
    return [
        {"fieldname": field, "label": _(label), "fieldtype": fieldtype,
         "options": options, "width": width}
        for field, label, fieldtype, options, width in definitions
    ]
