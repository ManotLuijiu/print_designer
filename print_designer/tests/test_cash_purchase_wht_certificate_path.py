"""The tests of the retired path of the certificate of a cash purchase.

The certificate of the withholding tax of Thailand names the payment that
pays it: the `payment_entry` of the `Withholding Tax Certificate` is a
mandatory field.  A cash purchase carries no payment entry, so the path
that created a certificate from the purchase invoice could never insert one
and made the submit of the purchase invoice fail.  That path is retired; the
certificate of a payment is created from the payment entry.

The tests create a disposable purchase invoice inside a savepoint that is
rolled back at the end, so that the site keeps no row of the test.
"""

import unittest
from typing import Any

import frappe

SAVEPOINT = "cash_purchase_wht_certificate_test"

COMPANY = "_Test Company"
SUPPLIER = "_Test Supplier"
ITEM = "_TEST WHT Cash Service"

RETIRED_HOOK = "print_designer.custom.purchase_invoice_wht_generator.on_submit_purchase_invoice"


class TestTheRetiredCashPurchasePath(unittest.TestCase):
    """The retirement of the certificate of a cash purchase."""

    def setUp(self):
        frappe.db.savepoint(SAVEPOINT)

    def tearDown(self):
        frappe.db.rollback(save_point=SAVEPOINT)

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

    def _the_item(self) -> str:
        """A disposable service item of the test."""
        if not frappe.db.exists("Item", ITEM):
            item = frappe.get_doc(
                {
                    "doctype": "Item",
                    "item_code": ITEM,
                    "item_name": ITEM,
                    "is_stock_item": 0,
                    "item_group": "_Test Item Group",
                    "company": COMPANY,
                }
            )
            item.insert(ignore_permissions=True)

        return ITEM

    def _the_cash_purchase(self) -> Any:
        """A disposable cash purchase of a service with the tax of Thailand."""
        cost_center = frappe.get_all(
            "Cost Center", filters={"company": COMPANY, "is_group": 0}, pluck="name"
        )
        if not cost_center:
            self.skipTest("the site has no cost center")

        purchase_invoice = frappe.get_doc(
            {
                "doctype": "Purchase Invoice",
                "company": COMPANY,
                "supplier": SUPPLIER,
                "currency": frappe.db.get_value("Company", COMPANY, "default_currency"),
                "is_paid": 1,
                "cash_bank_account": self._the_account("Bank"),
                "pd_custom_apply_thai_wht_compliance": 1,
                "pd_custom_bill_cash": 1,
                "items": [
                    {
                        "item_code": self._the_item(),
                        "qty": 1,
                        "rate": 1000,
                        "cost_center": cost_center[0],
                    }
                ],
            }
        )
        purchase_invoice.insert(ignore_permissions=True)

        return purchase_invoice

    def test_the_retired_path_is_not_registered(self):
        hooks = frappe.get_hooks("doc_events")
        on_submit = (hooks.get("Purchase Invoice") or {}).get("on_submit") or []

        self.assertNotIn(RETIRED_HOOK, on_submit)

    def test_the_module_of_the_retired_path_is_gone(self):
        with self.assertRaises(ImportError):
            __import__(
                "print_designer.custom.purchase_invoice_wht_generator",
                fromlist=["on_submit_purchase_invoice"],
            )

    def test_a_cash_purchase_submits_without_a_certificate(self):
        purchase_invoice = self._the_cash_purchase()

        purchase_invoice.submit()

        self.assertEqual(purchase_invoice.docstatus, 1)
        self.assertFalse(
            frappe.db.exists(
                "Withholding Tax Certificate", {"purchase_invoice": purchase_invoice.name}
            )
        )
