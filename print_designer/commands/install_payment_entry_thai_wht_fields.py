"""
DRAFT: Payment Entry Thai WHT Compliance Fields for Pay transactions
TODO: Implement after Purchase Order and Purchase Invoice debugging is complete
"""

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """
    TODO: Install Thai WHT Compliance fields for Payment Entry (Pay) transactions
    Focus on supplier payments where WHT is deducted when paying
    """

    # TODO: Uncomment after Purchase Order/Invoice debugging complete
    # custom_fields = {
    #     "Payment Entry": [
    #         # Thai WHT Compliance for Supplier Payments (Pay)
    #         {
    #             "fieldname": "apply_thai_wht_compliance_pay",
    #             "label": _("Apply Thai WHT Compliance (Pay)"),
    #             "fieldtype": "Check",
    #             "insert_after": "tax_withholding_category",
    #             "depends_on": "eval:doc.payment_type == 'Pay'",
    #             "description": _("Enable Thai WHT deduction when paying suppliers"),
    #             "default": "0",
    #         },
    #
    #         # Thai WHT Section for Pay transactions
    #         {
    #             "fieldname": "thai_wht_pay_section",
    #             "label": _("Thai WHT Deductions (Supplier Payment)"),
    #             "fieldtype": "Section Break",
    #             "insert_after": "apply_thai_wht_compliance_pay",
    #             "depends_on": "eval:doc.apply_thai_wht_compliance_pay && doc.payment_type == 'Pay'",
    #             "collapsible": 1,
    #         },
    #
    #         # WHT Details Column
    #         {
    #             "fieldname": "wht_pay_column_break",
    #             "fieldtype": "Column Break",
    #             "insert_after": "thai_wht_pay_section",
    #         },
    #
    #         # WHT Income Type for supplier payment
    #         {
    #             "fieldname": "pd_custom_supplier_wht_income_type",
    #             "label": _("WHT Income Type"),
    #             "fieldtype": "Select",
    #             "insert_after": "wht_pay_column_break",
    #             "depends_on": "eval:doc.apply_thai_wht_compliance_pay",
    #             "options": "\nprofessional_services\nrental\nservice_fees\nconstruction\nadvertising\nother_services",
    #         },
    #
    #         # WHT Rate for supplier payment
    #         {
    #             "fieldname": "pd_custom_supplier_wht_rate",
    #             "label": _("WHT Rate (%)"),
    #             "fieldtype": "Percent",
    #             "insert_after": "pd_custom_supplier_wht_income_type",
    #             "depends_on": "eval:doc.apply_thai_wht_compliance_pay",
    #         },
    #
    #         # WHT Amount deducted from supplier payment
    #         {
    #             "fieldname": "pd_custom_supplier_wht_amount",
    #             "label": _("WHT Amount Deducted"),
    #             "fieldtype": "Currency",
    #             "insert_after": "pd_custom_supplier_wht_rate",
    #             "depends_on": "eval:doc.apply_thai_wht_compliance_pay",
    #             "options": "Company:company:default_currency",
    #             "read_only": 1,
    #         },
    #
    #         # Amounts Column
    #         {
    #             "fieldname": "amounts_pay_column_break",
    #             "fieldtype": "Column Break",
    #             "insert_after": "pd_custom_supplier_wht_amount",
    #         },
    #
    #         # Base payment amount (before WHT deduction)
    #         {
    #             "fieldname": "pd_custom_base_payment_amount",
    #             "label": _("Base Payment Amount"),
    #             "fieldtype": "Currency",
    #             "insert_after": "amounts_pay_column_break",
    #             "depends_on": "eval:doc.apply_thai_wht_compliance_pay",
    #             "options": "Company:company:default_currency",
    #             "read_only": 1,
    #             "description": _("Original amount before WHT deduction"),
    #         },
    #
    #         # Actual cash amount paid to supplier
    #         {
    #             "fieldname": "pd_custom_actual_payment_amount",
    #             "label": _("Actual Payment Amount"),
    #             "fieldtype": "Currency",
    #             "insert_after": "pd_custom_base_payment_amount",
    #             "depends_on": "eval:doc.apply_thai_wht_compliance_pay",
    #             "options": "Company:company:default_currency",
    #             "read_only": 1,
    #             "description": _("Amount actually paid to supplier (after WHT)"),
    #         },
    #
    #         # WHT Certificate details
    #         {
    #             "fieldname": "pd_custom_wht_certificate_no",
    #             "label": _("WHT Certificate No."),
    #             "fieldtype": "Data",
    #             "insert_after": "pd_custom_actual_payment_amount",
    #             "depends_on": "eval:doc.apply_thai_wht_compliance_pay",
    #             "description": _("Government WHT certificate number"),
    #         },
    #     ]
    # }

    # TODO: Uncomment installation code
    # print("Installing Payment Entry Thai WHT Compliance fields for Pay transactions...")
    # create_custom_fields(custom_fields, update=True)
    # frappe.clear_cache(doctype="Payment Entry")
    # print("✅ Successfully installed Payment Entry Thai WHT fields")

    print("🚧 DRAFT: Payment Entry Thai WHT fields code ready for implementation")
    print("📋 TODO: Uncomment after Purchase Order/Invoice debugging complete")
    return True


@frappe.whitelist()
def check_payment_entry_thai_wht_fields():
    """
    TODO: Check if Payment Entry Thai WHT fields are installed
    """

    # TODO: Implement field checking logic
    # required_fields = [
    #     "apply_thai_wht_compliance_pay",
    #     "thai_wht_pay_section",
    #     "pd_custom_supplier_wht_income_type",
    #     "pd_custom_supplier_wht_rate",
    #     "pd_custom_supplier_wht_amount",
    #     "pd_custom_base_payment_amount",
    #     "pd_custom_actual_payment_amount",
    #     "pd_custom_wht_certificate_no",
    # ]

    print("🚧 DRAFT: Payment Entry Thai WHT field checking ready")
    print("📋 TODO: Implement after Purchase Order/Invoice debugging")
    return False  # Return False until implemented


def uninstall_payment_entry_thai_wht_fields():
    """
    TODO: Remove Payment Entry Thai WHT fields during app uninstall
    """

    # TODO: Implement uninstall logic
    # fields_to_remove = [
    #     "apply_thai_wht_compliance_pay",
    #     "thai_wht_pay_section",
    #     "wht_pay_column_break",
    #     "pd_custom_supplier_wht_income_type",
    #     "pd_custom_supplier_wht_rate",
    #     "pd_custom_supplier_wht_amount",
    #     "amounts_pay_column_break",
    #     "pd_custom_base_payment_amount",
    #     "pd_custom_actual_payment_amount",
    #     "pd_custom_wht_certificate_no",
    # ]

    print("🚧 DRAFT: Payment Entry Thai WHT field removal ready")
    print("📋 TODO: Implement uninstall logic")
    return True