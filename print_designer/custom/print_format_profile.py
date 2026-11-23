"""Transaction profile of a Print Designer format.

A *profile* classifies a print format by the transaction it serves, so the
print selector can offer the layout that matches the document.  The profile
is advisory: it never changes posting, tax calculation or ledger data.

The profile lives in two optional Print Designer-owned Print Format fields
so it survives a download of the format and the installation of the
template:

``pd_custom_transaction_direction``
    The direction of the transaction.  Only ``Payment Entry`` carries a
    direction; a ``Sales Invoice`` is always a sale.

``pd_custom_transaction_type``
    Whether the transaction is for ``Services`` or for ``Goods``.

A format without a profile stays a general-purpose template: it remains
selectable for every document of its DocType.
"""

from __future__ import annotations

import frappe

TRANSACTION_DIRECTIONS = ("Pay", "Receive")
TRANSACTION_TYPES = ("Services", "Goods")

DIRECTION_FIELD = "pd_custom_transaction_direction"
TYPE_FIELD = "pd_custom_transaction_type"

# The DocTypes that can carry a profile.
SALES_DOCTYPE = "Sales Invoice"
PAYMENT_DOCTYPE = "Payment Entry"

# The profile of a format, keyed by the DocType of the format.
PROFILE_BY_DOCTYPE = {
    SALES_DOCTYPE: {"direction": None, "type": True},
    PAYMENT_DOCTYPE: {"direction": True, "type": True},
}


def get_profile_fields() -> list[dict]:
    """The custom field definitions of the profile.

    Both fields carry a blank first option.  Frappe fills the value of a
    new Select with its first option, so a field that starts with "Pay"
    or with "Services" would give every new format a profile.  A format
    without a profile stays a general purpose template.
    """
    return [
        {
            "fieldname": DIRECTION_FIELD,
            "label": "Transaction Direction",
            "fieldtype": "Select",
            "options": "\n" + "\n".join(TRANSACTION_DIRECTIONS),
            "insert_after": "pdf_generator",
            "depends_on": "eval:doc.doc_type == 'Payment Entry'",
            "description": "Direction of the transaction this format serves",
        },
        {
            "fieldname": TYPE_FIELD,
            "label": "Transaction Type",
            "fieldtype": "Select",
            "options": "\n" + "\n".join(TRANSACTION_TYPES),
            "insert_after": DIRECTION_FIELD,
            "depends_on": (
                "eval:doc.doc_type == 'Payment Entry' || doc.doc_type == 'Sales Invoice'"
            ),
            "description": "Type of the transaction this format serves",
        },
    ]


def install_profile_fields() -> None:
    """Install the profile fields on the Print Format DocType.

    The fields must exist before a template that carries a profile is
    imported, otherwise the profile is dropped on the insert.
    """
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    create_custom_fields({"Print Format": get_profile_fields()}, update=True)


def supports_profile(doc_type: str | None) -> bool:
    """True when a format of ``doc_type`` can carry a profile."""
    return (doc_type or "") in PROFILE_BY_DOCTYPE


def validate_profile(
    doc_type: str | None,
    direction: str | None = None,
    transaction_type: str | None = None,
) -> None:
    """Validate a profile against the DocType of the format.

    :raises frappe.ValidationError: when a value does not belong to the
            DocType of the format.
    """
    if not supports_profile(doc_type):
        if direction or transaction_type:
            frappe.throw(
                frappe._(
                    "A transaction profile is only available for Sales Invoice and Payment Entry"
                )
            )
        return

    rules = PROFILE_BY_DOCTYPE[str(doc_type)]

    if direction:
        if not rules["direction"]:
            frappe.throw(frappe._("A Sales Invoice format has no transaction direction"))
        if direction not in TRANSACTION_DIRECTIONS:
            frappe.throw(frappe._("Unknown transaction direction: {0}").format(direction))

    if transaction_type and transaction_type not in TRANSACTION_TYPES:
        frappe.throw(frappe._("Unknown transaction type: {0}").format(transaction_type))


def get_profile(print_format) -> dict:
    """The profile of a Print Format document."""
    return {
        "direction": print_format.get(DIRECTION_FIELD) or None,
        "transaction_type": print_format.get(TYPE_FIELD) or None,
    }


def classify_transaction(doc) -> dict:
    """The profile that a transaction document suggests.

    The direction is read from the document itself.  The transaction type
    is derived with the rules of the tax workflow, so the layout that is
    suggested is the layout that the tax workflow uses.

    A ``Payment Entry`` is classified through its linked invoices: a
    receipt follows its Sales Invoice references, a supplier payment
    follows its Purchase Invoice references.  A classification is only
    suggested when the linked invoices agree.  A mixed or unclassified
    transaction keeps the manual selection.
    """
    direction = None
    doc_type = doc.get("doctype")
    transaction_type = None

    if doc_type == PAYMENT_DOCTYPE:
        payment_type = doc.get("payment_type")
        if payment_type in TRANSACTION_DIRECTIONS:
            direction = payment_type

        transaction_type = _classify_payment_entry(doc)
    elif doc_type == SALES_DOCTYPE:
        transaction_type = _classify_items(doc.get("items"))

    return {"direction": direction, "transaction_type": transaction_type}


def _classify_items(items) -> str | None:
    """Classify the item rows of a document.

    The classification uses the tax workflow rules: an item is a service
    when the service flag or the service item group says so, otherwise it
    is a stock item.  Rows that disagree leave the document unclassified.
    """
    item_codes = [row.get("item_code") for row in (items or []) if row.get("item_code")]

    return _classify_item_codes(item_codes)


def _classify_item_codes(item_codes) -> str | None:
    """Classify a list of item codes as ``Services`` or ``Goods``.

    The classification is only returned when every known item agrees.  An
    unknown item is ignored, a mixed list stays unclassified.
    """
    from print_designer.custom.sales_invoice_tax_contract import get_item_tax_info

    codes = [code for code in (item_codes or []) if code]
    if not codes:
        return None

    info = get_item_tax_info(codes)

    services = 0
    goods = 0
    for code in codes:
        row = info.get(code)
        if not row:
            continue

        if row.get("is_service"):
            services += 1
        elif row.get("is_stock"):
            goods += 1

    if services and not goods:
        return "Services"

    if goods and not services:
        return "Goods"

    return None


def _classify_payment_entry(doc) -> str | None:
    """Classify a Payment Entry through its linked invoices.

    A receipt follows its Sales Invoice references, a supplier payment
    follows its Purchase Invoice references.  The other kind of reference
    is used when the preferred kind is absent.  The classification is only
    returned when the linked invoices agree.
    """
    payment_type = doc.get("payment_type")
    preferred = "Sales Invoice" if payment_type == "Receive" else "Purchase Invoice"

    references: dict[str, list[str]] = {}
    for row in doc.get("references") or []:
        reference_doctype = row.get("reference_doctype")
        reference_name = row.get("reference_name")
        if reference_doctype in ("Sales Invoice", "Purchase Invoice") and reference_name:
            references.setdefault(reference_doctype, []).append(reference_name)

    invoices = references.get(preferred) or []
    if not invoices:
        for names in references.values():
            if names:
                invoices = names
                break

    if not invoices:
        return _classify_items(doc.get("items"))

    classified = set()
    for invoice in invoices:
        transaction_type = _classify_invoice(invoice)
        if transaction_type:
            classified.add(transaction_type)

    if len(classified) == 1:
        return classified.pop()

    return None


def _classify_invoice(invoice: str) -> str | None:
    """Classify a linked invoice through its item rows."""
    doctype = None
    for candidate in ("Sales Invoice", "Purchase Invoice"):
        if frappe.db.exists(candidate, invoice):
            doctype = candidate
            break

    if not doctype:
        return None

    # The endpoint only checks the permission of the printed document.  A
    # linked invoice may be restricted, and the rows of a child table are
    # not gated by the permission of their parent, so the permission of
    # the invoice itself is checked here.
    if not frappe.has_permission(doctype, "read", invoice):
        return None

    item_field = frappe.get_meta(doctype).get_field("items")
    if not item_field:
        return None

    item_codes = frappe.get_all(item_field.options, filters={"parent": invoice}, pluck="item_code")

    return _classify_item_codes(item_codes)
