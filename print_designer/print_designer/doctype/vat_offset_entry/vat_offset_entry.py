# Copyright (c) 2026, Manot L. and contributors
# For license information, please see license.txt

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

from print_designer.custom.document_permission import has_document_permission


class VATOffsetEntry(Document):
    """
    VAT Offset Entry — AR-AP Netting for Thai VAT

    When a customer is also a supplier, they often net AR against AP and only
    pay the difference. This DocType creates a single Journal Entry that:
    - Clears the Purchase Invoice (AP) by the off-set amount
    - Clears the Sales Invoice (AR) in full
    - Posts the difference to a user-selected account
    - Records the actual cash movement
    """

    # The DocType fields, Frappe assigns them on the instance when the
    # document is loaded. The defaults only describe the fields for the
    # type checker, they are never written to the database.
    sales_invoice: str = ""
    purchase_invoice: str = ""
    company: str = ""
    party: str = ""
    offset_mode: str = ""
    difference_account: str = ""
    difference_label: str = ""
    cash_bank_account: str = ""
    remark: str = ""
    posting_date: str = ""
    ar_outstanding: float = 0.0
    ap_outstanding: float = 0.0
    ar_account: str = ""
    ap_account: str = ""
    offset_amount: float = 0.0
    difference_amount: float = 0.0
    cash_amount: float = 0.0
    journal_entry: str = ""

    def validate(self):
        self.validate_invoices()
        self.validate_same_party()
        self.validate_same_company()
        self.validate_outstanding_amounts()
        self.validate_offset_mode()
        self.validate_cash_account()

    def validate_invoices(self):
        """Both invoices must be submitted"""
        for field, label in [
            ("sales_invoice", "Sales Invoice"),
            ("purchase_invoice", "Purchase Invoice"),
        ]:
            docname = self.get(field)
            if not docname:
                frappe.throw(_("{0} is required").format(label))
            docstatus = frappe.db.get_value(
                "Sales Invoice" if field == "sales_invoice" else "Purchase Invoice",
                str(docname),
                "docstatus",
            )
            if docstatus != 1:
                frappe.throw(_("{0} {1} must be submitted").format(label, docname))

    def validate_same_party(self):
        """Party must match on both invoices"""
        if not (self.sales_invoice and self.purchase_invoice):
            return

        si_party = frappe.db.get_value("Sales Invoice", self.sales_invoice, "customer")
        pi_party = frappe.db.get_value("Purchase Invoice", self.purchase_invoice, "supplier")
        if si_party != pi_party:
            frappe.throw(
                _(
                    "Party mismatch: Sales Invoice party is '{0}' but "
                    "Purchase Invoice party is '{1}'. "
                    "Both must be the same party."
                ).format(si_party, pi_party)
            )

        # Also validate self.party field matches
        if self.party and self.party != si_party:
            frappe.throw(
                _(
                    "Party '{0}' does not match the party on Sales Invoice "
                    "('{1}') and Purchase Invoice ('{2}')."
                ).format(self.party, si_party, pi_party)
            )

    def validate_same_company(self):
        """Both invoices must belong to the same company"""
        if not (self.sales_invoice and self.purchase_invoice):
            return

        si_company = frappe.db.get_value("Sales Invoice", self.sales_invoice, "company")
        pi_company = frappe.db.get_value("Purchase Invoice", self.purchase_invoice, "company")
        if si_company != pi_company:
            frappe.throw(
                _(
                    "Company mismatch: Sales Invoice belongs to '{0}' but "
                    "Purchase Invoice belongs to '{1}'. "
                    "Both must be the same company."
                ).format(si_company, pi_company)
            )

        if self.company and self.company != si_company:
            frappe.throw(
                _(
                    "Company '{0}' does not match the company on Sales Invoice "
                    "('{1}') and Purchase Invoice ('{2}')."
                ).format(self.company, si_company, pi_company)
            )

    def validate_outstanding_amounts(self):
        """Both invoices must have outstanding > 0"""
        for field, label, doctype in [
            ("sales_invoice", "Sales Invoice", "Sales Invoice"),
            ("purchase_invoice", "Purchase Invoice", "Purchase Invoice"),
        ]:
            docname = self.get(field)
            if not docname:
                continue
            outstanding: Any = frappe.db.get_value(doctype, str(docname), "outstanding_amount")
            if flt(outstanding) <= 0:
                frappe.throw(
                    _("{0} {1} has no outstanding amount. It may already be fully paid.").format(
                        label, docname
                    )
                )

    def validate_offset_mode(self):
        """Validate offset mode specific rules"""
        if self.offset_mode == "Partial Offset":
            if not self.difference_account:
                frappe.throw(
                    _("Difference Account is required when Off-set Mode is 'Partial Offset'.")
                )
        elif self.offset_mode == "Full Offset":
            # Full offset: difference must be within tolerance (0.50 THB)
            if flt(self.difference_amount) > 0.5:
                frappe.throw(
                    _(
                        "Difference Amount ({0}) exceeds the Full Offset "
                        "tolerance of 0.50 THB. Use 'Partial Offset' mode instead."
                    ).format(self.difference_amount)
                )

    def validate_cash_account(self):
        """Cash/Bank account is required"""
        if not self.cash_bank_account:
            frappe.throw(_("Cash / Bank Account is required to record the payment movement."))

    def fetch_invoice_details(self):
        """Populate read-only fields from selected invoices"""
        if self.sales_invoice:
            si: Any = frappe.get_doc("Sales Invoice", self.sales_invoice)
            self.ar_outstanding = si.outstanding_amount
            self.ar_account = si.debit_to
            self.company = si.company
            self.party = si.customer

        if self.purchase_invoice:
            pi: Any = frappe.get_doc("Purchase Invoice", self.purchase_invoice)
            self.ap_outstanding = pi.outstanding_amount
            self.ap_account = pi.credit_to
            if not self.company:
                self.company = pi.company
            if not self.party:
                self.party = pi.supplier

        self.calculate_offset_amounts()

    def calculate_offset_amounts(self):
        """Calculate offset and difference amounts"""
        ar = flt(self.ar_outstanding)
        ap = flt(self.ap_outstanding)

        self.offset_amount = min(ar, ap)
        self.difference_amount = abs(ar - ap)

        # Auto-calculate cash amount if not set.
        # The cash movement can never exceed the difference, the rest of the
        # difference is booked on the difference account. This keeps the
        # journal entry balanced (see get_je_account_rows).
        if not self.cash_amount:
            self.cash_amount = min(self.offset_amount, self.difference_amount)

    def on_submit(self):
        if self.journal_entry:
            frappe.throw(
                _(
                    "VAT Offset Entry {0} already has a Journal Entry {1}. "
                    "It may have already been submitted."
                ).format(self.name, self.journal_entry)
            )
        self.make_journal_entry()
        self.db_set("journal_entry", self.journal_entry)

    def on_cancel(self):
        if self.journal_entry:
            je = frappe.get_doc("Journal Entry", self.journal_entry)
            if je.docstatus == 1:
                je.cancel()
            self.db_set("journal_entry", None)

    def make_journal_entry(self):
        """Create and submit the Journal Entry for this off-set"""
        accounts = self.get_je_account_rows()
        if not accounts:
            frappe.throw(_("No Journal Entry account rows could be generated."))

        default_cash_account = frappe.db.get_value("Company", self.company, "default_cash_account")
        cash_account = self.cash_bank_account or default_cash_account

        if not cash_account:
            frappe.throw(
                _(
                    "Cash / Bank Account is required. Please set a "
                    "Cash / Bank Account or ensure the Company has a "
                    "Default Cash Account."
                )
            )

        # Build remark from difference label and remark field
        remarks = []
        if self.difference_label:
            remarks.append(self.difference_label)
        if self.remark:
            remarks.append(self.remark)
        user_remark = " | ".join(remarks) if remarks else None

        je = frappe.get_doc(
            {
                "doctype": "Journal Entry",
                "voucher_type": "Journal Entry",
                "posting_date": self.posting_date or getdate(),
                "company": self.company,
                "user_remark": user_remark,
                "accounts": accounts,
            }
        )

        je.insert(ignore_permissions=True)
        je.submit()

        self.journal_entry = str(je.name)
        frappe.msgprint(
            _("Journal Entry {0} created successfully").format(je.name),
            alert=True,
        )

    def get_je_account_rows(self):
        """
        Build Journal Entry account rows for the off-set.

        The rows always balance: the off-set clears the payable and the
        receivable, the difference is settled in cash and the remainder of
        the difference is booked on the difference account.

        Scenario AR=107, AP=53.5 (receiving), offset=53.5, diff=53.5, cash=53.5:
            Dr AP Account        53.5   (clears PI payable)
            Dr Cash/Bank Account 53.5   (cash received from the customer)
            Cr AR Account       107.0   (clears SI receivable)

        Scenario AR=35, AP=53.5 (paying), offset=35, diff=18.5, cash=18.5:
            Dr AP Account        53.5   (clears PI payable in full)
            Cr AR Account        35.0   (clears SI receivable in full)
            Cr Cash/Bank Account 18.5   (cash paid out)

        The difference account carries the part of the difference that is not
        settled in cash (difference - cash).
        """
        offset_amount = flt(self.offset_amount)
        ar_outstanding = flt(self.ar_outstanding)
        ap_outstanding = flt(self.ap_outstanding)
        cash_amount = flt(self.cash_amount)
        diff_amount = flt(self.difference_amount)
        # the difference account carries the difference that is not settled in cash
        difference_row_amount = max(0, diff_amount - cash_amount)

        rows = []

        # Determine direction: AP > AR means we pay out, AR > AP means we receive
        receiving = ar_outstanding >= ap_outstanding

        if receiving:
            # We receive cash: Dr AP clears supplier invoice, Dr diff if any, Dr cash, Cr AR
            # Dr AP Account
            rows.append(
                {
                    "account": self.ap_account,
                    "debit_in_account_currency": offset_amount,
                    "credit_in_account_currency": 0,
                    "party_type": "Supplier",
                    "party": self.party,
                    "reference_type": "Purchase Invoice",
                    "reference_name": self.purchase_invoice,
                    "is_advance": "No",
                    "user_remark": "Off-set: clear AP {0}".format(self.purchase_invoice),
                }
            )

            # Dr Difference Account (only the part that is not settled in cash)
            if difference_row_amount > 0 and self.difference_account:
                rows.append(
                    {
                        "account": self.difference_account,
                        "debit_in_account_currency": difference_row_amount,
                        "credit_in_account_currency": 0,
                        "party_type": None,
                        "party": None,
                        "user_remark": self.difference_label or "Off-set difference (AR > AP)",
                    }
                )

            # Dr Cash / Bank Account
            if cash_amount > 0:
                rows.append(
                    {
                        "account": self.cash_bank_account,
                        "debit_in_account_currency": cash_amount,
                        "credit_in_account_currency": 0,
                        "party_type": None,
                        "party": None,
                        "user_remark": "Off-set payment received from {0}".format(self.party),
                    }
                )

            # Cr AR Account (clear in full)
            rows.append(
                {
                    "account": self.ar_account,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": ar_outstanding,
                    "party_type": "Customer",
                    "party": self.party,
                    "reference_type": "Sales Invoice",
                    "reference_name": self.sales_invoice,
                    "is_advance": "No",
                    "user_remark": "Off-set: clear AR {0}".format(self.sales_invoice),
                }
            )

        else:
            # We pay out cash (AP < AR): Dr AP, Cr AR, Cr diff, Cr cash
            # Dr AP Account
            rows.append(
                {
                    "account": self.ap_account,
                    "debit_in_account_currency": ap_outstanding,
                    "credit_in_account_currency": 0,
                    "party_type": "Supplier",
                    "party": self.party,
                    "reference_type": "Purchase Invoice",
                    "reference_name": self.purchase_invoice,
                    "is_advance": "No",
                    "user_remark": "Off-set: clear AP {0}".format(self.purchase_invoice),
                }
            )

            # Cr AR Account (partial clear = offset_amount)
            rows.append(
                {
                    "account": self.ar_account,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": offset_amount,
                    "party_type": "Customer",
                    "party": self.party,
                    "reference_type": "Sales Invoice",
                    "reference_name": self.sales_invoice,
                    "is_advance": "No",
                    "user_remark": "Off-set: partial AR clear {0}".format(self.sales_invoice),
                }
            )

            # Cr Difference Account (the excess we overpaid, not settled in cash)
            if difference_row_amount > 0 and self.difference_account:
                rows.append(
                    {
                        "account": self.difference_account,
                        "debit_in_account_currency": 0,
                        "credit_in_account_currency": difference_row_amount,
                        "party_type": None,
                        "party": None,
                        "user_remark": self.difference_label or "Off-set excess (AP > AR)",
                    }
                )

            # Cr Cash / Bank Account
            if cash_amount > 0:
                rows.append(
                    {
                        "account": self.cash_bank_account,
                        "debit_in_account_currency": 0,
                        "credit_in_account_currency": cash_amount,
                        "party_type": None,
                        "party": None,
                        "user_remark": "Off-set payment made to {0}".format(self.party),
                    }
                )

        return rows


@frappe.whitelist()
def get_invoice_info(doctype, docname):
    """Fetch outstanding and account info from an invoice for the form"""
    if doctype not in ("Sales Invoice", "Purchase Invoice"):
        return {}

    # The invoice carries the money of the company, so the details are only
    # answered for a caller that may read the invoice itself.  The right of
    # the document is asked before the document is read, so that an invoice
    # that is not on the site is refused like an invoice that the caller may
    # not read.
    if not has_document_permission(doctype, "read", docname):
        frappe.throw(
            _("Not permitted to read the {0} {1}").format(doctype, docname),
            frappe.PermissionError,
        )

    doc: Any = frappe.get_doc(doctype, docname)

    if doctype == "Sales Invoice":
        return {
            "ar_outstanding": doc.outstanding_amount,
            "ar_account": doc.debit_to,
            "company": doc.company,
            "party": doc.customer,
        }
    else:
        return {
            "ap_outstanding": doc.outstanding_amount,
            "ap_account": doc.credit_to,
            "company": doc.company,
            "party": doc.supplier,
        }
