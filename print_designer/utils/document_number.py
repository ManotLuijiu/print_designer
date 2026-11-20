"""
Printed Document Number
=======================

Resolves which document number is printed on a document.

By default an amended document is printed with the number of the ORIGINAL
document (the root of the ``amended_from`` chain), e.g. ``SAL-QTN-2026-00001``
is printed for both ``SAL-QTN-2026-00001-1`` and ``SAL-QTN-2026-00001-2``.

The behaviour is controlled by the Print Settings check field
``pd_print_document_number``:

    1 -> print the root document number (default)
    0 -> print the document's own number

The value is read from ``doc.flags.print_settings`` - Frappe merges the saved
Print Settings with the values of the print preview sidebar into that dict -
so the sidebar can switch it per print job. Nothing is persisted: the number
is resolved at print time and the document name is never changed.
"""

import frappe
from frappe.utils import cint

# Print Settings check field that controls the behaviour
PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME = "pd_print_document_number"

# Safety limit for the amendment chain walk
MAX_AMENDMENT_DEPTH = 20


def get_root_document_number(doctype, name, max_depth=MAX_AMENDMENT_DEPTH):
	"""Return the number of the first document of the amendment chain.

	Walks ``amended_from`` upwards. Stops on a cycle, on a missing parent or
	after ``max_depth`` steps, so it can never loop forever.
	"""
	if not doctype or not name:
		return name

	if not frappe.get_meta(doctype).get_field("amended_from"):
		return name

	current = name
	seen = {name}

	for _ in range(max_depth):
		amended_from = frappe.db.get_value(doctype, current, "amended_from")
		if not amended_from or amended_from in seen:
			break
		seen.add(amended_from)
		current = amended_from

	return current


def is_root_document_number_enabled(doc, print_settings=None):
	"""True when the root document number has to be printed."""
	if print_settings is None:
		flags = getattr(doc, "flags", None)
		print_settings = getattr(flags, "print_settings", None) or {}

	value = print_settings.get(PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME)
	if value is None:
		value = frappe.db.get_single_value(
			"Print Settings", PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME
		)
	if value is None:
		# Never stored: fall back to the field default
		df = frappe.get_meta("Print Settings").get_field(PRINT_ROOT_DOCUMENT_NUMBER_FIELDNAME)
		value = df.default if df else 0
	return cint(value if isinstance(value, (int, float, str)) else 0) == 1


def resolve_printed_document_number(doc):
	"""The number that has to be printed for `doc`."""
	if isinstance(doc, dict):
		name = doc.get("name")
		doctype = doc.get("doctype")
	else:
		name = getattr(doc, "name", None)
		doctype = getattr(doc, "doctype", None)

	if not name or not doctype or not is_root_document_number_enabled(doc):
		return name

	root = get_root_document_number(doctype, name)
	return root or name


def print_field_value(doc, fieldname):
	"""Jinja helper: the printed value of a field of the document.

	Behaves like ``doc.get_formatted(fieldname)`` for every field, except the
	document number, which follows the root document number rule.
	"""
	if fieldname == "name":
		number = resolve_printed_document_number(doc)
		if number:
			return number

	get_formatted = getattr(doc, "get_formatted", None)
	if get_formatted is None:
		return doc.get(fieldname) if isinstance(doc, dict) else None

	return get_formatted(fieldname)


def apply_printed_document_number(doc, *args, **kwargs):
	"""Print hook: print the root document number of an amended document.

	The print templates render the document number with
	``doc.get_formatted("name")``. For the print run only that call is wrapped,
	so the number of the original document (the root of the amendment chain) is
	printed instead of the number of the amendment.

	Nothing is persisted and the document name is never changed.
	"""
	if not doc or not getattr(doc, "flags", None):
		return

	if not doc.flags.in_print:
		return

	if getattr(doc, "_printed_document_number_patched", False):
		return

	print_settings = getattr(doc.flags, "print_settings", None) or {}
	if not print_settings:
		for value in list(args) + list(kwargs.values()):
			if isinstance(value, dict):
				print_settings = value
				break

	if not is_root_document_number_enabled(doc, print_settings):
		return

	original_get_formatted = doc.get_formatted

	def get_formatted(fieldname, *args, **kwargs):
		if fieldname == "name":
			number = resolve_printed_document_number(doc)
			if number:
				return number
		return original_get_formatted(fieldname, *args, **kwargs)

	doc.get_formatted = get_formatted
	doc._printed_document_number_patched = True
