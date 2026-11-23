"""The transactions of the withholding tax of the site.

The certificate of the withholding tax of Thailand is `Withholding Tax
Certificate` and the incomes of a certificate are its child rows `Withholding
Tax Item`.  Both are owned by Print Designer, so the reading of the
transactions belongs here as well; the Thai Business Suite reads them through
this module.
"""

from __future__ import annotations

from typing import Any

import frappe

CERTIFICATE_DOCTYPE = "Withholding Tax Certificate"
ITEM_DOCTYPE = "Withholding Tax Item"

THE_LIMIT = 100


def get_the_certificates_of_the_site() -> list[Any]:
    """Read the incomes of the certificates of the withholding tax of the site.

    A certificate carries the party whose income was withheld as its
    supplier, and every income of the certificate carries the gross amount of
    the income, its rate and its tax.  One row is returned for every income
    of every submitted certificate.

    The older query cut the joined rows of the certificate at a hundred, so
    the answer carries at most a hundred transactions of a certificate, and
    the rows are cut here in the same way.

    Returns:
        list: the incomes of the certificates of the site, one row for every
        income, with the name of the certificate, the name of the party, the
        date of the certificate, the rate, the tax and the gross amount.
    """
    the_certificates = frappe.get_list(
        CERTIFICATE_DOCTYPE,
        filters={"docstatus": 1},
        fields=["name", "supplier_name", "certificate_date", "payment_date"],
        order_by="certificate_date desc",
        limit=THE_LIMIT,
    )

    the_names = [the_certificate.name for the_certificate in the_certificates]

    if not the_names:
        return []

    the_incomes = frappe.get_all(
        ITEM_DOCTYPE,
        filters={"parent": ["in", the_names]},
        fields=["parent", "tax_rate", "tax_amount", "gross_amount"],
        limit_page_length=0,
    )

    the_incomes_of: dict[str, list[Any]] = {}
    for the_income in the_incomes:
        the_incomes_of.setdefault(the_income.parent, []).append(the_income)

    the_rows = []
    for the_certificate in the_certificates:
        the_date = the_certificate.certificate_date or the_certificate.payment_date
        for the_income in the_incomes_of.get(the_certificate.name, []):
            the_rows.append(
                frappe._dict(
                    {
                        "name": the_certificate.name,
                        "supplier": the_certificate.supplier_name,
                        "posting_date": the_date,
                        "rate": the_income.tax_rate,
                        "tax_amount": the_income.tax_amount,
                        "total_amount": the_income.gross_amount,
                    }
                )
            )

    return the_rows[:THE_LIMIT]
