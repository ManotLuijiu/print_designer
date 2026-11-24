"""The balance of an account, the way ERPNext computes it.

ERPNext keeps no balance on the Account doctype, so the balance of an account
is the sum of the entries of its ledger. The account API reads that balance
from the ledger through the functions of ERPNext, and the tests use entries of
the ledger as their fixture, because the balance is exactly that sum.

The entries of the ledger are written straight into the table of the ledger:
a document of the ledger cannot be saved on every site, and the balance does
not read anything else of it.
"""

from typing import Any
from unittest import mock
from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate

from print_designer.api.account_api import get_accounts_enhanced, get_accounts_with_thai_names
from print_designer.api.account_balance import the_balances_of

THE_COMPANY = "_Test Company"
THE_CASH = "Cash - _TC"
THE_CASH_GROUP = "Cash In Hand - _TC"
THE_DEBTORS = "Debtors - _TC"
THE_BANK_GROUP = "Bank Accounts - _TC"


class TestTheAccountBalances(FrappeTestCase):
    """The balance of the accounts of the account API."""

    def setUp(self):
        super().setUp()
        self._the_entries_of_the_tests()

    def _the_entries_of_the_tests(self):
        """Every test starts with a ledger without entries of its own."""
        frappe.db.sql("delete from `tabGL Entry` where name like 'PD-BAL-%'")

    def _the_entry(
        self,
        the_account: str,
        the_debit: float = 0.0,
        the_credit: float = 0.0,
        the_cancelled: int = 0,
        the_party: str | None = None,
    ) -> str:
        """One entry of the ledger."""
        the_name = f"PD-BAL-{uuid4().hex[:12]}"
        the_currency = frappe.db.get_value("Account", the_account, "account_currency")
        frappe.db.sql(
            """
            insert into `tabGL Entry`
                (name, creation, modified, modified_by, owner, docstatus, posting_date,
                 account, account_currency, debit, credit, debit_in_account_currency,
                 credit_in_account_currency, company, is_cancelled, voucher_type,
                 voucher_no, party_type, party)
            values
                (%(name)s, now(), now(), 'Administrator', 'Administrator', 0,
                 %(posting_date)s, %(account)s, %(currency)s, %(debit)s, %(credit)s,
                 %(debit)s, %(credit)s, %(company)s, %(cancelled)s, 'Journal Entry',
                 %(name)s, %(party_type)s, %(party)s)
            """,
            {
                "name": the_name,
                "posting_date": nowdate(),
                "account": the_account,
                "currency": the_currency,
                "debit": the_debit,
                "credit": the_credit,
                "company": THE_COMPANY,
                "cancelled": the_cancelled,
                "party_type": "Customer" if the_party else None,
                "party": the_party,
            },
        )
        return the_name

    def _the_row_of(self, the_account: str, the_result: dict[str, Any]) -> dict[str, Any]:
        """The row of one account of a result."""
        for the_row in the_result["data"]:
            if the_row["name"] == the_account:
                return the_row
        self.fail(f"the account {the_account} is not in the result")

    def test_the_balance_of_an_account_is_the_sum_of_the_entries_of_its_ledger(self):
        """The balance of an account is not always zero."""
        self._the_entry(THE_CASH, the_debit=123.45)

        the_result = get_accounts_enhanced(company=THE_COMPANY, include_balance=True)

        self.assertTrue(the_result["success"])
        self.assertEqual(self._the_row_of(THE_CASH, the_result)["current_balance"], 123.45)

    def test_the_balance_of_a_group_account_covers_its_children(self):
        """The balance of a group account is the balance of its children."""
        self._the_entry(THE_CASH, the_debit=50.0)

        the_result = get_accounts_enhanced(company=THE_COMPANY, include_balance=True)

        self.assertEqual(self._the_row_of(THE_CASH_GROUP, the_result)["current_balance"], 50.0)

    def test_an_account_without_entries_has_a_balance_of_zero(self):
        """An account without entries of the ledger has a balance of zero."""
        the_result = get_accounts_enhanced(company=THE_COMPANY, include_balance=True)

        self.assertTrue(the_result["success"])
        self.assertEqual(self._the_row_of(THE_BANK_GROUP, the_result)["current_balance"], 0.0)

    def test_the_entries_of_a_cancelled_voucher_are_not_counted(self):
        """The entries of a cancelled voucher do not change a balance."""
        self._the_entry(THE_CASH, the_debit=75.0, the_cancelled=1)

        the_result = get_accounts_enhanced(company=THE_COMPANY, include_balance=True)

        self.assertTrue(the_result["success"])
        self.assertEqual(self._the_row_of(THE_CASH, the_result)["current_balance"], 0.0)

    def test_every_account_carries_its_own_balance(self):
        """Every account of the result carries the balance of its own ledger."""
        self._the_entry(THE_CASH, the_debit=100.0)
        self._the_entry(THE_DEBTORS, the_credit=40.0, the_party="_Test Customer")

        the_result = get_accounts_enhanced(company=THE_COMPANY, include_balance=True)

        self.assertTrue(the_result["success"])
        self.assertEqual(self._the_row_of(THE_CASH, the_result)["current_balance"], 100.0)
        self.assertEqual(self._the_row_of(THE_DEBTORS, the_result)["current_balance"], -40.0)

    def test_the_accounts_without_a_balance_keep_their_own_shape(self):
        """A request without a balance carries no balance."""
        the_result = get_accounts_enhanced(company=THE_COMPANY)

        self.assertTrue(the_result["success"])
        self.assertNotIn("current_balance", self._the_row_of(THE_CASH, the_result))

    def test_a_flag_of_the_request_that_is_the_string_false_asks_for_no_balance(self):
        """A flag of a request arrives as a string, so "false" is a flag that is off."""
        self._the_entry(THE_CASH, the_debit=25.0)

        the_result = get_accounts_enhanced(company=THE_COMPANY, include_balance="false")

        self.assertTrue(the_result["success"])
        self.assertNotIn("current_balance", self._the_row_of(THE_CASH, the_result))

    def test_a_flag_of_the_request_that_is_the_string_true_asks_for_the_balance(self):
        """A flag of a request that is the string "true" asks for the balance."""
        self._the_entry(THE_CASH, the_debit=25.0)

        the_result = get_accounts_enhanced(company=THE_COMPANY, include_balance="true")

        self.assertTrue(the_result["success"])
        self.assertEqual(self._the_row_of(THE_CASH, the_result)["current_balance"], 25.0)

    def test_the_thai_accounts_carry_their_balance(self):
        """The accounts with a Thai name carry their balance as well."""
        self._the_entry(THE_CASH, the_debit=25.0)

        the_result = get_accounts_with_thai_names(company=THE_COMPANY, include_balance=True)

        self.assertTrue(the_result["success"])
        self.assertEqual(self._the_row_of(THE_CASH, the_result)["current_balance"], 25.0)

    def test_a_caller_that_may_not_read_an_account_receives_no_balance(self):
        """A balance is financial data, so a guest receives none."""
        frappe.set_user("Guest")
        self.addCleanup(frappe.set_user, "Administrator")

        with mock.patch("frappe.log_error"):
            the_result = get_accounts_enhanced(company=THE_COMPANY, include_balance=True)

        self.assertFalse(the_result["success"])
        self.assertIn("permission to read Account", the_result["error"])

    def test_a_failure_of_the_calculation_is_not_reported_as_a_balance_of_zero(self):
        """A failure of the calculation is reported, not passed off as a balance."""
        with mock.patch(
            "print_designer.api.account_balance.the_balances_of_the_ledger",
            side_effect=RuntimeError("the ledger is not readable"),
        ):
            with mock.patch("frappe.log_error"):
                the_result = get_accounts_enhanced(company=THE_COMPANY, include_balance=True)

        self.assertFalse(the_result["success"])
        self.assertIn("the ledger is not readable", the_result["error"])

    def test_the_helper_reports_a_failure_of_the_calculation(self):
        """The helper itself does not pass a failure off as a balance of zero."""
        with mock.patch(
            "print_designer.api.account_balance.the_balances_of_the_ledger",
            side_effect=RuntimeError("the ledger is not readable"),
        ):
            with self.assertRaises(RuntimeError):
                the_balances_of([{"name": THE_CASH, "company": THE_COMPANY}])

    def test_the_helper_refuses_a_caller_that_may_not_read_an_account(self):
        """The helper refuses a caller that may not read Account."""
        frappe.set_user("Guest")
        self.addCleanup(frappe.set_user, "Administrator")

        with self.assertRaises(frappe.PermissionError):
            the_balances_of([{"name": THE_CASH, "company": THE_COMPANY}])
