"""Read-only VAT preview of a draft Sales Invoice.

SI-03, Task A of ``wiki/si-vat-preview-reports-minimax.md``.

The preview is a proposal of the VAT of one saved draft invoice.  It is not
a posted ledger, not a tax invoice, not a filing and not a recognition event:
the module writes nothing, it creates no row of the Output VAT Undue ledger
and it posts no GL entry.

The values come from the SI-01 contract
(``print_designer/custom/sales_invoice_tax_contract.py``), so the preview
shows the same decision that the ledger of a submitted invoice would carry.

Only a saved draft of one invoice is accepted.  A submitted invoice has its
own reports, a new invoice has no stored values yet, and a preview never
mixes a draft into the totals of the filed reports.
"""

import frappe
from frappe import _

from print_designer.custom.output_vat_undue_tracking import status_for_snapshot
from print_designer.custom.sales_invoice_tax_contract import (
    CLASSIFICATION_SERVICES,
    REASON_ALREADY_DUE,
    REASON_DEFERRED_SERVICE,
    get_service_tax_snapshot,
)

#: The banner that every projection of this module carries.
DRAFT_PREVIEW_MARKER = "Draft Preview — Not Posted"

#: The note under the banner.
DRAFT_PREVIEW_NOTE = (
    "This is a proposal of the VAT of a draft invoice. It is not a posted "
    "ledger, not a tax invoice, not a filing and not a recognition event."
)


@frappe.whitelist()
def get_draft_vat_preview(sales_invoice):
    """Return the read-only VAT projection of one saved draft invoice."""
    if not sales_invoice:
        frappe.throw(_("The VAT preview needs the name of a saved Sales Invoice."))

    if not frappe.db.exists("Sales Invoice", sales_invoice):
        frappe.throw(_("The Sales Invoice {0} does not exist.").format(sales_invoice))

    invoice = frappe.get_doc("Sales Invoice", sales_invoice)

    if invoice.get("docstatus") != 0:
        frappe.throw(_("The VAT preview is only available for a draft Sales Invoice."))

    if not frappe.has_permission("Sales Invoice", "read", doc=invoice):
        frappe.throw(_("Not permitted to read this Sales Invoice."), frappe.PermissionError)

    if not invoice.get("company"):
        frappe.throw(_("The Sales Invoice has no company."))

    return build_vat_preview(invoice)


def build_vat_preview(invoice):
    """Build the projection of a draft invoice from the SI-01 contract."""
    snapshot = get_service_tax_snapshot(invoice)
    due_amount, undue_amount = split_vat(snapshot)
    registration = snapshot.registration

    return {
        "marker": DRAFT_PREVIEW_MARKER,
        "note": DRAFT_PREVIEW_NOTE,
        "is_draft_preview": True,
        "sales_invoice": invoice.get("name"),
        "company": invoice.get("company"),
        "posting_date": _date_text(invoice.get("posting_date")),
        "customer": invoice.get("customer"),
        "customer_name": invoice.get("customer_name") or invoice.get("customer"),
        "customer_tax_id": invoice.get("tax_id"),
        "base_net_total": invoice.get("base_net_total"),
        "total_taxes_and_charges": invoice.get("total_taxes_and_charges"),
        "currency": snapshot.currency,
        "company_currency": snapshot.company_currency,
        "classification": snapshot.classification,
        "is_service_sale": snapshot.is_service_sale,
        "is_tracked": snapshot.classification == CLASSIFICATION_SERVICES,
        "treatment": snapshot.treatment,
        "treatment_source": snapshot.treatment_source,
        "treatment_reason": snapshot.treatment_reason,
        "registration_status": registration.status if registration else None,
        "service_base_amount": snapshot.eligible_service_base,
        "service_base_amount_currency": snapshot.eligible_service_base_currency,
        "vat_amount": snapshot.vat_amount,
        "vat_amount_currency": snapshot.vat_amount_currency,
        "due_vat_amount": due_amount,
        "undue_vat_amount": undue_amount,
        "status": status_for_snapshot(snapshot),
        "warnings": list(snapshot.warnings or []),
    }


def _date_text(value):
    """Return a date as a plain string, without a time of the day."""
    return str(value) if value else None


def split_vat(snapshot):
    """Split the VAT of the invoice into the part that is due and the undue part.

    A deferred service sale carries a prospective undue VAT: it is not due
    yet.  A sale whose tax point has been reached carries a due VAT.  A sale
    without a VAT liability carries neither.
    """
    if snapshot.treatment_reason == REASON_DEFERRED_SERVICE:
        return 0.0, snapshot.vat_amount

    if snapshot.treatment_reason == REASON_ALREADY_DUE:
        return snapshot.vat_amount, 0.0

    return 0.0, 0.0
