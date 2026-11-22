# Copyright (c) 2026, Manot L. and contributors
# For license information, please see license.txt

"""Thai VAT Recognition.

The recognition of the output VAT of a sale, on the day the tax becomes due
under the Thai law:

- Goods: the VAT is due on the delivery, and the ordinary entries of the
  Sales Invoice carry it.
- Services: the VAT is due on the payment, and it is recognized when the
  payment is received.

The document belongs to Print Designer since the relocation of the Thai VAT
DocTypes.  The controller and the endpoints of the old path of Thai Business
Suite are here; the old path keeps working as a shim that delegates to this
module.

The controller does not import Thai Business Suite, so that the VAT behaviour
of Print Designer works on a site where that app is not installed.

The flags of the recognition on the Sales Invoice and on its items are the
fields that the site installs.  A field that the document does not carry is
not written, so that the recognition still lives on the recognition document
alone on a site without those fields, and no value is written that the save
would drop.
"""

# The fields of a Frappe document are not known to the type checker.  The
# same suppression is used by the other modules of the app that work with the
# documents of the framework.
# pyright: reportAttributeAccessIssue=false
# pyright: reportUninitializedInstanceVariable=false

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today

from print_designer.custom.document_permission import (
    require_doctype_permission,
    require_document_read,
)


class ThaiVATRecognition(Document):
    def validate(self):
        self.validate_recognition_type()
        self.validate_trigger_document()
        self.set_reference_information()
        self.calculate_vat_amount()
        self.normalize_dates()

    def on_submit(self):
        self.create_vat_gl_entry()
        self.update_sales_invoice_vat_status()
        self.update_thai_sales_vat()
        # The status is written after the document has been saved, so it
        # needs the write of the database and not only the value of the
        # document.
        self.db_set("status", "Active")

    def on_cancel(self):
        self.reverse_vat_gl_entry()
        self.reverse_sales_invoice_vat_status()
        self.revert_thai_sales_vat()
        self.db_set("status", "Cancelled")

    def normalize_dates(self):
        """The dates of the recognition are dates, not the text of a date.

        A date that is written as text travels through the document and
        reaches the entry of the ledger as text, where the date of the entry
        has to be a date.  The recognition and the invoice carry the same
        date, in the same shape, so that a comparison of the two does not
        depend on where the value came from.
        """
        if self.recognition_date:
            self.recognition_date = getdate(self.recognition_date)
        if self.posting_date:
            self.posting_date = getdate(self.posting_date)

    def validate_recognition_type(self):
        """Validate recognition type matches trigger document"""
        valid_combinations = {"Delivery": "Delivery Note", "Payment": "Payment Entry"}

        if self.recognition_type and self.trigger_document_type:
            expected_trigger = valid_combinations.get(self.recognition_type)
            if expected_trigger != self.trigger_document_type:
                frappe.throw(
                    _(
                        "Recognition Type '{0}' must be used with Trigger Document Type '{1}'"
                    ).format(self.recognition_type, expected_trigger)
                )

    def validate_trigger_document(self):
        """Validate trigger document exists and is submitted"""
        if not self.trigger_document:
            return

        if not frappe.db.exists(self.trigger_document_type, self.trigger_document):
            frappe.throw(
                _("Trigger document {0} {1} does not exist").format(
                    self.trigger_document_type, self.trigger_document
                )
            )

        doc_status = frappe.db.get_value(
            self.trigger_document_type, self.trigger_document, "docstatus"
        )

        if doc_status != 1:
            frappe.throw(
                _("Trigger document {0} {1} must be submitted").format(
                    self.trigger_document_type, self.trigger_document
                )
            )

    def set_reference_information(self):
        """Set reference information from Sales Invoice"""
        if not self.sales_invoice:
            return

        si = frappe.get_doc("Sales Invoice", self.sales_invoice)

        self.customer = si.customer
        self.customer_name = si.customer_name
        self.company = si.company
        self.posting_date = getdate(si.posting_date)
        self.base_net_total = si.base_net_total
        self.base_total_taxes_and_charges = si.base_total_taxes_and_charges

    def calculate_vat_amount(self):
        """Calculate VAT amount for recognized items"""
        if not self.items:
            return

        total_vat = 0
        for item in self.items:
            # Calculate VAT for this item
            item_vat = flt(item.amount) * (flt(item.tax_rate) / 100)
            item.vat_amount = item_vat
            total_vat += item_vat

        self.vat_amount = total_vat

    def update_sales_invoice_vat_status(self):
        """Update VAT recognition status in Sales Invoice"""
        if not self.sales_invoice:
            return

        si = frappe.get_doc("Sales Invoice", self.sales_invoice)

        # Update item-level VAT recognition
        for item in self.items:
            for si_item in si.items:
                if si_item.name == item.sales_invoice_item:
                    set_the_field_when_it_is_there(si_item, "custom_vat_recognized", 1)
                    break

        # Check if all VAT is now recognized
        all_recognized = all(item.get("custom_vat_recognized", 0) for item in si.items)

        if all_recognized:
            set_the_field_when_it_is_there(si, "custom_vat_fully_recognized", 1)
            set_the_field_when_it_is_there(si, "custom_goods_vat_pending", 0)
            set_the_field_when_it_is_there(si, "custom_service_vat_pending", 0)
        else:
            # Update partial recognition status
            goods_recognized = all(
                item.get("custom_vat_recognized", 0)
                for item in si.items
                if item.get("custom_vat_timing_type") == "Goods"
            )
            services_recognized = all(
                item.get("custom_vat_recognized", 0)
                for item in si.items
                if item.get("custom_vat_timing_type") == "Services"
            )

            if goods_recognized:
                set_the_field_when_it_is_there(si, "custom_goods_vat_pending", 0)
            if services_recognized:
                set_the_field_when_it_is_there(si, "custom_service_vat_pending", 0)

        # Update summary
        set_the_field_when_it_is_there(
            si, "custom_vat_recognition_summary", self.get_vat_recognition_summary(si)
        )

        si.save(ignore_permissions=True)

    def reverse_sales_invoice_vat_status(self):
        """Reverse VAT recognition status in Sales Invoice"""
        if not self.sales_invoice:
            return

        si = frappe.get_doc("Sales Invoice", self.sales_invoice)

        # Reverse item-level VAT recognition
        for item in self.items:
            for si_item in si.items:
                if si_item.name == item.sales_invoice_item:
                    set_the_field_when_it_is_there(si_item, "custom_vat_recognized", 0)
                    break

        # Reset invoice-level status
        set_the_field_when_it_is_there(si, "custom_vat_fully_recognized", 0)

        # Recalculate pending status
        if si.get("custom_has_goods"):
            set_the_field_when_it_is_there(si, "custom_goods_vat_pending", 1)
        if si.get("custom_has_services"):
            set_the_field_when_it_is_there(si, "custom_service_vat_pending", 1)

        set_the_field_when_it_is_there(
            si, "custom_vat_recognition_summary", self.get_vat_recognition_summary(si)
        )

        si.save(ignore_permissions=True)

    def get_vat_recognition_summary(self, sales_invoice):
        """Generate VAT recognition summary"""
        summary = []

        if sales_invoice.get("custom_has_goods"):
            goods_status = (
                "✅ Recognized"
                if not sales_invoice.get("custom_goods_vat_pending")
                else "⏳ Pending Delivery"
            )
            summary.append(f"Goods VAT: {goods_status}")

        if sales_invoice.get("custom_has_services"):
            service_status = (
                "✅ Recognized"
                if not sales_invoice.get("custom_service_vat_pending")
                else "⏳ Pending Payment"
            )
            summary.append(f"Service VAT: {service_status}")

        return "\n".join(summary)

    def create_vat_gl_entry(self):
        """
        Create a Journal Entry when VAT is recognized on payment.

        For recognition_type = "Payment" (VAT on services, recognized when payment received):
          Dr: VAT Receivable (input VAT waiting to be transferred)
          Cr: VAT Payable (output VAT liability)

        The JE is linked back to this Thai VAT Recognition for audit trail.
        """
        if not self.vat_amount or self.vat_amount <= 0:
            return

        if self.recognition_type != "Payment":
            return  # Goods: VAT recognized on delivery via normal SI GL entries

        # Get VAT accounts
        vat_receivable = self._get_vat_account("vat_receivable")
        vat_payable = self._get_vat_account("vat_payable")
        if not vat_receivable or not vat_payable:
            return

        # Get cost center from Sales Invoice
        cost_center = None
        if self.sales_invoice:
            cost_center = frappe.db.get_value("Sales Invoice", self.sales_invoice, "cost_center")

        je_date = self.recognition_date or today()
        remark = _("VAT recognized on payment for {0}").format(
            self.sales_invoice or self.trigger_document or ""
        )

        je = frappe.new_doc("Journal Entry")
        je.voucher_type = "Journal Entry"
        je.posting_date = je_date
        je.company = self.company
        je.user_remark = remark

        # Dr: VAT Receivable, Cr: VAT Payable
        #
        # The VAT accounts are not the accounts of the customer: a party on
        # them would open an outstanding amount for the customer.  ERPNext
        # only accepts a party on a receivable, a payable or an equity
        # account, so the rows carry none.  A site that models a VAT
        # account as a receivable or a payable gets the requirement of
        # ERPNext waived instead.
        vat_rows = [
            {
                "account": vat_receivable,
                "debit": flt(self.vat_amount),
                "credit": 0,
            },
            {
                "account": vat_payable,
                "debit": 0,
                "credit": flt(self.vat_amount),
            },
        ]

        if any(
            frappe.db.get_value("Account", row["account"], "account_type")
            in ("Receivable", "Payable")
            for row in vat_rows
        ):
            je.party_not_required = 1

        for row in vat_rows:
            je.append(
                "accounts",
                {
                    "account": row["account"],
                    "debit_in_account_currency": flt(row["debit"]),
                    "credit_in_account_currency": flt(row["credit"]),
                    "cost_center": cost_center,
                    "user_remark": remark,
                },
            )

        je.insert(ignore_permissions=True)
        je.submit()

        # The link to the entry of the ledger is written after the document
        # has been saved, so it needs the write of the database: a
        # recognition that is read again has to find the entry that it
        # reverses.
        self.db_set("journal_entry", je.name)

    def reverse_vat_gl_entry(self):
        """Cancel the linked Journal Entry when ThaiVATRecognition is cancelled."""
        if not self.journal_entry:
            return

        if not frappe.db.exists("Journal Entry", self.journal_entry):
            return

        je = frappe.get_doc("Journal Entry", self.journal_entry)
        if je.docstatus == 1:
            je.cancel()

    def update_thai_sales_vat(self):
        """Mark the related ThaiSalesVAT record as VAT Due (payment received)."""
        if not self.sales_invoice:
            return

        records = frappe.get_all(
            "Thai Sales VAT",
            filters={"sales_invoice": self.sales_invoice},
            fields=["name"],
        )
        for rec in records:
            doc = frappe.get_doc("Thai Sales VAT", rec.name)
            # If VAT was Undue (pending) and is now recognized on payment
            if doc.vat_type == "VAT Undue":
                doc.vat_type = "VAT Due"
                if self.trigger_document and self.trigger_document_type == "Payment Entry":
                    doc.payment_entry_reference = self.trigger_document
                doc.vat_conversion_date = self.recognition_date
                doc.save(ignore_permissions=True)

    def revert_thai_sales_vat(self):
        """Revert ThaiSalesVAT back to VAT Undue when recognition is cancelled."""
        if not self.sales_invoice:
            return

        records = frappe.get_all(
            "Thai Sales VAT",
            filters={"sales_invoice": self.sales_invoice},
            fields=["name"],
        )
        for rec in records:
            doc = frappe.get_doc("Thai Sales VAT", rec.name)
            if doc.vat_type == "VAT Due":
                doc.vat_type = "VAT Undue"
                doc.payment_entry_reference = None
                doc.vat_conversion_date = None
                doc.save(ignore_permissions=True)

    def _get_vat_account(self, account_type):
        """The VAT account of the company.

        The account of the company is the one of Print Designer.  The field of
        Thai Business Suite is read as a fallback, for the sites that carry
        it, and the name of the account is the last fallback.
        """
        company = self.company or frappe.defaults.get_default("company")
        if not company:
            return None

        if account_type == "vat_receivable":
            fields = ("default_input_vat_account", "tbs_default_vat_input_account")
            name_pattern = "%VAT%Receivable%"
        else:
            fields = ("default_output_vat_account", "tbs_default_vat_output_account")
            name_pattern = "%VAT%Payable%"

        # A field that the site does not carry is not read: the query of a
        # column that does not exist is an error of the database.
        try:
            meta = frappe.get_meta("Company")
        except Exception:
            meta = None

        for field in fields:
            if meta is not None and not meta.has_field(field):
                continue
            account = frappe.db.get_value("Company", company, field)
            if account:
                return account

        accounts = frappe.get_all(
            "Account",
            filters={
                "company": company,
                "account_name": ["like", name_pattern],
                "is_group": 0,
            },
            fields=["name"],
            limit=1,
        )
        if accounts:
            return accounts[0].name
        return None


def set_the_field_when_it_is_there(document: Any, fieldname: str, value: Any) -> bool:
    """Write the field of the document when the document carries it.

    The flags of the recognition live on the Sales Invoice and on its items.
    They are the fields that the site installs.  A field that the document
    does not carry is not written, so that the write leaves no value behind
    that the save would drop.

    Args:
            document: the document that carries the field.
            fieldname: the name of the field.
            value: the value of the field.

    Returns:
            True when the field was written, and False when the document does not
            carry the field.
    """
    meta = getattr(document, "meta", None)
    if meta is None or not meta.has_field(fieldname):
        return False

    document.set(fieldname, value)
    return True


@frappe.whitelist(methods=["POST"])
def create_vat_recognition(
    sales_invoice,
    recognition_type,
    trigger_document_type,
    trigger_document,
    items_data=None,
):
    """Create Thai VAT Recognition record"""

    require_doctype_permission("Thai VAT Recognition", "create")
    require_document_read("Sales Invoice", sales_invoice)

    if isinstance(items_data, str):
        import json

        try:
            items_data = json.loads(items_data)
        except json.JSONDecodeError:
            frappe.throw(_("The items are not valid JSON"), frappe.ValidationError)

    vat_recognition = frappe.new_doc("Thai VAT Recognition")
    vat_recognition.sales_invoice = sales_invoice
    vat_recognition.recognition_type = recognition_type
    vat_recognition.trigger_document_type = trigger_document_type
    vat_recognition.trigger_document = trigger_document
    vat_recognition.recognition_date = getdate()

    # Add items
    if items_data:
        for item_data in items_data:
            vat_recognition.append(
                "items",
                {
                    "sales_invoice_item": item_data.get("sales_invoice_item"),
                    "item_code": item_data.get("item_code"),
                    "item_name": item_data.get("item_name"),
                    "qty": item_data.get("qty"),
                    "rate": item_data.get("rate"),
                    "amount": item_data.get("amount"),
                    "tax_rate": item_data.get("tax_rate", 7.0),
                    "vat_timing_type": item_data.get("vat_timing_type"),
                },
            )

    vat_recognition.save()
    vat_recognition.submit()

    return vat_recognition.name


@frappe.whitelist()
def get_vat_recognition_by_payment_entry(payment_entry: str | None = None) -> dict[str, Any] | None:
    """Return Thai VAT Recognition record linked to a Payment Entry for dashboard display."""
    # The recognitions of the site are only answered for a caller that may
    # read them.  The right of the doctype is asked before the records are
    # read, so that the answer of the request does not tell the caller that
    # the site holds a recognition of that payment entry.
    require_doctype_permission("Thai VAT Recognition", "read")

    if not payment_entry:
        return None

    # The recognition carries a company of its own, so the records are read
    # in the way that keeps the companies of the caller.
    records = frappe.get_list(
        "Thai VAT Recognition",
        filters={
            "trigger_document": payment_entry,
            "trigger_document_type": "Payment Entry",
        },
        fields=["name", "status", "vat_amount", "recognition_date", "sales_invoice"],
    )
    return records[0] if records else None


@frappe.whitelist(methods=["POST"])
def create_vat_recognition_from_payment(
    payment_entry: str,
    invoice_names: list[str] | str,
    recognition_date: str,
    vat_amount: float,
) -> str | None:
    """
    Create and submit a Thai VAT Recognition for the given Sales Invoices
    when a Payment Entry is received (VAT-on-payment for services).

    Called from payment_entry_thai.js dialog.
    """
    require_doctype_permission("Thai VAT Recognition", "create")
    require_document_read("Payment Entry", payment_entry)

    if isinstance(invoice_names, str):
        import json

        try:
            invoice_names = json.loads(invoice_names)
        except json.JSONDecodeError:
            frappe.throw(_("The invoice names are not valid JSON"), frappe.ValidationError)

    if not invoice_names:
        frappe.throw(_("No Sales Invoices selected."))

    # Get the first invoice to establish reference info (customer, company, etc.)
    first_si = frappe.get_doc("Sales Invoice", invoice_names[0])

    vat_recognition = frappe.new_doc("Thai VAT Recognition")
    vat_recognition.sales_invoice = invoice_names[0]
    vat_recognition.recognition_type = "Payment"
    vat_recognition.trigger_document_type = "Payment Entry"
    vat_recognition.trigger_document = payment_entry
    vat_recognition.recognition_date = getdate(recognition_date) if recognition_date else getdate()
    vat_recognition.customer = first_si.customer
    vat_recognition.customer_name = first_si.customer_name
    vat_recognition.company = first_si.company
    vat_recognition.posting_date = first_si.posting_date
    vat_recognition.vat_amount = flt(vat_amount)

    # Add items from the Sales Invoice(s) for services only
    for inv_name in invoice_names:
        si = frappe.get_doc("Sales Invoice", inv_name)
        for item in si.items:
            # Only include service items (custom_vat_timing_type == "Services")
            vat_timing = item.get("custom_vat_timing_type")
            if vat_timing == "Services":
                # Get tax rate from SI taxes child table
                tax_rate = 0
                for tax in si.taxes:
                    if tax.category == "Total" and tax.rate:
                        tax_rate = tax.rate
                        break
                vat_recognition.append(
                    "items",
                    {
                        "sales_invoice_item": item.name,
                        "item_code": item.item_code,
                        "item_name": item.item_name,
                        "qty": item.qty,
                        "rate": item.rate,
                        "amount": item.amount,
                        "tax_rate": tax_rate,
                        "vat_timing_type": "Services",
                    },
                )

    vat_recognition.save()
    vat_recognition.submit()

    return vat_recognition.name
