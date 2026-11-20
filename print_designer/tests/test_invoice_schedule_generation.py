"""Tests for the milestone invoice workflow of the Sales Order.

The workflow is: save the Sales Order, generate the milestone invoices,
submit the Sales Order and submit the invoices afterwards. These tests cover
the parts that decide what happens - the plan, the mapping exception, the
guard in front of the submission and the ownership of the invoice links.

They do not need a company, a customer or an item, so they run on any site
that has the app installed.
"""

import unittest
from typing import Any
from unittest.mock import patch

import frappe
from frappe.utils import flt

from print_designer.custom import invoice_schedule as ms


class Order(frappe._dict):
    """A Sales Order that is just enough for the planning code.

    The real document has a ``precision`` method and an ``is_new`` method, so
    the stub carries them as well. Everything else is plain dictionary access.
    """

    def precision(self, fieldname: str, parentfield: str | None = None) -> int:
        return 2

    def is_new(self) -> bool:
        return bool(self.get("__islocal"))

    def check_permission(self, *args: Any, **kwargs: Any) -> None:
        return None


class Invoice:
    """A Sales Invoice that records how it was inserted."""

    def __init__(self, name: str = "SINV-0001") -> None:
        self.name = name
        self.inserted: list[dict[str, Any]] = []

    def insert(self, **kwargs: Any) -> None:
        self.inserted.append(kwargs)


def _row(**kwargs: Any) -> Any:
    row = frappe._dict(
        name="row-1",
        payment_term="Upfront",
        invoice_portion=20,
        invoice_amount=60000.0,
        invoice_date="2026-08-21",
        milestone_status=ms.STATUS_NOT_INVOICED,
        sales_invoice=None,
    )
    row.update(kwargs)
    return row


def _order(rows: list[Any], **kwargs: Any) -> Any:
    values: dict[str, Any] = {
        "name": "SAL-ORD-0001",
        "doctype": "Sales Order",
        "docstatus": 0,
        "company": "Test Company",
        "customer": "Test Customer",
        "currency": "THB",
        "net_total": 300000,
        "items": [],
        "pd_custom_enable_invoice_schedule": 1,
        "pd_custom_invoice_schedule": rows,
    }
    values.update(kwargs)
    return Order(values)


class TestMilestonePlan(unittest.TestCase):
    """Which milestones get an invoice and which ones are skipped."""

    def test_a_milestone_with_a_portion_and_a_date_is_eligible(self):
        row = _row()
        doc = _order([row])

        eligible, skipped = ms._partition_milestones(doc)

        self.assertEqual([item.name for item in eligible], ["row-1"])
        self.assertEqual(skipped, [])

    def test_a_placeholder_row_is_skipped_before_the_date_is_looked_at(self):
        """A row that covers nothing must never block the rows that do."""
        empty = _row(name="row-1", payment_term="Empty", invoice_portion=0, invoice_date=None)
        real = _row(name="row-2", payment_term="Real", invoice_portion=60)
        doc = _order([empty, real])

        eligible, skipped = ms._partition_milestones(doc)

        self.assertEqual([item.name for item in eligible], ["row-2"])
        self.assertEqual(skipped[0]["milestone"], "Empty")

    def test_a_positive_milestone_without_a_date_is_reported(self):
        doc = _order([_row(invoice_date=None)])

        with self.assertRaises(frappe.ValidationError) as error:
            ms._partition_milestones(doc)

        self.assertIn("Upfront", str(error.exception))

    def test_a_negative_portion_is_rejected(self):
        doc = _order([_row(invoice_portion=-10)])

        with self.assertRaises(frappe.ValidationError) as error:
            ms._partition_milestones(doc)

        self.assertIn("Upfront", str(error.exception))

    def test_the_portions_may_not_add_up_to_more_than_the_contract(self):
        doc = _order([_row(invoice_portion=60), _row(name="row-2", invoice_portion=60)])

        with self.assertRaises(frappe.ValidationError) as error:
            ms._validate_portion_total(doc)

        self.assertIn("100", str(error.exception))

    def test_a_milestone_that_already_has_an_invoice_is_not_regenerated(self):
        doc = _order([_row(milestone_status=ms.STATUS_DRAFT_CREATED)])

        eligible, skipped = ms._partition_milestones(doc)

        self.assertEqual(eligible, [])
        self.assertEqual(skipped[0]["reason"], ms.STATUS_DRAFT_CREATED)

    def test_a_stale_link_is_released_and_the_milestone_is_billed_again(self):
        row = _row(sales_invoice="SINV-GONE-0001")
        doc = _order([row])

        with (
            patch.object(frappe.db, "exists", return_value=False),
            patch.object(frappe.db, "set_value") as set_value,
        ):
            eligible, skipped = ms._partition_milestones(doc)

        self.assertEqual([item.name for item in eligible], ["row-1"])
        self.assertEqual(skipped, [])
        set_value.assert_called_once()
        self.assertIsNone(set_value.call_args[0][2]["sales_invoice"])

    def test_the_plan_says_what_is_going_to_be_invoiced(self):
        row = _row()
        doc = _order([row])

        plan = ms._milestone_plan(doc, [row])

        self.assertEqual(plan[0]["milestone"], "Upfront")
        self.assertEqual(plan[0]["invoice_portion"], 20.0)
        self.assertEqual(plan[0]["invoice_amount"], 60000.0)
        self.assertEqual(plan[0]["invoice_date"], "2026-08-21")

    def test_the_truthy_helper_reads_the_ways_a_client_can_say_yes(self):
        self.assertTrue(ms._is_truthy(1))
        self.assertTrue(ms._is_truthy("1"))
        self.assertTrue(ms._is_truthy("true"))
        self.assertTrue(ms._is_truthy(True))
        self.assertFalse(ms._is_truthy(0))
        self.assertFalse(ms._is_truthy(None))
        self.assertFalse(ms._is_truthy(""))


class TestDraftMappingContext(unittest.TestCase):
    """The mapping of a draft Sales Order is only allowed for our own call."""

    def _table_maps(self) -> dict[str, Any]:
        return {"Sales Order": {"doctype": "Sales Invoice", "validation": {"docstatus": ["=", 1]}}}

    def _source(self, name: str = "SAL-ORD-0001", docstatus: int = 0, enabled: int = 1) -> Any:
        return Order(
            doctype="Sales Order",
            name=name,
            docstatus=docstatus,
            pd_custom_enable_invoice_schedule=enabled,
        )

    def test_without_a_context_the_mapping_is_not_touched(self):
        table_maps = self._table_maps()

        ms.on_sales_invoice_before_mapping(
            frappe._dict(), "before_mapping", self._source(), table_maps
        )

        self.assertEqual(table_maps["Sales Order"]["validation"], {"docstatus": ["=", 1]})

    def test_an_order_without_the_schedule_is_not_relaxed(self):
        table_maps = self._table_maps()
        ms._set_draft_generation_context({"sales_order": "SAL-ORD-0001"})
        try:
            ms.on_sales_invoice_before_mapping(
                frappe._dict(),
                "before_mapping",
                self._source(enabled=0),
                table_maps,
            )
        finally:
            ms._clear_draft_generation_context()

        self.assertEqual(table_maps["Sales Order"]["validation"], {"docstatus": ["=", 1]})

    def test_a_context_for_another_order_does_not_relax_the_mapping(self):
        table_maps = self._table_maps()
        ms._set_draft_generation_context({"sales_order": "SAL-ORD-OTHER"})
        try:
            ms.on_sales_invoice_before_mapping(
                frappe._dict(), "before_mapping", self._source(), table_maps
            )
        finally:
            ms._clear_draft_generation_context()

        self.assertEqual(table_maps["Sales Order"]["validation"], {"docstatus": ["=", 1]})

    def test_a_submitted_order_does_not_need_the_exception(self):
        table_maps = self._table_maps()
        ms._set_draft_generation_context({"sales_order": "SAL-ORD-0001"})
        try:
            ms.on_sales_invoice_before_mapping(
                frappe._dict(), "before_mapping", self._source(docstatus=1), table_maps
            )
        finally:
            ms._clear_draft_generation_context()

        self.assertEqual(table_maps["Sales Order"]["validation"], {"docstatus": ["=", 1]})

    def test_the_context_relaxes_the_draft_mapping_of_that_order_only(self):
        table_maps = self._table_maps()
        ms._set_draft_generation_context({"sales_order": "SAL-ORD-0001"})
        try:
            ms.on_sales_invoice_before_mapping(
                frappe._dict(), "before_mapping", self._source(), table_maps
            )
        finally:
            ms._clear_draft_generation_context()

        self.assertEqual(table_maps["Sales Order"]["validation"], {})

    def test_only_the_docstatus_check_is_removed(self):
        table_maps = self._table_maps()
        table_maps["Sales Order"]["validation"]["customer"] = ["!=", "Test Customer"]
        ms._set_draft_generation_context({"sales_order": "SAL-ORD-0001"})
        try:
            ms.on_sales_invoice_before_mapping(
                frappe._dict(), "before_mapping", self._source(), table_maps
            )
        finally:
            ms._clear_draft_generation_context()

        self.assertEqual(
            table_maps["Sales Order"]["validation"], {"customer": ["!=", "Test Customer"]}
        )

    def test_the_context_is_gone_again_after_the_call(self):
        ms._set_draft_generation_context({"sales_order": "SAL-ORD-0001"})
        ms._clear_draft_generation_context()

        self.assertIsNone(ms._draft_generation_context())

    def test_clearing_a_context_that_is_not_there_is_harmless(self):
        ms._clear_draft_generation_context()

        self.assertIsNone(ms._draft_generation_context())


class TestSubmitGuard(unittest.TestCase):
    """A Sales Order cannot be submitted before its milestones are billed."""

    def test_a_milestone_without_an_invoice_blocks_the_submission(self):
        doc = _order([_row()])

        with self.assertRaises(frappe.ValidationError) as error:
            ms.on_sales_order_before_submit(doc)

        self.assertIn("Generate Invoice", str(error.exception))
        self.assertIn("Upfront", str(error.exception))

    def test_an_order_without_milestones_is_not_blocked(self):
        doc = _order([_row(invoice_portion=0)])

        ms.on_sales_order_before_submit(doc)

    def test_an_order_with_the_schedule_off_is_not_blocked(self):
        doc = _order([_row()], pd_custom_enable_invoice_schedule=0)

        ms.on_sales_order_before_submit(doc)

    def test_a_milestone_that_is_already_invoiced_does_not_block(self):
        doc = _order([_row(milestone_status=ms.STATUS_INVOICED)])

        ms.on_sales_order_before_submit(doc)

    def test_a_link_to_a_missing_invoice_blocks_the_submission(self):
        doc = _order(
            [_row(milestone_status=ms.STATUS_DRAFT_CREATED, sales_invoice="SINV-GONE-0001")]
        )

        with patch.object(frappe.db, "exists", return_value=False):
            with self.assertRaises(frappe.ValidationError) as error:
                ms.on_sales_order_before_submit(doc)

        self.assertIn("SINV-GONE-0001", str(error.exception))

    def test_a_link_to_an_invoice_of_another_company_blocks_the_submission(self):
        doc = _order([_row(milestone_status=ms.STATUS_DRAFT_CREATED, sales_invoice="SINV-0001")])

        with (
            patch.object(frappe.db, "exists", return_value=True),
            patch.object(
                frappe.db,
                "get_value",
                side_effect=[0, "Other Company", "Test Customer", "THB"],
            ),
        ):
            with self.assertRaises(frappe.ValidationError) as error:
                ms.on_sales_order_before_submit(doc)

        self.assertIn("another company", str(error.exception))

    def test_a_link_to_an_invoice_of_another_customer_blocks_the_submission(self):
        doc = _order([_row(milestone_status=ms.STATUS_DRAFT_CREATED, sales_invoice="SINV-0001")])

        with (
            patch.object(frappe.db, "exists", return_value=True),
            patch.object(
                frappe.db,
                "get_value",
                side_effect=[0, "Test Company", "Other Customer", "THB"],
            ),
        ):
            with self.assertRaises(frappe.ValidationError) as error:
                ms.on_sales_order_before_submit(doc)

        self.assertIn("another customer", str(error.exception))

    def test_a_link_to_a_submitted_invoice_blocks_the_submission(self):
        doc = _order([_row(milestone_status=ms.STATUS_DRAFT_CREATED, sales_invoice="SINV-0001")])

        with (
            patch.object(frappe.db, "exists", return_value=True),
            patch.object(
                frappe.db,
                "get_value",
                side_effect=[1, "Test Company", "Test Customer", "THB"],
            ),
        ):
            with self.assertRaises(frappe.ValidationError) as error:
                ms.on_sales_order_before_submit(doc)

        self.assertIn("not a draft", str(error.exception))

    def test_a_draft_invoice_of_this_order_does_not_block(self):
        doc = _order([_row(milestone_status=ms.STATUS_DRAFT_CREATED, sales_invoice="SINV-0001")])

        with (
            patch.object(frappe.db, "exists", return_value=True),
            patch.object(
                frappe.db,
                "get_value",
                side_effect=[0, "Test Company", "Test Customer", "THB", "2026-08-21"],
            ),
        ):
            ms.on_sales_order_before_submit(doc)


class TestAmendmentAndLinkOwnership(unittest.TestCase):
    """An amendment is a new contract, and the links have to follow that."""

    def test_an_amendment_releases_the_links_it_inherited(self):
        row = _row(milestone_status=ms.STATUS_INVOICED, sales_invoice="SINV-OLD-0001")
        doc = _order([row], amended_from="SAL-ORD-0001", __islocal=1)

        ms.prepare_amended_schedule(doc)

        self.assertEqual(row.milestone_status, ms.STATUS_NOT_INVOICED)
        self.assertIsNone(row.sales_invoice)

    def test_a_normal_draft_keeps_its_links(self):
        row = _row(milestone_status=ms.STATUS_INVOICED, sales_invoice="SINV-OLD-0001")
        doc = _order([row], __islocal=1)

        ms.prepare_amended_schedule(doc)

        self.assertEqual(row.milestone_status, ms.STATUS_INVOICED)
        self.assertEqual(row.sales_invoice, "SINV-OLD-0001")

    def test_an_amendment_that_was_saved_already_keeps_its_own_links(self):
        row = _row(milestone_status=ms.STATUS_INVOICED, sales_invoice="SINV-OLD-0001")
        doc = _order([row], amended_from="SAL-ORD-0001", __islocal=0)

        ms.prepare_amended_schedule(doc)

        self.assertEqual(row.sales_invoice, "SINV-OLD-0001")

    def test_the_submission_keeps_a_link_that_belongs_to_this_order(self):
        row = _row(milestone_status=ms.STATUS_DRAFT_CREATED, sales_invoice="SINV-0001")
        doc = _order([row])

        with (
            patch.object(ms, "_invoice_belongs_to_order", return_value=True),
            patch.object(frappe.db, "set_value") as set_value,
        ):
            ms.on_sales_order_submit(doc)

        set_value.assert_not_called()
        self.assertEqual(row.sales_invoice, "SINV-0001")

    def test_the_submission_releases_a_link_of_another_contract(self):
        row = _row(milestone_status=ms.STATUS_INVOICED, sales_invoice="SINV-OLD-0001")
        doc = _order([row])

        with (
            patch.object(ms, "_invoice_belongs_to_order", return_value=False),
            patch.object(frappe.db, "set_value") as set_value,
        ):
            ms.on_sales_order_submit(doc)

        self.assertEqual(row.milestone_status, ms.STATUS_NOT_INVOICED)
        self.assertIsNone(row.sales_invoice)
        self.assertEqual(row.invoice_amount, 60000.0)
        set_value.assert_called_once()


class TestGeneration(unittest.TestCase):
    """What the generation endpoint does with the plan."""

    def _milestones(self) -> list[Any]:
        return [
            _row(name="row-1", payment_term="Upfront", invoice_portion=20),
            _row(
                name="row-2",
                payment_term="Delivery",
                invoice_portion=80,
                invoice_amount=240000.0,
            ),
        ]

    def _generate(self, rows: list[Any], **kwargs: Any) -> Any:
        doc = _order(rows, **kwargs)

        return doc

    def test_the_preview_reports_the_plan_and_creates_nothing(self):
        rows = self._milestones()
        doc = self._generate(rows)

        with (
            patch.object(frappe, "get_doc", return_value=doc),
            patch.object(frappe, "has_permission", return_value=True),
            patch.object(ms, "_lock_sales_order"),
            patch.object(ms, "_build_milestone_invoice") as build,
        ):
            result = ms.generate_milestone_invoices("SAL-ORD-0001", preview=1)

        build.assert_not_called()
        self.assertEqual(result["created"], [])
        self.assertEqual(len(result["plan"]), 2)
        self.assertEqual(result["plan"][0]["milestone"], "Upfront")
        self.assertEqual(result["plan"][0]["invoice_amount"], 60000.0)
        self.assertEqual(result["plan"][1]["invoice_amount"], 240000.0)

    def test_every_milestone_gets_its_own_draft_invoice(self):
        rows = self._milestones()
        doc = self._generate(rows)
        invoices = [Invoice("SINV-0001"), Invoice("SINV-0002")]

        with (
            patch.object(frappe, "get_doc", return_value=doc),
            patch.object(frappe, "has_permission", return_value=True),
            patch.object(ms, "_lock_sales_order"),
            patch.object(ms, "_build_milestone_invoice", side_effect=invoices),
            patch.object(frappe.db, "set_value") as set_value,
        ):
            result = ms.generate_milestone_invoices("SAL-ORD-0001")

        self.assertEqual(len(result["created"]), 2)
        self.assertEqual(result["created"][0]["sales_invoice"], "SINV-0001")
        self.assertEqual(result["created"][1]["sales_invoice"], "SINV-0002")
        self.assertEqual(result["created"][0]["milestone"], "Upfront")

        for invoice in invoices:
            self.assertEqual(invoice.inserted, [{"ignore_permissions": True}])

        self.assertEqual(set_value.call_count, 2)
        self.assertEqual(
            set_value.call_args_list[0][0][2]["milestone_status"], ms.STATUS_DRAFT_CREATED
        )
        self.assertEqual(set_value.call_args_list[0][0][2]["sales_invoice"], "SINV-0001")

        self.assertEqual(rows[0].milestone_status, ms.STATUS_DRAFT_CREATED)
        self.assertEqual(rows[0].sales_invoice, "SINV-0001")

    def test_a_second_run_creates_nothing(self):
        rows = self._milestones()
        for row in rows:
            row.milestone_status = ms.STATUS_DRAFT_CREATED
            row.sales_invoice = "SINV-0001"

        doc = self._generate(rows)

        with (
            patch.object(frappe, "get_doc", return_value=doc),
            patch.object(frappe, "has_permission", return_value=True),
            patch.object(ms, "_lock_sales_order"),
            patch.object(ms, "_build_milestone_invoice") as build,
        ):
            result = ms.generate_milestone_invoices("SAL-ORD-0001")

        build.assert_not_called()
        self.assertEqual(result["created"], [])
        self.assertEqual(len(result["skipped"]), 2)

    def test_the_order_has_to_be_saved_before_anything_is_created(self):
        doc = _order(self._milestones(), name=None)

        with (
            patch.object(frappe, "get_doc", return_value=doc),
            patch.object(frappe, "has_permission", return_value=True),
            patch.object(ms, "_lock_sales_order"),
            patch.object(ms, "_build_milestone_invoice") as build,
        ):
            with self.assertRaises(frappe.ValidationError) as error:
                ms.generate_milestone_invoices(None)

        build.assert_not_called()
        self.assertIn("Save the Sales Order before generating invoices.", str(error.exception))

    def test_a_failure_rolls_the_invoices_back(self):
        rows = self._milestones()
        doc = self._generate(rows)
        failing = Invoice("SINV-0001")

        with (
            patch.object(frappe, "get_doc", return_value=doc),
            patch.object(frappe, "has_permission", return_value=True),
            patch.object(ms, "_lock_sales_order"),
            patch.object(
                ms,
                "_build_milestone_invoice",
                side_effect=[failing, RuntimeError("no invoice for you")],
            ),
            patch.object(frappe.db, "set_value"),
            patch.object(frappe.db, "rollback") as rollback,
        ):
            with self.assertRaises(RuntimeError):
                ms.generate_milestone_invoices("SAL-ORD-0001")

        rollback.assert_called_once()

    def test_the_order_is_locked_while_the_invoices_are_made(self):
        doc = _order(self._milestones())

        with (
            patch.object(frappe, "get_doc", return_value=doc),
            patch.object(frappe, "has_permission", return_value=True),
            patch.object(ms, "_lock_sales_order") as lock,
            patch.object(ms, "_build_milestone_invoice"),
        ):
            ms.generate_milestone_invoices("SAL-ORD-0001", preview=1)

        lock.assert_called_once_with("SAL-ORD-0001")

    def test_the_schedule_has_to_be_enabled(self):
        doc = _order(self._milestones(), pd_custom_enable_invoice_schedule=0)

        with (
            patch.object(frappe, "get_doc", return_value=doc),
            patch.object(frappe, "has_permission", return_value=True),
        ):
            with self.assertRaises(frappe.ValidationError) as error:
                ms.generate_milestone_invoices("SAL-ORD-0001")

        self.assertIn("Invoice Schedule", str(error.exception))

    def test_the_user_has_to_be_allowed_to_create_an_invoice(self):
        doc = _order(self._milestones())

        with (
            patch.object(frappe, "get_doc", return_value=doc),
            patch.object(frappe, "has_permission", return_value=False),
        ):
            with self.assertRaises(frappe.ValidationError) as error:
                ms.generate_milestone_invoices("SAL-ORD-0001")

        self.assertIn("Not permitted", str(error.exception))


class _Tax(frappe._dict):
    """A row of the tax table of an invoice."""

    def precision(self, fieldname: str, parentfield: str | None = None) -> int:
        return 2


class _Invoice(frappe._dict):
    """A Sales Invoice that is just enough for the allocation."""

    def precision(self, fieldname: str, parentfield: str | None = None) -> int:
        return 2


class TestFixedAmountAllocation(unittest.TestCase):
    """A flat charge and a fixed discount belong to the whole contract.

    The mapper copies them onto every invoice it builds, so a plan of several
    milestones would charge them once per milestone.
    """

    def _invoice(self, discount: float = 1000, tax: float = 100) -> Any:
        return _Invoice(
            {
                "discount_amount": discount,
                "additional_discount_percentage": 0,
                "taxes": [_Tax({"charge_type": "Actual", "tax_amount": tax})],
            }
        )

    def test_a_fixed_amount_is_split_over_the_milestones(self):
        portions = [20, 60, 20]

        allocated = [
            ms._allocate_fixed_value(100, portions, index, 2) for index in range(len(portions))
        ]

        self.assertEqual(allocated, [20.0, 60.0, 20.0])
        self.assertEqual(flt(sum(allocated)), 100.0)

    def test_the_last_milestone_carries_the_rounding_remainder(self):
        portions = [33.33, 33.33, 33.34]

        allocated = [
            ms._allocate_fixed_value(1000, portions, index, 2) for index in range(len(portions))
        ]

        self.assertEqual(flt(sum(allocated)), 1000.0)

    def test_a_milestone_without_a_portion_gets_nothing(self):
        self.assertEqual(ms._allocate_fixed_value(100, [0, 100], 0, 2), 0)

    def test_the_flat_charge_and_the_fixed_discount_are_split(self):
        rows = [
            _row(name="row-1", invoice_portion=40),
            _row(name="row-2", invoice_portion=60),
        ]
        so = _order(rows)

        first = self._invoice()
        ms._allocate_fixed_amounts(first, so, rows[0])

        self.assertEqual(first.get("discount_amount"), 400.0)
        self.assertEqual(first["taxes"][0]["tax_amount"], 40.0)

        second = self._invoice()
        ms._allocate_fixed_amounts(second, so, rows[1])

        self.assertEqual(second.get("discount_amount"), 600.0)
        self.assertEqual(second["taxes"][0]["tax_amount"], 60.0)

        # the invoices of the plan add up to the contract amount
        self.assertEqual(flt(first.get("discount_amount") + second.get("discount_amount")), 1000.0)
        self.assertEqual(
            flt(first["taxes"][0]["tax_amount"] + second["taxes"][0]["tax_amount"]),
            100.0,
        )

    def test_a_discount_in_percent_is_left_to_erpnext(self):
        # ERPNext works a discount in percent out again from the total of the
        # invoice, so it follows the milestone on its own.
        rows = [_row(name="row-1", invoice_portion=40)]
        so = _order(rows)
        invoice = self._invoice()
        invoice.additional_discount_percentage = 5

        ms._allocate_fixed_amounts(invoice, so, rows[0])

        self.assertEqual(invoice.get("discount_amount"), 1000)

    def test_a_charge_in_percent_is_left_to_erpnext(self):
        rows = [_row(name="row-1", invoice_portion=40)]
        so = _order(rows)
        invoice = _Invoice(
            {"taxes": [_Tax({"charge_type": "On Net Total", "tax_amount": 0, "rate": 7})]}
        )

        ms._allocate_fixed_amounts(invoice, so, rows[0])

        self.assertEqual(invoice["taxes"][0]["tax_amount"], 0)
