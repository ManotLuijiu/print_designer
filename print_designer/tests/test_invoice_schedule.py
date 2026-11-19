"""Tests for the Sales Order milestone (Invoice Schedule) billing.

The parts that only do arithmetic are tested without touching the database,
so they still give a signal before the Invoice Schedule DocType has been
migrated in. The document level tests are skipped until then.
"""

import unittest
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from print_designer.custom import invoice_schedule as ms


def _invoice_schedule_installed():
	return frappe.db.exists("DocType", "Invoice Schedule") and frappe.db.exists(
		"Custom Field", {"dt": "Sales Order", "fieldname": "pd_custom_invoice_schedule"}
	)


class TestMilestoneArithmetic(unittest.TestCase):
	"""The pure calculation helpers."""

	def test_milestone_qty_is_a_clean_fraction_of_the_contract(self):
		so_item = frappe._dict(qty=40, rate=7500, amount=300000)

		self.assertEqual(ms._milestone_qty(so_item, 20), 8.0)
		self.assertEqual(ms._milestone_qty(so_item, 60), 24.0)
		self.assertEqual(ms._milestone_qty(so_item, 20), 8.0)

	def test_milestone_qty_totals_back_to_the_contract_quantity(self):
		so_item = frappe._dict(qty=40, rate=7500, amount=300000)

		total = sum(ms._milestone_qty(so_item, p) for p in (20, 60, 20))

		self.assertEqual(total, so_item.qty)

	def test_milestone_qty_keeps_fractional_portions_usable(self):
		so_item = frappe._dict(qty=3, rate=10000, amount=30000)

		self.assertAlmostEqual(ms._milestone_qty(so_item, 33.33), 0.9999, places=4)
		self.assertAlmostEqual(ms._milestone_qty(so_item, 33.33) * 3, 2.9997, places=4)

	def test_milestone_line_multiplies_out(self):
		"""The whole point - the invoice line adds up without any override."""
		so_item = frappe._dict(qty=40, rate=7500, amount=300000)

		qty = ms._milestone_qty(so_item, 20)
		amount = qty * so_item.rate

		self.assertEqual(amount, 60000.0)

	def test_item_description_states_the_derivation(self):
		so_item = frappe._dict(qty=40, rate=7500, amount=300000, description="Software build")
		row = frappe._dict(payment_term="Upfront")

		description = ms._build_item_description(so_item, row, 20)

		self.assertIn("Upfront", description)
		self.assertIn("40", description)
		self.assertIn("7,500.00", description)
		self.assertIn("300,000.00", description)
		self.assertIn("60,000.00", description)
		self.assertIn("Software build", description)

	def test_flt_formats_with_thousands_separator(self):
		self.assertEqual(ms._flt(300000), "300,000.00")
		self.assertEqual(ms._flt(60), "60.00")

	def test_remaining_portion_is_what_is_still_not_covered(self):
		doc = frappe._doc = frappe._dict(
			pd_custom_invoice_schedule=[
				frappe._dict(invoice_portion=20),
				frappe._dict(invoice_portion=60),
			]
		)

		self.assertEqual(ms._remaining_portion(doc), 20.0)

	def test_remaining_portion_never_goes_below_zero(self):
		doc = frappe._dict(
			pd_custom_invoice_schedule=[frappe._dict(invoice_portion=120)]
		)

		self.assertEqual(ms._remaining_portion(doc), 0.0)

	def test_next_milestone_label_avoids_a_collision(self):
		doc = frappe._dict(
			pd_custom_invoice_schedule=[frappe._dict(payment_term="Milestone 1")]
		)

		label = ms._next_milestone_label(doc)

		self.assertNotEqual(label.lower(), "milestone 1")
		self.assertTrue(label.startswith("Milestone"))


class TestInvoiceScheduleDocument(FrappeTestCase):
	"""Document level behaviour."""

	def setUp(self):
		if not _invoice_schedule_installed():
			self.skipTest("Invoice Schedule has not been migrated in yet")

	def test_refresh_invoice_amounts_uses_the_contract_base(self):
		doc = frappe.new_doc("Sales Order")
		doc.net_total = 300000
		doc.pd_custom_enable_invoice_schedule = 1
		doc.append(
			"pd_custom_invoice_schedule",
			{"payment_term": "Upfront", "invoice_portion": 20},
		)
		doc.append(
			"pd_custom_invoice_schedule",
			{"payment_term": "Delivery", "invoice_portion": 60},
		)

		ms.refresh_invoice_amounts(doc)

		self.assertEqual(doc.pd_custom_invoice_schedule[0].invoice_amount, 60000.0)
		self.assertEqual(doc.pd_custom_invoice_schedule[1].invoice_amount, 180000.0)
		self.assertEqual(
			doc.pd_custom_invoice_schedule[0].milestone_status, ms.STATUS_NOT_INVOICED
		)

	def test_refresh_invoice_amounts_freezes_an_invoiced_milestone(self):
		doc = frappe.new_doc("Sales Order")
		doc.net_total = 300000
		doc.pd_custom_enable_invoice_schedule = 1
		doc.append(
			"pd_custom_invoice_schedule",
			{
				"payment_term": "Upfront",
				"invoice_portion": 20,
				"invoice_amount": 60000.0,
				"milestone_status": ms.STATUS_INVOICED,
			},
		)

		ms.refresh_invoice_amounts(doc)

		self.assertEqual(doc.pd_custom_invoice_schedule[0].invoice_amount, 60000.0)

	def test_refresh_invoice_amounts_marks_a_row_without_a_source_as_manual(self):
		doc = frappe.new_doc("Sales Order")
		doc.net_total = 300000
		doc.pd_custom_enable_invoice_schedule = 1
		doc.append(
			"pd_custom_invoice_schedule",
			{"payment_term": "Hand written", "invoice_portion": 10},
		)

		ms.refresh_invoice_amounts(doc)

		row = doc.pd_custom_invoice_schedule[0]
		self.assertEqual(row.milestone_source, ms.SOURCE_MANUAL)
		self.assertEqual(row.invoice_amount, 30000.0)

	def test_refresh_invoice_amounts_keeps_the_seed_source(self):
		doc = frappe.new_doc("Sales Order")
		doc.net_total = 300000
		doc.pd_custom_enable_invoice_schedule = 1
		doc.append(
			"pd_custom_invoice_schedule",
			{
				"payment_term": "Upfront",
				"invoice_portion": 20,
				"milestone_source": ms.SOURCE_PAYMENT_SCHEDULE,
			},
		)

		ms.refresh_invoice_amounts(doc)

		self.assertEqual(
			doc.pd_custom_invoice_schedule[0].milestone_source, ms.SOURCE_PAYMENT_SCHEDULE
		)

	def test_refresh_invoice_amounts_is_a_no_op_when_disabled(self):
		doc = frappe.new_doc("Sales Order")
		doc.net_total = 300000
		doc.append("pd_custom_invoice_schedule", {"payment_term": "Upfront", "invoice_portion": 20})

		ms.refresh_invoice_amounts(doc)

		self.assertFalse(doc.pd_custom_invoice_schedule[0].invoice_amount)

	def test_an_amended_order_starts_with_a_clean_plan(self):
		"""An amendment is a new contract, so its milestones start over."""
		doc = frappe.new_doc("Sales Order")
		doc.net_total = 300000
		doc.pd_custom_enable_invoice_schedule = 1
		row = doc.append(
			"pd_custom_invoice_schedule",
			{
				"payment_term": "Upfront",
				"invoice_portion": 20,
				"invoice_amount": 60000.0,
				"milestone_status": ms.STATUS_INVOICED,
				"sales_invoice": "SINV-TEST-0001",
			},
		)
		row.name = "test-milestone-row"

		with patch.object(frappe.db, "set_value") as set_value:
			ms.on_sales_order_submit(doc)

		self.assertEqual(row.milestone_status, ms.STATUS_NOT_INVOICED)
		self.assertIsNone(row.sales_invoice)
		# the amount is worked out against the contract, not the portion
		self.assertEqual(row.invoice_amount, 60000.0)

		set_value.assert_called_once()
		values = set_value.call_args[0][2]
		self.assertEqual(values["milestone_status"], ms.STATUS_NOT_INVOICED)
		self.assertIsNone(values["sales_invoice"])
		self.assertEqual(values["invoice_amount"], 60000.0)

	def test_a_milestone_without_an_invoice_is_left_alone_on_submit(self):
		doc = frappe.new_doc("Sales Order")
		doc.net_total = 300000
		doc.pd_custom_enable_invoice_schedule = 1
		row = doc.append(
			"pd_custom_invoice_schedule",
			{
				"payment_term": "Upfront",
				"invoice_portion": 20,
				"invoice_amount": 60000.0,
				"milestone_status": ms.STATUS_NOT_INVOICED,
			},
		)
		row.name = "test-milestone-row"

		with patch.object(frappe.db, "set_value") as set_value:
			ms.on_sales_order_submit(doc)

		set_value.assert_not_called()
		self.assertEqual(row.milestone_status, ms.STATUS_NOT_INVOICED)

	def test_service_order_skips_the_delivery_note(self):
		doc = frappe.new_doc("Sales Order")
		doc.pd_custom_enable_invoice_schedule = 1
		doc.append("items", {"item_code": "NON-EXISTENT-SERVICE-ITEM", "qty": 1, "rate": 100})

		ms.set_skip_delivery_note(doc)

		self.assertEqual(doc.skip_delivery_note, 1)

	def test_stock_order_keeps_the_delivery_note(self):
		stock_item = frappe.db.get_value("Item", {"is_stock_item": 1}, "name")
		if not stock_item:
			self.skipTest("This site has no stock item to test with")

		doc = frappe.new_doc("Sales Order")
		doc.pd_custom_enable_invoice_schedule = 1
		doc.append("items", {"item_code": stock_item, "qty": 1, "rate": 100})

		ms.set_skip_delivery_note(doc)

		self.assertEqual(doc.skip_delivery_note, 0)

	def test_disabled_order_keeps_the_delivery_note(self):
		doc = frappe.new_doc("Sales Order")
		doc.pd_custom_enable_invoice_schedule = 0
		doc.append("items", {"item_code": "NON-EXISTENT-SERVICE-ITEM", "qty": 1, "rate": 100})

		ms.set_skip_delivery_note(doc)

		self.assertEqual(doc.skip_delivery_note, 0)


class TestInvoiceScheduleAutoCopy(FrappeTestCase):
	"""The Invoice Schedule fills itself from the Payment Schedule."""

	def setUp(self):
		if not _invoice_schedule_installed():
			self.skipTest("Invoice Schedule has not been migrated in yet")

	def _order(self, enabled=1, previous_enabled=None):
		doc = frappe.new_doc("Sales Order")
		doc.pd_custom_enable_invoice_schedule = enabled

		if previous_enabled is not None:
			previous = frappe.new_doc("Sales Order")
			previous.pd_custom_enable_invoice_schedule = previous_enabled
			doc._doc_before_save = previous

		return doc

	def test_the_payment_schedule_is_copied_when_billing_starts(self):
		doc = self._order()
		doc.append("payment_schedule", {"payment_term": "Upfront", "invoice_portion": 20})
		doc.append("payment_schedule", {"payment_term": "Delivery", "invoice_portion": 80})

		ms.sync_invoice_schedule_from_payment_schedule(doc)

		self.assertEqual(len(doc.pd_custom_invoice_schedule), 2)
		self.assertEqual(doc.pd_custom_invoice_schedule[0].payment_term, "Upfront")
		self.assertEqual(doc.pd_custom_invoice_schedule[0].invoice_portion, 20.0)
		self.assertEqual(doc.pd_custom_invoice_schedule[1].invoice_portion, 80.0)
		self.assertEqual(
			doc.pd_custom_invoice_schedule[0].milestone_source, ms.SOURCE_PAYMENT_SCHEDULE
		)

	def test_nothing_is_copied_while_billing_is_off(self):
		doc = self._order(enabled=0)
		doc.append("payment_schedule", {"payment_term": "Upfront", "invoice_portion": 20})

		ms.sync_invoice_schedule_from_payment_schedule(doc)

		self.assertEqual(len(doc.pd_custom_invoice_schedule), 0)

	def test_nothing_is_copied_when_billing_was_already_on(self):
		doc = self._order(previous_enabled=1)
		doc.append("payment_schedule", {"payment_term": "Upfront", "invoice_portion": 20})

		ms.sync_invoice_schedule_from_payment_schedule(doc)

		self.assertEqual(len(doc.pd_custom_invoice_schedule), 0)

	def test_a_milestone_that_is_already_there_is_never_overwritten(self):
		doc = self._order()
		doc.append("payment_schedule", {"payment_term": "Upfront", "invoice_portion": 20})
		doc.append("payment_schedule", {"payment_term": "Delivery", "invoice_portion": 80})
		doc.append(
			"pd_custom_invoice_schedule", {"payment_term": "Upfront", "invoice_portion": 10}
		)

		ms.sync_invoice_schedule_from_payment_schedule(doc)

		self.assertEqual(len(doc.pd_custom_invoice_schedule), 2)
		# the edited portion survives
		self.assertEqual(doc.pd_custom_invoice_schedule[0].invoice_portion, 10.0)
		# the missing one is added
		self.assertEqual(doc.pd_custom_invoice_schedule[1].payment_term, "Delivery")
		self.assertEqual(doc.pd_custom_invoice_schedule[1].invoice_portion, 80.0)

	def test_a_payment_schedule_row_without_a_portion_is_ignored(self):
		doc = self._order()
		doc.append("payment_schedule", {"payment_term": "Upfront", "invoice_portion": 0})

		ms.sync_invoice_schedule_from_payment_schedule(doc)

		self.assertEqual(len(doc.pd_custom_invoice_schedule), 0)

	def test_the_validate_hook_copies_the_plan_and_computes_the_amounts(self):
		doc = self._order()
		doc.net_total = 300000
		doc.append("payment_schedule", {"payment_term": "Upfront", "invoice_portion": 20})

		ms.sales_order_invoice_schedule(doc)

		self.assertEqual(len(doc.pd_custom_invoice_schedule), 1)
		self.assertEqual(doc.pd_custom_invoice_schedule[0].invoice_amount, 60000.0)

	def test_seeding_reports_what_it_added_and_what_it_left_alone(self):
		doc = self._order()
		doc.append("payment_schedule", {"payment_term": "Upfront", "invoice_portion": 20})
		doc.append("payment_schedule", {"payment_term": "Delivery", "invoice_portion": 80})
		doc.append(
			"pd_custom_invoice_schedule", {"payment_term": "Upfront", "invoice_portion": 10}
		)

		added, skipped = ms._seed_missing_milestones(doc)

		self.assertEqual(added, 1)
		self.assertEqual(skipped, 1)


class TestMilestoneInvoiceDeletion(FrappeTestCase):
	"""A draft milestone invoice has to be deletable again."""

	def test_a_deleted_invoice_releases_its_milestone(self):
		doc = frappe.new_doc("Sales Invoice")
		doc.name = "TEST-MILESTONE-INVOICE"

		with patch.object(frappe.db, "set_value") as set_value, patch.object(
			frappe,
			"get_all",
			return_value=[frappe._dict({"name": "row-1", "parent": "TEST-SALES-ORDER-0001"})],
		):
			ms.on_sales_invoice_delete(doc)

		set_value.assert_called_once_with(
			"Invoice Schedule",
			"row-1",
			{"sales_invoice": None, "milestone_status": ms.STATUS_NOT_INVOICED},
		)

	def test_the_invoice_schedule_link_does_not_block_the_deletion(self):
		from print_designer import hooks

		self.assertIn("Invoice Schedule", hooks.ignore_links_on_delete)

	def test_the_delete_hook_is_wired_up(self):
		from print_designer import hooks

		self.assertEqual(
			hooks.doc_events["Sales Invoice"]["after_delete"],
			"print_designer.custom.invoice_schedule.on_sales_invoice_delete",
		)
