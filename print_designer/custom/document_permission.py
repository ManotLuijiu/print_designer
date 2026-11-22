# Copyright (c) 2026, MooCoding and contributors
# For license information, please see license.txt

"""The right of the caller on one document, without the answer of a document
that is not there.

The check of the right needs the document itself, and Frappe loads that
document to check it.  A document that is not on the site is therefore
reported as a missing document, and the report stays in the log of the
messages of the request.  The answer of the request carries that log, so a
caller without the right could ask for a name and learn whether the site
holds a document of that name.

The helper here mutes the messages of the check, so that the check leaves
nothing behind in the log of the messages, and it takes the report of the
missing document out of the log as well, should a version of Frappe leave
it there.  The answer of the request is then the same for a document that is
not there and for a document that the caller may not touch.

A failure of another kind is not swallowed: a broken permission hook or a
broken database must still raise.  A missing document that is raised from
anywhere inside the check is reported as no right held, so that the answer of
the request never tells a document that is not there from a document that the
caller may not touch.

This helper belongs to Print Designer.  It does not import Thai Business
Suite, so that the VAT behaviour of Print Designer works on a site where that
app is not installed.
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import frappe
from frappe import _


def has_document_permission(doctype: str, ptype: str, name: Any) -> bool:
    """The right of the caller on the document.

    Args:
            doctype: the doctype of the document.
            ptype: the right that is checked, ``read`` or ``write``.
            name: the name of the document.

    Returns:
            True when the caller holds the right on the document, and False when
            the caller holds no right on it or when the document is not on the
            site.  The answer does not tell the two apart.  The Administrator
            holds every right and is therefore answered with True.
    """
    the_name = _the_name_of(name)

    # A document that was not named is no document at all, and a check
    # without a document would be a check of the whole doctype.  The answer
    # of the caller is no right, so that the check never widens itself on
    # its own.
    if not the_name:
        return False

    try:
        with _the_messages_of_the_check_muted():
            return bool(frappe.has_permission(doctype, ptype, doc=the_name))
    except frappe.DoesNotExistError as the_missing_document:
        _forget_the_report_of_the_missing_document(the_missing_document)
        return False


def _the_name_of(name: Any) -> str:
    """The name of the document, as the check of the right wants it.

    A document carries its own name, and a name that was not given is no
    name at all.

    Args:
            name: the name of the document, or the document itself.

    Returns:
            The name of the document, without the spaces around it.
    """
    the_name = getattr(name, "name", name)

    return str(the_name or "").strip()


@contextmanager
def _the_messages_of_the_check_muted() -> Generator[None, None, None]:
    """The messages of the check of the right do not reach the answer.

    The check of the right leaves a report in the log of the messages of the
    request: the report of a document that is not there, and the report that
    tells why the right of a document that is on the site was refused.  The
    first report is there only when the document is not there, and the
    second only when it is, so either of them tells the caller which of the
    two it is.  The report of the check is muted here, so that the answer of
    the request is the same for the two.

    Args:
            None.

    Yields:
            The check of the right, with its reports muted.
    """
    the_was_muted = frappe.flags.mute_messages
    frappe.flags.mute_messages = True

    try:
        yield
    finally:
        frappe.flags.mute_messages = the_was_muted


def _forget_the_report_of_the_missing_document(the_error: BaseException) -> None:
    """Take the report of the missing document out of the log of the messages.

    The check of the right is muted, so the report of the missing document
    is not normally there.  This is the second line of the defence, for a
    version of Frappe that leaves the report in the log in spite of the
    muting.  Frappe gives the report and the error it raises the same mark,
    so the report of this error is found by that mark.  Only the reports of
    that mark are removed; the other messages of the request are left alone.

    Args:
            the_error: the error that Frappe raised for the missing document.
    """
    the_mark = getattr(the_error, "__frappe_exc_id", None)

    if not the_mark:
        return

    # The log of the messages is the list itself, so the report is taken out
    # of the answer that is built from it later on.
    the_log: list[Any] | None = getattr(frappe.local, "message_log", None)

    if not isinstance(the_log, list):
        return

    the_reports = [
        the_index
        for the_index, the_message in enumerate(the_log)
        if isinstance(the_message, dict) and the_message.get("__frappe_exc_id") == the_mark
    ]

    for the_index in reversed(the_reports):
        del the_log[the_index]


def require_document_read(doctype: str, name: Any) -> str:
    """Refuse the caller that may not read the document.

    Args:
            doctype: the doctype of the document.
            name: the name of the document.

    Returns:
            The name of the document, as it was given.

    Raises:
            frappe.PermissionError: when the name is empty or the caller may not
                    read the document.
    """
    document_name = str(name or "").strip()

    if not document_name:
        frappe.throw(
            _("The name of the {0} is required").format(doctype),
            frappe.PermissionError,
        )

    # The document does not exist, so there is nothing to read.  The check of
    # the permission needs the document, and a missing document is refused
    # instead of being reported as a missing document.
    if not has_document_permission(doctype, "read", document_name):
        frappe.throw(
            _("Not permitted to read the {0} {1}").format(doctype, document_name),
            frappe.PermissionError,
        )

    return document_name


def require_document_write(doctype: str, name: Any) -> str:
    """Refuse the caller that may not write the document.

    Args:
            doctype: the doctype of the document.
            name: the name of the document.

    Returns:
            The name of the document, as it was given.

    Raises:
            frappe.PermissionError: when the name is empty or the caller may not
                    write the document.
    """
    document_name = str(name or "").strip()

    if not document_name:
        frappe.throw(
            _("The name of the {0} is required").format(doctype),
            frappe.PermissionError,
        )

    # The document does not exist, so there is nothing to write.
    if not has_document_permission(doctype, "write", document_name):
        frappe.throw(
            _("Not permitted to write the {0} {1}").format(doctype, document_name),
            frappe.PermissionError,
        )

    return document_name


def require_doctype_permission(doctype: str, ptype: str) -> None:
    """Refuse the caller that may not use the doctype.

    The doctype of a record that does not exist yet can only be asked for
    with the right of the doctype, and that is the right the endpoints use
    for the records they create.

    Args:
            doctype: the doctype of the records.
            ptype: the right that is asked for, ``read``, ``write`` or ``create``.

    Raises:
            frappe.PermissionError: when the caller does not hold the right.
    """
    if not frappe.has_permission(doctype, ptype):
        frappe.throw(
            _("Not permitted to {0} the {1}").format(ptype, doctype),
            frappe.PermissionError,
        )
