"""
Thai WHT Income Type Data Installation

This module provides functionality to import Thai Withholding Tax income type
master data from CSV file into the Thai WHT Income Type DocType.

Usage:
    from print_designer.commands.install_thai_wht_income_type import install_thai_wht_income_types
    install_thai_wht_income_types()
"""

import csv
import os

import frappe
from frappe import _
from frappe.utils import flt


# Thai translations mapping for income categories
THAI_TRANSLATIONS = {
    # Income Categories
    "Rental Income": "ค่าเช่าอสังหาริมทรัพย์",
    "Rental Income (Ship Lease)": "ค่าเช่าเรือ (ส่งเสริมการเดินเรือ)",
    "Professional Services": "ค่าจ้างวิชาชีพ",
    "Services Income": "ค่าจ้างทำของ/รับเหมา",
    "Prize & Awards": "รางวัล/ชิงโชค",
    "Entertainment Income": "ค่าแสดงสาธารณะ",
    "Advertising Income": "ค่าโฆษณา",
    "Service Fees": "ค่าบริการ",
    "Transport Fees": "ค่าขนส่ง",
    "Sales Promotion Income": "รางวัลส่งเสริมการขาย",
    "Commission & Royalties": "ค่านายหน้า/ค่าลิขสิทธิ์",
    "Interest Income": "ดอกเบี้ย",
    "Bond Interest": "ดอกเบี้ยพันธบัตร",
    "Dividend Income": "เงินปันผล",
    "Dividend Income (Foreign)": "เงินปันผล (ต่างประเทศ)",
    "Interest Income (Foreign)": "ดอกเบี้ย (ต่างประเทศ)",
    "Royalty (Foreign)": "ค่าสิทธิ (ต่างประเทศ)",
    "Professional Services (Foreign)": "ค่าจ้างวิชาชีพอิสระ (ต่างประเทศ)",
    "Contracting Services (Foreign)": "ค่ารับเหมา/จ้างทำของ (ต่างประเทศ)",
    "Ship Rental": "ค่าเช่าเรือ",
    "Contracting Services": "ค่าจ้างทำของ",
    "Foreign Contractor Fees": "ค่าจ้างผู้รับเหมาต่างประเทศ",
    "Insurance Premiums": "เบี้ยประกันวินาศภัย",
    "Agricultural Trading Income": "ซื้อพืชผลเกษตร",
    # Conditions
    "Resident individual": "บุคคลธรรมดา (มีถิ่นที่อยู่)",
    "Individual recipient": "บุคคลธรรมดา",
    "Foreign resident": "บุคคลธรรมดา (ต่างประเทศ)",
    "Filming in Thailand with permission": "ถ่ายทำในไทยโดยได้รับอนุญาต",
    "Not end-consumer": "ไม่ใช่ผู้บริโภคปลายทาง",
    "Thai company": "บริษัทไทย",
    "Foundation/Association": "มูลนิธิ/สมาคม",
    "Thai company (non-financial)": "บริษัทไทย (ไม่ใช่สถาบันการเงิน)",
    "Financial institutions": "สถาบันการเงิน",
    "Foreign company operating in Thailand": "บริษัทต่างประเทศที่ดำเนินงานในไทย",
    "Thai company (non-exempt cases)": "บริษัทไทย (กรณีไม่ได้รับยกเว้น)",
    "Thai insurance company": "บริษัทประกันภัยไทย",
    "Thai company (exporter/producer only)": "บริษัทไทย (ผู้ส่งออก/ผู้ผลิตเท่านั้น)",
    # Income Descriptions
    "Rent or benefits from leasing buildings/houses/structures (Section 40(5))": "ค่าเช่าหรือประโยชน์จากการให้เช่าอาคาร/บ้าน/สิ่งปลูกสร้าง (มาตรา 40(5))",
    "Ship rental under Maritime Promotion Act (international transport)": "ค่าเช่าเรือตาม พ.ร.บ.ส่งเสริมการพาณิชยนาวี (ขนส่งระหว่างประเทศ)",
    "Law / Medical / Engineering / Architecture / Accounting / Fine Arts (Section 40(6))": "กฎหมาย / แพทย์ / วิศวกรรม / สถาปัตยกรรม / บัญชี / ประณีตศิลป์ (มาตรา 40(6))",
    "Contracting / hire of work (Section 40(7),(8))": "รับเหมา / จ้างทำของ (มาตรา 40(7),(8))",
    "Contest / competition / lucky draw prizes": "รางวัลจากการแข่งขัน / ชิงโชค",
    "Public performers (actors / singers / musicians / athletes)": "นักแสดงสาธารณะ (นักแสดง / นักร้อง / นักดนตรี / นักกีฬา)",
    "Advertising fees": "ค่าโฆษณา",
    "General services excluding transport/hotel/insurance": "ค่าบริการทั่วไป (ไม่รวมขนส่ง/โรงแรม/ประกัน)",
    "Freight and transport fees (non-public transport)": "ค่าขนส่ง (ไม่ใช่ขนส่งสาธารณะ)",
    "Rewards / discounts / benefits from promotion": "รางวัล / ส่วนลด / ผลประโยชน์จากการส่งเสริมการขาย",
    "Commission / goodwill / copyright / rights (Section 40(2),(3))": "ค่านายหน้า / ค่าความนิยม / ลิขสิทธิ์ / สิทธิ (มาตรา 40(2),(3))",
    "Interest under Section 40(4)(a)": "ดอกเบี้ยตามมาตรา 40(4)(ก)",
    "Bond or debenture interest": "ดอกเบี้ยพันธบัตรหรือหุ้นกู้",
    "Dividends / profit sharing (Section 40(4)(b))": "เงินปันผล / ส่วนแบ่งกำไร (มาตรา 40(4)(ข))",
    "Dividends paid to foreign company (Section 40(4)(b))": "เงินปันผล / ส่วนแบ่งกำไรที่จ่ายให้บริษัทต่างประเทศ (มาตรา 40(4)(ข))",
    "Interest paid to foreign company (Section 40(4))": "ดอกเบี้ยที่จ่ายให้บริษัทต่างประเทศ (มาตรา 40(4))",
    "Royalties paid to foreign company (Section 40(3))": "ค่าสิทธิ / แฟรนไชส์ / ลิขสิทธิ์ที่จ่ายให้บริษัทต่างประเทศ (มาตรา 40(3))",
    "Professional services paid to foreign company (Section 40(6))": "ค่าบริการวิชาชีพอิสระที่จ่ายให้บริษัทต่างประเทศ (มาตรา 40(6))",
    "Contracting services paid to foreign company (Section 40(2),(7),(8))": "รับเหมา / จ้างทำของที่จ่ายให้บริษัทต่างประเทศ (มาตรา 40(2),(7),(8))",
    "Rent of buildings/houses/structures (Section 40(5))": "ค่าเช่าอาคาร/บ้าน/สิ่งปลูกสร้าง (มาตรา 40(5))",
    "Ship lease for international transport": "ค่าเช่าเรือสำหรับขนส่งระหว่างประเทศ",
    "Hire of work / contracting (Section 40(7),(8))": "จ้างทำของ / รับเหมา (มาตรา 40(7),(8))",
    "Foreign company without permanent branch in Thailand": "บริษัทต่างประเทศไม่มีสาขาถาวรในไทย",
    "Contest / competition prizes": "รางวัลจากการแข่งขัน",
    "Rewards / discounts / promotion benefits": "รางวัล / ส่วนลด / ผลประโยชน์ส่งเสริมการขาย",
    "Non-life insurance premiums": "เบี้ยประกันวินาศภัย",
    "Purchase of rubber/rice/cassava/palm/coffee (exporter/producer only)": "ซื้อยาง/ข้าว/มันสำปะหลัง/ปาล์ม/กาแฟ (ผู้ส่งออก/ผู้ผลิตเท่านั้น)",
}

# Thai form type mapping
FORM_TYPE_TH = {
    "PND3": "ภงด.3",
    "PND53": "ภงด.53",
    "PND54": "ภงด.54",
}

RECIPIENT_TYPE_TH = {
    "Individual": "บุคคลธรรมดา",
    "Corporation": "นิติบุคคล",
    "Foundation/Association": "มูลนิธิ/สมาคม",
    "Oversea": "ต่างประเทศ",
    "Government": "รัฐบาล",
}


def get_csv_path():
    """Get the path to the WHT data CSV file."""
    app_path = frappe.get_app_path("print_designer")
    return os.path.join(app_path, "data", "withholding_tax_PND3_PND53.csv")


def translate_to_thai(text):
    """Get Thai translation for English text."""
    if not text:
        return ""
    return THAI_TRANSLATIONS.get(text.strip(), text)


def parse_csv_data():
    """Parse the WHT CSV file and return structured data."""
    csv_path = get_csv_path()

    if not os.path.exists(csv_path):
        frappe.throw(_("WHT data CSV file not found at: {0}").format(csv_path))

    records = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            form_type = row.get("Form", "").strip()
            if not form_type:
                continue

            records.append({
                "form_type": form_type,
                "recipient_type": row.get("Recipient Type", "").strip(),
                "income_category": row.get("Income Category", "").strip(),
                "income_description": row.get("Income Description", "").strip(),
                "conditions": row.get("Conditions", "").strip(),
                "tax_rate": flt(row.get("Tax Rate (%)", 0)),
            })

    return records


def install_thai_wht_income_types():
    """
    Install Thai WHT Income Type master data from CSV.

    This function:
    1. Reads data from withholding_tax_PND3_PND53.csv
    2. Creates Thai WHT Income Type records
    3. Adds Thai translations for each field
    """
    if not frappe.db.exists("DocType", "Thai WHT Income Type"):
        frappe.log_error(
            "Thai WHT Income Type DocType does not exist. Run bench migrate first.",
            "WHT Income Type Installation"
        )
        return

    records = parse_csv_data()
    created_count = 0
    updated_count = 0

    # Pre-build collision map: (form_type, income_category) -> has multiple records?
    # Only add suffix when collision exists.
    from collections import defaultdict
    form_cat_counts = defaultdict(int)
    for record in records:
        form_cat_counts[(record["form_type"], record["income_category"])] += 1

    # Group collision records: (form_type, income_category) -> list of conditions (normalized)
    form_cat_conditions = defaultdict(list)
    for record in records:
        cv = " ".join(record["conditions"].split()) if record["conditions"] else ""
        form_cat_conditions[(record["form_type"], record["income_category"])].append(cv)

    for record in records:
        # Normalize whitespace to handle any embedded newlines/tabs in CSV
        conditions_val = " ".join(record["conditions"].split()) if record["conditions"] else ""
        existing = frappe.db.get_value(
            "Thai WHT Income Type",
            {
                "form_type": record["form_type"],
                "income_category": record["income_category"],
                "tax_rate": record["tax_rate"],
                "recipient_type": record["recipient_type"],
                "conditions": conditions_val,
            },
            "name",
        )

        doc_data = {
            "doctype": "Thai WHT Income Type",
            "form_type": record["form_type"],
            "form_type_th": FORM_TYPE_TH.get(record["form_type"], record["form_type"]),
            "recipient_type": record["recipient_type"],
            "recipient_type_th": RECIPIENT_TYPE_TH.get(record["recipient_type"], record["recipient_type"]),
            "income_category": record["income_category"],
            "income_category_th": translate_to_thai(record["income_category"]),
            "income_description": record["income_description"],
            "income_description_th": translate_to_thai(record["income_description"]) if record["income_description"] else "",
            "conditions": conditions_val,
            "conditions_th": translate_to_thai(conditions_val),
            "tax_rate": record["tax_rate"],
            "is_active": 1,
            # Compound Thai display name: {income_category_th} {recipient_type_th} {tax_rate} {form_type_th}
            "doc_title_th": f"{translate_to_thai(record['income_category'])} {RECIPIENT_TYPE_TH.get(record['recipient_type'], record['recipient_type'])} {record['tax_rate']} {FORM_TYPE_TH.get(record['form_type'], record['form_type'])}",
        }

        if existing:
            # Update existing record IN-PLACE (preserves current doc name, avoids duplicate insert)
            doc = frappe.get_doc("Thai WHT Income Type", existing)
            doc.update(doc_data)
            doc.save(ignore_permissions=True)
            updated_count += 1
        else:
            # English doc name: {income_category} {recipient_type} {tax_rate} {form_type}
            # Example: "Advertising Income Corporation 2 PND53"
            # Space-separated, no special characters (Tier 2.2 naming)
            income_cat = record["income_category"]
            recipient = record["recipient_type"]
            rate_val = record["tax_rate"]
            form_code = record["form_type"]
            doc_name = f"{income_cat} {recipient} {rate_val} {form_code}"

            # Safety check: if English name already exists (partial migration state), update it instead
            if frappe.db.exists("Thai WHT Income Type", doc_name):
                doc = frappe.get_doc("Thai WHT Income Type", doc_name)
                doc.update(doc_data)
                doc.save(ignore_permissions=True)
                updated_count += 1
            else:
                # Insert via SQL to bypass Frappe autoname interference entirely
                doc_data["name"] = doc_name
                # Remove doctype (it's a Frappe meta field, not a DB column)
                insert_data = {k: v for k, v in doc_data.items() if k != "doctype"}
                columns = list(insert_data.keys())
                placeholders = ["%s"] * len(columns)
                values = [insert_data[c] for c in columns]
                frappe.db.sql(
                    f"INSERT INTO `tabThai WHT Income Type` ({', '.join(columns)}) VALUES ({', '.join(placeholders)})",
                    values,
                )
                created_count += 1

    frappe.db.commit()

    print(f"Thai WHT Income Type installation complete:")
    print(f"  - Created: {created_count} records")
    print(f"  - Updated: {updated_count} records")
    print(f"  - Total: {created_count + updated_count} records")

    return {
        "created": created_count,
        "updated": updated_count,
        "total": created_count + updated_count
    }


def check_thai_wht_income_types():
    """Check if Thai WHT Income Types are installed."""
    if not frappe.db.exists("DocType", "Thai WHT Income Type"):
        return False

    count = frappe.db.count("Thai WHT Income Type")
    return count > 0


# CLI command function
def main():
    """CLI entry point for installing Thai WHT Income Types."""
    site = frappe.local.site
    frappe.init(site=site)
    frappe.connect()

    try:
        install_thai_wht_income_types()
    finally:
        frappe.destroy()


if __name__ == "__main__":
    main()
