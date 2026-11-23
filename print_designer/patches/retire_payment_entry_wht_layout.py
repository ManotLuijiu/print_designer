import frappe

from print_designer.commands.install_payment_entry_fields import get_payment_entry_custom_fields_definition

LEGACY_FIELDS = ("pd_custom_wht_section", "pd_custom_thai_tax_column_3", "pd_custom_thai_tax_column_4")


def execute():
    fields = frappe.get_all(
        "Custom Field",
        filters={"dt": "Payment Entry", "fieldname": ["in", LEGACY_FIELDS]},
        fields=["name", "fieldname", "insert_after", "fieldtype"],
    )
    if any(field.fieldtype not in ("Section Break", "Column Break") for field in fields):
        frappe.throw("Expected only obsolete Payment Entry section and column breaks.")

    legacy_anchors = {field.fieldname: field.insert_after for field in fields}
    if not legacy_anchors:
        return 0

    definitions = get_payment_entry_custom_fields_definition()["Payment Entry"]
    preferred_anchors = {field["fieldname"]: field["insert_after"] for field in definitions}
    meta = frappe.get_meta("Payment Entry", cached=False)
    for field in frappe.get_all(
        "Custom Field",
        filters={"dt": "Payment Entry", "insert_after": ["in", tuple(legacy_anchors)]},
        fields=["name", "fieldname", "insert_after"],
    ):
        if field.fieldname in legacy_anchors:
            continue
        anchor = preferred_anchors.get(field.fieldname)
        if not anchor or anchor in legacy_anchors or not meta.has_field(anchor):
            anchor = field.insert_after
            seen = set()
            while anchor in legacy_anchors and anchor not in seen:
                seen.add(anchor)
                anchor = legacy_anchors[anchor]
            if not anchor or anchor in seen or anchor == field.fieldname or not meta.has_field(anchor):
                anchor = "remarks"
        frappe.db.set_value("Custom Field", field.name, "insert_after", anchor, update_modified=False)

    for field in fields:
        frappe.delete_doc("Custom Field", field.name)
    frappe.clear_cache(doctype="Payment Entry")
    return len(fields)
