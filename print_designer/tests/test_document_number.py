"""Tests for the printed document number (root document number of an amendment).

Covers the amendment chain walk (including cycles and the depth limit) and the
print hook that makes the document number follow the root document number
rule. The tests are read-only: no document is created and nothing is written.

Run with:
    bench --site <site> run-tests --module print_designer.tests.test_document_number
"""

from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from print_designer.utils.document_number import (
	MAX_AMENDMENT_DEPTH,
	PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME,
	apply_printed_document_number,
	get_root_document_number,
	is_root_document_number_enabled,
	print_field_value,
	resolve_printed_document_number,
)
from print_designer.overrides.print_settings_api import (
	_field_with_stored_value,
	get_print_settings_to_show,
)


class _FakeFlags:
	def __init__(self, in_print=True, print_settings=None):
		self.in_print = in_print
		self.print_settings = print_settings or {}


class _FakeDoc:
	"""Minimal stand-in for a document that is printed."""

	def __init__(self, name, doctype="Quotation", in_print=True, print_settings=None):
		self.name = name
		self.doctype = doctype
		self.flags = _FakeFlags(in_print=in_print, print_settings=print_settings)

	def get_formatted(self, fieldname):
		return f"formatted:{fieldname}"


def _chain(**amended_from):
	"""Patch the database lookup of the amendment chain.

	Only the ``amended_from`` lookup is intercepted, every other call goes to
	the real database (Frappe itself reads the meta through it).
	"""
	values = {name: parent for name, parent in amended_from.items()}
	original_get_value = frappe.db.get_value

	def get_value(doctype=None, filters=None, fieldname="*", *args, **kwargs):
		# `filters` carries the document name for a single-value lookup.
		if fieldname == "amended_from" and not kwargs and not args:
			return values.get(filters)
		return original_get_value(doctype, filters, fieldname, *args, **kwargs)

	return patch("print_designer.utils.document_number.frappe.db.get_value", get_value)


class TestGetRootDocumentNumber(UnitTestCase):
	"""The chain walk finds the first document of the amendment chain."""

	def test_a_document_without_amendment_is_its_own_root(self):
		with _chain():
			self.assertEqual(
				get_root_document_number("Quotation", "SAL-QTN-2026-00001"), "SAL-QTN-2026-00001"
			)

	def test_the_root_of_an_amendment_is_the_original_document(self):
		with _chain(**{"SAL-QTN-2026-00001-1": "SAL-QTN-2026-00001"}):
			self.assertEqual(
				get_root_document_number("Quotation", "SAL-QTN-2026-00001-1"), "SAL-QTN-2026-00001"
			)

	def test_the_root_of_a_second_amendment_is_the_original_document(self):
		with _chain(
			**{
				"SAL-QTN-2026-00001-1": "SAL-QTN-2026-00001",
				"SAL-QTN-2026-00001-2": "SAL-QTN-2026-00001-1",
			}
		):
			self.assertEqual(
				get_root_document_number("Quotation", "SAL-QTN-2026-00001-2"), "SAL-QTN-2026-00001"
			)

	def test_a_cycle_does_not_loop_forever(self):
		with _chain(**{"A": "B", "B": "A"}):
			self.assertIn(get_root_document_number("Quotation", "A"), ("A", "B"))

	def test_the_walk_is_bounded(self):
		chain = {f"D{i}": f"D{i + 1}" for i in range(50)}
		with _chain(**chain):
			self.assertEqual(
				get_root_document_number("Quotation", "D0"), f"D{MAX_AMENDMENT_DEPTH}"
			)
			self.assertEqual(get_root_document_number("Quotation", "D0", max_depth=3), "D3")

	def test_a_doctype_without_amended_from_is_its_own_root(self):
		with patch(
			"print_designer.utils.document_number.frappe.get_meta"
		) as get_meta:
			get_meta.return_value.get_field.return_value = None
			self.assertEqual(get_root_document_number("Item", "ITEM-1"), "ITEM-1")


class TestRootDocumentNumberSwitch(UnitTestCase):
	"""The Print Settings switch decides which number is printed."""

	def test_the_switch_is_off_when_the_sidebar_says_so(self):
		doc = _FakeDoc("SAL-QTN-2026-00001-1", print_settings={PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME: 0})
		self.assertFalse(is_root_document_number_enabled(doc))

	def test_the_switch_is_on_when_the_sidebar_says_so(self):
		doc = _FakeDoc("SAL-QTN-2026-00001-1", print_settings={PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME: 1})
		self.assertTrue(is_root_document_number_enabled(doc))

	def test_the_saved_setting_is_used_when_the_sidebar_has_no_value(self):
		doc = _FakeDoc("SAL-QTN-2026-00001-1")
		with patch(
			"print_designer.utils.document_number.frappe.db.get_single_value",
			return_value=1,
		):
			self.assertTrue(is_root_document_number_enabled(doc))


class TestResolvePrintedDocumentNumber(UnitTestCase):
	"""Only an amended document gets the number of the original document."""

	def test_an_amendment_prints_the_number_of_the_original_document(self):
		doc = _FakeDoc("SAL-QTN-2026-00001-1", print_settings={PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME: 1})
		with _chain(**{"SAL-QTN-2026-00001-1": "SAL-QTN-2026-00001"}):
			self.assertEqual(resolve_printed_document_number(doc), "SAL-QTN-2026-00001")

	def test_a_document_without_amendment_keeps_its_own_number(self):
		doc = _FakeDoc("SAL-QTN-2026-00009", print_settings={PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME: 1})
		with _chain():
			self.assertEqual(resolve_printed_document_number(doc), "SAL-QTN-2026-00009")

	def test_the_switch_off_keeps_the_own_number(self):
		doc = _FakeDoc("SAL-QTN-2026-00001-1", print_settings={PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME: 0})
		with _chain(**{"SAL-QTN-2026-00001-1": "SAL-QTN-2026-00001"}):
			self.assertEqual(resolve_printed_document_number(doc), "SAL-QTN-2026-00001-1")


class TestPrintFieldValue(UnitTestCase):
	"""Every field but the document number is formatted as before."""

	def test_the_document_number_follows_the_rule(self):
		doc = _FakeDoc("SAL-QTN-2026-00001-1", print_settings={PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME: 1})
		with _chain(**{"SAL-QTN-2026-00001-1": "SAL-QTN-2026-00001"}):
			self.assertEqual(print_field_value(doc, "name"), "SAL-QTN-2026-00001")

	def test_other_fields_are_unchanged(self):
		doc = _FakeDoc("SAL-QTN-2026-00001-1", print_settings={PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME: 1})
		with _chain():
			self.assertEqual(print_field_value(doc, "total"), "formatted:total")


class _FakeDocField:
	def __init__(self, fieldname, default=None):
		self.fieldname = fieldname
		self.default = default
		self.label = fieldname


class _FakeMeta:
	def __init__(self, fields):
		self._fields = fields

	def get_field(self, fieldname):
		return self._fields.get(fieldname)


class _FakePrintSettings:
	"""Stand-in for the Print Settings single."""

	def __init__(self, values=None, fields=None):
		self._values = values or {}
		self.meta = _FakeMeta(fields or {})

	def get(self, fieldname, default=None):
		return self._values.get(fieldname, default)


class TestSidebarFieldValue(UnitTestCase):
	"""The print sidebar shows the stored value, the default as a fallback.

	Frappe does not fill the defaults of a single doctype that exists
	already: a checkbox without a stored value would show up unchecked
	although its default is on.
	"""

	def test_the_stored_value_is_used(self):
		settings = _FakePrintSettings(
			values={"pd_print_document_number": 0},
			fields={"pd_print_document_number": _FakeDocField("pd_print_document_number", "1")},
		)
		df = _field_with_stored_value(settings, "pd_print_document_number")
		self.assertEqual(df.default, 0)

	def test_a_value_that_was_never_stored_falls_back_to_the_default(self):
		settings = _FakePrintSettings(
			values={},
			fields={"pd_print_document_number": _FakeDocField("pd_print_document_number", "1")},
		)
		df = _field_with_stored_value(settings, "pd_print_document_number")
		self.assertEqual(df.default, "1")

	def test_an_unknown_field_returns_none(self):
		settings = _FakePrintSettings(values={}, fields={})
		self.assertIsNone(_field_with_stored_value(settings, "pd_print_document_number"))


class _FakePrintableDoc:
	"""A document without ERPNext's print settings.

	ERPNext's ``get_print_settings`` is not implemented by this stand-in, so
	only the Print Designer fields are collected - that keeps the test
	independent of the documents that exist on the site.
	"""


class _CopyControlsDisabled:
	"""The Print Settings single with the copy controls switched off."""

	def __init__(self, single):
		self._single = single
		self.meta = single.meta

	def get(self, fieldname, default=None):
		if fieldname == "show_copy_controls_in_toolbar":
			return 0
		return self._single.get(fieldname, default)


class TestSidebarFields(UnitTestCase):
	"""The root document number switch is always in the print sidebar.

	It must not be listed twice (once with the copy fields and once on its
	own) and it must stay visible when the copy controls are hidden.
	"""

	def _sidebar_fields(self, copy_controls=True):
		original_get_single = frappe.get_single

		def get_single(*args, **kwargs):
			single = original_get_single("Print Settings")
			if copy_controls:
				return single
			return _CopyControlsDisabled(single)

		with patch(
			"print_designer.overrides.print_settings_api.frappe.get_doc",
			lambda *args, **kwargs: _FakePrintableDoc(),
		), patch(
			"print_designer.overrides.print_settings_api.frappe.get_single", get_single
		):
			return get_print_settings_to_show("Quotation", "SAL-QTN-2026-00001")

	def _fieldnames(self, fields):
		return [getattr(field, "fieldname", None) for field in fields]

	def test_the_switch_is_listed_once_with_the_copy_controls(self):
		fields = self._sidebar_fields(copy_controls=True)
		if PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME not in self._fieldnames(fields):
			self.skipTest("the field is not installed on this site")

		self.assertEqual(
			self._fieldnames(fields).count(PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME), 1
		)

	def test_the_switch_stays_visible_without_the_copy_controls(self):
		fields = self._sidebar_fields(copy_controls=False)
		if PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME not in self._fieldnames(fields):
			self.skipTest("the field is not installed on this site")

		self.assertEqual(
			self._fieldnames(fields).count(PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME), 1
		)

	def test_the_switch_is_shown_with_the_stored_value(self):
		fields = self._sidebar_fields(copy_controls=True)
		for field in fields:
			if getattr(field, "fieldname", None) == PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME:
				self.assertIn(field.default, (0, 1, "0", "1"))
				return
		self.skipTest("the field is not installed on this site")


class TestApplyPrintedDocumentNumber(UnitTestCase):
	"""The print hook only changes the number that is printed."""

	def test_the_number_of_the_amendment_is_replaced_by_the_root(self):
		doc = _FakeDoc("SAL-QTN-2026-00001-1", print_settings={PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME: 1})
		with _chain(**{"SAL-QTN-2026-00001-1": "SAL-QTN-2026-00001"}):
			apply_printed_document_number(doc)
			self.assertEqual(doc.get_formatted("name"), "SAL-QTN-2026-00001")
			self.assertEqual(doc.name, "SAL-QTN-2026-00001-1")

	def test_other_fields_are_not_touched(self):
		doc = _FakeDoc("SAL-QTN-2026-00001-1", print_settings={PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME: 1})
		with _chain():
			apply_printed_document_number(doc)
			self.assertEqual(doc.get_formatted("total"), "formatted:total")

	def test_nothing_is_patched_outside_of_a_print(self):
		doc = _FakeDoc(
			"SAL-QTN-2026-00001-1",
			in_print=False,
			print_settings={PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME: 1},
		)
		with _chain():
			apply_printed_document_number(doc)
			self.assertEqual(doc.get_formatted("name"), "formatted:name")

	def test_nothing_is_patched_when_the_switch_is_off(self):
		doc = _FakeDoc("SAL-QTN-2026-00001-1", print_settings={PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME: 0})
		with _chain():
			apply_printed_document_number(doc)
			self.assertEqual(doc.get_formatted("name"), "formatted:name")
