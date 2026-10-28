"""Unit tests for the automatic "Subject to Withholding Tax" flag.

The flag ``pd_custom_subject_to_wht`` must be switched on automatically when the
document items contain an item whose Item Group is "Services" (for example the
"Dashboard for BI" item).

Run standalone (no site required):

    cd /home/frappe/frappe-bench
    env/bin/python -m unittest apps.print_designer.print_designer.tests.test_service_item_wht
"""

import unittest

from print_designer.custom.service_item_wht import (
	SERVICE_ITEM_GROUP,
	SUBJECT_TO_WHT_FIELD,
	apply_subject_to_wht_from_items,
	get_service_item_codes,
	is_service_item_group,
)


class FakeMeta:
	"""Minimal stand-in for frappe model meta."""

	def __init__(self, fields):
		self._fields = list(fields)

	def has_field(self, fieldname):
		return fieldname in self._fields


class FakeDoc:
	"""Minimal stand-in for a Frappe document."""

	doctype = "Sales Order"

	def __init__(self, items, fields=(SUBJECT_TO_WHT_FIELD,), **values):
		self.name = "SO-TEST-0001"
		self.items = items
		self.meta = FakeMeta(fields)
		self._values = dict(values)

	def get(self, key, default=None):
		if key == "items":
			return self.items
		return self._values.get(key, default)

	def set(self, key, value):
		self._values[key] = value


class FakeSalesInvoice(FakeDoc):
	"""Sales Invoice variant - the field is installed for Sales Invoice as well."""

	doctype = "Sales Invoice"

	def __init__(self, items, **values):
		super().__init__(items, **values)
		self.name = "SINV-TEST-0001"


class TestIsServiceItemGroup(unittest.TestCase):
	def test_exact_match(self):
		self.assertTrue(is_service_item_group("Services"))

	def test_case_insensitive(self):
		self.assertTrue(is_service_item_group("services"))
		self.assertTrue(is_service_item_group("SERVICES"))
		self.assertTrue(is_service_item_group("  Services  "))

	def test_other_groups(self):
		for group in ("Products", "All Item Groups", "Service", "Services Extra"):
			self.assertFalse(is_service_item_group(group), group)

	def test_empty(self):
		self.assertFalse(is_service_item_group(None))
		self.assertFalse(is_service_item_group(""))

	def test_service_group_constant(self):
		self.assertEqual(SERVICE_ITEM_GROUP, "Services")


class TestGetServiceItemCodes(unittest.TestCase):
	def test_no_items(self):
		self.assertEqual(get_service_item_codes(FakeDoc([])), [])

	def test_service_row(self):
		doc = FakeDoc([{"item_code": "Dashboard for BI", "item_group": "Services"}])
		self.assertEqual(get_service_item_codes(doc), ["Dashboard for BI"])

	def test_mixed_rows(self):
		doc = FakeDoc(
			[
				{"item_code": "Laptop", "item_group": "Products"},
				{"item_code": "Dashboard for BI", "item_group": "Services"},
			]
		)
		self.assertEqual(get_service_item_codes(doc), ["Dashboard for BI"])

	def test_row_without_item_group_uses_item_group_map(self):
		doc = FakeDoc([{"item_code": "Dashboard for BI"}])
		group_map = {"Dashboard for BI": "Services"}
		self.assertEqual(get_service_item_codes(doc, group_map), ["Dashboard for BI"])

	def test_row_without_item_group_and_without_map(self):
		doc = FakeDoc([{"item_code": "Dashboard for BI"}])
		self.assertEqual(get_service_item_codes(doc, {}), [])

	def test_rows_without_item_code_are_ignored(self):
		doc = FakeDoc([{"item_group": "Services"}])
		self.assertEqual(get_service_item_codes(doc), [])


class TestApplySubjectToWhtFromItems(unittest.TestCase):
	def test_enables_flag_for_service_item(self):
		doc = FakeDoc([{"item_code": "Dashboard for BI", "item_group": "Services"}])
		result = apply_subject_to_wht_from_items(doc)
		self.assertEqual(result, ["Dashboard for BI"])
		self.assertEqual(doc.get(SUBJECT_TO_WHT_FIELD), 1)

	def test_keeps_flag_untouched_without_service_item(self):
		doc = FakeDoc([{"item_code": "Laptop", "item_group": "Products"}])
		result = apply_subject_to_wht_from_items(doc)
		self.assertEqual(result, [])
		self.assertIsNone(doc.get(SUBJECT_TO_WHT_FIELD))

	def test_never_clears_a_manually_set_flag(self):
		doc = FakeDoc(
			[{"item_code": "Laptop", "item_group": "Products"}],
			**{SUBJECT_TO_WHT_FIELD: 1},
		)
		apply_subject_to_wht_from_items(doc)
		self.assertEqual(doc.get(SUBJECT_TO_WHT_FIELD), 1)

	def test_manually_set_flag_stays_set_for_service_item(self):
		doc = FakeDoc(
			[{"item_code": "Dashboard for BI", "item_group": "Services"}],
			**{SUBJECT_TO_WHT_FIELD: 1},
		)
		apply_subject_to_wht_from_items(doc)
		self.assertEqual(doc.get(SUBJECT_TO_WHT_FIELD), 1)

	def test_no_field_on_document_is_a_noop(self):
		doc = FakeDoc(
			[{"item_code": "Dashboard for BI", "item_group": "Services"}],
			fields=(),
		)
		result = apply_subject_to_wht_from_items(doc)
		self.assertEqual(result, [])
		self.assertIsNone(doc.get(SUBJECT_TO_WHT_FIELD))

	def test_empty_document(self):
		doc = FakeDoc([])
		self.assertEqual(apply_subject_to_wht_from_items(doc), [])
		self.assertIsNone(doc.get(SUBJECT_TO_WHT_FIELD))


class TestSalesInvoice(unittest.TestCase):
	"""The rule applies to Sales Invoice as well (the field is installed there)."""

	def test_enables_flag_for_service_item(self):
		doc = FakeSalesInvoice([{"item_code": "Dashboard for BI", "item_group": "Services"}])
		self.assertEqual(apply_subject_to_wht_from_items(doc), ["Dashboard for BI"])
		self.assertEqual(doc.get(SUBJECT_TO_WHT_FIELD), 1)

	def test_keeps_flag_untouched_without_service_item(self):
		doc = FakeSalesInvoice([{"item_code": "Laptop", "item_group": "Products"}])
		self.assertEqual(apply_subject_to_wht_from_items(doc), [])
		self.assertIsNone(doc.get(SUBJECT_TO_WHT_FIELD))

	def test_never_clears_a_manually_set_flag(self):
		doc = FakeSalesInvoice(
			[{"item_code": "Laptop", "item_group": "Products"}],
			**{SUBJECT_TO_WHT_FIELD: 1},
		)
		apply_subject_to_wht_from_items(doc)
		self.assertEqual(doc.get(SUBJECT_TO_WHT_FIELD), 1)


if __name__ == "__main__":
	unittest.main()
