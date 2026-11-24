"""The balance of an account, the way ERPNext computes it.

ERPNext keeps no balance on the Account doctype. The balance of an account is
the sum of the entries of its ledger, and ERPNext owns that calculation in
``erpnext.accounts.utils``. Print Designer uses those functions instead of
reading a column that does not exist.

The balance is financial data. It is computed only for a caller that may read
Account, and a failure of the calculation is reported to the caller instead of
being passed off as a balance of zero.
"""

from typing import Any

import frappe
from frappe.utils import flt


def the_balances_of(the_accounts: list[dict[str, Any]]) -> dict[str, float]:
    """The balance of every account, in the currency of the company.

    The accounts are grouped by company, because ERPNext computes the balance
    of a company.
    """
    if not the_accounts:
        return {}

    try:
        the_may_read = frappe.has_permission("Account", "read")
    except frappe.DoesNotExistError:
        # A site without ERPNext has no accounts at all.
        frappe.throw(
            frappe._(
                "The balance of an account needs ERPNext, which is not installed on this site."
            )
        )

    if not the_may_read:
        frappe.throw(
            frappe._("The balance of an account needs the permission to read Account."),
            frappe.PermissionError,
        )

    the_balances: dict[str, float] = {}
    for the_company, the_names in the_accounts_of_every_company(the_accounts).items():
        the_balances.update(the_balances_of_the_company(the_company, the_names))

    return the_balances


def the_accounts_of_every_company(the_accounts: list[dict[str, Any]]) -> dict[str, list[str]]:
    """The names of the accounts of every company."""
    the_companies: dict[str, list[str]] = {}
    for the_account in the_accounts:
        the_companies.setdefault(the_account.get("company") or "", []).append(the_account["name"])

    return the_companies


def the_balances_of_the_company(the_company: str, the_names: list[str]) -> dict[str, float]:
    """The balance of every account of one company, in the currency of the company.

    ERPNext reads the whole ledger of a company in one query when it can. That
    query needs the permission to read the ledger, so the accounts are read one
    by one when the caller may not read the ledger.
    """
    if the_company and the_ledger_is_readable():
        the_balances = the_balances_of_the_ledger(the_company)
        if the_balances is not None:
            the_missing = [the_name for the_name in the_names if the_name not in the_balances]
            if the_missing:
                # The scan of the ledger does not return an account when the
                # caller may not read it, so a missing account is a missing
                # permission and not a balance of zero.
                frappe.throw(
                    frappe._(
                        "The balance of every account needs the permission to read the accounts of the company."
                    ),
                    frappe.PermissionError,
                )
            return {the_name: the_balances.get(the_name, 0.0) for the_name in the_names}

    return {the_name: the_balance_of_the_account(the_name, the_company) for the_name in the_names}


def the_ledger_is_readable() -> bool:
    """Whether the caller may read the ledger of the company.

    A site without ERPNext has no ledger at all, so the ledger is not
    readable there and the balance cannot be computed.
    """
    try:
        return bool(frappe.has_permission("GL Entry", "read"))
    except frappe.DoesNotExistError:
        return False


def the_balances_of_the_ledger(the_company: str) -> dict[str, float] | None:
    """The balance of every account of a company, in the currency of the company.

    ``None`` when the installed ERPNext has no such calculation.
    """
    try:
        from erpnext.accounts.utils import get_account_balances_coa
    except ImportError:
        return None

    return {
        the_row["value"]: flt(the_row["balance"], 2)
        for the_row in get_account_balances_coa(the_company)
    }


def the_balance_of_the_account(the_name: str, the_company: str) -> float:
    """The balance of one account, in the currency of the company."""
    try:
        from erpnext.accounts.utils import get_balance_on
    except ImportError:
        frappe.throw(
            frappe._(
                "The balance of an account needs ERPNext, which is not installed on this site."
            )
        )

    return flt(
        get_balance_on(
            account=the_name,
            company=the_company or None,
            in_account_currency=False,
        ),
        2,
    )
