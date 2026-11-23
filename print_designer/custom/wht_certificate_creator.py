"""The creation of the certificate of the withholding tax of a payment.

Print Designer holds the certificate of the withholding tax of Thailand in
one document: ``Withholding Tax Certificate``.  This module is the single
place that creates that document.  Both entry points of Print Designer use
it:

- ``print_designer.custom.thai_tax_calculator.create_withholding_tax_certificate``,
  the path of the settings of the tax of the site;
- ``print_designer.custom.wht_certificate_generator.create_wht_certificate_from_payment_entry``,
  the path of the payment entry of a purchase invoice.

The income type of the certificate is the income type of the site, the
``Thai WHT Income Type`` of Print Designer, which works together with the
``Tax Withholding Category`` of ERPNext.  The mapping of that income type
onto the statutory values of the certificate is in
``print_designer.custom.wht_canonical_mapping``.

The certificate is the certificate of an outgoing withholding.  The incoming
withholding of Thailand is a different document of the site, the
``Receive WHT Register``: it carries the certificate of the customer, which
the site receives, and not a certificate that the site issues.
"""

from typing import Any, cast

import frappe
from frappe.model.naming import make_autoname
from frappe.utils import flt, getdate

from print_designer.custom.payment_wht_certificate_link import (
    set_issued_wht_certificate,
)
from print_designer.custom.wht_canonical_mapping import (
    DEFAULT_INCOME_TYPE,
    WHT_CONDITION,
    get_tax_month,
    get_tax_year,
    resolve_income_type,
)

#: The document of the certificate of the withholding tax of Thailand.
CERTIFICATE_DOCTYPE = "Withholding Tax Certificate"

#: The field of the payment entry that names its certificate.
LINK_FIELD = "pd_custom_wht_certificate"

#: The fields of the payment entry that carry the income type of the
#: withholding tax.  The first one is the category of ERPNext, the second one
#: is the detail of it.
INCOME_TYPE_FIELDS = ("pd_custom_wht_income_type", "pd_custom_wht_income_type_details")

#: The fields of the payment entry that carry the amounts of the withholding
#: tax, for a payment entry that carries no row of the withholding tax.
AMOUNT_FIELDS = {
    "tax_amount": "pd_custom_withholding_tax_amount_details",
    "rate": "pd_custom_withholding_tax_pct_details",
    "gross_amount": "pd_custom_tax_base_amount",
}


def _as_row(tax: Any) -> dict[str, Any]:
    """The row of the withholding tax as a dictionary.

    A row of a child table is a document of the site, and a document is no
    dictionary.  A row that reaches the certificate as a plain dictionary
    stays a dictionary.
    """
    if hasattr(tax, "as_dict"):
        return dict(tax.as_dict())

    return dict(tax)


def get_wht_rows(payment_entry: Any) -> list[dict[str, Any]]:
    """The rows of the withholding tax of a payment entry.

    A row is a row of the withholding tax when it carries a withholding tax
    account and an amount of tax.  A payment entry that carries no such row
    carries the amounts of the withholding tax in its own fields.
    """
    rows: list[dict[str, Any]] = []

    for tax in payment_entry.get("taxes") or []:
        if tax.get("is_tax_withholding_account") and flt(tax.get("tax_amount")) > 0:
            rows.append(_as_row(tax))

    if rows:
        return rows

    amounts = {key: flt(payment_entry.get(fieldname)) for key, fieldname in AMOUNT_FIELDS.items()}
    if amounts["tax_amount"] > 0:
        return [amounts]

    return []


def get_transaction_income_type(payment_entry: Any) -> str | None:
    """The income type of the withholding tax of a payment entry.

    The value is the name of a ``Tax Withholding Category`` of ERPNext or the
    name of a ``Thai WHT Income Type`` of Print Designer.
    """
    for fieldname in INCOME_TYPE_FIELDS:
        value = payment_entry.get(fieldname)
        if value:
            return str(value)

    return None


def get_entity_type(payment_entry: Any) -> str:
    """The kind of the payee of a payment entry.

    The kind of the payee is ``Individual``, ``Company`` or ``Government``.
    It is the fallback of an income type that the site carries as the
    statutory section of the law of Thailand.
    """
    if payment_entry.get("party_type") != "Supplier":
        return "Company"

    party = payment_entry.get("party")
    if not party:
        return "Company"

    supplier_group = frappe.db.get_value("Supplier", party, "supplier_group")
    return entity_type_of_group(cast(str | None, supplier_group))


def entity_type_of_group(group: str | None) -> str:
    """The kind of party of a group of a supplier.

    A group that carries the name of the government or of an individual is
    the group of that kind of party.
    """
    if not group:
        return "Company"

    group_lower = group.lower()
    if "government" in group_lower or "รัฐ" in group_lower:
        return "Government"
    if "individual" in group_lower or "บุคคล" in group_lower:
        return "Individual"

    return "Company"


def get_supplier_address(payment_entry: Any) -> str:
    """The address of the supplier of a payment entry, as text."""
    if payment_entry.get("party_type") != "Supplier":
        return ""

    party = payment_entry.get("party")
    if not party:
        return ""

    address = frappe.db.get_value("Supplier", party, "supplier_primary_address")
    if not address:
        return ""

    lines = []
    for field in ("address_line1", "address_line2", "city", "pincode", "country"):
        value = frappe.db.get_value("Address", address, field)
        if value:
            lines.append(str(value))

    return ", ".join(lines)


def _merge_fallback(resolved: dict[str, Any], fallback: dict[str, Any] | None) -> dict[str, Any]:
    """The values of the fallback that the resolution of the site lacks.

    A fallback carries the values that the site cannot know, for a site that
    carries no income type of its own.  It fills the gaps of the canonical
    mapping and never replaces a value of that mapping with nothing.
    """
    if not fallback:
        return resolved

    merged = dict(resolved)
    for key, value in fallback.items():
        if value:
            merged[key] = value

    return merged


def resolve_certificate_income_type(
    payment_entry: Any,
    entity_type: str,
    fallback: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """The income type of the certificate of a payment entry.

    The income type of the site is the source of the values of the
    certificate.  The fallback is the income type of the caller, for a site
    that carries no income type of its own.
    """
    resolved = resolve_income_type(get_transaction_income_type(payment_entry), entity_type)

    if resolved.get("income_type"):
        return resolved

    if fallback:
        default = resolve_income_type(DEFAULT_INCOME_TYPE, entity_type)
        return {**_merge_fallback(default, fallback), "source": "fallback"}

    return resolve_income_type(DEFAULT_INCOME_TYPE, entity_type)


def build_income_items(
    payment_entry: Any,
    rows: list[dict[str, Any]],
    entity_type: str,
    fallback: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """The rows of the income items of the certificate.

    Every row of the withholding tax of the payment entry becomes a row of
    the income items of the certificate.  The income type of the row is the
    income type of the row of the withholding tax, or the income type of the
    transaction when the row carries none.
    """
    payment_date = getdate(payment_entry.get("posting_date"))
    transaction_income_type = get_transaction_income_type(payment_entry)
    items = []

    for row in rows:
        raw_income_type = row.get("tbs_income_type") or transaction_income_type

        if raw_income_type:
            resolved = resolve_income_type(raw_income_type, entity_type)
            if not resolved.get("income_type"):
                resolved = _merge_fallback(
                    resolve_income_type(DEFAULT_INCOME_TYPE, entity_type), fallback
                )
        else:
            resolved = _merge_fallback(
                resolve_income_type(DEFAULT_INCOME_TYPE, entity_type), fallback
            )

        rate = flt(row.get("rate"))
        if rate <= 0:
            rate = flt(resolved.get("rate"))

        tax_amount = flt(row.get("tax_amount"))
        gross_amount = flt(row.get("gross_amount"))
        if gross_amount <= 0:
            gross_amount = tax_amount / (rate / 100) if rate > 0 else tax_amount

        items.append(
            {
                "payment_date": payment_date,
                "income_type": resolved.get("item_income_type") or "",
                "income_type_description": resolved.get("description") or "",
                "tax_rate": rate,
                "gross_amount": gross_amount,
                "tax_amount": tax_amount,
                "net_amount": gross_amount - tax_amount,
            }
        )

    return items


def build_certificate_values(
    payment_entry: Any,
    items: list[dict[str, Any]],
    entity_type: str,
    remarks: str | None = None,
    fallback: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """The values of the certificate of the withholding tax.

    The income type of the certificate is the income type of the transaction:
    the field `pd_custom_wht_income_type` of the payment entry, which holds
    the name of a `Thai WHT Income Type` or the name of a
    `Tax Withholding Category` of ERPNext.  A transaction that carries none
    falls back to the income type of the kind of the payee.

    The rate of the certificate is the rate of its first row of the incomes.
    """
    resolved = resolve_certificate_income_type(payment_entry, entity_type, fallback)

    posting_date = getdate(payment_entry.get("posting_date"))

    total_gross_amount = sum(flt(item.get("gross_amount")) for item in items)
    total_tax_amount = sum(flt(item.get("tax_amount")) for item in items)

    first_rate = flt(items[0].get("tax_rate")) if items else 0.0

    company = payment_entry.get("company")
    party = payment_entry.get("party")

    values = {
        "doctype": CERTIFICATE_DOCTYPE,
        "certificate_number": make_autoname(
            "WHTC-{0}{1}-.#####".format(
                get_tax_year(posting_date)[-2:],
                str(posting_date.month).zfill(2) if posting_date else "00",
            )
        )
        if posting_date
        else "",
        "certificate_date": posting_date,
        "tax_year": get_tax_year(posting_date),
        "tax_month": get_tax_month(posting_date) or "",
        "status": "Issued",
        "supplier": party,
        "supplier_name": payment_entry.get("party_name"),
        "supplier_tax_id": frappe.db.get_value("Supplier", party, "tax_id") if party else None,
        "supplier_address": get_supplier_address(payment_entry),
        "supplier_branch_code": "00000",
        "supplier_type_classification": resolved.get("classification") or "",
        "payment_entry": payment_entry.name,
        "payment_date": posting_date,
        "company": company,
        "company_branch": "00000",
        "income_type": resolved.get("income_type") or "",
        "income_description": resolved.get("description") or "",
        "wht_rate": first_rate,
        "wht_condition": WHT_CONDITION,
        "tax_base_amount": total_gross_amount,
        "wht_amount": total_tax_amount,
        "net_payment_amount": total_gross_amount - total_tax_amount,
        "total_payment_amount": total_gross_amount,
        "remarks": remarks or "",
        "pnd_form_type": resolved.get("pnd_form"),
        "income_items": items,
    }

    return values


def get_existing_certificate(payment_entry: Any) -> str | None:
    """The name of the certificate of a payment entry, when it has one."""
    existing = frappe.db.exists(
        CERTIFICATE_DOCTYPE,
        {"payment_entry": payment_entry.name, "docstatus": ["<", 2]},
    )

    return str(existing) if existing else None


def create_certificate(payment_entry: Any, values: dict[str, Any]) -> Any:
    """Create the certificate of the withholding tax of a payment entry.

    The certificate of the payment entry is kept when it has one already:
    a payment entry carries one withholding certificate.
    """
    existing = get_existing_certificate(payment_entry)
    if existing:
        certificate = frappe.get_doc(CERTIFICATE_DOCTYPE, existing)
        _link_the_payment_entry(payment_entry, str(certificate.name))

        return certificate

    certificate = frappe.get_doc(values)
    certificate.insert()
    certificate.submit()
    _link_the_payment_entry(payment_entry, str(certificate.name))

    return certificate


def _link_the_payment_entry(payment_entry: Any, certificate_name: str) -> None:
    """Keep the link of the payment entry and the certificate of its tax.

    The payment entry names the certificate that holds its withholding, so
    that the site shows the certificate of the payment entry.  A site
    without the field of the link has no link to keep; the certificate is
    then the only record of the withholding.
    """
    if not payment_entry.meta.get_field(LINK_FIELD):
        return

    set_issued_wht_certificate(payment_entry, certificate_name)


def create_certificate_for_payment_entry(
    payment_entry: Any,
    remarks: str | None = None,
    fallback: dict[str, Any] | None = None,
    rows: list[dict[str, Any]] | None = None,
) -> Any:
    """Create the certificate of the withholding tax of a payment entry.

    The certificate is the certificate of an outgoing withholding.  A payment
    entry that receives money carries no certificate of the site; the
    incoming withholding of Thailand is the ``Receive WHT Register``.
    """
    if payment_entry.get("payment_type") != "Pay":
        return None

    if payment_entry.get("party_type") != "Supplier":
        # The certificate of Thailand names the supplier that is paid.
        return None

    wht_rows = rows if rows is not None else get_wht_rows(payment_entry)
    if not wht_rows:
        return None

    entity_type = get_entity_type(payment_entry)
    items = build_income_items(payment_entry, wht_rows, entity_type, fallback)
    values = build_certificate_values(
        payment_entry,
        items,
        entity_type,
        remarks=remarks,
        fallback=fallback,
    )

    return create_certificate(payment_entry, values)
