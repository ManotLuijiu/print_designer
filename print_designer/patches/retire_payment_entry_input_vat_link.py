import re
from typing import Any, cast

import frappe

from print_designer.custom.payment_vat_link import VAT_LINK_FIELDS, sync_payment_vat_link
from print_designer.patches.retire_payment_entry_tax_details import (
    _install_replacements,
    _update_print_formats,
)

LEGACY_FIELD = "pd_custom_input_vat_ref"
REPLACEMENTS = {LEGACY_FIELD: "pd_custom_vat_ref"}


def execute():
    legacy = cast(
        Any,
        frappe.db.get_value(
            "Custom Field",
            {"dt": "Payment Entry", "fieldname": LEGACY_FIELD},
            ["name", "insert_after"],
            as_dict=True,
        ),
    )
    if not legacy:
        return 0

    if LEGACY_FIELD in frappe.db.get_table_columns("Payment Entry"):
        linked = frappe.get_all(
            "Payment Entry",
            filters={"payment_type": "Pay", "docstatus": 1, LEGACY_FIELD: ["is", "set"]},
            pluck="name",
        )
        if linked:
            _install_replacements(REPLACEMENTS, (VAT_LINK_FIELDS[0],))
            for payment in linked:
                sync_payment_vat_link(frappe.get_doc("Payment Entry", payment))

    meta = frappe.get_meta("Payment Entry")
    anchor = "pd_custom_vat_ref" if meta.has_field("pd_custom_vat_ref") else legacy.insert_after
    for field in frappe.get_all(
        "Custom Field", filters={"dt": "Payment Entry", "insert_after": LEGACY_FIELD}, pluck="name"
    ):
        if field != "Payment Entry-pd_custom_vat_ref":
            frappe.db.set_value(
                "Custom Field", field, "insert_after", anchor, update_modified=False
            )

    _update_print_formats(REPLACEMENTS, re.compile(r"\b" + LEGACY_FIELD + r"\b"))
    frappe.delete_doc("Custom Field", legacy.name)
    frappe.clear_cache(doctype="Payment Entry")
    return 1
