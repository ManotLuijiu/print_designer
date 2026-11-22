"""Tests for the read-only VAT preview of a draft Sales Invoice (SI-03).

``print_designer/api/sales_invoice_vat_preview.py`` is the one endpoint of
the preview.  It projects the decision of the SI-01 contract for one saved
draft invoice.

The tests cover:

* the split of the VAT of the invoice into the part that is due and the
  prospective undue part,
* the projection: the marker of a draft, the status, the base and the VAT,
* the guards: a new invoice, an unknown invoice, a submitted invoice and an
  invoice the user may not read are refused,
* the fact that the preview writes nothing: no row of the Output VAT Undue
  ledger, no GL entry and no change of the invoice.
"""

import unittest
from unittest.mock import patch

import frappe
import frappe.utils
from frappe.tests.utils import FrappeTestCase

from print_designer.api import sales_invoice_vat_preview as preview
from print_designer.custom.sales_invoice_tax_contract import (
	CLASSIFICATION_GOODS,
	CLASSIFICATION_SERVICES,
	REASON_ALREADY_DUE,
	REASON_DEFERRED_SERVICE,
	REASON_EXEMPT_SUPPLY,
	VAT_TREATMENT_DUE,
	VAT_TREATMENT_EXEMPT,
	VAT_TREATMENT_UNDUE,
	build_service_tax_snapshot,
)
from print_designer.custom.thai_company_registration import (
	VAT_STATUS_REGISTERED,
	CompanyRegistration,
)

SERVICE_ITEM = "PD-SERVICE-TEST"
VAT_ACCOUNT = "VAT - Test"


def make_registration(kind=VAT_STATUS_REGISTERED, status="Registered"):
	return CompanyRegistration(kind=kind, status=status)


def service_row(item_code=SERVICE_ITEM, base=1000.0, currency=1000.0):
	return {
		"item_code": item_code,
		"is_service": True,
		"is_stock": False,
		"base_net_amount": base,
		"net_amount": currency,
	}


def goods_row(item_code=SERVICE_ITEM, base=1000.0, currency=1000.0):
	return {
		"item_code": item_code,
		"is_service": False,
		"is_stock": True,
		"base_net_amount": base,
		"net_amount": currency,
	}


def vat_row(account=VAT_ACCOUNT, rate=7.0, amount=70.0, base=70.0):
	return {
		"account_head": account,
		"description": "VAT",
		"charge_type": "On Net Total",
		"rate": rate,
		"tax_amount": amount,
		"base_tax_amount": base,
		"is_tax_withholding_account": 0,
	}


def build(**kwargs):
	"""Build a snapshot of a decision with sensible defaults."""
	params = {
		"identity": {
			"sales_invoice": "SINV-0001",
			"docstatus": 0,
			"posting_date": "2026-01-15",
			"company": "Test Company",
			"currency": "THB",
			"company_currency": "THB",
			"net_total": 1000.0,
		},
		"registration": make_registration(),
		"treatment": VAT_TREATMENT_UNDUE,
		"item_rows": [service_row()],
		"vat_rows": [vat_row()],
	}
	params.update(kwargs)
	return build_service_tax_snapshot(**params)


def invoice_doc(**overrides):
	"""A document of a draft invoice."""
	doc = frappe._dict(
		{
			"name": "SINV-0001",
			"company": "Test Company",
			"posting_date": "2026-01-15",
			"customer": "Test Customer",
			"docstatus": 0,
		}
	)
	doc.update(overrides)
	return doc


class TestTheSplitOfTheVat(unittest.TestCase):
	"""The VAT of the invoice is split into the due part and the undue part."""

	def test_a_deferred_service_carries_a_prospective_undue_vat(self):
		due, undue = preview.split_vat(build())

		self.assertEqual(due, 0.0)
		self.assertEqual(undue, 70.0)

	def test_a_sale_whose_tax_point_is_reached_carries_a_due_vat(self):
		due, undue = preview.split_vat(build(treatment=VAT_TREATMENT_DUE))

		self.assertEqual(due, 70.0)
		self.assertEqual(undue, 0.0)

	def test_a_sale_without_a_vat_liability_carries_neither(self):
		due, undue = preview.split_vat(build(treatment=VAT_TREATMENT_EXEMPT))

		self.assertEqual(due, 0.0)
		self.assertEqual(undue, 0.0)


class TestTheProjection(unittest.TestCase):
	"""The projection carries the decision of the invoice."""

	def _projection(self, **kwargs):
		snapshot = build(**kwargs)
		with patch.object(preview, "get_service_tax_snapshot", return_value=snapshot):
			return preview.build_vat_preview(invoice_doc())

	def test_the_projection_is_marked_as_a_draft_preview(self):
		result = self._projection()

		self.assertEqual(result["marker"], preview.DRAFT_PREVIEW_MARKER)
		self.assertTrue(result["is_draft_preview"])

	def test_the_projection_carries_the_identity_of_the_invoice(self):
		result = self._projection()

		self.assertEqual(result["sales_invoice"], "SINV-0001")
		self.assertEqual(result["company"], "Test Company")
		self.assertEqual(result["customer"], "Test Customer")

	def test_a_deferred_service_is_pending_with_an_undue_vat(self):
		result = self._projection()

		self.assertEqual(result["status"], "Pending")
		self.assertEqual(result["treatment_reason"], REASON_DEFERRED_SERVICE)
		self.assertEqual(result["undue_vat_amount"], 70.0)
		self.assertEqual(result["due_vat_amount"], 0.0)

	def test_a_sale_whose_tax_point_is_reached_is_already_due(self):
		result = self._projection(treatment=VAT_TREATMENT_DUE)

		self.assertEqual(result["status"], "Already Due")
		self.assertEqual(result["treatment_reason"], REASON_ALREADY_DUE)
		self.assertEqual(result["due_vat_amount"], 70.0)
		self.assertEqual(result["undue_vat_amount"], 0.0)

	def test_an_exempt_supply_carries_no_liability(self):
		result = self._projection(treatment=VAT_TREATMENT_EXEMPT)

		self.assertEqual(result["status"], "Not Applicable")
		self.assertEqual(result["treatment_reason"], REASON_EXEMPT_SUPPLY)
		self.assertEqual(result["due_vat_amount"], 0.0)
		self.assertEqual(result["undue_vat_amount"], 0.0)

	def test_the_projection_carries_the_base_and_the_vat(self):
		result = self._projection()

		self.assertEqual(result["service_base_amount"], 1000.0)
		self.assertEqual(result["vat_amount"], 70.0)

	def test_a_service_sale_is_tracked(self):
		result = self._projection()

		self.assertEqual(result["classification"], CLASSIFICATION_SERVICES)
		self.assertTrue(result["is_tracked"])

	def test_a_goods_sale_is_not_tracked(self):
		result = self._projection(item_rows=[goods_row()])

		self.assertEqual(result["classification"], CLASSIFICATION_GOODS)
		self.assertFalse(result["is_tracked"])


class TestTheGuards(unittest.TestCase):
	"""Only a saved draft of one invoice is accepted."""

	def test_a_missing_name_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			preview.get_draft_vat_preview("")

	def test_an_unknown_invoice_is_refused(self):
		with patch.object(frappe.db, "exists", return_value=0):
			with self.assertRaises(frappe.ValidationError):
				preview.get_draft_vat_preview("SINV-NOT-THERE")

	def test_a_submitted_invoice_is_refused(self):
		doc = invoice_doc(docstatus=1)
		with patch.object(frappe.db, "exists", return_value=1):
			with patch.object(frappe, "get_doc", return_value=doc):
				with self.assertRaises(frappe.ValidationError):
					preview.get_draft_vat_preview("SINV-0001")

	def test_an_invoice_that_may_not_be_read_is_refused(self):
		doc = invoice_doc()
		with patch.object(frappe.db, "exists", return_value=1):
			with patch.object(frappe, "get_doc", return_value=doc):
				with patch.object(frappe, "has_permission", return_value=False):
					with self.assertRaises(frappe.PermissionError):
						preview.get_draft_vat_preview("SINV-0001")

	def test_an_invoice_without_a_company_is_refused(self):
		doc = invoice_doc(company=None)
		with patch.object(frappe.db, "exists", return_value=1):
			with patch.object(frappe, "get_doc", return_value=doc):
				with patch.object(frappe, "has_permission", return_value=True):
					with self.assertRaises(frappe.ValidationError):
						preview.get_draft_vat_preview("SINV-0001")


class TestThePreviewOnTheSite(FrappeTestCase):
	"""The preview of a saved draft on a site that carries ERPNext."""

	company: str
	customer: str

	@classmethod
	def setUpClass(cls):
		super().setUpClass()

		if "erpnext" not in frappe.get_installed_apps():
			raise unittest.SkipTest("ERPNext is not installed on this site")

		companies = frappe.get_all("Company", filters={"is_group": 0}, limit=1, pluck="name")
		customers = frappe.get_all("Customer", filters={"disabled": 0}, limit=1, pluck="name")
		cls.company = companies[0] if companies else ""
		cls.customer = customers[0] if customers else ""

		if not (cls.company and cls.customer):
			raise unittest.SkipTest("this site has no company or customer")

	@classmethod
	def tearDownClass(cls):
		frappe.db.rollback()
		super().tearDownClass()

	def tearDown(self):
		frappe.db.rollback()
		super().tearDown()

	def _draft_invoice(self):
		"""A saved draft invoice with one service row."""
		# The item is taken inside the test: the rollback of the test takes
		# the item of the class with it, so it has to exist again.
		item_code = _service_item(self.company)
		invoice = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"company": self.company,
				"customer": self.customer,
				"posting_date": frappe.utils.nowdate(),
				"due_date": frappe.utils.add_days(frappe.utils.nowdate(), 30),
				"items": [
					{
						"item_code": item_code,
						"qty": 1,
						"rate": 1000,
						"delivery_date": frappe.utils.nowdate(),
					}
				],
			}
		)
		invoice.insert(ignore_permissions=True)
		return invoice

	def test_the_preview_of_a_draft_carries_the_marker(self):
		invoice = self._draft_invoice()

		result = preview.get_draft_vat_preview(invoice.name)

		self.assertEqual(result["marker"], preview.DRAFT_PREVIEW_MARKER)
		self.assertEqual(result["sales_invoice"], invoice.name)
		self.assertEqual(result["company"], self.company)

	def test_the_preview_writes_nothing(self):
		invoice = self._draft_invoice()
		modified = frappe.db.get_value("Sales Invoice", invoice.name, "modified")

		preview.get_draft_vat_preview(invoice.name)

		if frappe.db.table_exists("Output VAT Undue"):
			self.assertEqual(
				frappe.db.count("Output VAT Undue", {"sales_invoice": invoice.name}), 0
			)

		self.assertEqual(
			frappe.db.count(
				"GL Entry", {"voucher_type": "Sales Invoice", "voucher_no": invoice.name}
			),
			0,
		)
		self.assertEqual(frappe.db.get_value("Sales Invoice", invoice.name, "docstatus"), 0)
		self.assertEqual(
			frappe.db.get_value("Sales Invoice", invoice.name, "modified"), modified
		)

	def test_a_submitted_invoice_is_refused_on_the_site(self):
		invoice = self._draft_invoice()
		invoice.submit()

		with self.assertRaises(frappe.ValidationError):
			preview.get_draft_vat_preview(invoice.name)


def _service_item(company):
	"""A service item for the test."""
	existing = frappe.get_all(
		"Item",
		filters={"is_stock_item": 0, "disabled": 0, "item_group": "Services"},
		limit=1,
		pluck="name",
	)
	if existing:
		return str(existing[0])

	item = frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": SERVICE_ITEM,
			"item_name": SERVICE_ITEM,
			"item_group": "Services",
			"is_stock_item": 0,
			"is_sales_item": 1,
			"company": company,
		}
	)
	item.insert(ignore_permissions=True)
	return str(item.name)
