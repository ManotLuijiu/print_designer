"""Typed helpers to read dynamic fields of Frappe documents.

Frappe stores the values of DocType specific fields in the instance dictionary of a
document, so static type checkers cannot see them. These helpers read such fields
with an explicit type instead of accessing undeclared attributes.
"""

from typing import Any, cast

from frappe.model.document import Document


def field_value(doc: Document, fieldname: str) -> Any:
    """The raw value of a dynamic field of a Frappe document."""
    return cast("Any", doc.get(fieldname))


def field_text(doc: Document, fieldname: str) -> str:
    """The value of a dynamic field of a Frappe document as text."""
    value = field_value(doc, fieldname)
    return "" if value is None else str(value)
