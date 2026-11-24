import frappe

from print_designer.print_designer.doctype.receive_wht_register.receive_wht_register import (
    fill_customer_branch,
    get_payment_income_type,
)
from print_designer.utils.db import set_values


def execute():
    if not frappe.db.exists("DocType", "Receive WHT Register"):
        return
    meta = frappe.get_meta("Receive WHT Register", cached=False)
    if not meta.has_field("legacy_income_type"):
        return

    fields = ("income_type", "legacy_income_type", "customer_branch_code", "customer_branch_name")
    for register in frappe.get_all(
        "Receive WHT Register", fields=["name", "payment_entry", "customer", *fields]
    ):
        before = {field: register.get(field) for field in fields}
        if register.income_type and not frappe.db.exists(
            "Tax Withholding Category", register.income_type
        ):
            register.legacy_income_type = register.legacy_income_type or register.income_type
            register.income_type = None
        if not register.income_type:
            register.income_type = get_payment_income_type(register.payment_entry)
        fill_customer_branch(register)
        changes = {
            field: register.get(field) for field in fields if before[field] != register.get(field)
        }
        if changes:
            set_values("Receive WHT Register", register.name, changes, update_modified=False)
