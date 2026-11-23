# Copyright (c) 2024, AWS Solution Ltd. and contributors
# For license information, please see license.txt

from typing import Any, cast

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

from print_designer.custom.document_fields import field_text, field_value
from print_designer.custom.payment_wht_certificate_link import (
    get_received_wht_register,
    set_received_wht_register,
)


def _branch_code(value):
    code = "" if value is None else str(value).strip()
    if not code:
        return "00000"
    return code.zfill(5) if code.isascii() and code.isdigit() else code


def fill_customer_branch(register):
    customer = field_text(register, "customer")
    if not customer:
        return
    customer_doc = frappe.get_cached_doc("Customer", customer)
    customer_code = _branch_code(
        customer_doc.get("pd_custom_branch_code") or customer_doc.get("branch_code")
    )
    existing_code = field_text(register, "customer_branch_code")
    code = _branch_code(existing_code) if existing_code else customer_code
    register.set("customer_branch_code", code)
    if field_value(register, "customer_branch_name"):
        return
    if code == "00000":
        register.set("customer_branch_name", "สำนักงานใหญ่")
    else:
        customer_name = customer_doc.get("pd_custom_branch_name") or customer_doc.get("branch_name")
        register.set(
            "customer_branch_name",
            (customer_name if code == customer_code else None) or f"สาขา {code}",
        )


def get_payment_income_type(payment_name):
    if not payment_name or not frappe.get_meta("Payment Entry").has_field(
        "pd_custom_wht_income_type"
    ):
        return None
    category = cast(
        "str | None",
        frappe.db.get_value("Payment Entry", payment_name, "pd_custom_wht_income_type"),
    )
    return category if category and frappe.db.exists("Tax Withholding Category", category) else None


def _dynamic_link_fieldname(doc: Document, fieldname: str) -> str:
    """The fieldname of a dynamic link field of the document."""
    field = doc.meta.get_field(fieldname)
    if not field or field.fieldtype != "Dynamic Link":
        frappe.throw(_("Install the Payment Entry WHT Certificate Dynamic Link first."))
    return fieldname


class ReceiveWHTRegister(Document):
    def validate(self):
        """Validate the WHT Register entry"""
        self.validate_certificate_number()
        self.validate_customer_details()
        fill_customer_branch(self)
        income_type_field = self.meta.get_field("income_type")
        if (
            not field_value(self, "income_type")
            and income_type_field
            and income_type_field.fieldtype == "Link"
        ):
            self.set("income_type", get_payment_income_type(field_text(self, "payment_entry")))
        self.validate_wht_amounts()

    def validate_certificate_number(self):
        """Ensure certificate number is provided"""
        if not field_value(self, "wht_certificate_no"):
            frappe.throw(_("WHT Certificate Number is required"))

    def validate_customer_details(self):
        """Auto-fill customer details if not provided"""
        customer = field_text(self, "customer")
        if customer and not field_value(self, "customer_name"):
            self.set("customer_name", frappe.db.get_value("Customer", customer, "customer_name"))

        if customer and not field_value(self, "customer_tax_id"):
            self.set("customer_tax_id", frappe.db.get_value("Customer", customer, "tax_id"))

    def validate_wht_amounts(self):
        """Validate WHT amounts are consistent"""
        wht_rate = flt(field_value(self, "wht_rate"))
        wht_amount = flt(field_value(self, "wht_amount"))
        tax_base_amount = flt(field_value(self, "tax_base_amount"))
        if wht_rate and wht_amount and tax_base_amount:
            expected_wht = tax_base_amount * (wht_rate / 100)
            if abs(expected_wht - wht_amount) > 0.01:
                frappe.msgprint(
                    _(
                        "WHT Amount ({0}) does not match expected amount ({1}) based on {2}% rate"
                    ).format(wht_amount, round(expected_wht, 2), wht_rate),
                    indicator="orange",
                    alert=True,
                )

    def on_submit(self):
        """On submit, update Payment Entry if linked"""
        if field_value(self, "payment_entry"):
            self.update_payment_entry()

    def update_payment_entry(self):
        """Update Payment Entry with reference to this register"""
        payment_entry = field_text(self, "payment_entry")
        payment = frappe.get_doc("Payment Entry", payment_entry)
        set_received_wht_register(payment, self.name)
        frappe.msgprint(
            _("Payment Entry {0} updated with WHT Register reference").format(payment_entry),
            indicator="green",
            alert=True,
        )

    def on_cancel(self):
        """On cancel, remove reference from Payment Entry"""
        payment_entry = field_text(self, "payment_entry")
        if payment_entry:
            payment = frappe.get_doc("Payment Entry", payment_entry)
            if get_received_wht_register(payment) == self.name:
                set_received_wht_register(payment, None)


@frappe.whitelist(methods=["POST"])
def create_from_payment_entry(payment_entry: str, certificate_no: str, certificate_date: str):
    """Record a customer's WHT certificate against a saved receipt."""
    if not frappe.has_permission("Receive WHT Register", "create"):
        frappe.throw(
            _("You do not have permission to create Receive WHT Register"), frappe.PermissionError
        )

    pe = frappe.get_doc("Payment Entry", payment_entry, for_update=True)
    pe.check_permission("read")
    if (
        pe.get("payment_type") != "Receive"
        or pe.get("party_type") != "Customer"
        or pe.docstatus == 2
    ):
        frappe.throw(_("Choose a saved, non-cancelled customer receipt."))

    certificate_no = (certificate_no or "").strip()
    if not certificate_no or not certificate_date:
        frappe.throw(_("Enter the WHT certificate number and date."))
    certificate_date_value = getdate(certificate_date)

    existing = cast(
        "str | None",
        get_received_wht_register(pe)
        or frappe.db.get_value(
            "Receive WHT Register", {"payment_entry": pe.name, "docstatus": ["<", 2]}, "name"
        ),
    )
    if existing:
        register = frappe.get_doc("Receive WHT Register", existing)
        register.check_permission("read")
        if (
            register.get("wht_certificate_no") != certificate_no
            or getdate(cast("Any", register.get("wht_certificate_date"))) != certificate_date_value
        ):
            frappe.throw(_("This Payment Entry already has a received WHT certificate."))
        if not get_received_wht_register(pe):
            set_received_wht_register(pe, register.name)
        return {"name": register.name}

    link_fieldname = _dynamic_link_fieldname(pe, "pd_custom_wht_certificate")
    if pe.get(link_fieldname):
        frappe.throw(_("This Payment Entry already has a different WHT certificate link."))

    register = frappe.new_doc("Receive WHT Register")
    register.set("wht_certificate_no", certificate_no)
    register.set("wht_certificate_date", certificate_date_value)
    register.set("customer", pe.get("party"))
    register.set("customer_name", pe.get("party_name"))
    register.set("payment_entry", pe.name)
    register.set("payment_date", pe.get("posting_date"))
    register.set("company", pe.get("company"))
    register.set("wht_rate", pe.get("pd_custom_withholding_tax_pct_details"))
    register.set("wht_amount", pe.get("pd_custom_withholding_tax_amount_details"))
    register.set("tax_base_amount", pe.get("pd_custom_tax_base_amount"))
    register.set("status", "Draft")
    register.insert()

    # Link back to Payment Entry
    set_received_wht_register(pe, register.name)

    return {
        "name": register.name,
        "message": _("Receive WHT Register {0} created successfully").format(register.name),
    }


@frappe.whitelist()
def get_payment_entry_wht_details(payment_entry):
    """
    Get WHT details from Payment Entry for creating WHT Register.

    Args:
        payment_entry: Payment Entry name

    Returns:
        dict: WHT details from Payment Entry
    """
    pe = frappe.get_doc("Payment Entry", payment_entry)
    pe.check_permission("read")
    certificate = cast("str | None", get_received_wht_register(pe))
    register = frappe.get_doc("Receive WHT Register", certificate) if certificate else None
    if register:
        register.check_permission("read")

    return {
        "wht_certificate_no": register.get("wht_certificate_no") if register else None,
        "wht_certificate_date": register.get("wht_certificate_date") if register else None,
        "customer": pe.get("party"),
        "customer_name": pe.get("party_name"),
        "company": pe.get("company"),
        "payment_date": pe.get("posting_date"),
        "wht_rate": pe.get("pd_custom_withholding_tax_pct_details"),
        "wht_amount": pe.get("pd_custom_withholding_tax_amount_details"),
        "tax_base_amount": pe.get("pd_custom_tax_base_amount"),
        "income_type": pe.get("pd_custom_wht_income_type"),
    }
