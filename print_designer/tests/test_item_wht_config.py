"""Tests for the item driven WHT configuration.

``print_designer/custom/item_wht_config.py`` fills the WHT fields of a
transaction from the items it contains:

* ``pd_custom_vat_treatment``   - "VAT Undue" for service items
* ``pd_custom_wht_income_type`` - the income type of the item master
* ``pd_custom_withholding_tax_pct`` / ``pd_custom_withholding_tax_amount`` -
  the rate of that income type and the resulting amount
"""

import unittest

import frappe

from print_designer.custom.item_wht_config import (
	DEFAULT_VAT_TREATMENT,
	SERVICE_VAT_TREATMENT,
	get_description,
	parse_rate_from_name,
	resolve_wht_fields,
)

SERVICE_ITEM = "มัดจำสำหรับ Dashboard for BI"
GOODS_ITEM = "Item-001"

INCOME_TYPE = "Service Fees 3% (PND53)"


def _site_available():
	"""Return True when the tests run against a connected site."""
	try:
		frappe.db.sql("select 1")
		return True
	except Exception:
		return False



class TestParseRateFromName(unittest.TestCase):
	"""The rate can be derived from the name of the category."""

	def test_parses_percentage(self):
		self.assertEqual(parse_rate_from_name("Service Fees 3% (PND53)"), 3)
		self.assertEqual(parse_rate_from_name("Agricultural 0.75% (PND53)"), 0.75)
		self.assertEqual(parse_rate_from_name("Royalty (Foreign) 15% (PND54)"), 15)

	def test_returns_none_without_percentage(self):
		self.assertIsNone(parse_rate_from_name("Service Fees"))
		self.assertIsNone(parse_rate_from_name(""))
		self.assertIsNone(parse_rate_from_name(None))


class TestResolveWhtFields(unittest.TestCase):
	"""The pure resolution of the WHT fields from the items."""

	def setUp(self):
		self.item_config_map = {
			SERVICE_ITEM: {"income_type": INCOME_TYPE, "is_service_item": 1},
			GOODS_ITEM: {"income_type": None, "is_service_item": 0},
		}
		self.rate_map = {INCOME_TYPE: 3}

	def resolve(self, **kwargs):
		params = {
			"rows": [{"item_code": SERVICE_ITEM}],
			"item_config_map": self.item_config_map,
			"rate_map": self.rate_map,
		}
		params.update(kwargs)
		return resolve_wht_fields(**params)

	def test_income_type_taken_from_the_item(self):
		result = self.resolve()
		self.assertEqual(result["income_type"], INCOME_TYPE)
		self.assertTrue(result["income_type_auto"])

	def test_manual_income_type_is_kept(self):
		result = self.resolve(doc_income_type="Rental 5% (PND53)")
		self.assertEqual(result["income_type"], "Rental 5% (PND53)")
		self.assertFalse(result["income_type_auto"])

	def test_rate_is_taken_from_the_income_type(self):
		result = self.resolve()
		self.assertEqual(result["wht_rate"], 3)
		self.assertEqual(result["withholding_tax_pct"], 3)

	def test_manual_percentage_is_kept(self):
		result = self.resolve(doc_pct=5)
		self.assertEqual(result["withholding_tax_pct"], 5)

	def test_service_item_sets_vat_undue(self):
		result = self.resolve(doc_vat_treatment=DEFAULT_VAT_TREATMENT)
		self.assertEqual(result["vat_treatment"], SERVICE_VAT_TREATMENT)
		self.assertTrue(result["has_service_item"])

	def test_goods_item_keeps_standard_vat(self):
		result = self.resolve(
			rows=[{"item_code": GOODS_ITEM}],
			doc_vat_treatment=DEFAULT_VAT_TREATMENT,
		)
		self.assertEqual(result["vat_treatment"], DEFAULT_VAT_TREATMENT)
		self.assertFalse(result["has_service_item"])

	def test_manual_exempt_vat_treatment_is_kept(self):
		result = self.resolve(doc_vat_treatment="Exempt from VAT")
		self.assertEqual(result["vat_treatment"], "Exempt from VAT")

	def test_manual_zero_rated_vat_treatment_is_kept(self):
		result = self.resolve(doc_vat_treatment="Zero-rated for Export")
		self.assertEqual(result["vat_treatment"], "Zero-rated for Export")

	def test_first_item_with_an_income_type_wins(self):
		result = self.resolve(
			rows=[{"item_code": GOODS_ITEM}, {"item_code": SERVICE_ITEM}]
		)
		self.assertEqual(result["income_type"], INCOME_TYPE)

	def test_no_items_leaves_everything_untouched(self):
		result = self.resolve(rows=[])
		self.assertIsNone(result["income_type"])
		self.assertIsNone(result["wht_rate"])
		self.assertIsNone(result["vat_treatment"])


class TestGetDescription(unittest.TestCase):
	"""The description of a *Tax Withholding Category*."""

	def test_returns_empty_without_an_income_type(self):
		self.assertEqual(get_description(None), "")
		self.assertEqual(get_description(""), "")


@unittest.skipUnless(_site_available(), "requires a connected site")
class TestGetDescriptionFromSite(unittest.TestCase):
	"""The description is read from the installed category."""

	def test_description_is_taken_from_the_category(self):
		rows = frappe.get_all(
			"Tax Withholding Category",
			filters={"name": INCOME_TYPE},
			fields=["category_name", "category_name_en"],
			limit=1,
		)
		if not rows:
			self.skipTest("the category is not installed on this site")
		expected = rows[0].get("category_name_en") or rows[0].get("category_name")
		self.assertEqual(get_description(INCOME_TYPE), expected)


if __name__ == "__main__":
	unittest.main()
