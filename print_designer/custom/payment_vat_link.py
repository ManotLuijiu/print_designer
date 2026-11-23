"""Maintain the direct Payment Entry link to a single recorded VAT document."""

import frappe

VAT_RECORD_DOCTYPE = {
    "Pay": "Thai Purchase VAT",
    "Receive": "Thai Sales VAT",
}

VAT_LINK_FIELDS = ("pd_custom_vat_ref_doctype", "pd_custom_vat_ref")


def get_payment_vat_link_values(payment_type, vat_record_names):
    """Return a direct link when exactly one VAT record applies."""
    doctype = VAT_RECORD_DOCTYPE.get(payment_type)
    names = list(dict.fromkeys(name for name in vat_record_names if name))
    has_single_record = bool(doctype and len(names) == 1)
    return {
        "pd_custom_vat_ref_doctype": doctype if has_single_record else None,
        "pd_custom_vat_ref": names[0] if has_single_record else None,
    }


def get_payment_vat_treatment(payment):
    return payment.get("pd_custom_vat_treatment")


def sync_payment_vat_link(payment):
    """Refresh the pair from the records belonging to this submitted payment."""
    if not all(payment.meta.has_field(field) for field in VAT_LINK_FIELDS):
        return

    payment_type = payment.get("payment_type")
    doctype = VAT_RECORD_DOCTYPE.get(payment_type)
    names = []
    if payment.docstatus == 1 and doctype and frappe.db.exists("DocType", doctype):
        if payment_type == "Pay":
            records = frappe.get_all(
                doctype,
                filters={"payment_entry": payment.name, "docstatus": ["<", 2]},
                fields=["name", "workflow_state"],
            )
            names = [record.name for record in records if record.workflow_state != "Cancelled"]
        else:
            names = frappe.get_all(
                doctype,
                filters={
                    "payment_entry_reference": payment.name,
                    "vat_type": "VAT Due",
                    "docstatus": ["<", 2],
                },
                pluck="name",
            )

    values = get_payment_vat_link_values(payment_type, names)
    if any(payment.get(field) != value for field, value in values.items()):
        frappe.db.set_value("Payment Entry", payment.name, values.copy(), update_modified=False)
        payment.update(values)
