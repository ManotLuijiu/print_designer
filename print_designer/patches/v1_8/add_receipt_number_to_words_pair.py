import json

import frappe

from print_designer.utils.number_to_words_fields import merge_number_to_words_pair

PAIR = {
    "source_field": "pd_custom_net_total_after_wht_details",
    "target_field": "pd_custom_net_total_after_wht_words_details",
}


def execute():
    if not frappe.db.exists("Print Format", "Receipt"):
        return
    if frappe.db.get_value("Print Format", "Receipt", "doc_type") != "Payment Entry":
        return

    for fieldname in (PAIR["source_field"], PAIR["target_field"]):
        if not frappe.db.exists(
            "Custom Field",
            {"dt": "Payment Entry", "fieldname": fieldname},
        ):
            return

    settings_json = frappe.db.get_value(
        "Print Format",
        "Receipt",
        "print_designer_settings",
    )
    settings = frappe.parse_json(settings_json or "{}") or {}
    if not merge_number_to_words_pair(settings, PAIR):
        return

    frappe.db.set_value(
        "Print Format",
        "Receipt",
        "print_designer_settings",
        json.dumps(settings),
        update_modified=False,
    )
