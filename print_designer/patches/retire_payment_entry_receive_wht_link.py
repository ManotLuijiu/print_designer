import frappe

from print_designer.commands.install_payment_entry_fields import (
    get_payment_entry_custom_fields_definition,
    migrate_wht_certificate_link,
)
from print_designer.custom.payment_wht_certificate_link import (
    get_received_wht_register,
    set_received_wht_register,
)

LEGACY_FIELD = "pd_custom_receive_wht_register"


def execute():
    legacy = frappe.db.get_value(
        "Custom Field", {"dt": "Payment Entry", "fieldname": LEGACY_FIELD},
        ["name", "insert_after"], as_dict=True,
    )
    if not legacy:
        return 0

    linked = frappe.get_all(
        "Payment Entry", filters={LEGACY_FIELD: ["is", "set"]}, fields=["name", LEGACY_FIELD]
    )
    if linked:
        definitions = get_payment_entry_custom_fields_definition()["Payment Entry"]
        migrate_wht_certificate_link(definitions)
        for row in linked:
            payment = frappe.get_doc("Payment Entry", row.name)
            register = row.get(LEGACY_FIELD)
            active = get_received_wht_register(payment)
            if active == register:
                continue
            if payment.get("pd_custom_wht_certificate"):
                frappe.throw(f"Payment Entry {payment.name} already has a different WHT link.")
            if not frappe.db.exists(
                "Receive WHT Register", {"name": register, "payment_entry": payment.name, "docstatus": ["<", 2]}
            ):
                frappe.throw(f"Payment Entry {payment.name} has an unresolved received WHT register.")
            set_received_wht_register(payment, register)
    else:
        meta = frappe.get_meta("Payment Entry")
        link = meta.get_field("pd_custom_wht_certificate")
        if link and link.fieldtype == "Link" and frappe.db.exists("DocType", "Receive WHT Register"):
            definitions = get_payment_entry_custom_fields_definition()["Payment Entry"]
            migrate_wht_certificate_link(definitions)

    frappe.db.set_value(
        "Custom Field", {"dt": "Payment Entry", "insert_after": LEGACY_FIELD},
        "insert_after", legacy.insert_after, update_modified=False,
    )
    frappe.delete_doc("Custom Field", legacy.name)
    frappe.clear_cache(doctype="Payment Entry")
    return 1
