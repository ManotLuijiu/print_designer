# Copyright (c) 2026, Manot L. and contributors
# For license information, please see license.txt

import unittest
from typing import Any

import frappe
from frappe.utils import flt, nowdate


class TestVATOffsetEntry(unittest.TestCase):
    """Test cases for VAT Offset Entry — AR-AP Netting"""

    PARTY_NAME = "VOE Test Party"

    @classmethod
    def setUpClass(cls):
        # The test needs a company with a chart of accounts, a party that is
        # both a customer and a supplier, an item and the tax/cash accounts.
        cls.company = cls._pick_company()
        cls.company_currency = (
            frappe.db.get_value("Company", cls.company, "default_currency") or "THB"
        )
        cls.customer = cls._pick_or_create_party()
        cls.supplier = cls.customer
        cls.item = cls._pick_item()
        cls.tax_account = cls._pick_account("Tax")
        cls.cash_account = cls._pick_account("Bank")

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
        """A party that exists as a customer and as a supplier.

        The offsetting requires the same party on both invoices, so an
        existing pair is preferred and a test pair is created otherwise.
        """
        customers = frappe.get_all("Customer", pluck="name", limit=500)
        suppliers = set(frappe.get_all("Supplier", pluck="name", limit=500))
        for customer in customers:
            if customer in suppliers:
                return customer

        cls._create_party(cls.PARTY_NAME)

        return cls.PARTY_NAME

    @classmethod
    def _create_party(cls, name):
        """Create the customer and the supplier with the same name."""
        if not frappe.db.exists("Customer", name):
            frappe.get_doc(
                {
                    "doctype": "Customer",
                    "customer_name": name,
                    "customer_type": "Company",
                    "customer_group": cls._pick_group("Customer Group"),
                    "territory": cls._pick_territory(),
                }
            ).insert(ignore_permissions=True)

        if not frappe.db.exists("Supplier", name):
            frappe.get_doc(
                {
                    "doctype": "Supplier",
                    "supplier_name": name,
                    "supplier_group": cls._pick_group("Supplier Group"),
                    "territory": cls._pick_territory(),
                    "is_transporter": 0,
                    "is_company": 1,
                }
            ).insert(ignore_permissions=True)

    @classmethod
    def _pick_group(cls, doctype):
        groups = frappe.get_all(doctype, pluck="name", limit=50)
        for group in groups:
            if group.startswith("_Test"):
                return group

        if not groups:
            raise unittest.SkipTest(f"no {doctype} on this site")

        return groups[0]

    @classmethod
    def _pick_territory(cls):
        territories = frappe.get_all("Territory", pluck="name", limit=50)
        for territory in territories:
            if territory.startswith("_Test"):
                return territory

        if not territories:
            raise unittest.SkipTest("no territory on this site")

        return territories[0]

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
        # Clean up any test docs from previous runs
        for dt in [
            "Sales Invoice",
            "Purchase Invoice",
            "VAT Offset Entry",
            "Journal Entry",
        ]:
            for doc in frappe.get_all(dt, filters={"naming_series": "VOE-.TEST.-"}, limit=10):
                try:
                    doc_obj: Any = frappe.get_doc(dt, doc.name)
                    if doc_obj.docstatus == 1:
                        doc_obj.cancel()
                    frappe.delete_doc(dt, doc.name, force=True)
                except Exception:
                    pass

    def tearDown(self):
        # Clean up test docs
        for dt in [
            "Sales Invoice",
            "Purchase Invoice",
            "VAT Offset Entry",
            "Journal Entry",
        ]:
            for doc in frappe.get_all(dt, filters={"naming_series": "VOE-.TEST.-"}, limit=10):
                try:
                    doc_obj: Any = frappe.get_doc(dt, doc.name)
                    if doc_obj.docstatus == 1:
                        doc_obj.cancel()
                    frappe.delete_doc(dt, doc.name, force=True)
                except Exception:
                    pass

    def _make_sales_invoice(self, amount, vat_rate=7, customer=None) -> Any:
        """Create and submit a Sales Invoice"""
        si: Any = frappe.get_doc(
            {
                "doctype": "Sales Invoice",
                "naming_series": "VOE-.TEST.-",
                "customer": customer or self.customer,
                "company": self.company,
                "currency": self.company_currency,
                "taxes": [],
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
        # Add VAT
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

    def _make_purchase_invoice(self, amount, vat_rate=7, supplier=None) -> Any:
        """Create and submit a Purchase Invoice"""
        pi: Any = frappe.get_doc(
            {
                "doctype": "Purchase Invoice",
                "naming_series": "VOE-.TEST.-",
                "supplier": supplier or self.supplier,
                "company": self.company,
                "currency": self.company_currency,
                # the Thai compliance requires the supplier invoice number
                "bill_no": "VOE-TEST-0001",
                "bill_date": nowdate(),
                "taxes": [],
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
        pi.append(
            "taxes",
            {
                "account_head": self.tax_account,
                "add_deduct_tax": "Add",
                "charge_type": "On Net Total",
                "rate": vat_rate,
                "description": "VAT {0}%".format(vat_rate),
            },
        )
        pi.insert()
        pi.submit()
        return pi

    def _make_voe(
        self,
        si_name,
        pi_name,
        mode="Partial Offset",
        diff_account=None,
        cash_account=None,
        insert=True,
    ) -> Any:
        """Create a VAT Offset Entry

        The document is only inserted when `insert` is set, the validation
        tests build the document and run the validation themselves.
        """
        voe: Any = frappe.get_doc(
            {
                "doctype": "VAT Offset Entry",
                "naming_series": "VOE-.TEST.-",
                "company": self.company,
                "party": self.customer,
                "offset_mode": mode,
                "sales_invoice": si_name,
                "purchase_invoice": pi_name,
                "difference_account": diff_account,
                "difference_label": "Material supply off-set",
                "cash_bank_account": (self.cash_account if cash_account is None else cash_account),
            }
        )
        if insert:
            voe.insert()
        return voe

    def _pick_difference_account(self) -> Any:
        """A leaf account that can carry the off-set difference.

        The account types differ per chart of accounts, so the accounts are
        filtered in Python. The receivable, payable, bank, cash and tax
        accounts are excluded, they are used by the off-set itself.
        """
        rows = frappe.get_all(
            "Account",
            filters={"company": self.company, "is_group": 0, "disabled": 0},
            fields=["name", "account_type"],
            limit=200,
        )
        preferred = (
            "Expense",
            "Income",
            "Liability",
            "Cost of Goods Sold",
            "Expenses Included In Asset Valuation",
            "Expenses Included In Valuation",
            "Other Expenses",
        )
        excluded = (
            "Receivable",
            "Payable",
            "Bank",
            "Cash",
            "Tax",
            "Equity",
            "Fixed Asset",
        )

        for row in rows:
            if row.account_type in preferred:
                return row.name

        for row in rows:
            if row.account_type not in excluded:
                return row.name

        raise unittest.SkipTest(f"no difference account in {self.company}")

    def test_partial_offset_ar_greater_than_ap(self):
        """Scenario: AR > AP, the difference is settled in cash"""
        # Create SI: 100 + 7 VAT
        si: Any = self._make_sales_invoice(100, vat_rate=7)
        ar_amount = flt(si.outstanding_amount)

        # Create PI: 50 + 7 VAT (the Thai compliance may add further taxes)
        pi: Any = self._make_purchase_invoice(50, vat_rate=7)
        ap_amount = flt(pi.outstanding_amount)

        self.assertGreater(ar_amount, ap_amount)

        diff_account = self._pick_difference_account()

        # Create and submit VOE
        voe: Any = self._make_voe(
            si.name, pi.name, mode="Partial Offset", diff_account=diff_account
        )
        voe.fetch_invoice_details()
        voe.calculate_offset_amounts()

        expected_offset = min(ar_amount, ap_amount)
        expected_difference = abs(ar_amount - ap_amount)
        expected_cash = min(expected_offset, expected_difference)

        self.assertAlmostEqual(flt(voe.offset_amount), expected_offset, places=2)
        self.assertAlmostEqual(flt(voe.difference_amount), expected_difference, places=2)
        self.assertAlmostEqual(flt(voe.cash_amount), expected_cash, places=2)
        self.assertAlmostEqual(flt(voe.ar_outstanding), ar_amount, places=2)
        self.assertAlmostEqual(flt(voe.ap_outstanding), ap_amount, places=2)
        self.assertEqual(voe.ar_account, si.debit_to)
        self.assertEqual(voe.ap_account, pi.credit_to)

        voe.save()
        voe.submit()

        # Verify JE was created and linked
        self.assertTrue(voe.journal_entry)
        je: Any = frappe.get_doc("Journal Entry", voe.journal_entry)
        self.assertEqual(je.docstatus, 1)
        # Dr AP, Dr Cash, Cr AR -> the difference is settled in cash,
        # so no difference row is needed
        self.assertEqual(len(je.accounts), 3)

        # Verify JE rows
        accounts: Any = {row.account: row for row in je.accounts}
        self.assertAlmostEqual(
            flt(accounts[voe.ap_account].debit_in_account_currency),
            expected_offset,
            places=2,
        )
        self.assertAlmostEqual(
            flt(accounts[voe.ar_account].credit_in_account_currency),
            ar_amount,
            places=2,
        )
        self.assertAlmostEqual(
            flt(accounts[self.cash_account].debit_in_account_currency),
            expected_cash,
            places=2,
        )
        # the difference is fully settled in cash
        self.assertNotIn(diff_account, accounts)

        # the journal entry has to balance
        total_debit = sum(flt(row.debit_in_account_currency) for row in je.accounts)
        total_credit = sum(flt(row.credit_in_account_currency) for row in je.accounts)
        self.assertAlmostEqual(total_debit, total_credit, places=2)

        # AR should be linked to the sales invoice
        ar_row: Any = accounts[voe.ar_account]
        self.assertEqual(ar_row.reference_type, "Sales Invoice")
        self.assertEqual(ar_row.reference_name, si.name)

        # Verify SI outstanding was updated
        si.reload()
        self.assertEqual(flt(si.outstanding_amount), 0)

        # Verify PI outstanding was updated
        pi.reload()
        self.assertEqual(flt(pi.outstanding_amount), 0)

        # Test cancel
        voe.cancel()
        je.reload()
        self.assertEqual(je.docstatus, 2)  # Cancelled

    def test_partial_offset_difference_on_difference_account(self):
        """Scenario: the part of the difference that is not cash is booked
        on the difference account"""
        si: Any = self._make_sales_invoice(100, vat_rate=7)
        pi: Any = self._make_purchase_invoice(50, vat_rate=7)

        diff_account = self._pick_difference_account()

        voe: Any = self._make_voe(
            si.name, pi.name, mode="Partial Offset", diff_account=diff_account
        )
        voe.fetch_invoice_details()
        voe.calculate_offset_amounts()

        # only a part of the difference is settled in cash
        cash_amount = flt(voe.difference_amount) / 2
        voe.cash_amount = cash_amount
        voe.save()
        voe.submit()

        je: Any = frappe.get_doc("Journal Entry", voe.journal_entry)
        self.assertEqual(je.docstatus, 1)
        # Dr AP, Dr Difference, Dr Cash, Cr AR
        self.assertEqual(len(je.accounts), 4)

        accounts: Any = {row.account: row for row in je.accounts}
        expected_difference = flt(voe.difference_amount) - cash_amount
        self.assertAlmostEqual(
            flt(accounts[diff_account].debit_in_account_currency),
            expected_difference,
            places=2,
        )
        self.assertAlmostEqual(
            flt(accounts[self.cash_account].debit_in_account_currency),
            cash_amount,
            places=2,
        )

        # the journal entry has to balance
        total_debit = sum(flt(row.debit_in_account_currency) for row in je.accounts)
        total_credit = sum(flt(row.credit_in_account_currency) for row in je.accounts)
        self.assertAlmostEqual(total_debit, total_credit, places=2)

        voe.cancel()

    def test_full_offset_within_tolerance(self):
        """Scenario: AR == AP (within 0.50 tolerance = full offset)"""
        # Both same amount
        si: Any = self._make_sales_invoice(100, vat_rate=7)
        # Create PI with same base, same VAT
        pi: Any = self._make_purchase_invoice(100, vat_rate=7)

        self.assertAlmostEqual(flt(si.outstanding_amount), 107, places=2)
        self.assertAlmostEqual(flt(pi.outstanding_amount), 107, places=2)

        voe: Any = self._make_voe(si.name, pi.name, mode="Full Offset", diff_account=None)
        voe.fetch_invoice_details()
        voe.calculate_offset_amounts()
        self.assertEqual(flt(voe.offset_amount), 107)
        self.assertAlmostEqual(flt(voe.difference_amount), 0, places=2)
        self.assertEqual(voe.offset_mode, "Full Offset")

        # Full Offset should not require difference account
        # It should pass validation
        voe.save()
        voe.submit()
        self.assertTrue(voe.journal_entry)

    def test_validate_party_mismatch(self):
        """Validation: party on SI must match party on PI"""
        other_customer: Any = frappe.get_all(
            "Customer",
            filters={"name": ["!=", self.customer]},
            pluck="name",
            limit=1,
        )
        if not other_customer:
            self.skipTest("No alternative customer for party mismatch test")

        # the Sales Invoice is created for another customer
        si: Any = self._make_sales_invoice(100, vat_rate=7, customer=other_customer[0])
        pi: Any = self._make_purchase_invoice(50, vat_rate=7)

        voe: Any = self._make_voe(
            si.name,
            pi.name,
            mode="Partial Offset",
            diff_account=self._pick_difference_account(),
            insert=False,
        )
        voe.party = other_customer[0]

        with self.assertRaises(frappe.ValidationError) as ctx:
            voe.run_method("validate")
        self.assertIn("Party mismatch", str(ctx.exception))

    def test_validate_differences_exceeds_tolerance(self):
        """Validation: Full Offset mode fails if difference > 0.50"""
        si: Any = self._make_sales_invoice(100, vat_rate=7)
        pi: Any = self._make_purchase_invoice(50, vat_rate=7)

        voe: Any = self._make_voe(si.name, pi.name, mode="Full Offset", insert=False)
        voe.fetch_invoice_details()
        voe.calculate_offset_amounts()

        # Difference is bigger than 0.50, Full Offset is not allowed
        with self.assertRaises(frappe.ValidationError) as ctx:
            voe.run_method("validate")
        self.assertIn("Partial Offset", str(ctx.exception))

    def test_validate_difference_account_required_for_partial(self):
        """Validation: Partial Offset requires difference_account"""
        si: Any = self._make_sales_invoice(100, vat_rate=7)
        pi: Any = self._make_purchase_invoice(50, vat_rate=7)

        voe: Any = self._make_voe(
            si.name, pi.name, mode="Partial Offset", diff_account=None, insert=False
        )
        voe.fetch_invoice_details()
        voe.calculate_offset_amounts()
        # Remove difference_account after fetch
        voe.difference_account = None

        with self.assertRaises(frappe.ValidationError) as ctx:
            voe.run_method("validate")
        self.assertIn("Difference Account", str(ctx.exception))

    def test_validate_cash_account_required(self):
        """Validation: cash_bank_account is required"""
        si: Any = self._make_sales_invoice(100, vat_rate=7)
        pi: Any = self._make_purchase_invoice(50, vat_rate=7)

        voe: Any = self._make_voe(
            si.name,
            pi.name,
            mode="Partial Offset",
            diff_account=self._pick_difference_account(),
            cash_account="",
            insert=False,
        )
        voe.cash_bank_account = None
        voe.fetch_invoice_details()
        voe.calculate_offset_amounts()

        with self.assertRaises(frappe.ValidationError) as ctx:
            voe.run_method("validate")
        self.assertIn("Cash", str(ctx.exception))

    def test_validate_invoice_not_submitted(self):
        """Validation: both invoices must be submitted"""
        si: Any = self._make_sales_invoice(100, vat_rate=7)
        pi: Any = frappe.get_doc(
            {
                "doctype": "Purchase Invoice",
                "naming_series": "VOE-.TEST.-",
                "supplier": self.supplier,
                "company": self.company,
                "currency": self.company_currency,
                # the Thai compliance requires the supplier invoice number
                "bill_no": "VOE-TEST-0002",
                "bill_date": nowdate(),
                "items": [
                    {
                        "item_code": self.item,
                        "qty": 1,
                        "rate": 50,
                        "amount": 50,
                    }
                ],
            }
        )
        pi.insert()
        # NOT submitted

        voe: Any = self._make_voe(
            si.name,
            pi.name,
            mode="Partial Offset",
            diff_account=self._pick_difference_account(),
            insert=False,
        )

        with self.assertRaises(frappe.ValidationError) as ctx:
            voe.run_method("validate")
        self.assertIn("submitted", str(ctx.exception).lower())
