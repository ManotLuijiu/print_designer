"""
DRAFT: Thai WHT Regional Override for Payment Entry (Pay) transactions
TODO: Implement after Purchase Order and Purchase Invoice debugging is complete

This extends the existing payment_entry.py regional override to handle
supplier payments where WHT is deducted when paying suppliers.
"""

import frappe
from frappe.utils import flt, cint
from frappe import _

# TODO: Uncomment after Purchase Order/Invoice debugging complete
def add_thai_wht_pay_regional_gl_entries(gl_entries, doc):
    """
    TODO: Add regional GL entries for Thai WHT compliance in Payment Entry (Pay)

    This handles supplier payments where we deduct WHT when paying.
    Different from Payment Entry (Receive) where customers pay us.

    GL Entry Pattern for Supplier Payment with WHT:
    Dr. Supplier (Accounts Payable)        ฿100.00
        Cr. Cash/Bank Account                   ฿97.00
        Cr. WHT Payable (Liability)             ฿3.00
    """

    # TODO: Only process Payment Entry (Pay) with Thai WHT enabled
    # if doc.doctype != "Payment Entry" or doc.payment_type != "Pay":
    #     return
    #
    # if not getattr(doc, 'apply_thai_wht_compliance_pay', 0):
    #     return
    #
    # wht_amount = flt(getattr(doc, 'pd_custom_supplier_wht_amount', 0))
    # if wht_amount <= 0:
    #     return

    # TODO: Adjust existing Cash/Bank GL entry for WHT deduction
    # _adjust_cash_gl_entry_for_supplier_wht(gl_entries, doc, wht_amount)

    # TODO: Add WHT Payable GL entry (Liability account)
    # _add_supplier_wht_payable_gl_entry(gl_entries, doc, wht_amount)

    print("🚧 DRAFT: Thai WHT Pay GL entries ready for implementation")
    print(f"📋 TODO: Process document {getattr(doc, 'name', 'Unknown')}")


# TODO: Uncomment helper functions after debugging complete
def _adjust_cash_gl_entry_for_supplier_wht(gl_entries, doc, wht_amount):
    """
    TODO: Adjust the Cash/Bank GL entry to reduce payment by WHT amount

    Standard ERPNext creates:
    Dr. Supplier ฿100
        Cr. Cash ฿100

    We need to change to:
    Dr. Supplier ฿100
        Cr. Cash ฿97 (reduced by WHT)
        Cr. WHT Payable ฿3
    """

    # TODO: Find and adjust cash/bank GL entry
    # for gl_entry in gl_entries:
    #     if gl_entry.get("account") == doc.paid_from:  # Cash/Bank account
    #         original_credit = flt(gl_entry.get("credit", 0))
    #         if original_credit > 0:
    #             # Reduce cash credit by WHT amount
    #             gl_entry["credit"] = original_credit - wht_amount
    #             gl_entry["credit_in_account_currency"] = original_credit - wht_amount
    #
    #             frappe.logger().info(
    #                 f"Adjusted Cash GL entry: {original_credit} → {gl_entry['credit']} "
    #                 f"(WHT deduction: {wht_amount})"
    #             )
    #             break

    pass  # TODO: Implement after debugging


def _add_supplier_wht_payable_gl_entry(gl_entries, doc, wht_amount):
    """
    TODO: Add WHT Payable GL entry (Liability account)

    This creates the WHT liability that we owe to the government
    """

    # TODO: Get WHT Payable account from Company settings
    # wht_payable_account = _get_wht_payable_account(doc.company)
    # if not wht_payable_account:
    #     frappe.throw(_("WHT Payable account not configured for company {0}").format(doc.company))

    # TODO: Create WHT Payable GL entry
    # wht_gl_entry = doc.get_gl_dict({
    #     "account": wht_payable_account,
    #     "credit": wht_amount,
    #     "credit_in_account_currency": wht_amount,
    #     "against": doc.party,
    #     "party_type": "Supplier",
    #     "party": doc.party,
    #     "remarks": f"WHT deducted on payment to {doc.party}",
    #     "against_voucher": doc.name,
    #     "against_voucher_type": doc.doctype,
    # })
    #
    # gl_entries.append(wht_gl_entry)
    #
    # frappe.logger().info(
    #     f"Added WHT Payable GL entry: {wht_payable_account} Cr. {wht_amount}"
    # )

    pass  # TODO: Implement after debugging


def _get_wht_payable_account(company):
    """
    TODO: Get the WHT Payable account for the company

    This should be a Liability account where we record WHT owed to government
    """

    # TODO: Check if company has WHT Payable account configured
    # wht_account = frappe.db.get_value(
    #     "Company",
    #     company,
    #     "default_wht_payable_account"  # TODO: Add this field to Company
    # )
    #
    # if not wht_account:
    #     # TODO: Create default WHT Payable account if not exists
    #     wht_account = _create_default_wht_payable_account(company)
    #
    # return wht_account

    # TODO: Return placeholder for now
    return "WHT Payable - Company"  # TODO: Implement proper account lookup


@frappe.whitelist()
def calculate_supplier_wht_amount(payment_entry_name):
    """
    TODO: Calculate WHT amount for supplier payment

    This will be called from client script to auto-calculate WHT
    """

    # TODO: Get payment entry document
    # doc = frappe.get_doc("Payment Entry", payment_entry_name)
    #
    # if doc.payment_type != "Pay":
    #     return {"wht_amount": 0, "message": "Not a supplier payment"}
    #
    # if not getattr(doc, 'apply_thai_wht_compliance_pay', 0):
    #     return {"wht_amount": 0, "message": "Thai WHT not enabled"}

    # TODO: Calculate WHT based on payment amount and rate
    # base_amount = flt(doc.paid_amount)
    # wht_rate = flt(getattr(doc, 'pd_custom_supplier_wht_rate', 0))
    #
    # if wht_rate <= 0:
    #     return {"wht_amount": 0, "message": "WHT rate not set"}
    #
    # wht_amount = flt(base_amount * wht_rate / 100, 2)
    # actual_payment = base_amount - wht_amount
    #
    # return {
    #     "wht_amount": wht_amount,
    #     "actual_payment": actual_payment,
    #     "calculation": f"{base_amount} × {wht_rate}% = {wht_amount}",
    #     "message": "WHT calculated successfully"
    # }

    return {
        "wht_amount": 0,
        "message": "🚧 DRAFT: WHT calculation ready for implementation"
    }