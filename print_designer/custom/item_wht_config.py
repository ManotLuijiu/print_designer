"""Fill the Thailand WHT fields of a transaction from its Item rows.

The withholding tax configuration of a transaction is driven by the items it
contains.  Every item can carry two master data fields:

``Item.pd_custom_is_service_item``
    Marks the item as a service (the field is also used for the VAT
    treatment suggestion).

``Item.pd_custom_wht_income_type``
    The *Tax Withholding Category* that applies to the item.

They drive three fields of the document:

``pd_custom_vat_treatment``
    An item that is flagged as a service is not subject to the standard VAT,
    so the treatment becomes ``VAT Undue``.  A deliberate manual choice
    (``Exempt from VAT`` / ``Zero-rated for Export``) is never overwritten.

``pd_custom_wht_income_type``
    The income type of the first item that defines one.  A value the user
    entered manually is kept.

``pd_custom_withholding_tax_pct`` / ``pd_custom_withholding_tax_amount``
    The rate of the effective income type is used for
    ``pd_custom_withholding_tax_pct``.  The amount itself is calculated from
    the net total by the DocType specific calculation (see
    ``quotation_calculations.calculate_withholding_tax_amounts`` and its
    Sales Order / Sales Invoice counterparts).

The rate of a *Tax Withholding Category* is resolved in this order:

1. the linked ``Thai WHT Income Type`` (``pd_custom_thai_wht_income_type``)
   and its ``tax_rate``
2. the percentage in the category name (``Service Fees 3% (PND53)`` -> 3)

The server side is authoritative.  The client script
``public/js/thailand_wht/thailand_wht_vat_helper.js`` mirrors the result
while the user edits the form.
"""

import json
import re

import frappe
from frappe.utils import flt

#: Item master fields
ITEM_INCOME_TYPE_FIELD = "pd_custom_wht_income_type"
ITEM_SERVICE_FIELD = "pd_custom_is_service_item"

#: Document fields
DOC_INCOME_TYPE_FIELD = "pd_custom_wht_income_type"
DOC_PCT_FIELD = "pd_custom_withholding_tax_pct"
DOC_VAT_TREATMENT_FIELD = "pd_custom_vat_treatment"
DOC_DESCRIPTION_FIELD = "pd_custom_wht_description"

#: VAT treatment values
DEFAULT_VAT_TREATMENT = "Standard VAT"
SERVICE_VAT_TREATMENT = "VAT Undue"
MANUAL_VAT_TREATMENTS = ("Exempt from VAT", "Zero-rated for Export")

#: "Service Fees 3% (PND53)" -> 3
_PERCENT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*%")


def parse_rate_from_name(name):
	"""Return the percentage encoded in a category name, e.g. 3 for "Fees 3% (PND53)"."""
	if not name:
		return None
	match = _PERCENT_PATTERN.search(str(name))
	if not match:
		return None
	return flt(match.group(1))


def _meta_has_field(doctype, fieldname):
	"""Return True when ``doctype`` has the given field."""
	if not frappe.db.exists("DocType", doctype):
		return False
	try:
		return bool(frappe.get_meta(doctype).has_field(fieldname))
	except Exception:
		return False


def _to_int(value):
	"""Return 1 for a truthy value, 0 otherwise."""
	return 1 if value else 0


def get_item_wht_config_map(item_codes):
	"""Return ``{item_code: {"income_type": str | None, "is_service_item": int}}``.

	Items without the master data fields are returned with empty values, so
	the caller can simply look up every item of the document.
	"""
	item_codes = [code for code in item_codes if code]
	if not item_codes:
		return {}

	fields = ["name"]
	has_income_type = _meta_has_field("Item", ITEM_INCOME_TYPE_FIELD)
	has_service_flag = _meta_has_field("Item", ITEM_SERVICE_FIELD)
	if has_income_type:
		fields.append(ITEM_INCOME_TYPE_FIELD)
	if has_service_flag:
		fields.append(ITEM_SERVICE_FIELD)

	rows = frappe.get_all(
		"Item",
		filters={"name": ["in", item_codes]},
		fields=fields,
		limit_page_length=0,
	)

	config_map = {}
	for code in item_codes:
		config_map[code] = {"income_type": None, "is_service_item": 0}

	for row in rows:
		config_map[row.name] = {
			"income_type": row.get(ITEM_INCOME_TYPE_FIELD) if has_income_type else None,
			"is_service_item": _to_int(row.get(ITEM_SERVICE_FIELD)) if has_service_flag else 0,
		}

	return config_map


def get_rate_map(income_types):
	"""Return ``{income_type: rate}`` for the given *Tax Withholding Category* names."""
	income_types = [name for name in income_types if name]
	if not income_types:
		return {}

	link_field = "pd_custom_thai_wht_income_type"
	has_link = _meta_has_field("Tax Withholding Category", link_field)

	linked = {}
	if has_link:
		for row in frappe.get_all(
			"Tax Withholding Category",
			filters={"name": ["in", income_types]},
			fields=["name", link_field],
			limit_page_length=0,
		):
			linked[row.name] = row.get(link_field)

	thai_types = [name for name in linked.values() if name]
	rates = {}
	if thai_types and frappe.db.exists("DocType", "Thai WHT Income Type"):
		for row in frappe.get_all(
			"Thai WHT Income Type",
			filters={"name": ["in", thai_types]},
			fields=["name", "tax_rate"],
			limit_page_length=0,
		):
			rates[row.name] = flt(row.get("tax_rate"))

	rate_map = {}
	for name in income_types:
		rate = rates.get(linked.get(name))
		if rate is None:
			rate = parse_rate_from_name(name)
		rate_map[name] = rate

	return rate_map


def get_description(income_type):
	"""Return the description of a *Tax Withholding Category* in the user language.

	The category carries a Thai (``category_name``) and an English
	(``category_name_en``) label.  The language of the current user decides
	which one is used, the same way the client script does it.
	"""
	if not income_type:
		return ""

	language = (frappe.local.lang or "en").lower()
	field = "category_name" if language.startswith("th") else "category_name_en"
	if not _meta_has_field("Tax Withholding Category", field):
		field = "category_name" if field == "category_name_en" else "category_name_en"
		if not _meta_has_field("Tax Withholding Category", field):
			return ""

	rows = frappe.get_all(
		"Tax Withholding Category",
		filters={"name": income_type},
		fields=[field],
		limit=1,
	)
	return (rows[0].get(field) or "") if rows else ""


def resolve_wht_fields(
	doc_income_type=None,
	doc_pct=None,
	doc_vat_treatment=None,
	rows=None,
	item_config_map=None,
	rate_map=None,
):
	"""Resolve the WHT fields of a document from its items (pure function).

	:param doc_income_type: current value of ``pd_custom_wht_income_type``
	:param doc_pct: current value of ``pd_custom_withholding_tax_pct``
	:param doc_vat_treatment: current value of ``pd_custom_vat_treatment``
	:param rows: the ``items`` child rows of the document
	:param item_config_map: ``{item_code: {"income_type": ..., "is_service_item": ...}}``
	:param rate_map: ``{income_type: rate}``

	:return: dict with the resolved values
	"""
	rows = rows or []
	item_config_map = item_config_map or {}
	rate_map = rate_map or {}

	item_income_type = None
	has_service_item = False
	for row in rows:
		item_code = row.get("item_code")
		if not item_code:
			continue
		config = item_config_map.get(item_code) or {}
		if config.get("is_service_item"):
			has_service_item = True
		if not item_income_type and config.get("income_type"):
			item_income_type = config["income_type"]

	# A manually entered income type wins over the item master
	income_type = doc_income_type or item_income_type
	income_type_auto = bool(item_income_type and not doc_income_type)

	rate = rate_map.get(income_type) if income_type else None

	# A manual percentage wins over the rate of the income type
	pct = doc_pct
	if rate is not None and not pct:
		pct = rate

	# A deliberate manual VAT treatment (exempt / zero rated) is kept
	vat_treatment = doc_vat_treatment
	if has_service_item and (not vat_treatment or vat_treatment == DEFAULT_VAT_TREATMENT):
		vat_treatment = SERVICE_VAT_TREATMENT

	return {
		"income_type": income_type,
		"income_type_auto": income_type_auto,
		"wht_rate": rate,
		"withholding_tax_pct": pct,
		"vat_treatment": vat_treatment,
		"has_service_item": has_service_item,
	}


def _doc_has_field(doc, fieldname):
	"""Return True when the document carries the given custom field."""
	meta = getattr(doc, "meta", None)
	if meta is None:
		return True
	return bool(meta.has_field(fieldname))


def apply_item_wht_config(doc):
	"""Update the WHT fields of ``doc`` from its items.

	Returns the resolved values (see :func:`resolve_wht_fields`).
	"""
	rows = doc.get("items") or []
	if not rows:
		return {}

	item_codes = [row.get("item_code") for row in rows if row.get("item_code")]
	item_config_map = get_item_wht_config_map(item_codes)

	doc_income_type = doc.get(DOC_INCOME_TYPE_FIELD)
	doc_pct = doc.get(DOC_PCT_FIELD)
	doc_vat_treatment = doc.get(DOC_VAT_TREATMENT_FIELD)

	item_income_type = None
	for row in rows:
		config = item_config_map.get(row.get("item_code")) or {}
		if config.get("income_type"):
			item_income_type = config["income_type"]
			break

	candidates = [name for name in (doc_income_type, item_income_type) if name]
	rate_map = get_rate_map(candidates)

	resolved = resolve_wht_fields(
		doc_income_type=doc_income_type,
		doc_pct=doc_pct,
		doc_vat_treatment=doc_vat_treatment,
		rows=rows,
		item_config_map=item_config_map,
		rate_map=rate_map,
	)

	if _doc_has_field(doc, DOC_INCOME_TYPE_FIELD) and resolved["income_type_auto"]:
		doc.set(DOC_INCOME_TYPE_FIELD, resolved["income_type"])
		frappe.logger().info(
			f"{doc.doctype} {getattr(doc, 'name', 'new')}: {DOC_INCOME_TYPE_FIELD} set to "
			f"'{resolved['income_type']}' from the item master"
		)

	if _doc_has_field(doc, DOC_PCT_FIELD) and resolved["withholding_tax_pct"] != doc_pct:
		doc.set(DOC_PCT_FIELD, resolved["withholding_tax_pct"])

	if (
		_doc_has_field(doc, DOC_VAT_TREATMENT_FIELD)
		and resolved["vat_treatment"] != doc_vat_treatment
	):
		doc.set(DOC_VAT_TREATMENT_FIELD, resolved["vat_treatment"])

	# Keep the description of the effective income type in sync (never
	# overwrite a description the user entered manually).
	if (
		resolved["income_type"]
		and _doc_has_field(doc, DOC_DESCRIPTION_FIELD)
		and not doc.get(DOC_DESCRIPTION_FIELD)
	):
		doc.set(DOC_DESCRIPTION_FIELD, get_description(resolved["income_type"]))

	return resolved


@frappe.whitelist()
def get_item_wht_config(item_codes=None, item_code=None):
	"""Return the WHT configuration of one or many items.

	Used by the client script to mirror the server side behaviour while the
	user edits the form.

	:return: dict with ``income_type``, ``is_service_item``, ``wht_rate`` and
		the per item configuration
	"""
	if item_codes:
		if isinstance(item_codes, str):
			try:
				item_codes = json.loads(item_codes)
			except ValueError:
				item_codes = [item_codes]
	elif item_code:
		item_codes = [item_code]
	else:
		item_codes = []

	item_codes = [code for code in item_codes if code]
	item_config_map = get_item_wht_config_map(item_codes)

	rows = [{"item_code": code} for code in item_codes]
	income_types = [
		config["income_type"]
		for config in item_config_map.values()
		if config.get("income_type")
	]
	rate_map = get_rate_map(income_types)

	resolved = resolve_wht_fields(
		rows=rows,
		item_config_map=item_config_map,
		rate_map=rate_map,
	)

	return {
		"income_type": resolved["income_type"],
		"is_service_item": 1 if resolved["has_service_item"] else 0,
		"wht_rate": resolved["wht_rate"],
		"description": get_description(resolved["income_type"]),
		"per_item": item_config_map,
	}
