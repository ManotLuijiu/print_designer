# Copyright (c) 2024, Digisoft ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

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
    if not register.customer:
        return
    customer = frappe.get_cached_doc("Customer", register.customer)
    customer_code = _branch_code(customer.get("pd_custom_branch_code") or customer.get("branch_code"))
    code = _branch_code(register.customer_branch_code) if register.customer_branch_code else customer_code
    register.customer_branch_code = code
    if register.customer_branch_name:
        return
    if code == "00000":
        register.customer_branch_name = "สำนักงานใหญ่"
    else:
        customer_name = customer.get("pd_custom_branch_name") or customer.get("branch_name")
        register.customer_branch_name = (customer_name if code == customer_code else None) or f"สาขา {code}"


def get_payment_income_type(payment_name):
    if not payment_name or not frappe.get_meta("Payment Entry").has_field("pd_custom_wht_income_type"):
        return None
    category = frappe.db.get_value("Payment Entry", payment_name, "pd_custom_wht_income_type")
    return category if category and frappe.db.exists("Tax Withholding Category", category) else None


class ReceiveWHTRegister(Document):
    def validate(self):
        """Validate the WHT Register entry"""
        self.validate_certificate_number()
        self.validate_customer_details()
        fill_customer_branch(self)
        if not self.income_type and self.meta.get_field("income_type").fieldtype == "Link":
            self.income_type = get_payment_income_type(self.payment_entry)
        self.validate_wht_amounts()

    def validate_certificate_number(self):
        """Ensure certificate number is provided"""
        if not self.wht_certificate_no:
            frappe.throw(_("WHT Certificate Number is required"))

    def validate_customer_details(self):
        """Auto-fill customer details if not provided"""
        if self.customer and not self.customer_name:
            self.customer_name = frappe.db.get_value("Customer", self.customer, "customer_name")

        if self.customer and not self.customer_tax_id:
            self.customer_tax_id = frappe.db.get_value("Customer", self.customer, "tax_id")

    def validate_wht_amounts(self):
        """Validate WHT amounts are consistent"""
        if self.wht_rate and self.wht_amount and self.tax_base_amount:
            expected_wht = self.tax_base_amount * (self.wht_rate / 100)
            if abs(expected_wht - self.wht_amount) > 0.01:
                frappe.msgprint(
                    _("WHT Amount ({0}) does not match expected amount ({1}) based on {2}% rate").format(
                        self.wht_amount, round(expected_wht, 2), self.wht_rate
                    ),
                    indicator="warning",
                    alert=True
                )

    def on_submit(self):
        """On submit, update Payment Entry if linked"""
        if self.payment_entry:
            self.update_payment_entry()

    def update_payment_entry(self):
        """Update Payment Entry with reference to this register"""
        payment = frappe.get_doc("Payment Entry", self.payment_entry)
        set_received_wht_register(payment, self.name)
        frappe.msgprint(
            _("Payment Entry {0} updated with WHT Register reference").format(self.payment_entry),
            indicator="green",
            alert=True
        )

    def on_cancel(self):
        """On cancel, remove reference from Payment Entry"""
        if self.payment_entry:
            payment = frappe.get_doc("Payment Entry", self.payment_entry)
            if get_received_wht_register(payment) == self.name:
                set_received_wht_register(payment, None)


@frappe.whitelist(methods=["POST"])
def create_from_payment_entry(payment_entry: str, certificate_no: str, certificate_date: str):
    """Record a customer's WHT certificate against a saved receipt."""
    if not frappe.has_permission("Receive WHT Register", "create"):
        frappe.throw(_("You do not have permission to create Receive WHT Register"), frappe.PermissionError)

    pe = frappe.get_doc("Payment Entry", payment_entry, for_update=True)
    pe.check_permission("read")
    if pe.payment_type != "Receive" or pe.party_type != "Customer" or pe.docstatus == 2:
        frappe.throw(_("Choose a saved, non-cancelled customer receipt."))

    certificate_no = (certificate_no or "").strip()
    if not certificate_no or not certificate_date:
        frappe.throw(_("Enter the WHT certificate number and date."))
    certificate_date = getdate(certificate_date)

    existing = get_received_wht_register(pe) or frappe.db.get_value(
        "Receive WHT Register", {"payment_entry": pe.name, "docstatus": ["<", 2]}, "name"
    )
    if existing:
        register = frappe.get_doc("Receive WHT Register", existing)
        register.check_permission("read")
        if register.wht_certificate_no != certificate_no or getdate(register.wht_certificate_date) != certificate_date:
            frappe.throw(_("This Payment Entry already has a received WHT certificate."))
        if not get_received_wht_register(pe):
            set_received_wht_register(pe, register.name)
        return {"name": register.name}

    field = pe.meta.get_field("pd_custom_wht_certificate")
    if not field or field.fieldtype != "Dynamic Link":
        frappe.throw(_("Install the Payment Entry WHT Certificate Dynamic Link first."))
    if pe.get(field.fieldname):
        frappe.throw(_("This Payment Entry already has a different WHT certificate link."))

    register = frappe.new_doc("Receive WHT Register")
    register.wht_certificate_no = certificate_no
    register.wht_certificate_date = certificate_date
    register.customer = pe.party
    register.customer_name = pe.party_name
    register.payment_entry = pe.name
    register.payment_date = pe.posting_date
    register.company = pe.company
    register.wht_rate = pe.get("pd_custom_withholding_tax_pct_details")
    register.wht_amount = pe.get("pd_custom_withholding_tax_amount_details")
    register.tax_base_amount = pe.get("pd_custom_tax_base_amount")
    register.status = "Draft"
    register.insert()

    # Link back to Payment Entry
    set_received_wht_register(pe, register.name)

    return {
        "name": register.name,
        "message": _("Receive WHT Register {0} created successfully").format(register.name)
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
    certificate = get_received_wht_register(pe)
    register = frappe.get_doc("Receive WHT Register", certificate) if certificate else None
    if register:
        register.check_permission("read")

    return {
        "wht_certificate_no": register.wht_certificate_no if register else None,
        "wht_certificate_date": register.wht_certificate_date if register else None,
        "customer": pe.party,
        "customer_name": pe.party_name,
        "company": pe.company,
        "payment_date": pe.posting_date,
        "wht_rate": pe.get("pd_custom_withholding_tax_pct_details"),
        "wht_amount": pe.get("pd_custom_withholding_tax_amount_details"),
        "tax_base_amount": pe.get("pd_custom_tax_base_amount"),
        "income_type": pe.get("pd_custom_wht_income_type"),
    }
