# Copyright (c) 2026, MooCoding and contributors
# For license information, please see license.txt

"""The intake of a tax invoice.

A tax invoice of a supplier arrives on paper, on a picture or in the mail.
The queue that received them from outside the site is gone, so the site
receives them again in a document of its own: the intake.

The intake carries the attachment of the invoice, the numbers of the
invoice, the amounts of the invoice and the states of the workflow.  The
workflow has three steps:

- the accountant verifies the invoice, and the state of the verification
  becomes "Verified" or "Rejected";
- the accountant creates the purchase invoice of the intake, and the state
  of the synchronization becomes "Synced";
- the sweep of the site synchronizes the intakes that are verified and
  still pending.

Every step answers a POST, because a GET may be triggered by a link, by a
prefetch of a browser or by a crawler, and none of those may change the
books of a company.  Every step asks for the right to write the intake
before it reads the attachment, before it changes a state and before it
creates the purchase invoice.  The purchase invoice itself is created with
the rights of the caller: the intake never writes the books of a company
with a right of its own.

The amounts of the intake are the amounts of the currency of the company.

The behaviour of this controller comes from the controller of Thai Business
Suite.  The dependency on that app is not there: the authorization of the
steps is the one of Print Designer
(`print_designer/custom/document_permission.py` and
`print_designer/custom/maintenance_access.py`), so the workflow of the
intake works on a site where Thai Business Suite is not installed.  The old
path of Thai Business Suite keeps working as a shim that delegates to this
module.
"""

from typing import Any, cast

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from print_designer.custom.document_permission import (
    require_doctype_permission,
    require_document_read,
    require_document_write,
)
from print_designer.custom.maintenance_access import require_system_manager

INTAKE = "Thai Tax Invoice Intake"
PURCHASE_INVOICE = "Purchase Invoice"

# The two kinds of invoice that the intake receives.
PURCHASE_TAX_INVOICE = "Purchase Tax Invoice"
SALES_TAX_INVOICE = "Sales Tax Invoice"

# The two kinds of party that the invoice of the intake may belong to.
SUPPLIER = "Supplier"
CUSTOMER = "Customer"

# The states of the verification that the accountant may set.
VERIFIED = "Verified"
REJECTED = "Rejected"

# The states of the synchronization of the intake.
SYNCED = "Synced"
FAILED = "Failed"
PENDING = "Pending"

# The tolerance of the comparison of the amounts is a cent, because the
# amounts of an invoice are rounded to the precision of the currency.
AMOUNT_TOLERANCE = 0.01

# The error of a synchronization is cut, because the column of the error is
# a text and a traceback of the framework is longer than a screen.
MAX_ERROR_LENGTH = 2000


class ThaiTaxInvoiceIntake(Document):
    """The intake of a tax invoice of a supplier."""

    # The fields of a document are added by the doctype, so a type checker
    # cannot verify an attribute of a document.  These are false positives
    # inherent to the ORM of Frappe and not defects of this module.
    company: str = ""
    invoice_type: str = ""
    party_type: str = ""
    party: str = ""
    party_tax_id: str = ""
    bill_no: str = ""
    bill_date: str = ""
    due_date: str = ""
    description: str = ""
    invoice_attachment: str = ""
    net_amount: float = 0.0
    vat_amount: float = 0.0
    vat_rate: float = 0.0
    total_amount: float = 0.0
    tax_account: str = ""
    expense_item: str = ""
    expense_account: str = ""
    verification_status: str = ""
    sync_status: str = ""
    verification_remark: str = ""
    purchase_invoice: str = ""
    sync_error: str = ""

    @frappe.whitelist(methods=["POST"])
    def set_verification_status(self, status: str = VERIFIED, remark: str | None = None):
        """Verify or reject the invoice of the intake.

        Args:
                status: "Verified" or "Rejected".
                remark: the note of the accountant (optional).

        Returns:
                dict: the new state of the verification.
        """
        require_document_write(INTAKE, self.name)

        verification = str(status or "").strip()
        if verification not in (VERIFIED, REJECTED):
            frappe.throw(_("The verification status must be Verified or Rejected."))

        if self.purchase_invoice:
            frappe.throw(
                _(
                    "The intake is already synchronized to the purchase invoice {0}. The verification may not change."
                ).format(self.purchase_invoice)
            )

        self.db_set("verification_status", verification, notify=True, commit=True)

        if remark:
            self.db_set(
                "verification_remark",
                str(remark)[:MAX_ERROR_LENGTH],
                notify=True,
                commit=True,
            )

        return {"verification_status": verification}

    @frappe.whitelist(methods=["POST"])
    def sync_to_purchase_invoice(self):
        """Create the purchase invoice of the intake.

        The invoice is created once: an intake that carries a purchase
        invoice refuses a second one, so the state of the site may not be
        changed twice by the same invoice of the supplier.

        Returns:
                dict: the name of the purchase invoice and the state of the
                        synchronization.
        """
        require_document_write(INTAKE, self.name)
        require_doctype_permission(PURCHASE_INVOICE, "create")

        linked = self.purchase_invoice or frappe.db.get_value(INTAKE, self.name, "purchase_invoice")
        if linked:
            frappe.throw(
                _("The intake is already synchronized to the purchase invoice {0}.").format(linked)
            )

        if self.verification_status != VERIFIED:
            frappe.throw(_("The invoice must be verified before it is synchronized."))

        self.validate_for_sync()

        # The attachment is read after the rights were asked for.  A file
        # that is not private is readable by everybody, so the right to
        # read it proves nothing; the right to write the intake does.
        file_document = self.read_attachment()

        save_point = "thai_tax_invoice_intake_sync"
        frappe.db.savepoint(save_point)

        try:
            invoice = self.create_purchase_invoice()
            # The copy of the file reuses the address of the file, so the
            # bytes of the invoice are not written a second time.  The copy
            # is written with the rights of the caller: the intake does not
            # write anything with a right of its own.
            cast(Any, file_document).create_attachment_copy(
                PURCHASE_INVOICE,
                invoice.name,
            )
        except Exception as error:
            # The save point undoes the invoice that was half created.  The
            # state of the intake is written after the undo, so the failure
            # is visible to the accountant.
            frappe.db.rollback(save_point=save_point)
            self.record_failure(error)
            raise

        frappe.db.release_savepoint(save_point)

        self.db_set("purchase_invoice", invoice.name, notify=True, commit=True)
        self.db_set("sync_status", SYNCED, notify=True, commit=True)
        self.db_set("sync_error", "", notify=True, commit=True)

        return {"purchase_invoice": invoice.name, "sync_status": SYNCED}

    def validate_for_sync(self):
        """Check the data of the intake before the invoice is created.

        Raises:
                frappe.ValidationError: when the intake does not carry the data
                        that the purchase invoice needs.
        """
        if self.invoice_type != PURCHASE_TAX_INVOICE:
            frappe.throw(
                _(
                    "This workflow synchronizes the purchase tax invoices only. The intake of a sales tax invoice is not synchronized into a purchase invoice."
                )
            )

        if self.party_type != SUPPLIER:
            frappe.throw(_("The party of the intake must be a supplier."))

        if not self.bill_no:
            frappe.throw(_("The number of the invoice is required."))

        if not self.bill_date:
            frappe.throw(_("The date of the invoice is required."))

        net_amount = flt(self.net_amount)
        if net_amount <= 0:
            frappe.throw(_("The net amount of the invoice must be greater than zero."))

        self.validate_the_amounts_of_the_invoice(net_amount)
        self.validate_the_booking_of_the_invoice()

    def validate_the_amounts_of_the_invoice(self, net_amount: float):
        """Check the numbers of the invoice of the intake.

        Args:
                net_amount: the net amount of the invoice, already checked.

        Raises:
                frappe.ValidationError: when the amounts of the intake do not
                        belong together.
        """
        if not self.expense_item:
            frappe.throw(_("The expense item of the intake is required."))

        if not self.expense_account:
            frappe.throw(_("The expense account of the intake is required."))

        vat_amount = flt(self.vat_amount)
        if vat_amount > 0 and not self.tax_account:
            frappe.throw(
                _("The VAT account of the intake is required when the invoice carries a VAT.")
            )

        total_amount = flt(self.total_amount)
        if abs(total_amount - (net_amount + vat_amount)) > AMOUNT_TOLERANCE:
            frappe.throw(
                _(
                    "The total amount {0} of the intake is not the net amount {1} and the VAT amount {2}."
                ).format(total_amount, net_amount, vat_amount)
            )

    def validate_the_booking_of_the_invoice(self):
        """Check the item and the order of the purchase of the invoice.

        Raises:
                frappe.ValidationError: when the item of the intake is a stock
                        item, or when the site asks for a purchase order.
        """
        found = frappe.db.get_value(
            "Item",
            self.expense_item,
            ["name", "item_name", "is_stock_item"],
            as_dict=True,
        )
        if not found:
            frappe.throw(_("The item {0} was not found.").format(self.expense_item))

        item = cast(dict[str, Any], found)

        if item.get("is_stock_item"):
            frappe.throw(
                _(
                    "The item {0} is a stock item. The intake books a service; a stock item is booked through a purchase receipt."
                ).format(self.expense_item)
            )

        if frappe.db.get_single_value(
            "Buying Settings", "po_required"
        ) == "Yes" and not frappe.db.get_value(
            "Supplier",
            self.party,
            "allow_purchase_invoice_creation_without_purchase_order",
        ):
            frappe.throw(
                _(
                    "This site asks for a purchase order before a purchase invoice. The purchase invoice of the intake is refused; the purchase order and the purchase invoice are created outside of the intake."
                )
            )

    def read_attachment(self):
        """The file of the invoice, after the right to write the intake was asked for.

        The right of the caller is asked for the file of this intake, and
        not for another file that carries the same address, because the
        right of another file is not the right of this intake.

        Returns:
                Document: the file of the invoice.

        Raises:
                frappe.ValidationError: when the intake carries no attachment or
                        when the attachment belongs to another document.
                frappe.PermissionError: when the caller may not read the file.
        """
        if not self.invoice_attachment:
            frappe.throw(_("The attachment of the invoice is required."))

        # The address of a file may be carried by several files of the
        # site, because a copy of an attachment keeps the address.  The
        # file of this intake is therefore looked for first, so the copy of
        # the attachment of a purchase invoice is never mistaken for the
        # attachment of the intake.
        name = cast(
            str,
            frappe.db.get_value(
                "File",
                {
                    "file_url": self.invoice_attachment,
                    "attached_to_doctype": INTAKE,
                    "attached_to_name": self.name,
                },
                "name",
            ),
        )
        if not name:
            name = cast(
                str,
                frappe.db.get_value("File", {"file_url": self.invoice_attachment}, "name"),
            )
        if not name:
            frappe.throw(_("The attachment of the invoice was not found."))

        # The right of the caller is asked for the file that is really
        # read.  The address alone would not do, because another file of
        # the site may carry the same address, and the right of that other
        # file is not the right of this intake.
        require_document_read("File", name)

        file_document: Any = frappe.get_doc("File", name)

        if file_document.attached_to_doctype and file_document.attached_to_doctype != INTAKE:
            frappe.throw(_("The attachment of the invoice belongs to another document."))

        return file_document

    def create_purchase_invoice(self):
        """The purchase invoice of the intake.

        Returns:
                Document: the purchase invoice that was created.
        """
        invoice: Any = frappe.new_doc(PURCHASE_INVOICE)
        invoice.company = self.company
        invoice.supplier = self.party
        invoice.bill_no = self.bill_no
        invoice.bill_date = self.bill_date
        invoice.posting_date = self.bill_date
        invoice.set_posting_time = 1

        if self.due_date:
            invoice.due_date = self.due_date

        if self.party_tax_id:
            invoice.tax_id = self.party_tax_id

        invoice.append(
            "items",
            {
                "item_code": self.expense_item,
                "qty": 1,
                "rate": flt(self.net_amount),
                "expense_account": self.expense_account,
                "description": self.description or self.bill_no,
            },
        )

        if flt(self.vat_amount) > 0:
            invoice.append(
                "taxes",
                {
                    "charge_type": "Actual",
                    "account_head": self.tax_account,
                    "description": _("VAT"),
                    "tax_amount": flt(self.vat_amount),
                },
            )

        # The invoice is created with the rights of the caller.  The intake
        # does not write the books of the company with a right of its own.
        invoice.insert()

        return invoice

    def record_failure(self, error: Exception):
        """Write the reason of a failed synchronization.

        Args:
                error: the error that stopped the synchronization.
        """
        self.db_set("sync_status", FAILED, notify=True, commit=True)
        self.db_set(
            "sync_error",
            str(error)[:MAX_ERROR_LENGTH],
            notify=True,
            commit=True,
        )


@frappe.whitelist(methods=["POST"])
def sweep_pending_intakes(company: str | None = None):
    """Synchronize the intakes that are verified and still pending.

    The sweep reaches the records of every company of the site, so it asks
    for the role of the System Manager.  One intake that fails does not stop
    the sweep; the failure is written on the intake itself.

    Args:
            company: the company of the intakes (optional).

    Returns:
            dict: the number of the intakes and the state of every one of them.
    """
    require_system_manager("synchronize the verified tax invoices of the site")

    filters: dict[str, Any] = {"verification_status": VERIFIED, "sync_status": PENDING}
    if company:
        filters["company"] = company

    names = frappe.get_all(INTAKE, filters=filters, pluck="name", order_by="bill_date asc")

    results = []
    for name in names:
        try:
            intake: Any = frappe.get_doc(INTAKE, name)
            result = intake.sync_to_purchase_invoice()
            results.append(
                {
                    "name": name,
                    "sync_status": SYNCED,
                    "purchase_invoice": result.get("purchase_invoice"),
                }
            )
        except frappe.PermissionError:
            # The right of the caller is not swallowed: the sweep of a
            # caller that may not write an intake stops.
            raise
        except Exception as error:
            results.append({"name": name, "sync_status": FAILED, "error": str(error)})

    return {"processed": len(results), "results": results}
