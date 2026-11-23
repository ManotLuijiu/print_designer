"""The certificates of the withholding tax of Thailand for the reports.

The canonical certificate of the withholding tax is `Withholding Tax
Certificate` and every income of a certificate is a row of `Withholding Tax
Item`.  Both are owned by Print Designer, so the reading of the certificates
belongs here as well; the reports of the Thai Business Suite read them
through this module and never name a table of the tax themselves.

The older `Withholding Tax Cert` carried one income per document and its
amounts in `total_gross_amount`, `total_tax_amount` and `total_net_amount`.
The canonical certificate carries the totals of the certificate in
`tax_base_amount`, `wht_amount` and `net_payment_amount`, and every income
of the certificate in the rows of `Withholding Tax Item`.  A report that needs
one row per income reads the incomes through `get_certificate_lines`, a
report that needs one row per certificate reads `get_certificates`.
"""

from __future__ import annotations

import re
from typing import Any

import frappe
from frappe.utils import flt

from print_designer.custom.wht_canonical_mapping import PND_FORM_DOCTYPES

CERTIFICATE_DOCTYPE = "Withholding Tax Certificate"
ITEM_DOCTYPE = "Withholding Tax Item"
RECEIVE_REGISTER_DOCTYPE = "Receive WHT Register"

#: The fields of the register of the incoming withholding tax.
RECEIVE_FIELDS = (
    "name",
    "wht_certificate_no",
    "wht_certificate_date",
    "customer",
    "customer_name",
    "customer_tax_id",
    "customer_branch_code",
    "customer_branch_name",
    "payment_entry",
    "payment_date",
    "company",
    "income_type",
    "legacy_income_type",
    "wht_rate",
    "tax_base_amount",
    "wht_amount",
    "status",
    "remarks",
)

#: The fields of the certificate that a report may need.
CERTIFICATE_FIELDS = (
    "name",
    "certificate_number",
    "certificate_date",
    "payment_date",
    "company",
    "supplier",
    "supplier_name",
    "supplier_tax_id",
    "supplier_address",
    "supplier_branch_code",
    "supplier_branch_name",
    "supplier_type_classification",
    "pnd_form_type",
    "income_type",
    "income_description",
    "wht_rate",
    "wht_condition",
    "tax_base_amount",
    "wht_amount",
    "net_payment_amount",
    "total_payment_amount",
    "tax_year",
    "tax_month",
    "status",
    "payment_entry",
    "purchase_invoice",
)

#: The fields of one income of a certificate.
ITEM_FIELDS = (
    "parent",
    "payment_date",
    "income_type",
    "income_type_description",
    "tax_rate",
    "gross_amount",
    "tax_amount",
    "net_amount",
    "remarks",
)

#: The code of the income of Thailand, e.g. ``40(1)`` or ``40(4)ก``.
INCOME_CODE_PATTERN = re.compile(r"^(40\(\d+\)[ก-ฮ]?)")

#: The code of the income of Thailand anywhere in a text, e.g. in the income
#: type of a certificate, where the code carries the description around it.
ANY_INCOME_CODE_PATTERN = re.compile(r"40\s*\(\s*\d+\s*\)\s*[ก-ฮ]?")


def get_pnd_form_type_names(pnd_types: list[str] | None) -> list[str] | None:
    """The names of the forms of the withholding tax of the forms of the report.

    The report of the Thai Business Suite names the form of the withholding tax
    as ``PND53``, the certificate names it as ``PND53 Form``.

    Args:
        pnd_types: the forms of the report, e.g. ``["PND53"]``.

    Returns:
        list: the names of the forms of the certificate, `None` when no form
        was given.
    """
    if not pnd_types:
        return None

    the_names = []
    for the_type in pnd_types:
        the_name = PND_FORM_DOCTYPES.get(the_type)
        if the_name:
            the_names.append(the_name)
        elif the_type:
            the_names.append(the_type)

    return the_names or None


def get_pnd_type_of_form(pnd_form_type: str | None) -> str:
    """The form of the withholding tax of the report of a name of a form.

    The certificate names the form of the withholding tax as ``PND53 Form``,
    the report of the Thai Business Suite names it as ``PND53``.

    Args:
        pnd_form_type: the name of the form of the certificate.

    Returns:
        str: the form of the report, an empty string when the name carries no
        form.
    """
    if not pnd_form_type:
        return ""

    for the_type, the_name in PND_FORM_DOCTYPES.items():
        if the_name == pnd_form_type:
            return the_type

    return str(pnd_form_type)


def get_income_code(income_type: str | None) -> str:
    """The code of the income of Thailand of an income type.

    The income type of a row of a certificate carries its code, e.g. ``40(8)
    ค่าบริการ/ค่าวิชาชีพอิสระ``.  The code of the income is returned without
    its description, e.g. ``40(8)``.

    Args:
        income_type: the income type of a row of a certificate.

    Returns:
        str: the code of the income, an empty string when the income type
        carries no code.
    """
    if not income_type:
        return ""

    match = INCOME_CODE_PATTERN.match(str(income_type).strip())
    return match.group(1) if match else ""


def find_income_code(income_type: str | None) -> str:
    """The code of the income of Thailand anywhere in an income type.

    The income type of a certificate carries its code around its description,
    e.g. ``8. ค่าโฆษณา - Advertising`` carries no code, but ``1. เงินเดือน
    ค่าจ้าง ฯลฯ 40(1) - Salary`` carries the code ``40(1)``.

    Args:
        income_type: the income type of a certificate.

    Returns:
        str: the code of the income, an empty string when the income type
        carries no code.
    """
    if not income_type:
        return ""

    match = ANY_INCOME_CODE_PATTERN.search(str(income_type))
    return match.group(0).replace(" ", "") if match else ""


def get_receive_registers(
    company: str | None = None,
    from_date: Any = None,
    to_date: Any = None,
    payment_from_date: Any = None,
    payment_to_date: Any = None,
    customer: str | None = None,
    tax_id: str | None = None,
    docstatus: int | None = None,
) -> list[frappe._dict]:
    """The canonical registers of the incoming withholding tax.

    The register of the incoming withholding tax is the counterpart of the
    certificate of the outgoing withholding tax.

    Args:
        company: the company of the registers.
        from_date: the first date of the register.
        to_date: the last date of the register.
        payment_from_date: the first date of the payment of the register.
        payment_to_date: the last date of the payment of the register.
        customer: the customer that paid the withholding tax.
        tax_id: the tax identification number of the customer.
        docstatus: the state of the register, 1 for a submitted register.

    Returns:
        list: the registers of the incoming withholding tax that match the
        filters.

    Raises:
        frappe.PermissionError: when the caller may not read the register.
    """
    if not frappe.has_permission(RECEIVE_REGISTER_DOCTYPE, "read"):
        frappe.throw(
            frappe._("Not permitted to read the {0} records").format(RECEIVE_REGISTER_DOCTYPE),
            frappe.PermissionError,
        )

    filters: dict[str, Any] = {}
    if company:
        filters["company"] = company
    if from_date or to_date:
        filters["wht_certificate_date"] = _date_range(from_date, to_date)
    if payment_from_date or payment_to_date:
        filters["payment_date"] = _date_range(payment_from_date, payment_to_date)
    if customer:
        filters["customer"] = customer
    if tax_id:
        filters["customer_tax_id"] = tax_id
    if docstatus is not None:
        filters["docstatus"] = docstatus

    return frappe.get_all(
        RECEIVE_REGISTER_DOCTYPE,
        filters=filters,
        fields=list(RECEIVE_FIELDS),
        order_by="payment_date asc, name asc",
        limit_page_length=0,
    )


def get_certificates(
    company: str | None = None,
    from_date: Any = None,
    to_date: Any = None,
    payment_from_date: Any = None,
    payment_to_date: Any = None,
    pnd_form_types: list[str] | None = None,
    statuses: list[str] | None = None,
    supplier: str | None = None,
    tax_id: str | None = None,
    docstatus: int | None = None,
) -> list[frappe._dict]:
    """The canonical certificates of the withholding tax that match the filters.

    Args:
        company: the company of the certificates.
        from_date: the first date of the certificate.
        to_date: the last date of the certificate.
        payment_from_date: the first date of the payment of the certificate.
        payment_to_date: the last date of the payment of the certificate.
        pnd_form_types: the forms of the withholding tax, e.g. ``PND53 Form``.
        statuses: the statuses of the certificate, e.g. ``Issued``.
        supplier: the supplier of the income.
        tax_id: the tax identification number of the supplier.
        docstatus: the state of the certificate, 1 for a submitted certificate.

    Returns:
        list: the certificates of the withholding tax that match the filters,
        the oldest certificate first.

    Raises:
        frappe.PermissionError: when the caller may not read the certificate.
    """
    if not frappe.has_permission(CERTIFICATE_DOCTYPE, "read"):
        frappe.throw(
            frappe._("Not permitted to read the {0} records").format(CERTIFICATE_DOCTYPE),
            frappe.PermissionError,
        )

    filters: dict[str, Any] = {}
    if company:
        filters["company"] = company
    if from_date or to_date:
        filters["certificate_date"] = _date_range(from_date, to_date)
    if payment_from_date or payment_to_date:
        filters["payment_date"] = _date_range(payment_from_date, payment_to_date)
    if pnd_form_types:
        filters["pnd_form_type"] = ["in", list(pnd_form_types)]
    if statuses:
        filters["status"] = ["in", list(statuses)]
    if supplier:
        filters["supplier"] = supplier
    if tax_id:
        filters["supplier_tax_id"] = tax_id
    if docstatus is not None:
        filters["docstatus"] = docstatus

    return frappe.get_all(
        CERTIFICATE_DOCTYPE,
        filters=filters,
        fields=list(CERTIFICATE_FIELDS),
        order_by="certificate_date asc, name asc",
        limit_page_length=0,
    )


def _date_range(from_date: Any, to_date: Any) -> list[Any]:
    """The filter of a range of dates, `>=` the first and `<=` the last."""
    if from_date and to_date:
        return [">=", from_date, "<=", to_date]
    if from_date:
        return [">=", from_date]
    return ["<=", to_date]


def get_income_items(certificate_names: list[str]) -> list[frappe._dict]:
    """The incomes of the certificates of the withholding tax.

    Args:
        certificate_names: the names of the certificates.

    Returns:
        list: the rows of the incomes of the certificates.
    """
    if not certificate_names:
        return []

    return frappe.get_all(
        ITEM_DOCTYPE,
        filters={"parent": ["in", list(certificate_names)]},
        fields=list(ITEM_FIELDS),
        order_by="parent asc, idx asc",
        limit_page_length=0,
    )


def get_certificate_lines(
    income_type_contains: str | None = None, **filters: Any
) -> list[frappe._dict]:
    """One row for every income of every certificate of the withholding tax.

    The filters are the filters of `get_certificates`, plus the income type of
    the report, which keeps only the incomes whose type carries it.

    A certificate without an income is still reported, with the totals of the
    certificate and the income type of the certificate itself.

    Returns:
        list: the incomes of the certificates that match the filters.
    """
    the_certificates = get_certificates(**filters)
    if not the_certificates:
        return []

    the_names = [str(the_certificate.name) for the_certificate in the_certificates]
    the_items = get_income_items(the_names)

    the_items_of: dict[str, list[frappe._dict]] = {}
    for the_item in the_items:
        the_parent = str(the_item.parent) if the_item.parent else ""
        the_items_of.setdefault(the_parent, []).append(the_item)

    the_lines = []
    for the_certificate in the_certificates:
        the_incomes = the_items_of.get(str(the_certificate.name)) or []
        if not the_incomes:
            the_line = _line_of_certificate(the_certificate, None)
            if _keeps_income_type(the_line, income_type_contains):
                the_lines.append(the_line)
            continue
        for the_income in the_incomes:
            the_line = _line_of_certificate(the_certificate, the_income)
            if _keeps_income_type(the_line, income_type_contains):
                the_lines.append(the_line)

    return the_lines


def _keeps_income_type(the_line: frappe._dict, income_type_contains: str | None) -> bool:
    """Whether an income of a report carries the income type of the report."""
    if not income_type_contains:
        return True

    the_income_type = str(the_line.get("line_income_type") or "")
    return the_income_type.startswith(income_type_contains)


def get_invalid_certificates() -> list[frappe._dict]:
    """The submitted certificates whose amounts do not agree with their rate.

    A certificate is invalid when it carries no amount, or when the tax of the
    certificate is not the tax of its base amount at its own rate.

    Returns:
        list: the invalid certificates of the withholding tax.
    """
    if not frappe.has_permission(CERTIFICATE_DOCTYPE, "read"):
        frappe.throw(
            frappe._("Not permitted to read the {0} records").format(CERTIFICATE_DOCTYPE),
            frappe.PermissionError,
        )

    the_certificates = frappe.get_all(
        CERTIFICATE_DOCTYPE,
        filters={"docstatus": 1},
        fields=[
            "name",
            "certificate_number",
            "company",
            "tax_base_amount",
            "wht_amount",
            "wht_rate",
        ],
        limit_page_length=0,
    )

    the_invalid = []
    for the_certificate in the_certificates:
        the_gross = flt(the_certificate.tax_base_amount)
        the_tax = flt(the_certificate.wht_amount)
        the_rate = flt(the_certificate.wht_rate)

        if the_tax <= 0 or the_gross <= 0:
            the_invalid.append(the_certificate)
            continue

        if abs(the_tax - (the_gross * the_rate / 100)) > 0.01:
            the_invalid.append(the_certificate)

    return the_invalid


def _line_of_certificate(
    the_certificate: frappe._dict, the_income: frappe._dict | None
) -> frappe._dict:
    """One row of a report, of a certificate and of one of its incomes."""
    return frappe._dict(
        {
            "certificate": the_certificate.name,
            "certificate_number": the_certificate.certificate_number,
            "certificate_date": the_certificate.certificate_date,
            "payment_date": the_certificate.payment_date,
            "company": the_certificate.company,
            "supplier": the_certificate.supplier,
            "supplier_name": the_certificate.supplier_name,
            "supplier_tax_id": the_certificate.supplier_tax_id,
            "supplier_address": the_certificate.supplier_address,
            "supplier_branch_code": the_certificate.supplier_branch_code,
            "supplier_branch_name": the_certificate.supplier_branch_name,
            "supplier_type_classification": the_certificate.supplier_type_classification,
            "pnd_form_type": the_certificate.pnd_form_type,
            "income_type": the_certificate.income_type,
            "income_description": the_certificate.income_description,
            "wht_rate": the_certificate.wht_rate,
            "wht_condition": the_certificate.wht_condition,
            "tax_base_amount": the_certificate.tax_base_amount,
            "wht_amount": the_certificate.wht_amount,
            "net_payment_amount": the_certificate.net_payment_amount,
            "total_payment_amount": the_certificate.total_payment_amount,
            "tax_year": the_certificate.tax_year,
            "tax_month": the_certificate.tax_month,
            "status": the_certificate.status,
            "payment_entry": the_certificate.payment_entry,
            "purchase_invoice": the_certificate.purchase_invoice,
            "line_income_type": (
                the_income.income_type if the_income else the_certificate.income_type
            ),
            "line_income_description": (
                the_income.income_type_description
                if the_income
                else (the_certificate.income_description or "")
            ),
            "line_tax_rate": the_income.tax_rate if the_income else the_certificate.wht_rate,
            "line_gross_amount": (
                the_income.gross_amount if the_income else the_certificate.tax_base_amount
            ),
            "line_tax_amount": (
                the_income.tax_amount if the_income else the_certificate.wht_amount
            ),
            "line_net_amount": (
                the_income.net_amount if the_income else the_certificate.net_payment_amount
            ),
            "income_code": (
                get_income_code(the_income.income_type)
                if the_income
                else find_income_code(the_certificate.income_type)
            ),
        }
    )
