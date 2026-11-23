"""The calculator of the Thai withholding tax.

This module holds the behaviour of the tax calculator of Thai Business Suite
(`thai_business_suite/thai_tax/utils/tax_calculator.py`).  Print Designer
holds the behaviour, so that the tax of Thailand works on a site where Thai
Business Suite is not installed.  The old path of Thai Business Suite is a
shim without behaviour of its own.

The functions here are the ones that read the withholding tax of a party and
the rate of an income type:

- the rate of an income type, from the `Thai WHT Rate Setting` and, when the
  site carries no rate for it, from the rates of the law of Thailand;
- the amount of the withholding tax of an amount;
- the form of the withholding tax (PND1, PND3, PND53) of an income type;
- the settings of the withholding tax of a party;
- the check of the tax identification number of Thailand;
- the check of the consistency of the withholding tax of a document;
- the address of a party, for the certificate of the withholding tax.

The certificate of the withholding tax of a payment entry is created here
with the certificate of Print Designer, the `Withholding Tax Certificate`.
The income type of the certificate is the income type of the site, the
`Thai WHT Income Type`, which works together with the `Tax Withholding
Category` of ERPNext; see `print_designer.custom.wht_canonical_mapping`.
The certificate is the certificate of an outgoing withholding: the incoming
withholding of Thailand is the `Receive WHT Register`.
"""

from typing import Any, cast

import frappe
from frappe.utils import flt, getdate, today

from print_designer.custom.wht_certificate_creator import (
    create_certificate_for_payment_entry,
    entity_type_of_group,
)

# The rates of the withholding tax of the law of Thailand, by the name of
# the income type.  They are the fallback of the rate of the `Thai WHT Rate
# Setting`, which the site may carry.
WHT_RATES = {
    "40(1) เงินเดือน ค่าจ้าง": 5.0,
    "40(2) ค่านายหน้า ค่าคอมมิชชั่น": 3.0,
    "40(3) ค่าลิขสิทธิ์": 5.0,
    "40(4)ก ดอกเบี้ย": 15.0,
    "40(4)ข เงินปันผล": 10.0,
    "40(5) ค่าเช่า": 5.0,
    "40(6) รางวัล ส่วนลด": 5.0,
    "40(7) ค่าจ้างทำของ": 3.0,
    "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ": 3.0,
    "40(8) ค่าบริการนิติบุคคล 3%": 3.0,
    "40(8) ค่าบริการนิติบุคคล 5%": 5.0,
    "40(8) ค่าขนส่ง 1%": 1.0,
    "40(8) ค่าเบี้ยประกัน 1%": 1.0,
    "40(8) ค่าโฆษณา 2%": 2.0,
}

# The income types of the individuals (form 1) and of the services (form 3).
PND1_TYPES = ("40(1) เงินเดือน ค่าจ้าง",)

PND3_TYPES = (
    "40(2) ค่านายหน้า ค่าคอมมิชชั่น",
    "40(3) ค่าลิขสิทธิ์",
    "40(4)ก ดอกเบี้ย",
    "40(4)ข เงินปันผล",
    "40(5) ค่าเช่า",
    "40(6) รางวัล ส่วนลด",
    "40(7) ค่าจ้างทำของ",
    "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ",
)

# The income types of the companies (form 53).
PND53_TYPES = (
    "40(8) ค่าบริการนิติบุคคล 3%",
    "40(8) ค่าบริการนิติบุคคล 5%",
    "40(8) ค่าขนส่ง 1%",
    "40(8) ค่าเบี้ยประกัน 1%",
    "40(8) ค่าโฆษณา 2%",
)


def get_withholding_tax_rate(income_type: str | None) -> float:
    """The rate of the withholding tax of an income type.

    The rate of the `Thai WHT Rate Setting` of the income type is the rate of
    the site, and the rates of the law of Thailand are the fallback of a site
    that carries no rate for it.
    """
    if not income_type:
        return 0.0

    rate_setting = frappe.db.get_value(
        "Thai WHT Rate Setting",
        {"income_type": income_type},
        "tax_rate",
    )

    if rate_setting:
        return flt(cast(Any, rate_setting))

    return flt(WHT_RATES.get(income_type, 0.0))


def calculate_withholding_tax(
    amount: float | None,
    income_type: str | None,
    custom_rate: float | None = None,
) -> float:
    """The amount of the withholding tax of an amount."""
    if not amount or flt(amount) <= 0:
        return 0.0

    tax_rate = flt(custom_rate) if custom_rate else get_withholding_tax_rate(income_type)
    if not tax_rate:
        return 0.0

    return flt(flt(amount) * tax_rate / 100, 2)


def get_pnd_type_from_income_type(income_type: str | None) -> str | None:
    """The form of the withholding tax of an income type."""
    if not income_type:
        return None

    if income_type in PND1_TYPES:
        return "PND1"

    if income_type in PND3_TYPES:
        return "PND3"

    if income_type in PND53_TYPES:
        return "PND53"

    return None


def validate_thai_tax_data(doc: Any, method: str | None = None) -> bool:
    """The check of the consistency of the tax of Thailand of a document."""
    errors: list[str] = []

    tax_id = doc.get("tax_id")
    if tax_id and not validate_thai_tax_id(tax_id):
        errors.append(frappe._("Invalid Tax ID format: {0}").format(tax_id))

    if doc.get("apply_wht"):
        wht_rate = doc.get("wht_rate") or doc.get("withholding_tax_rate")
        expected_tax = calculate_withholding_tax(
            doc.get("paid_amount", 0),
            doc.get("income_type"),
            wht_rate,
        )

        actual_tax = flt(doc.get("wht_amount", 0) or doc.get("withholding_tax_amount", 0))
        if abs(expected_tax - actual_tax) > 0.01:
            errors.append(
                frappe._("Withholding tax amount mismatch. Expected: {0}, Actual: {1}").format(
                    expected_tax, actual_tax
                )
            )

    if errors:
        frappe.throw("<br>".join(errors), title=frappe._("Thai Tax Validation Failed"))

    return True


def validate_thai_tax_id(tax_id: str | None) -> bool:
    """The check of the tax identification number of Thailand.

    The number has thirteen digits and the thirteenth is the check digit of
    the twelve first ones.
    """
    if not tax_id or len(tax_id) != 13:
        return False

    if not tax_id.isdigit():
        return False

    sum_value = 0
    for index in range(12):
        sum_value += int(tax_id[index]) * (13 - index)

    check_digit = (11 - (sum_value % 11)) % 10

    return check_digit == int(tax_id[12])


def get_wht_rate_from_setting(
    income_type: str | None,
    entity_type: str | None,
    company: str | None,
    posting_date: str | None = None,
) -> float:
    """The rate of the withholding tax of an income type and of a kind of party.

    The rate of the `Thai WHT Rate Setting` that is active on the date of the
    posting is the rate of the site, and the rates of the law of Thailand are
    the fallback of a site that carries no rate for it.
    """
    if not income_type:
        return 0.0

    posting_date = posting_date or today()

    rate_settings = frappe.get_all(
        "Thai WHT Rate Setting",
        filters={
            "income_type": income_type,
            "is_active": 1,
            "entity_type": ["in", [entity_type, "All"]],
        },
        fields=[
            "name",
            "individual_rate",
            "company_rate",
            "government_rate",
            "tax_rate",
            "effective_from",
            "effective_to",
        ],
    )

    for setting in rate_settings:
        from_date = setting.get("effective_from")
        to_date = setting.get("effective_to")
        posting_day = getdate(posting_date)
        start_day = getdate(from_date)
        end_day = getdate(to_date)
        if start_day and posting_day and posting_day < start_day:
            continue
        if end_day and posting_day and posting_day > end_day:
            continue

        rate = _the_rate_of_the_setting(setting, entity_type)
        if rate:
            return flt(rate)

    return flt(WHT_RATES.get(income_type, 0.0))


def get_wht_settings_for_party(
    party_type: str | None,
    party: str | None,
    company: str | None,
) -> dict[str, Any]:
    """The settings of the withholding tax of a party."""
    result: dict[str, Any] = {
        "income_type": None,
        "tax_withholding_category": None,
        "entity_type": "Company",
        "wht_rate": 0.0,
    }

    if not party:
        return result

    if party_type == "Supplier":
        supplier = frappe.get_doc("Supplier", party)
        result["tax_withholding_category"] = supplier.get("tax_withholding_category")
        result["income_type"] = supplier.get("dgs_custom_wht_income_type")

        supplier_group = supplier.get("supplier_group")
        if supplier_group:
            result["entity_type"] = _entity_type_of_the_group(cast(Any, supplier_group))
        else:
            result["entity_type"] = "Company"

    elif party_type == "Customer":
        customer = frappe.get_doc("Customer", party)
        result["tax_withholding_category"] = customer.get("tax_withholding_category")
        result["entity_type"] = "Company"

    result["wht_rate"] = get_wht_rate_from_setting(
        cast(Any, result["income_type"]),
        cast(Any, result["entity_type"]),
        company,
        today(),
    )

    return result


def get_thai_tax_settings() -> Any:
    """The settings of the tax of Thailand of the site."""
    return frappe.get_single("Thai Tax Settings")


def create_withholding_tax_certificate(payment_entry: Any) -> Any:
    """The certificate of the withholding tax of a payment entry.

    Every row of the withholding tax of the payment entry becomes a row of the
    income items of the certificate.
    """
    return create_certificate_for_payment_entry(payment_entry)


def get_party_address(party_type: str | None, party: str | None) -> str:
    """The address of a party, as text."""
    if not party:
        return ""

    address_field = None
    if party_type == "Customer":
        address_field = frappe.db.get_value("Customer", party, "customer_primary_address")
        if not address_field:
            address_field = frappe.db.get_value("Customer", party, "primary_address")
    elif party_type == "Supplier":
        address_field = frappe.db.get_value("Supplier", party, "supplier_primary_address")

    if address_field:
        address_lines = []
        for field in ("address_line1", "address_line2", "city", "pincode", "country"):
            value = frappe.db.get_value("Address", address_field, field)
            if value:
                address_lines.append(value)
        if address_lines:
            return ", ".join(address_lines)

    return ""


def _the_rate_of_the_setting(setting: Any, entity_type: str | None) -> float:
    """The rate of a row of the `Thai WHT Rate Setting` for a kind of party.

    The rate of the individual is the rate of an individual, the rate of the
    government is the rate of the government, and the rate of the company is
    the rate of a company.  The general rate of the row is the rate of a row
    that carries none of them.
    """
    if entity_type == "Individual" and setting.get("individual_rate"):
        return flt(cast(Any, setting["individual_rate"]))

    if entity_type == "Government" and setting.get("government_rate"):
        return flt(cast(Any, setting["government_rate"]))

    if entity_type in ("Company", "Government") and setting.get("company_rate"):
        return flt(cast(Any, setting["company_rate"]))

    if setting.get("tax_rate"):
        return flt(cast(Any, setting["tax_rate"]))

    return 0.0


def _entity_type_of_the_group(group: str | None) -> str:
    """The kind of party of a group of a supplier.

    A group that carries the name of the government or of an individual is
    the group of that kind of party.
    """
    return entity_type_of_group(group)
