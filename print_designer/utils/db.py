# Small database helpers shared across the app.
#
# frappe.db.set_value accepts a dict of column values at runtime (see
# frappe.database.database._get_update_dict), but the public type annotation
# of that signature only allows a single field name. These wrappers preserve
# the runtime behaviour while staying type-safe.

from typing import Any, cast

import frappe


def sql_rows(result: Any) -> list[dict[str, Any]]:
    # Narrow the result of an "as_dict=True" SQL query.
    #
    # frappe.db.sql is annotated with a union of return shapes, so the
    # mapping rows have to be narrowed before they are read.  The runtime
    # behaviour is unchanged.
    return cast("list[dict[str, Any]]", result)


def set_values(
    doctype: str,
    docname: str,
    values: dict[str, Any],
    update_modified: bool = True,
) -> None:
    # Update several columns of one document with a single UPDATE query.
    # Mirrors frappe.db.set_value(dt, dn, {field: value}).
    #
    # The dict is copied, because frappe adds the modified columns to the
    # dict that it receives when the modified timestamp is written.
    if update_modified:
        frappe.db.set_value(doctype, docname, cast(Any, dict(values)))
        return

    frappe.db.set_value(
        doctype,
        docname,
        cast(Any, dict(values)),
        update_modified=False,
    )
