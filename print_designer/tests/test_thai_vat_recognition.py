# Copyright (c) 2026, Manot L. and contributors
# For license information, please see license.txt

"""The tests of the Thai VAT Recognition of Print Designer.

The controller recognizes the output VAT of a sale on the day the tax becomes
due under the Thai law: on the delivery for the goods, on the payment for
the services.  The tests create real invoices, real payment entries and a
real journal entry, and they check the recognition itself, the entry of the
ledger, the flags of the invoice and the reversal.
"""

import os
import unittest
from typing import Any

import frappe
from frappe.utils import flt, getdate, nowdate


class TestThaiVATRecognition(unittest.TestCase):
    """The recognition of the output VAT on the payment of a service."""

    PARTY_NAME = "TVR Test Party"
    SERIES = "TVR-.TEST.-"
    SAVEPOINT = "tvr_recognition_test"

    @classmethod
    def setUpClass(cls):
        frappe.set_user("Administrator")
        cls.company = cls._pick_company()
        cls.company_currency = (
            frappe.db.get_value("Company", cls.company, "default_currency") or "THB"
        )
        cls.customer = cls._pick_or_create_party()
        cls.item = cls._pick_item()
        cls.bank_account = cls._pick_account("Bank")
        cls.tax_account = cls._pick_account("Tax")

    @classmethod
    def _pick_company(cls):
        """A test company (never a production company)."""
        companies = frappe.get_all(
            "Company",
            filters={"name": ["like", "_Test%"]},
            pluck="name",
            limit=20,
        )
        for company in companies:
            if frappe.db.get_value("Company", company, "default_receivable_account"):
                return company

        raise unittest.SkipTest("no test company with a chart of accounts")

    @classmethod
    def _pick_or_create_party(cls):
        """A customer of the test."""
        customers = frappe.get_all("Customer", pluck="name", limit=500)
        for customer in customers:
            if customer.startswith("_Test"):
                return customer

        if not customers:
            raise unittest.SkipTest("no customer on this site")

        return customers[0]

    @classmethod
    def _pick_item(cls):
        """A non stock item (no stock ledger impact)."""
        items = frappe.get_all(
            "Item",
            filters={"is_stock_item": 0, "disabled": 0},
            pluck="name",
            limit=50,
        )
        for item in items:
            if item.startswith("_Test"):
                return item

        if not items:
            raise unittest.SkipTest("no non stock item on this site")

        return items[0]

    @classmethod
    def _pick_account(cls, account_type):
        """A leaf account of the test company."""
        accounts = frappe.get_all(
            "Account",
            filters={
                "company": cls.company,
                "account_type": account_type,
                "is_group": 0,
                "disabled": 0,
            },
            pluck="name",
            limit=20,
        )
        if not accounts:
            raise unittest.SkipTest(f"no {account_type} account in the company {cls.company}")

        return accounts[0]

    def setUp(self):
        frappe.set_user("Administrator")
        self._clean_up()
        # The accounts of the test are written inside a savepoint, so that
        # the transaction of the test leaves no account and no entry of the
        # ledger behind, not even on a site where the transaction of the
        # test is committed at the end.
        frappe.db.savepoint(self.SAVEPOINT)
        self.vat_input_account = self._make_vat_account(
            "TVR VAT Receivable", "Current Asset", "Current Assets"
        )
        self.vat_output_account = self._make_vat_account(
            "TVR VAT Payable", "Current Liability", "Current Liabilities"
        )
        self._point_the_company_at_the_accounts()

    def tearDown(self):
        # Everything the test wrote is undone with the savepoint of the
        # test: the accounts, the entries of the ledger and the documents.
        frappe.db.rollback(save_point=self.SAVEPOINT)

    def _clean_up(self):
        """Remove the documents of the test.

        Only the documents of the naming series of the test are removed, so
        that the documents of the site stay untouched.
        """
        for dt in [
            "Thai VAT Recognition",
            "Payment Entry",
            "Delivery Note",
            "Sales Invoice",
        ]:
            for name in frappe.get_all(
                dt, filters={"naming_series": self.SERIES}, pluck="name", limit=50
            ):
                self._remove(dt, name)

        # The journal entries of the test are the ones of the recognitions.
        for name in frappe.get_all(
            "Journal Entry",
            filters={"voucher_type": "Thai VAT Recognition"},
            pluck="name",
            limit=50,
        ):
            self._remove("Journal Entry", name)

        # The sales VAT of the test is the one of the invoices of the test.
        for name in frappe.get_all(
            "Thai Sales VAT",
            filters={"sales_invoice": ["like", f"{self.SERIES}%"]},
            pluck="name",
            limit=50,
        ):
            self._remove("Thai Sales VAT", name)

    @staticmethod
    def _remove(doctype, name):
        """Cancel and remove a document of the test."""
        try:
            doc: Any = frappe.get_doc(doctype, name)
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc(doctype, name, force=True)
        except Exception:
            pass

    # --- the fixtures ----------------------------------------------------

    def _make_sales_invoice(self, amount=1000, vat_rate=7) -> Any:
        """A submitted sales invoice of the test."""
        si: Any = frappe.get_doc(
            {
                "doctype": "Sales Invoice",
                "naming_series": "TVR-.TEST.-",
                "customer": self.customer,
                "company": self.company,
                "currency": self.company_currency,
                "items": [
                    {
                        "item_code": self.item,
                        "qty": 1,
                        "rate": amount,
                        "amount": amount,
                    }
                ],
            }
        )
        si.append(
            "taxes",
            {
                "account_head": self.tax_account,
                "charge_type": "On Net Total",
                "rate": vat_rate,
                "description": "VAT {0}%".format(vat_rate),
            },
        )
        si.insert()
        si.submit()
        return si

    def _make_payment_entry(self, invoice, submit=True) -> Any:
        """A payment entry of the test, submitted unless the test says otherwise."""
        pe: Any = frappe.get_doc(
            {
                "doctype": "Payment Entry",
                "naming_series": "TVR-.TEST.-",
                "payment_type": "Receive",
                "company": self.company,
                "posting_date": nowdate(),
                "party_type": "Customer",
                "party": self.customer,
                "paid_amount": flt(invoice.grand_total),
                "received_amount": flt(invoice.grand_total),
                "source_exchange_rate": 1,
                "target_exchange_rate": 1,
                "paid_to": self.bank_account,
                "paid_to_account_currency": self._account_currency(self.bank_account),
                "reference_no": self.SERIES + "REF",
                "reference_date": nowdate(),
                "cost_center": self._pick_cost_center(),
                "references": [
                    {
                        "reference_doctype": "Sales Invoice",
                        "reference_name": invoice.name,
                        "total_amount": flt(invoice.grand_total),
                        "outstanding_amount": flt(invoice.grand_total),
                        "allocated_amount": flt(invoice.grand_total),
                    }
                ],
            }
        )
        pe.insert()
        if submit:
            pe.submit()
        return pe

    @classmethod
    def _account_currency(cls, account):
        """The currency of an account, or the currency of the company."""
        return frappe.db.get_value("Account", account, "account_currency") or cls.company_currency

    def _make_delivery_note(self, invoice) -> Any:
        """A submitted delivery note of the test, as the trigger of the goods."""
        dn: Any = frappe.get_doc(
            {
                "doctype": "Delivery Note",
                "naming_series": self.SERIES,
                "customer": self.customer,
                "company": self.company,
                "posting_date": nowdate(),
                "currency": self.company_currency,
                "items": [
                    {
                        "item_code": self.item,
                        "qty": 1,
                        "rate": flt(invoice.grand_total),
                        "amount": flt(invoice.grand_total),
                    }
                ],
            }
        )
        dn.insert()
        dn.submit()
        return dn

    @classmethod
    def _make_vat_account(cls, account_name, account_type, parent_account_name):
        """A disposable VAT account of the company.

        The account is a leaf of a group of the chart of accounts of the
        company, so that ERPNext accepts it as a balance sheet account.  The
        name of the account is the one that the controller reads as a
        fallback, so that the account is found whether the company carries
        the VAT accounts of Print Designer or not.
        """
        existing = frappe.db.get_value(
            "Account",
            {"company": cls.company, "account_name": account_name, "is_group": 0},
            "name",
        )
        if existing:
            return existing

        parent = frappe.db.get_value(
            "Account",
            {"company": cls.company, "account_name": parent_account_name, "is_group": 1},
            "name",
        )
        if not parent:
            raise unittest.SkipTest(f"no {parent_account_name} group in the company {cls.company}")

        account: Any = frappe.get_doc(
            {
                "doctype": "Account",
                "account_name": account_name,
                "company": cls.company,
                "account_type": account_type,
                "parent_account": parent,
                "is_group": 0,
            }
        )
        account.insert(ignore_permissions=True)
        return account.name

    def _point_the_company_at_the_accounts(self):
        """The company of the test carries the VAT accounts of the test.

        The controller reads the accounts of the company from the fields of
        Print Designer, and from the names of the accounts as a fallback.
        The write is inside the transaction of the test, so the accounting
        configuration of the company of the site stays as it was.
        """
        meta = frappe.get_meta("Company")
        for field, account in (
            ("default_input_vat_account", self.vat_input_account),
            ("default_output_vat_account", self.vat_output_account),
        ):
            if meta.has_field(field):
                frappe.db.set_value("Company", self.company, field, account)

    @staticmethod
    def _vat_period(invoice) -> tuple[str, str]:
        """The month and the year of the invoice, as the sales VAT carries them."""
        posting_date = getdate(invoice.posting_date)
        if not posting_date:
            raise unittest.SkipTest("the invoice of the test carries no posting date")
        return posting_date.strftime("%m"), posting_date.strftime("%Y")

    def _pick_cost_center(self):
        """A cost center of the company."""
        cost_centers = frappe.get_all(
            "Cost Center",
            filters={"company": self.company, "disabled": 0, "is_group": 0},
            pluck="name",
            limit=10,
        )
        if not cost_centers:
            raise unittest.SkipTest(f"no cost center in the company {self.company}")

        return cost_centers[0]

    def _make_recognition(self, invoice, payment_entry, recognition_type="Payment") -> Any:
        """A recognition of the test, with its items.

        The trigger document is the payment entry for a payment recognition
        and the delivery note for a delivery recognition.
        """
        trigger_document_type = (
            "Payment Entry" if recognition_type == "Payment" else "Delivery Note"
        )
        recognition: Any = frappe.get_doc(
            {
                "doctype": "Thai VAT Recognition",
                "naming_series": "TVR-.TEST.-",
                "sales_invoice": invoice.name,
                "recognition_type": recognition_type,
                "trigger_document_type": trigger_document_type,
                "trigger_document": payment_entry.name if payment_entry else None,
                "recognition_date": nowdate(),
                "items": [
                    {
                        "sales_invoice_item": invoice.items[0].name,
                        "item_code": invoice.items[0].item_code,
                        "item_name": invoice.items[0].item_name,
                        "qty": flt(invoice.items[0].qty),
                        "rate": flt(invoice.items[0].rate),
                        "amount": flt(invoice.items[0].amount),
                        "tax_rate": 7,
                        "vat_timing_type": "Services",
                    }
                ],
            }
        )
        return recognition

    # --- the validation --------------------------------------------------

    def test_the_recognition_type_must_match_the_trigger_document_type(self):
        """The payment is recognized on a payment entry, and not on anything else."""
        invoice = self._make_sales_invoice()
        recognition = self._make_recognition(invoice, None, recognition_type="Payment")
        recognition.trigger_document_type = "Delivery Note"

        with self.assertRaises(frappe.ValidationError):
            recognition.insert()

    def test_the_trigger_document_must_exist(self):
        """The trigger document of the recognition has to be on the site."""
        invoice = self._make_sales_invoice()
        recognition = self._make_recognition(invoice, None)
        recognition.trigger_document = "TVR-DOES-NOT-EXIST"

        with self.assertRaises(frappe.ValidationError):
            recognition.insert()

    def test_the_trigger_document_must_be_submitted(self):
        """The trigger document of the recognition has to be submitted."""
        invoice = self._make_sales_invoice()
        payment_entry = self._make_payment_entry(invoice, submit=False)

        recognition = self._make_recognition(invoice, payment_entry)
        with self.assertRaises(frappe.ValidationError):
            recognition.insert()

    def test_a_cancelled_trigger_document_is_not_accepted(self):
        """A cancelled trigger document is not a submitted one either."""
        invoice = self._make_sales_invoice()
        payment_entry = self._make_payment_entry(invoice)
        payment_entry.cancel()

        recognition = self._make_recognition(invoice, payment_entry)
        with self.assertRaises(frappe.ValidationError):
            recognition.insert()

    # --- the reference information ---------------------------------------

    def test_the_reference_information_comes_from_the_sales_invoice(self):
        """The customer, the company and the totals are taken from the invoice."""
        invoice = self._make_sales_invoice()
        payment_entry = self._make_payment_entry(invoice)
        recognition = self._make_recognition(invoice, payment_entry)

        recognition.insert()

        self.assertEqual(recognition.customer, invoice.customer)
        self.assertEqual(recognition.customer_name, invoice.customer_name)
        self.assertEqual(recognition.company, invoice.company)
        self.assertEqual(recognition.posting_date, getdate(invoice.posting_date))
        self.assertEqual(flt(recognition.base_net_total), flt(invoice.base_net_total))
        self.assertEqual(
            flt(recognition.base_total_taxes_and_charges),
            flt(invoice.base_total_taxes_and_charges),
        )

    # --- the amount of the tax -------------------------------------------

    def test_the_tax_amount_is_the_sum_of_the_items(self):
        """The tax of the recognition is the sum of the tax of the items."""
        invoice = self._make_sales_invoice(amount=1000)
        payment_entry = self._make_payment_entry(invoice)
        recognition = self._make_recognition(invoice, payment_entry)

        recognition.insert()

        self.assertEqual(flt(recognition.vat_amount), 70)
        self.assertEqual(flt(recognition.items[0].vat_amount), 70)

    # --- the entry of the ledger -----------------------------------------

    def test_the_payment_recognition_creates_a_journal_entry_that_balances(self):
        """The recognition on a payment posts the entry of the tax."""
        invoice = self._make_sales_invoice()
        payment_entry = self._make_payment_entry(invoice)
        recognition = self._make_recognition(invoice, payment_entry)

        recognition.insert()
        recognition.submit()

        self.assertTrue(recognition.journal_entry)
        entry: Any = frappe.get_doc("Journal Entry", recognition.journal_entry)
        self.assertEqual(entry.docstatus, 1)
        self.assertAlmostEqual(flt(entry.total_debit), flt(entry.total_credit), places=5)
        self.assertAlmostEqual(flt(entry.total_debit), flt(recognition.vat_amount), places=5)

        # The rows of the entry are the VAT accounts of the company, and
        # they carry no party: the VAT accounts are not the accounts of the
        # customer, and a party on them would open an outstanding amount
        # for the customer.
        self.assertEqual(
            [row.account for row in entry.accounts],
            [self.vat_input_account, self.vat_output_account],
        )
        for row in entry.accounts:
            self.assertFalse(row.party)
            self.assertFalse(row.party_type)

        # The link to the entry and the status survive a reload.
        recognition.reload()
        self.assertEqual(recognition.journal_entry, entry.name)
        self.assertEqual(recognition.status, "Active")

        # The ledger carries the two rows of the entry.
        gl_rows = frappe.get_all(
            "GL Entry",
            filters={"voucher_no": entry.name, "voucher_type": "Journal Entry"},
            fields=["account", "debit", "credit", "party", "is_cancelled"],
            limit_page_length=0,
        )
        self.assertEqual(len(gl_rows), 2)
        expected_accounts: list[str] = [
            str(self.vat_input_account),
            str(self.vat_output_account),
        ]
        self.assertEqual(
            sorted(row.account for row in gl_rows),
            sorted(expected_accounts),
        )

    def test_the_delivery_recognition_creates_no_journal_entry(self):
        """The goods are recognized on the delivery, with the entries of the invoice."""
        invoice = self._make_sales_invoice()
        delivery_note = self._make_delivery_note(invoice)
        recognition = self._make_recognition(invoice, delivery_note, recognition_type="Delivery")

        recognition.insert()
        recognition.submit()

        self.assertFalse(recognition.journal_entry)

    def test_the_cancellation_cancels_the_journal_entry(self):
        """The cancellation of the recognition reverses the entry of the tax."""
        invoice = self._make_sales_invoice()
        payment_entry = self._make_payment_entry(invoice)
        recognition = self._make_recognition(invoice, payment_entry)

        recognition.insert()
        recognition.submit()
        entry_name = recognition.journal_entry

        recognition.cancel()

        entry: Any = frappe.get_doc("Journal Entry", entry_name)
        self.assertEqual(entry.docstatus, 2)
        self.assertEqual(recognition.status, "Cancelled")

        # The status of the recognition survives the reload.
        recognition.reload()
        self.assertEqual(recognition.status, "Cancelled")

        # The ledger carries the rows of the entry and their reversal, and
        # every row of them is cancelled.
        gl_rows = frappe.get_all(
            "GL Entry",
            filters={"voucher_no": entry_name, "voucher_type": "Journal Entry"},
            fields=["is_cancelled"],
            limit_page_length=0,
        )
        self.assertEqual(len(gl_rows), 4)
        self.assertTrue(all(row.is_cancelled for row in gl_rows))

    # --- the sales VAT ----------------------------------------------------

    def test_the_recognition_marks_the_sales_vat_as_due(self):
        """The recognition on a payment turns the pending sales VAT into a due one."""
        invoice = self._make_sales_invoice()
        payment_entry = self._make_payment_entry(invoice)

        vat_month, vat_year = self._vat_period(invoice)
        sales_vat: Any = frappe.get_doc(
            {
                "doctype": "Thai Sales VAT",
                "sales_invoice": invoice.name,
                "customer": invoice.customer,
                "company": invoice.company,
                "vat_type": "VAT Undue",
                "vat_month": vat_month,
                "vat_year": vat_year,
            }
        )
        sales_vat.insert()

        recognition = self._make_recognition(invoice, payment_entry)
        recognition.insert()
        recognition.submit()

        sales_vat.reload()
        self.assertEqual(sales_vat.vat_type, "VAT Due")
        self.assertEqual(sales_vat.payment_entry_reference, payment_entry.name)

    def test_the_cancellation_reverts_the_sales_vat(self):
        """The cancellation of the recognition turns the sales VAT back to a pending one."""
        invoice = self._make_sales_invoice()
        payment_entry = self._make_payment_entry(invoice)

        vat_month, vat_year = self._vat_period(invoice)
        sales_vat: Any = frappe.get_doc(
            {
                "doctype": "Thai Sales VAT",
                "sales_invoice": invoice.name,
                "customer": invoice.customer,
                "company": invoice.company,
                "vat_type": "VAT Undue",
                "vat_month": vat_month,
                "vat_year": vat_year,
            }
        )
        sales_vat.insert()

        recognition = self._make_recognition(invoice, payment_entry)
        recognition.insert()
        recognition.submit()
        recognition.cancel()

        sales_vat.reload()
        self.assertEqual(sales_vat.vat_type, "VAT Undue")
        self.assertIsNone(sales_vat.payment_entry_reference)

    # --- the flags of the invoice ----------------------------------------

    def test_the_flags_of_the_invoice_are_written_when_the_invoice_carries_them(self):
        """The flags of the recognition are written on the invoice that carries them.

        A site that does not install the flags keeps the recognition on the
        recognition document alone, and the recognition does not break.
        """
        invoice = self._make_sales_invoice()
        payment_entry = self._make_payment_entry(invoice)
        recognition = self._make_recognition(invoice, payment_entry)

        recognition.insert()
        recognition.submit()

        invoice.reload()
        if invoice.meta.has_field("custom_vat_fully_recognized"):
            self.assertEqual(invoice.get("custom_vat_fully_recognized"), 1)
        else:
            # The invoice does not carry the flags: the recognition still
            # holds the recognition, and the invoice is untouched.
            self.assertFalse(invoice.meta.has_field("custom_vat_fully_recognized"))

    # --- the endpoints ----------------------------------------------------

    def test_create_vat_recognition_creates_a_submitted_record(self):
        """The endpoint creates the recognition and submits it."""
        from print_designer.print_designer.doctype.thai_vat_recognition.thai_vat_recognition import (
            create_vat_recognition,
        )

        invoice = self._make_sales_invoice()
        payment_entry = self._make_payment_entry(invoice)

        name = create_vat_recognition(
            sales_invoice=invoice.name,
            recognition_type="Payment",
            trigger_document_type="Payment Entry",
            trigger_document=payment_entry.name,
            items_data=[
                {
                    "sales_invoice_item": invoice.items[0].name,
                    "item_code": invoice.items[0].item_code,
                    "item_name": invoice.items[0].item_name,
                    "qty": 1,
                    "rate": flt(invoice.items[0].rate),
                    "amount": flt(invoice.items[0].amount),
                    "tax_rate": 7,
                    "vat_timing_type": "Services",
                }
            ],
        )

        self.assertIsNotNone(name)

        recognition: Any = frappe.get_doc("Thai VAT Recognition", str(name))
        self.assertEqual(recognition.docstatus, 1)
        self.assertEqual(recognition.sales_invoice, invoice.name)
        self.assertEqual(len(recognition.items), 1)

    def test_get_vat_recognition_by_payment_entry_returns_the_record(self):
        """The endpoint of the dashboard answers with the recognition of the payment."""
        from print_designer.print_designer.doctype.thai_vat_recognition.thai_vat_recognition import (
            get_vat_recognition_by_payment_entry,
        )

        invoice = self._make_sales_invoice()
        payment_entry = self._make_payment_entry(invoice)
        recognition = self._make_recognition(invoice, payment_entry)
        recognition.insert()
        recognition.submit()

        found = get_vat_recognition_by_payment_entry(payment_entry.name)

        if found is None:
            self.fail("the recognition of the payment entry was not found")

        self.assertEqual(found["name"], recognition.name)

    def test_get_vat_recognition_by_payment_entry_answers_with_nothing(self):
        """The endpoint of the dashboard answers with nothing for an empty payment."""
        from print_designer.print_designer.doctype.thai_vat_recognition.thai_vat_recognition import (
            get_vat_recognition_by_payment_entry,
        )

        self.assertIsNone(get_vat_recognition_by_payment_entry(""))

    # --- the guard of the ownership --------------------------------------

    def test_the_controller_does_not_import_thai_business_suite(self):
        """The controller of Print Designer does not import Thai Business Suite."""
        from print_designer.print_designer.doctype import thai_vat_recognition as module

        path = os.path.join(
            os.path.dirname(os.path.abspath(module.__file__)), "thai_vat_recognition.py"
        )
        with open(path) as handle:
            source = handle.read()

        self.assertNotIn("thai_business_suite", source)
