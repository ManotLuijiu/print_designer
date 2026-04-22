"""
Payment Entry Tax Events for Thai WHT.

Before saving Payment Entry, ensures Advance Taxes and Charges uses
the WHT liability account (2132-02) from TWC's accounts child table
instead of the asset account (1151-05).

This runs BEFORE PaymentTaxWithholding.calculate() to ensure the correct
account_head is set in the taxes child table rows.
"""

import frappe


def patch_twc_tax_accounts(doc, method):
    """
    Before saving Payment Entry, ensure Advance Taxes and Charges uses
    the WHT liability account (2132-02) instead of asset account (1151-05).

    This patches is_tax_withholding_account rows to use the liability account
    from TWC.accounts.pd_custom_wht_liability_account.
    """
    if not doc.tax_withholding_category:
        return

    if doc.payment_type not in ("Pay", "Internal Transfer"):
        return

    liability_account = get_wht_liability_account(doc)
    if not liability_account:
        return

    modified = False
    for row in doc.taxes:
        if row.is_tax_withholding_account and row.account_head != liability_account:
            row.account_head = liability_account
            modified = True

    if modified:
        frappe.msgprint(
            f"WHT tax account updated to liability account: {liability_account}",
            indicator="green",
            alert=True,
        )


def get_wht_liability_account(doc):
    """
    Get WHT liability account from TWC accounts child table.

    Priority:
    1. TWC.accounts[company].pd_custom_wht_liability_account
    2. Company.default_wht_debt_account (fallback)
    """
    twc_name = doc.tax_withholding_category
    if not twc_name:
        return None

    try:
        twc = frappe.get_cached_doc("Tax Withholding Category", twc_name)
        for row in twc.accounts:
            if row.company == doc.company:
                liability = row.get("pd_custom_wht_liability_account")
                if liability:
                    return liability
    except Exception:
        pass

    # Fallback: Company default WHT debt account
    debt_account = frappe.get_cached_value("Company", doc.company, "default_wht_debt_account")
    return debt_account or None
