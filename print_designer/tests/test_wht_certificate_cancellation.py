"""The tests of the cancellation of the certificate of the withholding tax.

The controller of the certificate removes the item of the form of the tax,
clears the link of the payment entry in both directions and leaves the
status of the certificate as it was written when the certificate was created.

That last part is the known drift of the status of the certificate: the
field carries `Draft`, `Issued`, `Submitted to Revenue Dept` and `Cancelled`,
and the controller moves it neither on a submit nor on a cancel.  Which of
them the field shall carry is a decision of the product and is tracked on
its own; the test holds the behaviour of today, so that a change of it is
visible and deliberate.

The cancellation of the certificate takes part in the transaction of the
caller: it clears the links of the certificate and of the payment entry
inside the transaction that asked for the cancellation, and it commits
nothing of its own.  The test therefore works inside a savepoint that is
rolled back at the end, so that the site keeps no row of the test.
"""

import unittest
from typing import Any

import frappe
from frappe.utils import nowdate

from print_designer.custom import wht_certificate_creator as creator

SAVEPOINT = "wht_certificate_cancellation_test"

#: The savepoint that proves that the cancellation of the certificate commits
#: nothing of its own.  A commit inside the controller ends the transaction of
#: the caller and takes its savepoints with it, so the rollback to this
#: savepoint fails when the controller committed.
PROBE = "wht_certificate_cancellation_probe"

COMPANY = "_Test Company"
SUPPLIER = "_Test Supplier"


class TestTheCancellationOfTheCertificate(unittest.TestCase):
    """The cancellation of the certificate of the withholding tax."""

    def setUp(self):
        self.certificate_names: list[str] = []
        self.payment_entry_names: list[str] = []
        frappe.db.savepoint(SAVEPOINT)

    def tearDown(self):
        try:
            frappe.db.rollback(save_point=SAVEPOINT)
        except Exception:
            # The savepoint of the test is gone: the transaction of the caller
            # was committed by the code under test.  The rows of the test are
            # removed one by one then, so that the site keeps no row of it.
            self._remove_the_certificates()
            self._remove_the_payment_entries()
            frappe.db.commit()

    def _remove_the_certificates(self):
        """Remove the certificates of the test.

        This is the fallback of the teardown, for the case where the
        transaction of the test was committed and its savepoint is gone.
        """
        for the_name in self.certificate_names:
            if not frappe.db.exists("Withholding Tax Certificate", the_name):
                continue

            the_certificate = frappe.get_doc("Withholding Tax Certificate", the_name)
            if the_certificate.docstatus == 1:
                the_certificate.cancel()

            frappe.delete_doc("Withholding Tax Certificate", the_name, force=True)

        self.certificate_names = []

    def _remove_the_payment_entries(self):
        """Remove the payment entries of the test."""
        for the_name in self.payment_entry_names:
            if not frappe.db.exists("Payment Entry", the_name):
                continue

            frappe.delete_doc("Payment Entry", the_name, force=True)

        self.payment_entry_names = []

    def _the_account(self, account_type: str) -> str:
        """An account of the company of the test."""
        accounts = frappe.get_all(
            "Account",
            filters={
                "company": COMPANY,
                "account_type": account_type,
                "is_group": 0,
                "disabled": 0,
            },
            pluck="name",
        )
        if not accounts:
            self.skipTest(f"the site has no {account_type} account")

        return accounts[0]

    def _the_payment_entry(self) -> Any:
        """A disposable payment entry that pays a supplier."""
        payment_entry = frappe.get_doc(
            {
                "doctype": "Payment Entry",
                "payment_type": "Pay",
                "company": COMPANY,
                "posting_date": nowdate(),
                "party_type": "Supplier",
                "party": SUPPLIER,
                "paid_from": self._the_account("Payable"),
                "paid_to": self._the_account("Bank"),
                "paid_amount": 1000,
                "received_amount": 1000,
                "source_exchange_rate": 1,
                "target_exchange_rate": 1,
                "paid_to_account_currency": frappe.db.get_value(
                    "Account", self._the_account("Bank"), "account_currency"
                ),
                "reference_no": "TEST-WHT-CANCEL",
                "reference_date": nowdate(),
                "pd_custom_withholding_tax_amount_details": 30,
                "pd_custom_withholding_tax_pct_details": 3,
                "pd_custom_tax_base_amount": 1000,
            }
        )
        payment_entry.insert(ignore_permissions=True)
        self.payment_entry_names.append(str(payment_entry.name))

        return payment_entry

    def _the_certificate(self) -> tuple[Any, Any]:
        """A submitted certificate of a disposable payment entry."""
        payment_entry = self._the_payment_entry()
        certificate = creator.create_certificate_for_payment_entry(payment_entry)
        self.certificate_names.append(str(certificate.name))

        return certificate, payment_entry

    def test_the_cancellation_marks_the_certificate_as_cancelled(self):
        certificate, _ = self._the_certificate()
        certificate.cancel()

        self.assertEqual(certificate.docstatus, 2)

    def test_the_cancellation_clears_the_link_of_the_payment_entry(self):
        certificate, payment_entry = self._the_certificate()
        certificate.cancel()

        self.assertIsNone(
            frappe.db.get_value("Withholding Tax Certificate", certificate.name, "payment_entry")
        )
        self.assertIsNone(
            frappe.db.get_value("Payment Entry", payment_entry.name, "pd_custom_wht_certificate")
        )

    def test_the_cancellation_leaves_the_status_of_the_certificate(self):
        """The known drift of the status: it is not moved on a cancel."""
        certificate, _ = self._the_certificate()
        certificate.cancel()

        self.assertEqual(certificate.status, "Issued")

    def test_the_cancellation_does_not_commit_the_transaction_of_the_caller(self):
        """The cancellation of the certificate commits nothing of its own.

        A commit inside the controller would end the transaction of the
        caller and would take its savepoints with it.  The test takes a
        savepoint before the cancellation and rolls back to it afterwards:
        the rollback fails when the cancellation committed the transaction
        of the caller.
        """
        certificate, payment_entry = self._the_certificate()

        frappe.db.savepoint(PROBE)
        certificate.cancel()

        # The cancellation did take place, so that the probe below speaks
        # about a cancellation and not about a cancellation that never ran.
        self.assertEqual(certificate.docstatus, 2)
        self.assertIsNone(
            frappe.db.get_value("Withholding Tax Certificate", certificate.name, "payment_entry")
        )
        self.assertIsNone(
            frappe.db.get_value("Payment Entry", payment_entry.name, "pd_custom_wht_certificate")
        )

        try:
            frappe.db.rollback(save_point=PROBE)
        except Exception as error:
            self.fail(
                "the cancellation of the certificate committed the transaction of the caller: "
                f"{error}"
            )
