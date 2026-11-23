"""Suggest the print format that matches a transaction.

The suggestion is advisory.  It preselects a format in the print selector
of the print view, so the layout that matches the transaction is one click
away, and the user keeps the manual selection.

The suggestion never changes the default print format of a DocType and it
never touches posting, tax calculation or ledger data.
"""

from __future__ import annotations

import frappe

from print_designer.custom.print_format_profile import (
    DIRECTION_FIELD,
    TYPE_FIELD,
    classify_transaction,
)


def _profile_fields_available() -> bool:
    """True when the profile fields exist on the site.

    The fields are installed by the app hooks.  A site that has not run
    the installation yet simply has no suggestions.
    """
    try:
        meta = frappe.get_meta("Print Format")
    except Exception:
        return False

    return meta.has_field(DIRECTION_FIELD) and meta.has_field(TYPE_FIELD)


def get_profile_aware_formats(doctype: str, docname: str | None = None) -> dict:
    """The print formats of a DocType and the profile of each format.

    :param doctype: the DocType of the document.
    :param docname: the document that is printed.  When it is given, the
            profile of the document is calculated as well.
    :returns: the formats with their profile, the profile of the document
            and the formats that match it.
    """
    result = {
        "profile": {"direction": None, "transaction_type": None},
        "formats": [],
        "suggestions": [],
        "available": False,
    }

    if not _profile_fields_available():
        return result

    result["available"] = True

    formats = frappe.get_all(
        "Print Format",
        filters={"doc_type": doctype, "disabled": 0},
        fields=["name", DIRECTION_FIELD, TYPE_FIELD],
        limit_page_length=0,
    )

    entries = []
    for row in formats:
        entries.append(
            {
                "name": row.get("name"),
                "direction": row.get(DIRECTION_FIELD) or None,
                "transaction_type": row.get(TYPE_FIELD) or None,
            }
        )

    result["formats"] = entries

    if docname and frappe.db.exists(doctype, docname):
        doc = frappe.get_doc(doctype, docname)
        result["profile"] = classify_transaction(doc)

    result["suggestions"] = suggest_formats(entries, result["profile"])

    return result


def suggest_formats(entries: list[dict], profile: dict) -> list[str]:
    """The formats of a list that match a profile.

    :param entries: the formats with their profile.
    :param profile: the profile of the document.
    """
    return [entry["name"] for entry in entries if matches_profile(entry, profile)]


def matches_profile(entry: dict, profile: dict) -> bool:
    """True when a format matches the profile of a document.

    A format without a profile is a general purpose template, it is never
    a suggestion.  A format that declares a profile only matches when the
    document carries the same value for every attribute that the format
    declares.  A document that the workflow could not classify never
    matches a format that declares a profile, so the manual selection
    stays available.
    """
    direction = entry.get("direction")
    transaction_type = entry.get("transaction_type")

    if not direction and not transaction_type:
        return False

    if direction:
        if not profile.get("direction") or profile["direction"] != direction:
            return False

    if transaction_type:
        if not profile.get("transaction_type") or profile["transaction_type"] != (transaction_type):
            return False

    return True


@frappe.whitelist()
def get_print_format_suggestions(doctype: str, docname: str | None = None) -> dict:
    """Suggest the print format that matches the printed document.

    :param doctype: the DocType of the document.
    :param docname: the document that is printed.
    """
    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(
            frappe._("You don't have permission to read this document"),
            frappe.PermissionError,
        )

    return get_profile_aware_formats(doctype, docname)
