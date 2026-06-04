# Copyright (c) 2024, Digisoft ERP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class ReceiveWHTRegister(Document):
    def validate(self):
        """Validate the WHT Register entry"""
        self.validate_certificate_number()
        self.validate_customer_details()
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
        frappe.db.set_value(
            "Payment Entry",
            self.payment_entry,
            "pd_custom_receive_wht_register",
            self.name
        )
        frappe.msgprint(
            _("Payment Entry {0} updated with WHT Register reference").format(self.payment_entry),
            indicator="green",
            alert=True
        )

    def on_cancel(self):
        """On cancel, remove reference from Payment Entry"""
        if self.payment_entry:
            frappe.db.set_value(
                "Payment Entry",
                self.payment_entry,
                "pd_custom_receive_wht_register",
                None
            )


@frappe.whitelist()
def create_from_payment_entry(payment_entry):
    """
    Create Receive WHT Register entry from Payment Entry (Receive) values.

    Args:
        payment_entry: Payment Entry name

    Returns:
        dict: Created document name or error message
    """
    if not frappe.has_permission("Receive WHT Register", "create"):
        frappe.throw(_("You do not have permission to create Receive WHT Register"))

    pe = frappe.get_doc("Payment Entry", payment_entry)

    # Validate it's a Receive payment
    if pe.payment_type != "Receive":
        frappe.throw(_("Only Payment Entry with payment_type 'Receive' can create WHT Register"))

    # Check if WHT certificate number is provided
    if not pe.get("pd_custom_wht_certificate_no"):
        frappe.throw(_("WHT Certificate Number is required"))

    # Create the register entry
    register = frappe.new_doc("Receive WHT Register")
    register.wht_certificate_no = pe.get("pd_custom_wht_certificate_no")
    register.wht_certificate_date = pe.get("pd_custom_wht_certificate_date")
    register.customer = pe.party
    register.customer_name = pe.party_name
    register.payment_entry = pe.name
    register.payment_date = pe.posting_date
    register.company = pe.company
    register.income_type = pe.get("pd_custom_wht_income_type")
    register.wht_rate = pe.get("pd_custom_withholding_tax_rate")
    register.wht_amount = pe.get("pd_custom_withholding_tax_amount")
    register.tax_base_amount = pe.get("pd_custom_tax_base_amount")
    register.status = "Draft"
    register.insert()

    # Link back to Payment Entry
    frappe.db.set_value("Payment Entry", pe.name, "pd_custom_receive_wht_register", register.name)

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

    return {
        "wht_certificate_no": pe.get("pd_custom_wht_certificate_no"),
        "wht_certificate_date": pe.get("pd_custom_wht_certificate_date"),
        "customer": pe.party,
        "customer_name": pe.party_name,
        "company": pe.company,
        "payment_date": pe.posting_date,
        "wht_rate": pe.get("pd_custom_withholding_tax_rate"),
        "wht_amount": pe.get("pd_custom_withholding_tax_amount"),
        "tax_base_amount": pe.get("pd_custom_tax_base_amount"),
        "income_type": pe.get("pd_custom_wht_income_type"),
    }