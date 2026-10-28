"""Auto-set ``pd_custom_subject_to_wht`` from the Item Group of the document items.

Thai withholding tax applies to service supplies.  A Sales Order / Quotation /
Sales Invoice that contains at least one item whose *Item Group* is ``Services``
is therefore subject to withholding tax, so the flag is switched on automatically.

Rules
-----
* The Item Group name is compared case insensitively against ``Services`` so the
  behaviour does not depend on the casing used on the site.
* The Item Group is read from the child row when it is available and falls back to
  the Item master, so rows added by data imports or scripts are handled as well.
* The flag is only ever switched **on** automatically.  It is never cleared, so a
  user can still tick it manually for documents without a service line (for
  example a service invoice posted without an item row).
* Nothing is changed when the target document does not carry the
  ``pd_custom_subject_to_wht`` field (the field is installed per site).

The server side is authoritative - the client script
``public/js/thailand_wht/thailand_wht_vat_helper.js`` only mirrors the result
while the user edits the form.
"""

import frappe

SERVICE_ITEM_GROUP = "Services"
SUBJECT_TO_WHT_FIELD = "pd_custom_subject_to_wht"


def is_service_item_group(item_group):
	"""Return True when ``item_group`` is the ``Services`` item group."""
	if not item_group:
		return False
	return str(item_group).strip().casefold() == SERVICE_ITEM_GROUP.casefold()


def get_item_group_map(item_codes):
	"""Return a map of item code -> item group for ``item_codes``."""
	item_codes = [code for code in item_codes if code]
	if not item_codes:
		return {}

	rows = frappe.get_all(
		"Item",
		filters={"name": ["in", item_codes]},
		fields=["name", "item_group"],
		limit_page_length=0,
	)
	return {row.name: row.item_group for row in rows}


def get_service_item_codes(doc, item_group_map=None):
	"""Return the item codes of ``doc`` that belong to the ``Services`` item group.

	:param doc: document holding an ``items`` child table
	:param item_group_map: optional pre-fetched map of item code -> item group
	"""
	rows = doc.get("items") or []
	if not rows:
		return []

	item_codes = [row.get("item_code") for row in rows if row.get("item_code")]

	# Only hit the database when a row does not carry its item group
	if item_group_map is None and any(not row.get("item_group") for row in rows):
		item_group_map = get_item_group_map(item_codes)
	item_group_map = item_group_map or {}

	service_codes = []
	for row in rows:
		item_group = row.get("item_group") or item_group_map.get(row.get("item_code"))
		if is_service_item_group(item_group) and row.get("item_code"):
			service_codes.append(row.get("item_code"))

	return service_codes


def has_subject_to_wht_field(doc):
	"""Return True when the document carries the ``pd_custom_subject_to_wht`` field."""
	meta = getattr(doc, "meta", None)
	if meta is None:
		# Plain object (unit tests) - assume the field exists
		return True
	return bool(meta.has_field(SUBJECT_TO_WHT_FIELD))


def apply_subject_to_wht_from_items(doc):
	"""Switch ``pd_custom_subject_to_wht`` on when the document has a service item.

	Returns the list of service item codes (empty when nothing was changed).
	"""
	if not has_subject_to_wht_field(doc):
		return []

	service_codes = get_service_item_codes(doc)
	if not service_codes:
		return []

	if not doc.get(SUBJECT_TO_WHT_FIELD):
		doc.set(SUBJECT_TO_WHT_FIELD, 1)
		frappe.logger().info(
			f"{doc.doctype} {getattr(doc, 'name', 'new')}: {SUBJECT_TO_WHT_FIELD} enabled "
			f"because of service item(s): {', '.join(service_codes)}"
		)

	return service_codes
