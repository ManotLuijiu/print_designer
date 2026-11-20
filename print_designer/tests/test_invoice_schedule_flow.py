"""The milestone invoice workflow of the Sales Order, end to end.

The test needs a company, a customer and a non stock item. It uses the ones
the site already has and skips itself when there are none, so it never has to
build a chart of accounts.
"""

import unittest
from contextlib import contextmanager
from typing import Any, cast
from unittest.mock import patch

import frappe
import frappe.utils
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from print_designer.custom import invoice_schedule as ms


def _first_company() -> str:
    companies = frappe.get_all("Company", filters={"is_group": 0}, limit=1, pluck="name")
    return companies[0] if companies else ""


def _first_customer() -> str:
    customers = frappe.get_all("Customer", filters={"disabled": 0}, limit=1, pluck="name")
    return customers[0] if customers else ""


def _first_service_item() -> str:
    items = frappe.get_all(
        "Item", filters={"is_stock_item": 0, "disabled": 0}, limit=1, pluck="name"
    )
    return items[0] if items else ""


def _number(value: Any) -> float:
    """A number out of a field of a document."""
    return flt(value)


def _children(doc: Any, fieldname: str) -> list[Any]:
    """The child rows of a field of a document."""
    return cast(list[Any], doc.get(fieldname) or [])


@contextmanager
def _allow_zero_qty_in_sales_order():
    """Let the Sales Order carry a line without a quantity.

    ERPNext keeps that behind a setting, so the test has to turn it on and
    turn it off again afterwards.
    """
    settings = frappe.get_doc("Selling Settings")
    previous = settings.get("allow_zero_qty_in_sales_order")
    settings.set("allow_zero_qty_in_sales_order", 1)
    settings.save(ignore_permissions=True)

    try:
        yield
    finally:
        settings = frappe.get_doc("Selling Settings")
        settings.set("allow_zero_qty_in_sales_order", previous)
        settings.save(ignore_permissions=True)


class TestMilestoneInvoiceFlow(FrappeTestCase):
    """Save the order, generate the invoices, submit the order, submit the invoices."""

    company: str
    customer: str
    item_code: str

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        if "erpnext" not in frappe.get_installed_apps():
            raise unittest.SkipTest("ERPNext is not installed on this site")

        cls.company = _first_company()
        cls.customer = _first_customer()
        cls.item_code = _first_service_item()

        if not (cls.company and cls.customer and cls.item_code):
            raise unittest.SkipTest("this site has no company, customer or service item")

    @classmethod
    def tearDownClass(cls) -> None:
        frappe.db.rollback()
        super().tearDownClass()

    def tearDown(self) -> None:
        frappe.db.rollback()
        super().tearDown()

    def _sales_order(self, margin: float | None = None) -> Any:
        line: dict[str, Any] = {
            "item_code": self.item_code,
            "qty": 10,
            "rate": 1000,
            "delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 10),
        }

        if margin is not None:
            # ERPNext works the rate of a line out again from the price list,
            # the margin and the pricing rules. A Sales Order line with a
            # margin is what proves that the milestone invoice does not apply
            # that margin a second time.
            line["margin_type"] = "Percentage"
            line["margin_rate_or_amount"] = margin

        so = frappe.get_doc(
            {
                "doctype": "Sales Order",
                "company": self.company,
                "customer": self.customer,
                "transaction_date": frappe.utils.add_days(frappe.utils.nowdate(), 1),
                "delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 10),
                "items": [line],
            }
        )

        try:
            so.insert()
        except frappe.ValidationError as error:
            message = str(error)
            if "milestone" in message.lower() or "invoice schedule" in message.lower():
                raise
            self.skipTest(f"this site cannot take the test order: {message}")

        so.set("pd_custom_enable_invoice_schedule", 1)

        so.append(
            "pd_custom_invoice_schedule",
            {
                "payment_term": "Upfront",
                "invoice_portion": 40,
                "invoice_date": frappe.utils.add_days(frappe.utils.nowdate(), 2),
                "milestone_source": "Manual",
            },
        )
        so.append(
            "pd_custom_invoice_schedule",
            {
                "payment_term": "Delivery",
                "invoice_portion": 60,
                "invoice_date": frappe.utils.add_days(frappe.utils.nowdate(), 5),
                "milestone_source": "Manual",
            },
        )
        so.save()

        return so

    def _milestones(self, so: Any) -> list[dict[str, Any]]:
        return frappe.get_all(
            "Invoice Schedule",
            filters={"parent": so.name},
            fields=["payment_term", "milestone_status", "sales_invoice"],
        )

    def test_the_preview_does_not_create_anything(self):
        so = self._sales_order()

        plan = ms.generate_milestone_invoices(so.name, preview=1)

        self.assertEqual(len(plan["plan"]), 2)
        self.assertEqual(plan["created"], [])
        self.assertEqual(frappe.db.count("Sales Invoice Item", {"sales_order": so.name}), 0)

    def test_every_milestone_gets_a_draft_invoice_of_the_right_size(self):
        so = self._sales_order()

        result = ms.generate_milestone_invoices(so.name)

        self.assertEqual(len(result["created"]), 2)

        invoices: list[Any] = [
            frappe.get_doc("Sales Invoice", row["sales_invoice"]) for row in result["created"]
        ]

        for invoice in invoices:
            self.assertEqual(invoice.get("docstatus"), 0)
            self.assertEqual(invoice.get("company"), self.company)
            self.assertEqual(invoice.get("customer"), self.customer)

            items = invoice.get("items")
            self.assertEqual(len(items), 1)

            item = items[0]
            self.assertEqual(item.get("sales_order"), so.name)
            self.assertTrue(item.get("so_detail"))
            self.assertEqual(item.get("qty"), 10)

        # 40% and 60% of a contract of 10 @ 1,000 - the quantity stays whole
        quantities = sorted(invoice.get("items")[0].get("qty") for invoice in invoices)
        self.assertEqual(quantities, [10.0, 10.0])

        rates = sorted(invoice.get("items")[0].get("rate") for invoice in invoices)
        self.assertEqual(rates, [400.0, 600.0])

        amounts = sorted(invoice.get("items")[0].get("amount") for invoice in invoices)
        self.assertEqual(amounts, [4000.0, 6000.0])

        portions = sorted(
            invoice.get("items")[0].get(ms.MILESTONE_PORTION_FIELD) for invoice in invoices
        )
        self.assertEqual(portions, [40.0, 60.0])

        for row in self._milestones(so):
            self.assertEqual(row["milestone_status"], ms.STATUS_DRAFT_CREATED)
            self.assertTrue(row["sales_invoice"])

    def test_a_second_run_creates_nothing(self):
        so = self._sales_order()
        ms.generate_milestone_invoices(so.name)

        result = ms.generate_milestone_invoices(so.name)

        self.assertEqual(result["created"], [])
        self.assertEqual(len(result["skipped"]), 2)

    def test_the_invoice_cannot_be_submitted_before_the_order(self):
        so = self._sales_order()
        result = ms.generate_milestone_invoices(so.name)

        invoice = frappe.get_doc("Sales Invoice", result["created"][0]["sales_invoice"])

        with self.assertRaises(frappe.ValidationError) as error:
            invoice.submit()

        self.assertIn("not submitted", str(error.exception))

    def test_the_order_cannot_be_submitted_before_the_milestones_are_billed(self):
        so = self._sales_order()

        with self.assertRaises(frappe.ValidationError) as error:
            so.submit()

        self.assertIn("Generate Invoice", str(error.exception))

    def test_the_order_can_be_submitted_and_keeps_its_invoice_links(self):
        so = self._sales_order()
        result = ms.generate_milestone_invoices(so.name)

        so.reload()
        so.submit()

        self.assertEqual(so.get("docstatus"), 1)

        rows = self._milestones(so)
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(row["milestone_status"], ms.STATUS_DRAFT_CREATED)
            self.assertTrue(row["sales_invoice"])

        # the invoice of a submitted order can be submitted as well
        invoice = frappe.get_doc("Sales Invoice", result["created"][0]["sales_invoice"])
        invoice.reload()
        invoice.submit()

        self.assertEqual(invoice.get("docstatus"), 1)

        rows = frappe.get_all(
            "Invoice Schedule",
            filters={"parent": so.name, "sales_invoice": invoice.name},
            fields=["milestone_status"],
        )
        self.assertEqual(rows[0]["milestone_status"], ms.STATUS_INVOICED)

    def test_a_margin_on_the_order_line_is_not_applied_a_second_time(self):
        so = self._sales_order(margin=10)
        line = so.items[0]

        # the site has to price the order, otherwise the margin changes
        # nothing and the test would prove nothing
        if not line.get("price_list_rate") or not line.get("margin_type"):
            self.skipTest("this site does not price the Sales Order line")

        contract_rate = line.rate
        contract_amount = line.amount

        result = ms.generate_milestone_invoices(so.name)

        invoice = frappe.get_doc("Sales Invoice", result["created"][0]["sales_invoice"])
        items = invoice.get("items") or []
        self.assertEqual(len(items), 1)
        milestone_line = items[0]
        portion = milestone_line.get(ms.MILESTONE_PORTION_FIELD)

        # the rate of the milestone is the rate of the contract, scaled by the
        # portion. The margin of the order line is not applied a second time,
        # ERPNext would work it out from the price list and the margin.
        expected_rate = flt(contract_rate * portion / 100, milestone_line.precision("rate"))
        self.assertEqual(milestone_line.rate, expected_rate)
        self.assertEqual(
            milestone_line.amount,
            flt(milestone_line.qty * expected_rate, milestone_line.precision("amount")),
        )
        self.assertEqual(
            milestone_line.amount,
            flt(contract_amount * portion / 100, milestone_line.precision("amount")),
        )

    def test_a_milestone_that_was_claimed_in_the_meantime_is_not_billed_again(self):
        so = self._sales_order()

        row_name = frappe.get_all(
            "Invoice Schedule",
            filters={"parent": so.name, "payment_term": "Upfront"},
            fields=["name"],
            limit=1,
        )[0]["name"]

        original_lock = ms._lock_sales_order

        def lock_and_claim(name: str) -> None:
            # another generation claims the first milestone while this one
            # waits for the lock of the order
            original_lock(name)
            frappe.db.set_value(
                "Invoice Schedule", row_name, "milestone_status", ms.STATUS_DRAFT_CREATED
            )

        with patch.object(ms, "_lock_sales_order", lock_and_claim):
            result = ms.generate_milestone_invoices(so.name)

        # only the milestone that was not claimed gets an invoice
        self.assertEqual(len(result["created"]), 1)
        self.assertEqual(result["created"][0]["milestone"], "Delivery")

    def test_a_line_without_a_quantity_does_not_block_the_order(self):
        # A Sales Order may carry a line without a quantity when the site
        # allows it. The milestone invoice must not carry that line - the
        # invoice would be refused for it - and the order still has to be
        # submittable afterwards.
        with _allow_zero_qty_in_sales_order():
            so = self._sales_order()
            so.append(
                "items",
                {
                    "item_code": self.item_code,
                    "qty": 0,
                    "rate": 500,
                    "delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 10),
                },
            )
            so.save()

            result = ms.generate_milestone_invoices(so.name)

            self.assertEqual(len(result["created"]), 2)

            invoice = frappe.get_doc("Sales Invoice", result["created"][0]["sales_invoice"])
            # only the line that has a quantity is billed
            items = invoice.get("items") or []
            self.assertEqual(len(items), 1)

            so.reload()
            so.submit()

            self.assertEqual(so.get("docstatus"), 1)

    def test_the_fixed_discount_is_split_over_the_milestones(self):
        # A fixed discount belongs to the whole contract. The mapper copies it
        # onto every invoice it builds, so a plan of two milestones would
        # discount the contract twice.
        so = self._sales_order()
        so.apply_discount_on = "Net Total"
        so.discount_amount = 1000
        so.save()

        # the contract is 10 @ 1,000 = 10,000 and the discount of 1,000 is
        # part of it
        contract_net = flt(so.get("net_total"))
        self.assertEqual(contract_net, 9000.0)

        result = ms.generate_milestone_invoices(so.name)

        invoices = [
            frappe.get_doc("Sales Invoice", row["sales_invoice"]) for row in result["created"]
        ]

        discounts = sorted(_number(invoice.get("discount_amount")) for invoice in invoices)
        self.assertEqual(discounts, [400.0, 600.0])

        nets = sorted(_number(invoice.get("net_total")) for invoice in invoices)
        self.assertEqual(nets, [3600.0, 5400.0])

        # the invoices of the plan add up to the net of the contract
        self.assertEqual(flt(sum(nets)), contract_net)

        # and every invoice bills the amount of its own milestone
        rows = frappe.get_all(
            "Invoice Schedule",
            filters={"parent": so.name},
            fields=["payment_term", "invoice_amount", "sales_invoice"],
        )
        for row in rows:
            invoice = frappe.get_doc("Sales Invoice", row["sales_invoice"])
            self.assertEqual(_number(invoice.get("net_total")), flt(row["invoice_amount"]))

    def test_a_flat_charge_is_split_over_the_milestones(self):
        accounts = frappe.get_all(
            "Account",
            filters={
                "company": self.company,
                "is_group": 0,
                "account_type": ["in", ["Tax", "Sales Taxes and Charges"]],
            },
            limit=1,
            pluck="name",
        )

        if not accounts:
            self.skipTest("this site has no tax account")

        so = self._sales_order()
        so.append(
            "taxes",
            {
                "charge_type": "Actual",
                "account_head": accounts[0],
                "tax_amount": 100,
                "description": "Flat fee",
            },
        )
        so.save()

        result = ms.generate_milestone_invoices(so.name)

        invoices = [
            frappe.get_doc("Sales Invoice", row["sales_invoice"]) for row in result["created"]
        ]

        charges = sorted(_number(invoice.get("total_taxes_and_charges")) for invoice in invoices)
        self.assertEqual(charges, [40.0, 60.0])

        # the invoices of the plan add up to the contract amount
        self.assertEqual(flt(sum(charges)), 100.0)

    def test_a_milestone_draft_that_no_longer_matches_the_order_is_rejected(self):
        so = self._sales_order()
        ms.generate_milestone_invoices(so.name)

        so.reload()
        row = so.get("pd_custom_invoice_schedule")[0]

        # the draft matches the order
        self.assertIsNone(ms._milestone_invoice_problem(so, row))

        item = so.get("items")[0]
        original_code = item.item_code
        original_uom = item.uom
        original_conversion = item.conversion_factor

        # the order bills another item now
        item.item_code = "SOMETHING-ELSE"
        self.assertIsNotNone(ms._milestone_invoice_problem(so, row))
        item.item_code = original_code

        # the order uses another unit of measure now
        item.uom = "A-OTHER-UNIT"
        self.assertIsNotNone(ms._milestone_invoice_problem(so, row))
        item.uom = original_uom

        # the order works with another conversion factor now
        item.conversion_factor = 2
        self.assertIsNotNone(ms._milestone_invoice_problem(so, row))
        item.conversion_factor = original_conversion

        # the milestone moved to another date
        row.invoice_date = frappe.utils.add_days(frappe.utils.nowdate(), 7)
        self.assertIsNotNone(ms._milestone_invoice_problem(so, row))

    def test_the_billing_date_can_still_be_changed_after_the_order_is_submitted(self):
        so = self._sales_order()
        ms.generate_milestone_invoices(so.name)

        so.reload()
        row = so.get("pd_custom_invoice_schedule")[0]
        invoice_name = row.get("sales_invoice")
        self.assertTrue(invoice_name)

        date_field = (
            "posting_date"
            if frappe.get_meta("Sales Invoice").has_field("posting_date")
            else "transaction_date"
        )

        invoice = frappe.get_doc("Sales Invoice", invoice_name)
        # the invoice is dated at the date of the milestone
        self.assertEqual(str(invoice.get(date_field))[:10], str(row.invoice_date)[:10])

        # the order is submitted, so its milestones are frozen from now on
        so.submit()

        # the billing date of the invoice is still the user's business
        new_date = frappe.utils.add_days(frappe.utils.nowdate(), -1)
        invoice.reload()
        invoice.set(date_field, new_date)
        invoice.save()
        invoice.reload()
        self.assertEqual(str(invoice.get(date_field))[:10], new_date)

    def test_a_stale_form_cannot_erase_the_generated_links(self):
        so = self._sales_order()
        # a second tab that was opened before the generation
        stale = frappe.get_doc("Sales Order", so.name)

        ms.generate_milestone_invoices(so.name)

        # the stale tab still shows the milestones without their links
        self.assertFalse(_children(stale, "pd_custom_invoice_schedule")[0].get("sales_invoice"))

        # the second line of defence keeps the link of the database
        ms.reconcile_milestone_links(stale)
        self.assertTrue(_children(stale, "pd_custom_invoice_schedule")[0].get("sales_invoice"))

        # and the timestamp of the order moved, so Frappe refuses the save of
        # the stale tab instead of losing the links
        with self.assertRaises(frappe.TimestampMismatchError):
            stale.save()

    def test_the_save_of_a_stale_form_keeps_the_link_of_the_database(self):
        so = self._sales_order()
        # a second tab that was opened before the generation
        stale = frappe.get_doc("Sales Order", so.name)

        ms.generate_milestone_invoices(so.name)

        # the timestamp of the order is put back, so Frappe does not stop the
        # save of the stale tab - the reconciliation has to keep the link
        frappe.db.set_value(
            "Sales Order", so.name, "modified", stale.modified, update_modified=False
        )

        stale.save()

        for row in self._milestones(so):
            self.assertTrue(row["sales_invoice"])
            self.assertEqual(row["milestone_status"], ms.STATUS_DRAFT_CREATED)
