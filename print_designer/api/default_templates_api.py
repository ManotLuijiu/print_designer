"""Administrative entry point for the missing-only default template installer."""

import frappe

from print_designer.default_templates_installer import install_missing_default_formats
from print_designer.utils.flags import is_truthy


@frappe.whitelist(methods=["POST"])
def run_default_template_installation(dry_run: bool | str | None = False):
    """Install every Print Designer default template that is missing.

    :param dry_run: when True nothing is inserted.  The candidates that would
            be installed are listed in the ``pending`` bucket of the result.

    :returns: the structured result of the installer.
    """
    if not _is_privileged():
        frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

    # The flag arrives from the request as a string, so "0" and "false" have to
    # read as "off".  The installer and the commit below have to agree on that
    # reading, otherwise a dry run would be committed or a real run would be
    # thrown away.  The annotation keeps the string form, because Frappe
    # validates the arguments of a whitelisted method against it before the
    # body runs, and a plain "bool" would reject "off" and "no" outright.
    dry_run = is_truthy(dry_run)

    results = install_missing_default_formats(dry_run=dry_run)
    if not dry_run:
        frappe.db.commit()

    return results


def _is_privileged() -> bool:
    if frappe.session.user == "Administrator":
        return True
    return "System Manager" in frappe.get_roles()
