# Copyright (c) 2026, Print Designer
# For license information, please see license.txt

"""
Output VAT Undue - tracks the sales whose VAT is not due yet.

The ledger itself is written by
:mod:`print_designer.custom.output_vat_undue_tracking` - that module is the
one orchestration path of the tracking.  This controller keeps the document
consistent: it derives the balance of a row and it protects the snapshot of
the source invoice.

The old helpers (``create_output_vat_undue_record`` and
``update_output_vat_on_tax_invoice``) stay available as thin wrappers, so a
caller of the old names does not break.  The conversion of a row is not a
side effect of the save of an invoice any more: it is an explicit event
(:func:`print_designer.custom.output_vat_undue_tracking.convert_to_output_vat`).
"""

import frappe
from frappe.model.document import Document
from frappe.utils import flt

from print_designer.custom import output_vat_undue_tracking as pd_ovu_tracking
from print_designer.custom.output_vat_undue_tracking import (
    STATUS_CANCELLED,
    STATUS_CONVERTED,
    STATUS_NOT_APPLICABLE,
    STATUS_PARTIALLY_CONVERTED,
    STATUS_PENDING,
)

#: The statuses that carry an active undue balance.
ACTIVE_STATUSES = (STATUS_PENDING, STATUS_PARTIALLY_CONVERTED)


class OutputVATUndue(Document):
    """One tracked sale."""

    def validate(self):
        """Keep the balance of the row consistent.

        The snapshot of the source invoice (the treatment, the registration
        and the amounts) is written once, when the row is created.  A later
        change of the company settings must never rewrite it, so only the
        balance is derived here.
        """
        self.set("remaining_vat_amount", self._remaining_vat_amount())

    def _remaining_vat_amount(self):
        """Return the VAT of the row that is still undue.

        For an active row the balance is the eligible VAT minus the VAT that
        has been recognized.  A closed row carries no balance: it keeps its
        snapshot as the history of the sale.
        """
        if self.get("status") in (
            STATUS_CANCELLED,
            STATUS_CONVERTED,
            STATUS_NOT_APPLICABLE,
        ):
            return 0

        eligible = flt(str(self.get("vat_amount") or 0))
        recognized = flt(str(self.get("recognized_vat_amount") or 0))
        return max(eligible - recognized, 0)


def check_if_service_sale(doc):
    """Check if Sales Invoice contains service items.

    The answer is the one of the tax contract: a service row is a row of the
    invoice whose item is a service, not every item that is not a stock item.
    """
    from print_designer.custom.sales_invoice_tax_contract import (
        CLASSIFICATION_SERVICES,
        get_service_tax_snapshot,
    )

    try:
        snapshot = get_service_tax_snapshot(doc)
    except Exception:
        return False

    return snapshot.classification == CLASSIFICATION_SERVICES


def create_output_vat_undue_record(doc, method=None):
    """Compatibility wrapper of the old submit hook.

    The row of the ledger is written by
    :mod:`print_designer.custom.output_vat_undue_tracking` - the one
    orchestration path of the tracking.  This wrapper only keeps the old
    name of that function alive.
    """
    return pd_ovu_tracking.create_output_vat_undue_record(doc, method)


def update_output_vat_on_tax_invoice(doc, method=None):
    """Compatibility wrapper of the old validate hook.

    The old behaviour converted the row as soon as a tax invoice number was
    typed into the invoice.  A number in a field is not evidence that a tax
    invoice was issued, so the conversion is an explicit event now.  The
    wrapper only keeps the snapshot of the tax invoice reference up to date.
    """
    if getattr(doc, "doctype", None) != "Sales Invoice":
        return None

    number = doc.get("pd_custom_tax_invoice_number")
    if not number:
        return None

    name = frappe.db.exists("Output VAT Undue", {"sales_invoice": doc.name})
    if not name:
        return None

    record = frappe.get_doc("Output VAT Undue", str(name))
    record.set("tax_invoice_number", number)
    record.set("tax_invoice_date", doc.get("pd_custom_tax_invoice_date"))
    record.save(ignore_permissions=True)
    return record
