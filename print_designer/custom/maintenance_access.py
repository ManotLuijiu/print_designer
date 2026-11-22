# Copyright (c) 2026, MooCoding and contributors
# For license information, please see license.txt

"""The right to run a command that changes the site for every company.

The maintenance endpoints of Print Designer (the installation of the fields of
the tax, the creation of the accounts of the tax, the reset of a field) change
metadata or data that every company of the site shares.  They therefore ask
for the ``System Manager`` role, which is the privileged role pattern of the
app.

``frappe.get_roles()`` returns every role for the Administrator, so the
administrator is allowed through the same check without a special case.

This helper belongs to Print Designer.  It does not import Thai Business
Suite, so that the tax behaviour of Print Designer works on a site where that
app is not installed.
"""

import frappe
from frappe import _


def require_system_manager(action: str) -> None:
    """Refuse the caller that may not run a command for the whole site.

    Args:
        action: a short description of the refused operation.  It is embedded
            in the message of the refusal, so that the caller knows what was
            denied.

    Raises:
        frappe.PermissionError: when the caller is not a System Manager.
    """
    if "System Manager" in frappe.get_roles():
        return

    frappe.throw(
        _("Not permitted to {0}. The System Manager role is required.").format(action),
        frappe.PermissionError,
    )
