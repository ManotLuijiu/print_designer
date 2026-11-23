"""The mapping of a Thai income type to the canonical withholding certificate.

The source of truth of the income type of the withholding tax of Thailand is
the ``Thai WHT Income Type`` DocType of Print Designer.  It works together
with the ``Tax Withholding Category`` of ERPNext:

``Tax Withholding Category``
    The category of a transaction (an item, a document).  It carries the
    link ``pd_custom_thai_wht_income_type`` to the income type.

``Thai WHT Income Type``
    The income type itself.  It carries the form of the tax (``PND3``,
    ``PND53``, ``PND54``), the kind of the recipient (``Individual``,
    ``Corporation``, ...), the rate and the description of the income.

The certificate of the withholding tax of Print Designer
(``Withholding Tax Certificate``) stores the income type as a *strict* value:
the income type of the certificate and the income type of a row of the
certificate are ``Select`` fields with an exact list of the statutory values
of Thailand.  The mapping below turns the income type of the site into those
exact values.

The mapping is explicit on purpose.  The values of the certificate are the
values of the Revenue Department; they are never derived from a name of the
site.  Every entry of the table names the statutory line it stands for:

``PND3`` (an individual)
    The income type of the row is the statutory section of the income
    (``40(7)``, ``40(8)``, ...).  The certificate carries the line of the
    income type of the form of the individual.

``PND53`` (a juristic person)
    The income type of the row is the statutory section of the income
    (``40(3)``, ``40(4)(ก)``, ...).  The certificate carries the numbered
    line of the form of the juristic person (``5.``, ``8.``, ``9.``, ...).

``PND54`` (a recipient outside Thailand)
    The withholding of a payment to a recipient outside Thailand.  The
    certificate carries the line of the service.

The rule of the choice of the line of the certificate is: the line of the
statutory section of the income type is used when the certificate offers one
with the same rate, otherwise the line of the same statutory section is used.
"""

from typing import Any

import frappe
from frappe.utils import flt, getdate

#: The income type of the certificate (``Withholding Tax Certificate``).
CERTIFICATE_INCOME_TYPE = "Withholding Tax Certificate"

#: The income type of a row of the certificate (``Withholding Tax Item``).
CERTIFICATE_ITEM_INCOME_TYPE = "Withholding Tax Item"

#: The master of the income types.
INCOME_TYPE_DOCTYPE = "Thai WHT Income Type"

#: The category of ERPNext that carries the link to the income type.
CATEGORY_DOCTYPE = "Tax Withholding Category"

#: The link of the category to the income type.
CATEGORY_LINK_FIELD = "pd_custom_thai_wht_income_type"

#: The withholding condition of an ordinary withholding.
WHT_CONDITION = "1. หัก ณ ที่จ่าย (Withhold at Source)"

#: The classification of an employee of the company.
CLASSIFICATION_STAFF = "Individual - Staff (PND.1)"

#: The classification of an individual that is not an employee.
CLASSIFICATION_NON_STAFF = "Individual - Non-staff (PND.3)"

#: The classification of a juristic person.
CLASSIFICATION_COMPANY = "Company/Juristic Person (PND.53)"

#: The months of the tax period of the certificate, by the number of the month.
TAX_MONTHS = {
    1: "01 - มกราคม (January)",
    2: "02 - กุมภาพันธ์ (February)",
    3: "03 - มีนาคม (March)",
    4: "04 - เมษายน (April)",
    5: "05 - พฤษภาคม (May)",
    6: "06 - มิถุนายน (June)",
    7: "07 - กรกฎาคม (July)",
    8: "08 - สิงหาคม (August)",
    9: "09 - กันยายน (September)",
    10: "10 - ตุลาคม (October)",
    11: "11 - พฤศจิกายน (November)",
    12: "12 - ธันวาคม (December)",
}

#: The DocType of the form of the tax, by the form type of the income type.
PND_FORM_DOCTYPES = {
    "PND1": "PND1 Form",
    "PND3": "PND3 Form",
    "PND53": "PND53 Form",
    "PND54": "PND54 Form",
}

#: The income type of the certificate and of a row of the certificate, by the
#: income category of the income type, the form type and the kind of the
#: recipient.
#:
#: The key is ``(income_category, form_type, recipient_type)``.
CERTIFICATE_INCOME_TYPES: dict[tuple[str, str, str], tuple[str, str]] = {
    # PND3 - an individual
    ("Advertising Income", "PND3", "Individual"): (
        "8. ค่าโฆษณา - Advertising",
        "40(8) ค่าโฆษณา 2%",
    ),
    ("Entertainment Income", "PND3", "Individual"): (
        "40 (8) ค่าแสดงให้แก่นักแสดงสาธารณะ - ในประเทศ (5%)",
        "40(6) รางวัล ส่วนลด",
    ),
    ("Prize & Awards", "PND3", "Individual"): (
        "40 (8) รางวัลจากการอื่นใดมี่มีลักษณะชิงโชค (5%)",
        "40(6) รางวัล ส่วนลด",
    ),
    ("Professional Services", "PND3", "Individual"): (
        "40 (8) ค่าจ้างทำของ(อื่นๆ) (3%)",
        "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ",
    ),
    ("Rental Income", "PND3", "Individual"): (
        "9. ค่าเช่า - Rent",
        "40(5) ค่าเช่า",
    ),
    ("Rental Income (Ship Lease)", "PND3", "Individual"): (
        "40 (5) ค่าเช่าเรือ ตามกฎหมายว่าด้วยการส่งเสริมพาณิชย์นาวีที่ใช้ในการขนส่งสินค้าระหว่างประเทศ (1%)",
        "40(5) ค่าเช่า",
    ),
    ("Sales Promotion Income", "PND3", "Individual"): (
        "40 (8) รางวัล ส่วนลด หรือประโยชน์ใด ๆ เนื่องจากการส่งเสริมการขาย (3%)",
        "40(6) รางวัล ส่วนลด",
    ),
    ("Service Fees", "PND3", "Individual"): (
        "40 (8) ค่าจ้างทำของ(อื่นๆ) (3%)",
        "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ",
    ),
    ("Services Income", "PND3", "Individual"): (
        "40 (7) ค่าจ้างทำของ(รับเหมา) (3%)",
        "40(7) ค่าจ้างทำของ",
    ),
    ("Transport Fees", "PND3", "Individual"): (
        "10. ค่าขนส่ง - Transportation",
        "40(8) ค่าขนส่ง 1%",
    ),
    # PND53 - a juristic person
    ("Advertising Income", "PND53", "Corporation"): (
        "8. ค่าโฆษณา - Advertising",
        "40(8) ค่าโฆษณา 2%",
    ),
    ("Agricultural Trading Income", "PND53", "Corporation"): (
        "40 (8) ซื้อยางแผ่น มันสำปะหลัง ปอ ข้าว ข้าวโพด อ้อย เมล็ดกาแฟ ผลปาล์มน้ำมัน - บริษัท (0.75%)",
        "40(8) ค่าบริการนิติบุคคล 3%",
    ),
    ("Bond Interest", "PND53", "Corporation"): (
        "40 (4)(ก) ดอกเบี้ย - บริษัท (1%)",
        "40(4)ก ดอกเบี้ย",
    ),
    ("Commission & Royalties", "PND53", "Corporation"): (
        "40 (3) ค่าแห่งกู้ดวิลล์ ค่าแห่งลิขสิทธิ์ หรือสิทธิอย่างอื่น - บริษัท (3%)",
        "40(2) ค่านายหน้า ค่าคอมมิชชั่น",
    ),
    ("Contracting Services", "PND53", "Corporation"): (
        "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service",
        "40(8) ค่าบริการนิติบุคคล 3%",
    ),
    ("Dividend Income", "PND53", "Corporation"): (
        "40 (4)(ข) เงินปันผล - บริษัทต่างประเทศ ประกอบการในไทย (10%)",
        "40(4)ข เงินปันผล",
    ),
    ("Foreign Contractor Fees", "PND53", "Corporation"): (
        "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service",
        "40(8) ค่าบริการนิติบุคคล 5%",
    ),
    ("Insurance Premiums", "PND53", "Corporation"): (
        "11. ค่าประกันภัย - Insurance",
        "40(8) ค่าเบี้ยประกัน 1%",
    ),
    ("Interest Income", "PND53", "Corporation"): (
        "40 (4)(ก) ดอกเบี้ย - บริษัท (1%)",
        "40(4)ก ดอกเบี้ย",
    ),
    ("Prize & Awards", "PND53", "Corporation"): (
        "40 (8) รางวัลจากการอื่นใดมี่มีลักษณะชิงโชค (5%)",
        "40(6) รางวัล ส่วนลด",
    ),
    ("Professional Services", "PND53", "Corporation"): (
        "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service",
        "40(8) ค่าบริการนิติบุคคล 3%",
    ),
    ("Rental Income", "PND53", "Corporation"): (
        "9. ค่าเช่า - Rent",
        "40(5) ค่าเช่า",
    ),
    ("Sales Promotion Income", "PND53", "Corporation"): (
        "40 (8) รางวัล ส่วนลด หรือประโยชน์ใด ๆ เนื่องจากการส่งเสริมการขาย (3%)",
        "40(6) รางวัล ส่วนลด",
    ),
    ("Service Fees", "PND53", "Corporation"): (
        "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service",
        "40(8) ค่าบริการนิติบุคคล 3%",
    ),
    ("Ship Rental", "PND53", "Corporation"): (
        "40 (5) ค่าเช่าเรือ ตามกฎหมายว่าด้วยการส่งเสริมพาณิชย์นาวีที่ใช้ในการขนส่งสินค้าระหว่างประเทศ (1%)",
        "40(5) ค่าเช่า",
    ),
    ("Transport Fees", "PND53", "Corporation"): (
        "10. ค่าขนส่ง - Transportation",
        "40(8) ค่าขนส่ง 1%",
    ),
    # PND53 - a foundation or an association
    ("Commission & Royalties", "PND53", "Foundation/Association"): (
        "40 (3) ค่าแห่งกู้ดวิลล์ ค่าแห่งลิขสิทธิ์ หรือสิทธิอย่างอื่น - สมาคม (10%)",
        "40(2) ค่านายหน้า ค่าคอมมิชชั่น",
    ),
    ("Interest Income", "PND53", "Foundation/Association"): (
        "40 (4)(ก) ดอกเบี้ย - สมาคม (10%)",
        "40(4)ก ดอกเบี้ย",
    ),
    # PND54 - a recipient outside Thailand
    ("Contracting Services (Foreign)", "PND54", "Oversea"): (
        "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service",
        "40(8) ค่าบริการนิติบุคคล 5%",
    ),
    ("Dividend Income (Foreign)", "PND54", "Oversea"): (
        "40 (4)(ข) เงินปันผล - บริษัทต่างประเทศ ประกอบการในไทย (10%)",
        "40(4)ข เงินปันผล",
    ),
    ("Interest Income (Foreign)", "PND54", "Oversea"): (
        "4. (ก) ดอกเบี้ย ฯลฯ 40(4)ก - Interest",
        "40(4)ก ดอกเบี้ย",
    ),
    ("Professional Services (Foreign)", "PND54", "Oversea"): (
        "40 (8) ค่าจ้างทำของ(อื่นๆ) (3%)",
        "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ",
    ),
    ("Royalty (Foreign)", "PND54", "Oversea"): (
        "40 (3) ค่าแห่งกู้ดวิลล์ ค่าแห่งลิขสิทธิ์ หรือสิทธิอย่างอื่น - บริษัท (3%)",
        "40(3) ค่าลิขสิทธิ์",
    ),
}

#: The income type of the certificate and of a row of the certificate, by the
#: statutory section of the income type of the legacy field
#: ``Advance Taxes and Charges.tbs_income_type``.
#:
#: The key is the statutory section, the value is the line of the certificate
#: and the income type of the row.
LEGACY_INCOME_TYPES: dict[str, tuple[str, str]] = {
    "40(1) เงินเดือน ค่าจ้าง": (
        "1. เงินเดือน ค่าจ้าง ฯลฯ 40(1) - Salary",
        "40(1) เงินเดือน ค่าจ้าง",
    ),
    "40(2) ค่านายหน้า ค่าคอมมิชชั่น": (
        "2. ค่าธรรมเนียม ค่านายหน้า ฯลฯ 40(2) - Fee/Commission",
        "40(2) ค่านายหน้า ค่าคอมมิชชั่น",
    ),
    "40(3) ค่าลิขสิทธิ์": (
        "3. ค่าแห่งลิขสิทธิ์ ฯลฯ 40(3) - Royalty",
        "40(3) ค่าลิขสิทธิ์",
    ),
    "40(4)ก ดอกเบี้ย": (
        "4. (ก) ดอกเบี้ย ฯลฯ 40(4)ก - Interest",
        "40(4)ก ดอกเบี้ย",
    ),
    "40(4)ข เงินปันผล": (
        "4. (ข) เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข - Dividend",
        "40(4)ข เงินปันผล",
    ),
    "40(5) ค่าเช่า": (
        "9. ค่าเช่า - Rent",
        "40(5) ค่าเช่า",
    ),
    "40(6) รางวัล ส่วนลด": (
        "40 (8) รางวัล ส่วนลด หรือประโยชน์ใด ๆ เนื่องจากการส่งเสริมการขาย (3%)",
        "40(6) รางวัล ส่วนลด",
    ),
    "40(7) ค่าจ้างทำของ": (
        "40 (7) ค่าจ้างทำของ(รับเหมา) (3%)",
        "40(7) ค่าจ้างทำของ",
    ),
    "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ": (
        "40 (8) ค่าจ้างทำของ(อื่นๆ) (3%)",
        "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ",
    ),
    "40(8) ค่าบริการนิติบุคคล 3%": (
        "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service",
        "40(8) ค่าบริการนิติบุคคล 3%",
    ),
    "40(8) ค่าบริการนิติบุคคล 5%": (
        "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service",
        "40(8) ค่าบริการนิติบุคคล 5%",
    ),
    "40(8) ค่าขนส่ง 1%": (
        "10. ค่าขนส่ง - Transportation",
        "40(8) ค่าขนส่ง 1%",
    ),
    "40(8) ค่าเบี้ยประกัน 1%": (
        "11. ค่าประกันภัย - Insurance",
        "40(8) ค่าเบี้ยประกัน 1%",
    ),
    "40(8) ค่าโฆษณา 2%": (
        "8. ค่าโฆษณา - Advertising",
        "40(8) ค่าโฆษณา 2%",
    ),
}

#: The line of the certificate of a legacy statutory section that depends on
#: the kind of the payee.  A service that is paid to a juristic person is
#: withheld under the line of the service of a company and is reported on the
#: form of a company, while the same service that is paid to an individual
#: uses the line of an individual.
LEGACY_COMPANY_INCOME_TYPES: dict[str, tuple[str, str]] = {
    "40(7) ค่าจ้างทำของ": (
        "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service",
        "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ",
    ),
    "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ": (
        "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service",
        "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ",
    ),
}

#: The form of the tax of a statutory section of the legacy field.
LEGACY_FORM_TYPES = {
    "40(1) เงินเดือน ค่าจ้าง": "PND1",
    "40(2) ค่านายหน้า ค่าคอมมิชชั่น": "PND3",
    "40(3) ค่าลิขสิทธิ์": "PND3",
    "40(4)ก ดอกเบี้ย": "PND3",
    "40(4)ข เงินปันผล": "PND3",
    "40(5) ค่าเช่า": "PND53",
    "40(6) รางวัล ส่วนลด": "PND3",
    "40(7) ค่าจ้างทำของ": "PND3",
    "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ": "PND3",
    "40(8) ค่าบริการนิติบุคคล 3%": "PND53",
    "40(8) ค่าบริการนิติบุคคล 5%": "PND53",
    "40(8) ค่าขนส่ง 1%": "PND53",
    "40(8) ค่าเบี้ยประกัน 1%": "PND53",
    "40(8) ค่าโฆษณา 2%": "PND53",
}

#: The income type of the certificate and of a row of the certificate of a
#: site that carries no income type of its own.
DEFAULT_INCOME_TYPE = "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ"


def _meta_has_field(doctype: str, fieldname: str) -> bool:
    """Return True when the DocType carries the given field."""
    if not frappe.db.exists("DocType", doctype):
        return False
    try:
        return bool(frappe.get_meta(doctype).has_field(fieldname))
    except Exception:
        return False


def get_tax_month(date) -> str | None:
    """Return the tax month of the certificate for a date."""
    if not date:
        return None

    parsed = getdate(date)
    if not parsed:
        return None

    return TAX_MONTHS.get(int(parsed.month))


def get_tax_year(date) -> str:
    """Return the tax year of the certificate (Buddhist Era) for a date."""
    if not date:
        return ""

    parsed = getdate(date)
    if not parsed:
        return ""

    return str(int(parsed.year) + 543)


def get_income_type_of_category(category: str | None) -> str | None:
    """Return the income type that a ``Tax Withholding Category`` points at."""
    if not category:
        return None

    if not _meta_has_field(CATEGORY_DOCTYPE, CATEGORY_LINK_FIELD):
        return None

    linked = frappe.db.get_value(CATEGORY_DOCTYPE, category, CATEGORY_LINK_FIELD)
    if not linked or not isinstance(linked, str):
        return None

    return linked


def get_income_type(income_type: str | None) -> dict[str, Any] | None:
    """Return the record of the ``Thai WHT Income Type`` of a value.

    The value is the name of an income type, of a category of ERPNext or of
    the legacy statutory section of the income type.
    """
    if not income_type:
        return None

    if not frappe.db.exists("DocType", INCOME_TYPE_DOCTYPE):
        return None

    fields = [
        "name",
        "income_category",
        "form_type",
        "recipient_type",
        "tax_rate",
        "income_description",
        "income_category_th",
    ]

    if frappe.db.exists(INCOME_TYPE_DOCTYPE, income_type):
        rows = frappe.get_all(
            INCOME_TYPE_DOCTYPE,
            filters={"name": income_type},
            fields=fields,
            limit=1,
        )
        return rows[0] if rows else None

    linked = get_income_type_of_category(income_type)
    if linked:
        rows = frappe.get_all(
            INCOME_TYPE_DOCTYPE,
            filters={"name": linked},
            fields=fields,
            limit=1,
        )
        return rows[0] if rows else None

    return None


def _legacy_form_type(income_type: str, entity_type: str | None) -> str:
    """Return the form of the tax of a legacy section for a kind of payee.

    The classification of the certificate names the form of the tax, so the
    form and the classification have to agree.  A juristic person is reported
    on the form of a company, an individual on the form of an individual.
    """
    if entity_type in ("Company", "Government"):
        return "PND53"

    if entity_type == "Individual":
        if income_type == "40(1) เงินเดือน ค่าจ้าง":
            return "PND1"
        return "PND3"

    # A payee of an unknown kind keeps the form of the table.
    return LEGACY_FORM_TYPES.get(income_type, "PND3")


def _classification_of_form(form_type: str, entity_type: str | None) -> str:
    """Return the classification of the certificate of a form of the tax."""
    if entity_type in ("Company", "Government"):
        return CLASSIFICATION_COMPANY

    if form_type == "PND1":
        return CLASSIFICATION_STAFF

    if form_type == "PND53":
        return CLASSIFICATION_COMPANY

    return CLASSIFICATION_NON_STAFF


def _classification_of(form_type: str, recipient_type: str) -> str:
    """Return the classification of the certificate for a kind of recipient."""
    if recipient_type == "Individual":
        if form_type == "PND1":
            return CLASSIFICATION_STAFF
        return CLASSIFICATION_NON_STAFF

    if recipient_type == "Oversea":
        # A recipient outside Thailand has no classification of the forms of
        # Thailand; the certificate leaves the field empty.
        return ""

    return CLASSIFICATION_COMPANY


def _fallback_income_types(form_type: str, recipient_type: str) -> tuple[str, str]:
    """Return the line of the certificate of an income type without a mapping."""
    if recipient_type == "Individual":
        if form_type == "PND1":
            return LEGACY_INCOME_TYPES["40(1) เงินเดือน ค่าจ้าง"]
        return (
            "40 (8) ค่าจ้างทำของ(อื่นๆ) (3%)",
            "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ",
        )

    if recipient_type == "Foundation/Association":
        return (
            "40 (3) ค่าแห่งกู้ดวิลล์ ค่าแห่งลิขสิทธิ์ หรือสิทธิอย่างอื่น - สมาคม (10%)",
            "40(2) ค่านายหน้า ค่าคอมมิชชั่น",
        )

    if recipient_type == "Oversea":
        return (
            "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service",
            "40(8) ค่าบริการนิติบุคคล 5%",
        )

    return (
        "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service",
        "40(8) ค่าบริการนิติบุคคล 3%",
    )


def resolve_income_type(
    income_type: str | None,
    entity_type: str | None = None,
) -> dict[str, Any]:
    """Resolve the values of the certificate of an income type.

    :param income_type: the income type of the transaction.  It is the name
        of a ``Thai WHT Income Type``, the name of a
        ``Tax Withholding Category`` or the statutory section of the legacy
        field ``Advance Taxes and Charges.tbs_income_type``.
    :param entity_type: the kind of the payee (``Individual``, ``Company``,
        ``Government``).  It is the fallback of a legacy income type.

    :return: a dict with the keys ``income_type`` (the line of the
        certificate), ``item_income_type`` (the income type of a row of the
        certificate), ``classification``, ``pnd_form``, ``rate`` and
        ``description``.
    """
    record = get_income_type(income_type)

    if record:
        form_type = record.get("form_type") or ""
        recipient_type = record.get("recipient_type") or ""
        key = (record.get("income_category") or "", form_type, recipient_type)
        mapped = CERTIFICATE_INCOME_TYPES.get(key)
        if not mapped:
            mapped = _fallback_income_types(form_type, recipient_type)

        description = (
            record.get("income_category_th")
            or record.get("income_description")
            or record.get("income_category")
            or ""
        )

        return {
            "income_type": mapped[0],
            "item_income_type": mapped[1],
            "classification": _classification_of(form_type, recipient_type),
            "pnd_form": PND_FORM_DOCTYPES.get(form_type),
            "rate": flt(record.get("tax_rate")),
            "description": description,
            "source": INCOME_TYPE_DOCTYPE,
        }

    legacy = LEGACY_INCOME_TYPES.get(income_type or "")
    if legacy:
        parent, child = legacy
        form_type = _legacy_form_type(income_type or "", entity_type)

        if entity_type in ("Company", "Government"):
            override = LEGACY_COMPANY_INCOME_TYPES.get(income_type or "")
            if override:
                parent, child = override

        return {
            "income_type": parent,
            "item_income_type": child,
            "classification": _classification_of_form(form_type, entity_type),
            "pnd_form": PND_FORM_DOCTYPES.get(form_type),
            "rate": 0.0,
            "description": income_type or "",
            "source": "legacy",
        }

    return {
        "income_type": "",
        "item_income_type": "",
        "classification": "",
        "pnd_form": None,
        "rate": 0.0,
        "description": income_type or "",
        "source": "",
    }
