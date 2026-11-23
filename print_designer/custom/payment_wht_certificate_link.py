import frappe

from print_designer.utils.db import set_values


def get_issued_wht_certificate(payment):
    if payment.payment_type != "Pay":
        return None

    field = payment.meta.get_field("pd_custom_wht_certificate")
    if not field:
        return None
    if field.fieldtype == "Dynamic Link" and payment.get(field.options) != "Withholding Tax Certificate":
        return None
    if field.fieldtype == "Link" and field.options != "Withholding Tax Certificate":
        return None
    return payment.get(field.fieldname)


def set_issued_wht_certificate(payment, certificate):
    field = payment.meta.get_field("pd_custom_wht_certificate")
    if not field:
        frappe.throw(frappe._("Install the Payment Entry WHT Certificate field first."))

    values = {field.fieldname: certificate}
    if field.fieldtype == "Dynamic Link":
        values[field.options] = "Withholding Tax Certificate" if certificate else None

    set_values("Payment Entry", payment.name, values, update_modified=False)
    payment.update(values)


def get_received_wht_register(payment):
    field = payment.meta.get_field("pd_custom_wht_certificate")
    if (
        payment.payment_type == "Receive"
        and field and field.fieldtype == "Dynamic Link"
        and payment.get(field.options) == "Receive WHT Register"
    ):
        return payment.get(field.fieldname)
    return None


def set_received_wht_register(payment, register):
    field = payment.meta.get_field("pd_custom_wht_certificate")
    if payment.payment_type != "Receive" or not field or field.fieldtype != "Dynamic Link":
        frappe.throw(frappe._("Install the Payment Entry WHT Certificate Dynamic Link for Receive payments."))

    values = {
        field.fieldname: register,
        field.options: "Receive WHT Register" if register else None,
    }
    set_values("Payment Entry", payment.name, values, update_modified=False)
    payment.update(values)
