import frappe

LEGACY_FIELDS = ("pd_custom_wht_certificate_no", "pd_custom_wht_certificate_date")


def execute():
    fields = frappe.get_all(
        "Custom Field",
        filters={"dt": "Payment Entry", "fieldname": ["in", LEGACY_FIELDS]},
        fields=["name", "fieldname", "insert_after"],
    )
    if not fields:
        return 0

    _verify_received_certificate_data()

    anchors = {field.fieldname: field.insert_after for field in fields}
    for field in frappe.get_all(
        "Custom Field",
        filters={"dt": "Payment Entry", "insert_after": ["in", tuple(anchors)]},
        fields=["name", "fieldname", "insert_after"],
    ):
        if field.fieldname in anchors:
            continue
        anchor = field.insert_after
        seen = {field.fieldname}
        while anchor in anchors and anchor not in seen:
            seen.add(anchor)
            anchor = anchors[anchor]
        if not anchor or anchor in seen or not frappe.get_meta("Payment Entry").has_field(anchor):
            anchor = "remarks"
        frappe.db.set_value("Custom Field", field.name, "insert_after", anchor, update_modified=False)

    # Frappe leaves the physical columns available for historical recovery.
    for field in fields:
        frappe.delete_doc("Custom Field", field.name)
    frappe.clear_cache(doctype="Payment Entry")
    return len(fields)


def _verify_received_certificate_data():
    columns = set(frappe.db.get_table_columns("Payment Entry"))
    legacy_fields = [field for field in LEGACY_FIELDS if field in columns]
    if not legacy_fields:
        return

    field_names = dict(zip(LEGACY_FIELDS, ("wht_certificate_no", "wht_certificate_date"), strict=True))
    receipts = frappe.get_all(
        "Payment Entry",
        filters={"payment_type": "Receive"},
        or_filters=[[field, "is", "set"] for field in legacy_fields],
        fields=["name", *legacy_fields],
    )
    for receipt in receipts:
        values = {field_names[field]: receipt[field] for field in legacy_fields if receipt.get(field)}
        if values and (
            not frappe.db.exists("DocType", "Receive WHT Register")
            or not frappe.db.exists(
                "Receive WHT Register", {"payment_entry": receipt.name, "docstatus": ["<", 2], **values}
            )
        ):
            frappe.throw(f"Payment Entry {receipt.name} has certificate data that is missing from its WHT register.")
