# Small database helpers shared across the app.
#
# frappe.db.set_value accepts a dict of column values at runtime (see
# frappe.database.database._get_update_dict), but the public type annotation
# of that signature only allows a single field name. These wrappers preserve
# the runtime behaviour while staying type-safe.

from typing import Any, cast

import frappe


def set_values(doctype: str, docname: str, values: dict[str, Any]) -> None:
    # Update several columns of one document with a single UPDATE query.
    # Mirrors frappe.db.set_value(dt, dn, {field: value}).
    frappe.db.set_value(doctype, docname, cast(Any, values))
