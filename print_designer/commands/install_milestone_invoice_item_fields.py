# Copyright (c) 2026, Frappe Technologies Pvt Ltd. and contributors
# For license information, please see license.txt

"""The percent column of the milestone Sales Invoice Item.

A milestone invoice bills a part of the contract, not the whole contract.
The part it bills is written into a column of its own, right after the
rate, so the customer sees it on the invoice and not only in the
description of the line.

The column is part of the lifecycle of the app:

- `after_install` installs it, so a fresh site has it right away.
- `after_migrate` installs it again on every migrate, so a site that was
  installed before the column existed catches up.
- `before_uninstall` removes it again, the column of the database stays
  behind like with every other custom field of the app.
"""

from typing import Any

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import cint

FIELDNAME = "pd_custom_invoice_portion"
DOCTYPE = "Sales Invoice Item"
ANCHOR = "rate"


def get_milestone_invoice_item_fields():
    """The custom field definition of the percent column."""
    return {
        DOCTYPE: [
            {
                "fieldname": FIELDNAME,
                "fieldtype": "Percent",
                "label": "%",
                "insert_after": ANCHOR,
                "in_list_view": 1,
                "columns": 1,
                "read_only": 1,
                "hidden": 0,
                "default": None,
                "description": "The part of the Sales Order this line bills, in percent.",
            }
        ]
    }


def get_position():
    """The distance of the column to the Rate column.

    1 means the column sits directly after the Rate column.
    """
    meta = frappe.get_meta(DOCTYPE)
    fieldnames = [df.fieldname for df in meta.fields]

    if FIELDNAME not in fieldnames or ANCHOR not in fieldnames:
        return None

    return fieldnames.index(FIELDNAME) - fieldnames.index(ANCHOR)


def _ensure_position():
    """Keep the column right after the Rate column.

    Frappe does not move an existing custom field when its `insert_after`
    changes, so the anchor is written again and the index of the field is
    recalculated. The field is never deleted, the percentages that are
    already stored on the milestone invoices stay untouched.
    """
    name = frappe.db.get_value("Custom Field", {"dt": DOCTYPE, "fieldname": FIELDNAME}, "name")
    if not isinstance(name, str) or not name:
        return

    if frappe.db.get_value("Custom Field", name, "insert_after") != ANCHOR:
        frappe.db.set_value("Custom Field", name, "insert_after", ANCHOR)

    raw_idx: Any = frappe.db.get_value("DocField", {"parent": DOCTYPE, "fieldname": ANCHOR}, "idx")
    anchor_idx = cint(raw_idx)
    if anchor_idx:
        frappe.db.set_value("Custom Field", name, "idx", anchor_idx + 1)

    frappe.clear_cache(doctype=DOCTYPE)


def install_milestone_invoice_item_fields():
    """Create or update the percent column of the Sales Invoice Item.

    The call is idempotent, it runs on every install and on every migrate.
    """
    try:
        create_custom_fields(get_milestone_invoice_item_fields(), update=True)
        _ensure_position()

        return {"success": True, "field": FIELDNAME, "position": get_position()}
    except Exception as e:
        error_msg = f"Error installing the milestone percent column: {str(e)}"
        frappe.log_error(error_msg, "Milestone Invoice Item Fields Installation Error")
        return {"success": False, "field": FIELDNAME, "error": error_msg}


def uninstall_milestone_invoice_item_fields():
    """Remove the percent column again."""
    name = frappe.db.get_value(
        "Custom Field",
        {"dt": DOCTYPE, "fieldname": FIELDNAME},
        "name",
    )

    if isinstance(name, str) and name:
        frappe.delete_doc("Custom Field", name, force=True)
        frappe.db.commit()

    return {"success": True, "field": FIELDNAME}


def main():
    """Main execution function for command line usage."""
    return install_milestone_invoice_item_fields()


if __name__ == "__main__":
    main()
