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

    for record in records:
        doc_name = f"{record['form_type']}-{record['income_category']}"

        doc_data = {
            "doctype": "Thai WHT Income Type",
            "form_type": record["form_type"],
            "recipient_type": record["recipient_type"],
            "income_category": record["income_category"],
            "income_category_th": translate_to_thai(record["income_category"]),
            "income_description": record["income_description"],
            "income_description_th": translate_to_thai(record["income_description"]) if record["income_description"] else "",
            "conditions": record["conditions"],
            "conditions_th": translate_to_thai(record["conditions"]),
            "tax_rate": record["tax_rate"],
            "is_active": 1
        }

        if frappe.db.exists("Thai WHT Income Type", doc_name):
            # Update existing record
            doc = frappe.get_doc("Thai WHT Income Type", doc_name)
            doc.update(doc_data)
            doc.save(ignore_permissions=True)
            updated_count += 1
        else:
            # Create new record
            doc = frappe.get_doc(doc_data)
            doc.insert(ignore_permissions=True)
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
