"""Print Designer owned helpers for the Thai withholding tax certificate form 50 ทวิ.

The statutory form itself is rendered by client specific print formats (for
example ``DGS Form 50 Tawi``).  Every reusable mapping rule - statutory row
selection, totals, amount in words and the checkbox derivation - lives here so
that a print format only binds presentation values and never repeats tax logic.
"""

import re
from typing import Any

import frappe
from frappe.utils import flt, getdate

from print_designer.utils.thai_amount_to_word import thai_money_in_words

FORM_50_TAWI_FORMAT_NAME = "DGS Form 50 Tawi"
"""Exact print format name that belongs to the client specific DGS form.

Every other print format is handled by the Print Designer path.
"""

FORM_50_TAWI_WRAPPER_CLASS = "dgs-form-50-tawi"
"""Marker class the form puts on its wrapper so its own CSS can be scoped."""

STATUTORY_ROW_KEYS = ("1", "2", "3", "4a", "4b", "5", "6")
"""The labeled rows of form 50 ทวิ (row 4 is split into 4a and 4b)."""

STATUTORY_ROW_LABELS = {
    "1": "เงินเดือน ค่าจ้าง เบี้ยเลี้ยง โบนัส ฯลฯ ตามมาตรา 40 (1)",
    "2": "ค่าธรรมเนียม ค่านายหน้า ฯลฯ ตามมาตรา 40 (2)",
    "3": "ค่าแห่งลิขสิทธิ์ ฯลฯ ตามมาตรา 40 (3)",
    "4a": "ดอกเบี้ย ฯลฯ ตามมาตรา 40 (4) (ก)",
    "4b": "เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ ตามมาตรา 40 (4) (ข)",
    "5": "การจ่ายเงินได้ที่ต้องหักภาษี ณ ที่จ่ายตามคำสั่งกรมสรรพากรที่ออกตามมาตรา 3 เตรส",
    "6": "อื่น ๆ (ระบุ)",
}

PND_FORM_CHECKBOX = {
    "PND1 Form": "1",
    "PND3 Form": "4",
    "PND53 Form": "7",
}
"""Printed form that matches each PND filing type of the certificate."""

CLASSIFICATION_CHECKBOX = {
    "Individual - Staff (PND.1)": "1",
    "Individual - Non-staff (PND.3)": "4",
    "Company/Juristic Person (PND.53)": "7",
}
"""Fallback classification of the certificate when no PND form type is stored."""

WHT_CONDITION_CHECKBOX = {
    "1. หัก ณ ที่จ่าย (Withhold at Source)": "1",
    "2. ออกให้ตลอดไป (Permanent)": "2",
    "3. ออกให้ครั้งเดียว (One Time)": "3",
    "4. อื่นๆ (Others)": "4",
}
"""Withholding method of the certificate mapped to the payer checkboxes."""

THAI_MONTHS = (
    "มกราคม",
    "กุมภาพันธ์",
    "มีนาคม",
    "เมษายน",
    "พฤษภาคม",
    "มิถุนายน",
    "กรกฎาคม",
    "สิงหาคม",
    "กันยายน",
    "ตุลาคม",
    "พฤศจิกายน",
    "ธันวาคม",
)

_SECTION_4A = re.compile(r"40\s*\(4\)\s*\(?\s*ก")
_SECTION_4B = re.compile(r"40\s*\(4\)\s*\(?\s*ข")
_SECTION = re.compile(r"40\s*\(\s*(\d)\s*\)")
_CATEGORY_PREFIX = re.compile(r"^\s*(\d{1,2})\s*\.")
_TAX_ID_SEPARATORS = re.compile(r"[\s\-]")


def is_dgs_form_50_tawi(print_format_name: str | None = None) -> bool:
    """Return True only for the print format named exactly ``DGS Form 50 Tawi``."""
    return (print_format_name or "") == FORM_50_TAWI_FORMAT_NAME


def get_form_50_tawi_wrapper_class(print_format_name: str | None = None) -> str:
    """Marker class a form puts on its wrapper so its CSS can be scoped to it.

    Only the DGS form owns a marker today.  Other forms/reports may declare
    their own unique marker (class or id) in their own template.
    """
    if is_dgs_form_50_tawi(print_format_name):
        return FORM_50_TAWI_WRAPPER_CLASS
    return ""


def map_income_type_to_row(income_type: str | None = None) -> str:
    """Map a certificate income type onto the statutory row of form 50 ทวิ.

    The statutory section decides the row when it is known.  The numbered
    income categories of the certificate (1 - 12) are used otherwise.
    """
    text = (income_type or "").strip()
    if not text:
        return "6"

    if _SECTION_4A.search(text):
        return "4a"
    if _SECTION_4B.search(text):
        return "4b"

    section = _SECTION.search(text)
    if section:
        number = section.group(1)
        if number in {"1", "2", "3"}:
            return number
        if number in {"5", "6", "7", "8"}:
            return "5"

    prefix = _CATEGORY_PREFIX.match(text)
    if prefix:
        category = int(prefix.group(1))
        if 1 <= category <= 3:
            return str(category)
        if 4 <= category <= 11:
            return "5"
        return "6"

    return "6"


def clean_tax_id(tax_id: str | None = None) -> str:
    """Normalize a tax id for the 13 digit boxes and keep leading zeros."""
    return _TAX_ID_SEPARATORS.sub("", tax_id or "")


def tax_id_for_boxes(tax_id: str | None = None) -> str:
    """Return the tax id only when it is a complete 13 digit id.

    The statutory form prints the tax id in thirteen single character boxes.
    An incomplete id must stay blank instead of being printed partially.
    """
    cleaned = clean_tax_id(tax_id)
    return cleaned if len(cleaned) == 13 else ""


def format_branch_text(branch_code: str | None = None) -> str:
    """Return the printed branch caption of a branch code."""
    code = (branch_code or "").strip()
    if not code:
        return ""
    if code == "00000":
        return "(สำนักงานใหญ่)"
    number = code.lstrip("0")
    if not number:
        return ""
    return "(สาขาที่ " + number + ")"


def format_payment_date(value: Any = None) -> str:
    """Format a payment date as ``dd/mm/พ.ศ.``."""
    if not value:
        return ""
    date = getdate(value)
    if not date:
        return ""
    return f"{date.day:02d}/{date.month:02d}/{date.year + 543}"


def _format_amount(value: Any = None) -> str:
    """Format an amount for the printed form."""
    return f"{flt(value):,.2f}"


def _empty_row(key: str) -> dict[str, Any]:
    return {
        "key": key,
        "label": STATUTORY_ROW_LABELS.get(key, ""),
        "date": "",
        "amount": 0.0,
        "amount_text": "0.00",
        "tax": 0.0,
        "tax_text": "0.00",
        "description": "",
        "income_type": "",
        "filled": False,
    }


def _get_company_address(company: str | None = None) -> str:
    if not company:
        return ""
    addresses = frappe.get_all(
        "Address",
        filters={
            "is_your_company_address": 1,
            "is_primary_address": 1,
            "link_doctype": "Company",
            "link_name": company,
        },
        fields=["address_line1", "address_line2", "city", "state"],
        limit=1,
    )
    if not addresses:
        return ""
    return _address_text(addresses[0])


def _address_text(address: Any) -> str:
    parts = []
    for field in ("address_line1", "address_line2", "city", "state"):
        value = (address.get(field) or "").strip()
        if value:
            parts.append(value)
    return " ".join(parts)


def _address_by_name(name: str | None = None) -> str:
    if not name:
        return ""
    addresses = frappe.get_all(
        "Address",
        filters={"name": name},
        fields=["address_line1", "address_line2", "city", "state"],
        limit=1,
    )
    if not addresses:
        return ""
    return _address_text(addresses[0])


def _get_supplier_address(doc: Any) -> str:
    """Resolve the payee address of the certificate.

    The certificate keeps the issued snapshot.  When the snapshot names an
    address record, the record is printed.  Otherwise the primary address of
    the linked supplier is used, the supplier link first and the display name
    only as a legacy fallback.
    """
    snapshot = (doc.get("supplier_address") or "").strip()
    if snapshot:
        resolved = _address_by_name(snapshot)
        return resolved or snapshot

    for link_name in (doc.get("supplier"), doc.get("supplier_name")):
        if not link_name:
            continue
        addresses = frappe.get_all(
            "Address",
            filters={
                "link_doctype": "Supplier",
                "link_name": link_name,
                "is_primary_address": 1,
            },
            fields=["address_line1", "address_line2", "city", "state"],
            limit=1,
        )
        if addresses:
            return _address_text(addresses[0])

    return ""


def _get_pnd_checkbox(doc: Any) -> str:
    pnd_form_type = (doc.get("pnd_form_type") or "").strip()
    if pnd_form_type in PND_FORM_CHECKBOX:
        return PND_FORM_CHECKBOX[pnd_form_type]

    classification = (doc.get("supplier_type_classification") or "").strip()
    return CLASSIFICATION_CHECKBOX.get(classification, "")


def _get_wht_condition_checkbox(doc: Any) -> str:
    condition = (doc.get("wht_condition") or "").strip()
    if condition in WHT_CONDITION_CHECKBOX:
        return WHT_CONDITION_CHECKBOX[condition]

    match = re.match(r"^\s*(\d)", condition)
    return match.group(1) if match else ""


def _build_rows(doc: Any, items: list[Any]) -> dict[str, dict[str, Any]]:
    rows = {key: _empty_row(key) for key in STATUTORY_ROW_KEYS}

    if items:
        for item in items:
            key = map_income_type_to_row(item.get("income_type"))
            row = rows[key]
            row["amount"] = flt(row["amount"]) + flt(item.get("gross_amount"))
            row["tax"] = flt(row["tax"]) + flt(item.get("tax_amount"))
            row["amount_text"] = _format_amount(row["amount"])
            row["tax_text"] = _format_amount(row["tax"])
            row["date"] = format_payment_date(item.get("payment_date") or doc.get("payment_date"))
            row["income_type"] = item.get("income_type") or ""
            row["description"] = item.get("income_type_description") or row["description"]
            row["filled"] = True
        return rows

    key = map_income_type_to_row(doc.get("income_type"))
    row = rows[key]
    row["amount"] = flt(doc.get("tax_base_amount"))
    row["tax"] = flt(doc.get("wht_amount"))
    row["amount_text"] = _format_amount(row["amount"])
    row["tax_text"] = _format_amount(row["tax"])
    row["date"] = format_payment_date(doc.get("payment_date"))
    row["income_type"] = doc.get("income_type") or ""
    row["description"] = doc.get("income_description") or ""
    row["filled"] = bool(row["income_type"] or row["amount"] or row["tax"])
    return rows


def build_form_50_tawi_data(doc: Any) -> dict[str, Any]:
    """Build the view model of form 50 ทวิ from a withholding tax certificate.

    The certificate is the single source of truth.  Amounts are never
    recalculated from a rate, they are read from the certificate.
    """
    items = list(doc.get("income_items") or [])
    rows = _build_rows(doc, items)

    sum_amount = sum(flt(row["amount"]) for row in rows.values())
    sum_tax = sum(flt(row["tax"]) for row in rows.values())

    recorded_amount = flt(doc.get("tax_base_amount"))
    recorded_tax = flt(doc.get("wht_amount"))

    total_amount = recorded_amount or sum_amount
    total_tax = recorded_tax or sum_tax

    certificate_date = doc.get("certificate_date")
    if certificate_date:
        certificate_date = getdate(certificate_date)

    return {
        "certificate_number": doc.get("certificate_number") or "",
        "certificate_date": format_payment_date(certificate_date),
        "signature_day": f"{certificate_date.day:02d}" if certificate_date else "",
        "signature_month": THAI_MONTHS[certificate_date.month - 1] if certificate_date else "",
        "signature_year": str(certificate_date.year + 543) if certificate_date else "",
        "tax_month": doc.get("tax_month") or "",
        "tax_year": doc.get("tax_year") or "",
        "company": doc.get("company") or "",
        "company_branch": doc.get("company_branch") or "",
        "company_branch_text": format_branch_text(doc.get("company_branch")),
        "company_tax_id": tax_id_for_boxes(
            frappe.get_cached_value("Company", doc.get("company"), "tax_id")
            if doc.get("company")
            else ""
        ),
        "company_address": _get_company_address(doc.get("company")),
        "supplier": doc.get("supplier") or "",
        "supplier_name": doc.get("supplier_name") or "",
        "supplier_tax_id": tax_id_for_boxes(doc.get("supplier_tax_id")),
        "supplier_branch_code": doc.get("supplier_branch_code") or "",
        "supplier_branch_text": format_branch_text(doc.get("supplier_branch_code")),
        "supplier_address": _get_supplier_address(doc),
        "income_type": doc.get("income_type") or "",
        "income_description": doc.get("income_description") or "",
        "wht_rate": flt(doc.get("wht_rate")),
        "wht_condition": doc.get("wht_condition") or "",
        "supplier_type_classification": doc.get("supplier_type_classification") or "",
        "pnd_form_type": doc.get("pnd_form_type") or "",
        "pnd_checkbox": _get_pnd_checkbox(doc),
        "wht_condition_checkbox": _get_wht_condition_checkbox(doc),
        "rows": rows,
        "row_order": list(STATUTORY_ROW_KEYS),
        "has_income_items": bool(items),
        "total_amount": total_amount,
        "total_tax": total_tax,
        "total_amount_text": _format_amount(total_amount),
        "total_tax_text": _format_amount(total_tax),
        "total_amount_words": thai_money_in_words(total_amount),
        "total_tax_words": thai_money_in_words(total_tax),
        "sum_amount": sum_amount,
        "sum_tax": sum_tax,
        "totals_match": (
            round(flt(sum_amount), 2) == round(flt(recorded_amount), 2)
            and round(flt(sum_tax), 2) == round(flt(recorded_tax), 2)
        )
        if items
        else True,
    }


def get_form_50_tawi_data(doc: Any) -> dict[str, Any]:
    """Jinja entry point of the form 50 ทวิ view model."""
    return build_form_50_tawi_data(doc)
