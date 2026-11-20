"""The dates of the payment schedule of a milestone invoice.

ERPNext compares the due dates of the payment schedule with `max()`. The
schedule that ERPNext builds for the invoice mixes the types: a date that
ERPNext worked out from the posting date of the invoice stays a string,
because the posting date of a new invoice is the default "Today", while a
date that came from the order is a date. The comparison then fails with a
TypeError and the invoice is refused before it is saved.

The tests below pin the normalisation of the dates of the schedule.
"""

import datetime
import unittest
from typing import Any, cast

import frappe
import frappe.utils
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from print_designer.custom import invoice_schedule as ms


class _ScheduleRow:
    """A row of a payment schedule that behaves like a Frappe child row."""

    due_date: Any
    discount_date: Any

    def __init__(self, **values: Any) -> None:
        self.__dict__.update(values)

    def get(self, key: str, default: Any = None) -> Any:
        return self.__dict__.get(key, default)


class _Invoice:
    """An invoice that carries a payment schedule, like the mapped one."""

    def __init__(self, rows: list[_ScheduleRow]) -> None:
        self.payment_schedule = rows

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


def _is_a_plain_date(value: Any) -> bool:
    """Is the value a date and not a datetime?"""
    return type(value) is datetime.date


class TestShiftPaymentSchedule(FrappeTestCase):
    """The dates of the schedule move with the milestone and keep one type."""

    order_date = datetime.date(2026, 8, 21)

    def _schedule(self) -> _Invoice:
        """A schedule that mixes a string with a date, like ERPNext builds it."""
        return _Invoice(
            [
                _ScheduleRow(due_date="2026-11-21", discount_date="2026-11-21"),
                _ScheduleRow(
                    due_date=datetime.date(2026, 11, 23),
                    discount_date=datetime.date(2026, 11, 21),
                ),
            ]
        )

    def test_a_positive_shift_moves_every_date_and_normalises_its_type(self):
        invoice = self._schedule()
        so = {"transaction_date": self.order_date}

        ms._shift_payment_schedule(invoice, so, datetime.date(2026, 11, 23))

        # 94 days between the order and the milestone
        self.assertEqual(invoice.payment_schedule[0].due_date, datetime.date(2027, 2, 23))
        self.assertEqual(invoice.payment_schedule[1].due_date, datetime.date(2027, 2, 25))
        self.assertEqual(invoice.payment_schedule[0].discount_date, datetime.date(2027, 2, 23))
        self.assertEqual(invoice.payment_schedule[1].discount_date, datetime.date(2027, 2, 23))

        for row in invoice.payment_schedule:
            self.assertTrue(_is_a_plain_date(row.due_date))
            self.assertTrue(_is_a_plain_date(row.discount_date))

        # the comparison of ERPNext works on the result
        self.assertEqual(
            max(row.due_date for row in invoice.payment_schedule),
            datetime.date(2027, 2, 25),
        )

    def test_a_zero_shift_normalises_the_types_and_keeps_the_days(self):
        invoice = self._schedule()
        so = {"transaction_date": self.order_date}

        ms._shift_payment_schedule(invoice, so, self.order_date)

        self.assertEqual(invoice.payment_schedule[0].due_date, datetime.date(2026, 11, 21))
        self.assertEqual(invoice.payment_schedule[1].due_date, datetime.date(2026, 11, 23))
        self.assertEqual(invoice.payment_schedule[0].discount_date, datetime.date(2026, 11, 21))
        self.assertEqual(invoice.payment_schedule[1].discount_date, datetime.date(2026, 11, 21))

        for row in invoice.payment_schedule:
            self.assertTrue(_is_a_plain_date(row.due_date))
            self.assertTrue(_is_a_plain_date(row.discount_date))

    def test_a_negative_shift_works_the_same_way(self):
        invoice = self._schedule()
        so = {"transaction_date": self.order_date}

        ms._shift_payment_schedule(invoice, so, datetime.date(2026, 6, 21))

        # 61 days back
        self.assertEqual(invoice.payment_schedule[0].due_date, datetime.date(2026, 9, 21))
        self.assertEqual(invoice.payment_schedule[1].due_date, datetime.date(2026, 9, 23))

        for row in invoice.payment_schedule:
            self.assertTrue(_is_a_plain_date(row.due_date))
            self.assertTrue(_is_a_plain_date(row.discount_date))

    def test_the_empty_dates_stay_empty_and_nothing_else_is_touched(self):
        invoice = _Invoice(
            [
                _ScheduleRow(due_date=None, discount_date=""),
                _ScheduleRow(due_date="2026-11-21", discount_date=None),
            ]
        )
        so = {"transaction_date": self.order_date}

        ms._shift_payment_schedule(invoice, so, datetime.date(2026, 11, 23))

        self.assertIsNone(invoice.payment_schedule[0].due_date)
        self.assertEqual(invoice.payment_schedule[0].discount_date, "")
        self.assertIsNone(invoice.payment_schedule[1].discount_date)
        self.assertEqual(invoice.payment_schedule[1].due_date, datetime.date(2027, 2, 23))

        # the order is not touched
        self.assertEqual(so, {"transaction_date": self.order_date})

    def test_without_a_milestone_date_the_schedule_is_not_touched(self):
        invoice = self._schedule()
        so = {"transaction_date": self.order_date}

        ms._shift_payment_schedule(invoice, so, None)

        self.assertEqual(invoice.payment_schedule[0].due_date, "2026-11-21")
        self.assertEqual(invoice.payment_schedule[1].due_date, datetime.date(2026, 11, 23))


class TestMilestoneInvoiceScheduleDates(FrappeTestCase):
    """The schedule of a milestone invoice carries dates that ERPNext accepts."""

    company: str
    customer: str
    item_code: str
    payment_terms: list[str]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        if "erpnext" not in frappe.get_installed_apps():
            raise unittest.SkipTest("ERPNext is not installed on this site")

        companies = frappe.get_all("Company", filters={"is_group": 0}, limit=1, pluck="name")
        customers = frappe.get_all("Customer", filters={"disabled": 0}, limit=1, pluck="name")
        items = frappe.get_all(
            "Item", filters={"is_stock_item": 0, "disabled": 0}, limit=1, pluck="name"
        )
        terms = frappe.get_all("Payment Term", limit=4, pluck="name")

        cls.company = companies[0] if companies else ""
        cls.customer = customers[0] if customers else ""
        cls.item_code = items[0] if items else ""
        cls.payment_terms = list(terms)

        if not (cls.company and cls.customer and cls.item_code):
            raise unittest.SkipTest("this site has no company, customer or service item")

        if len(cls.payment_terms) < 4:
            raise unittest.SkipTest("this site has fewer than four payment terms")

    def _payment_schedule(self, order_date: Any, today: Any) -> list[dict[str, Any]]:
        """The schedule of the order, the way a real one looks.

        The first row is worked out from the posting date of the invoice, so
        ERPNext keeps it a string. The other rows are taken from the order,
        so they are dates. Every row has a discount date, which is worked out
        the same way.
        """
        schedule = []

        for index, term in enumerate(self.payment_terms):
            row: dict[str, Any] = {
                "payment_term": term,
                "due_date": order_date if index == 0 else frappe.utils.add_days(today, 10 * index),
                "invoice_portion": [20, 30, 30, 20][index],
                "discount_validity_based_on": "Day(s) after invoice date",
                "discount_validity": 0,
                "discount_date": order_date,
            }

            if index == 0:
                row["due_date_based_on"] = "Day(s) after invoice date"
                row["credit_days"] = 0

            schedule.append(row)

        return schedule

    def _sales_order(self) -> Any:
        """A Sales Order with a payment schedule of four milestones."""
        today = cast(datetime.date, frappe.utils.getdate())
        order_date = frappe.utils.add_days(today, -30)

        so = frappe.get_doc(
            {
                "doctype": "Sales Order",
                "company": self.company,
                "customer": self.customer,
                "transaction_date": order_date,
                "delivery_date": frappe.utils.add_days(today, 60),
                "items": [
                    {
                        "item_code": self.item_code,
                        "qty": 10,
                        "rate": 1000,
                        "delivery_date": frappe.utils.add_days(today, 60),
                    }
                ],
                "payment_schedule": self._payment_schedule(order_date, today),
                "pd_custom_enable_invoice_schedule": 1,
            }
        )

        try:
            so.insert()
        except frappe.ValidationError as error:
            message = str(error)
            if "milestone" in message.lower() or "invoice schedule" in message.lower():
                raise
            self.skipTest(f"this site cannot take the test order: {message}")

        # the plan of the milestones, with a date on every milestone
        for index, row in enumerate(so.get("pd_custom_invoice_schedule") or []):
            row.invoice_date = frappe.utils.add_days(today, -30 + 5 * index)
            row.milestone_source = "Manual"

        so.save()

        return so

    def _milestone_rows(self, so: Any) -> list[Any]:
        return list(so.get("pd_custom_invoice_schedule") or [])

    def test_the_schedule_of_the_milestone_has_one_type_for_its_dates(self):
        so = self._sales_order()
        rows = self._milestone_rows(so)

        self.assertEqual(len(rows), 4)

        for row in rows:
            invoice = cast(Any, ms._build_milestone_invoice(so, row))

            for schedule_row in cast(list[Any], invoice.get("payment_schedule") or []):
                if schedule_row.get("due_date"):
                    self.assertTrue(_is_a_plain_date(schedule_row.due_date))
                if schedule_row.get("discount_date"):
                    self.assertTrue(_is_a_plain_date(schedule_row.discount_date))

    def test_erpnext_accepts_the_schedule_of_the_milestone_invoice(self):
        so = self._sales_order()
        row = self._milestone_rows(so)[0]

        invoice = ms._build_milestone_invoice(so, row)

        # the comparison of ERPNext is the one that failed before
        invoice.set_due_date()

        self.assertTrue(invoice.get("due_date"))

    def test_erpnext_refuses_a_schedule_that_mixes_the_types(self):
        """The reason the dates have to be normalised.

        ERPNext compares the dates of the schedule with `max()`, and that
        fails as soon as one of them is a string.
        """
        invoice = cast(Any, frappe.new_doc("Sales Invoice"))
        invoice.append("payment_schedule", {"due_date": "2026-11-21"})
        invoice.append("payment_schedule", {"due_date": datetime.date(2026, 12, 28)})

        with self.assertRaises(TypeError):
            invoice.set_due_date()

    def test_the_order_keeps_its_own_schedule_after_the_invoice_is_built(self):
        so = self._sales_order()

        before = [
            (row.payment_term, row.due_date, row.discount_date)
            for row in cast(list[Any], so.get("payment_schedule") or [])
        ]

        for row in self._milestone_rows(so):
            ms._build_milestone_invoice(so, row)

        reloaded = cast(Any, frappe.get_doc("Sales Order", so.name))
        after = [
            (row.payment_term, row.due_date, row.discount_date)
            for row in cast(list[Any], reloaded.get("payment_schedule") or [])
        ]

        self.assertEqual(after, before)

    def test_the_invoices_of_the_milestones_are_saved(self):
        so = self._sales_order()
        rows = self._milestone_rows(so)

        result = ms.generate_milestone_invoices(so.name)

        self.assertEqual(len(result["created"]), 4)

        base = flt(so.get("net_total"))

        for created, row in zip(result["created"], rows, strict=False):
            invoice = cast(Any, frappe.get_doc("Sales Invoice", created["sales_invoice"]))

            self.assertEqual(invoice.get("docstatus"), 0)

            # the milestone bills its part of the contract
            portion = flt(row.invoice_portion)
            self.assertEqual(invoice.get("net_total"), flt(base * portion / 100))

            # the invoice carries the date of its milestone
            self.assertEqual(invoice.get("posting_date"), row.invoice_date)

            for schedule_row in cast(list[Any], invoice.get("payment_schedule") or []):
                if schedule_row.get("due_date"):
                    self.assertTrue(_is_a_plain_date(schedule_row.due_date))
                if schedule_row.get("discount_date"):
                    self.assertTrue(_is_a_plain_date(schedule_row.discount_date))

            # the comparison of ERPNext works on the saved schedule
            invoice.set_due_date()
            self.assertTrue(invoice.get("due_date"))
