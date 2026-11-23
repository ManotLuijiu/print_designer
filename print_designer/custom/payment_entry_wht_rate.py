"""Carry Sales Invoice withholding details into a customer receipt."""

import frappe
from frappe.utils import flt


def apply_sales_invoice_wht_details(payment):
    field = "pd_custom_withholding_tax_pct_details"
    if (
        payment.get("payment_type") != "Receive" or payment.get("party_type") != "Customer"
        or not payment.meta.has_field(field)
    ):
        return None

    invoice_names = {
        ref.reference_name for ref in payment.get("references") or []
        if ref.reference_doctype == "Sales Invoice" and ref.reference_name and flt(ref.allocated_amount) > 0
    }
    if not invoice_names:
        return None
    meta = frappe.get_meta("Sales Invoice")
    if not all(meta.has_field(name) for name in ("pd_custom_subject_to_wht", "pd_custom_withholding_tax_pct")):
        return None

    fields = ["pd_custom_withholding_tax_pct"]
    invoice_income_type = meta.get_field("pd_custom_wht_income_type")
    payment_income_type = payment.meta.get_field("pd_custom_wht_income_type")
    if (
        invoice_income_type and payment_income_type
        and invoice_income_type.fieldtype == payment_income_type.fieldtype == "Link"
        and invoice_income_type.options == payment_income_type.options
    ):
        fields.append("pd_custom_wht_income_type")

    invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "name": ["in", sorted(invoice_names)],
            "docstatus": 1,
            "company": payment.company,
            "customer": payment.party,
            "is_return": 0,
            "pd_custom_subject_to_wht": 1,
        },
        fields=fields,
    )
    rates = {flt(invoice.pd_custom_withholding_tax_pct) for invoice in invoices}
    if not rates:
        return None

    # The header has one percentage, so different invoice rates have no single value.
    rate = next(iter(rates)) if len(rates) == 1 else 0
    payment.set(field, rate)
    income_types = {invoice.get("pd_custom_wht_income_type") for invoice in invoices} - {None, ""}
    if income_types:
        payment.set("pd_custom_wht_income_type", next(iter(income_types)) if len(income_types) == 1 else None)
    return rate
