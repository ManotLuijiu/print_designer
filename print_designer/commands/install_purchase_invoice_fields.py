#!/usr/bin/env python3

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def install_purchase_invoice_thai_tax_fields():
    """Install Thai Tax Compliance fields for Purchase Invoice in print_designer app"""

    # Thai Tax Compliance fields for Purchase Invoice
    thai_tax_fields = {
        "Purchase Invoice": [
            {
                "fieldname": "thai_tax_compliance_section",
                "fieldtype": "Tab Break",
                "label": "Thai Tax Compliance",
                "insert_after": "write_off_cost_center"
            },
            # Left Column Fields
            {
                "fieldname": "pd_custom_tax_invoice_number",
                "fieldtype": "Data",
                "label": "Tax Invoice Number",
                "insert_after": "thai_tax_compliance_section",
                "description": "Thai tax invoice number for compliance"
            },
            {
                "fieldname": "pd_custom_tax_invoice_date",
                "fieldtype": "Date",
                "label": "Tax Invoice Date",
                "insert_after": "pd_custom_tax_invoice_number",
                "description": "Thai tax invoice date"
            },
            {
                "fieldname": "pd_custom_income_type",
                "fieldtype": "Select",
                "label": "Income Type",
                "options": "\n1. เงินเดือน ค่าจ้าง ฯลฯ 40(1)\n2. ค่าธรรมเนียม ค่านายหน้า ฯลฯ 40(2)\n3. ค่าแห่งลิขสิทธิ์ ฯลฯ 40(3)\n4. ดอกเบี้ย ฯลฯ 40(4)ก\n5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส\n6. ค่าบริการ/ค่าสินค้าภาครัฐ",
                "insert_after": "pd_custom_tax_invoice_date",
                "description": "Type of income for withholding tax calculation"
            },
            {
                "fieldname": "pd_custom_tax_base_amount",
                "fieldtype": "Currency",
                "label": "Tax Base Amount",
                "insert_after": "pd_custom_income_type",
                "description": "Base amount for tax calculation"
            },
            # Column Break
            {
                "fieldname": "pd_custom_column_break_thai_tax",
                "fieldtype": "Column Break",
                "insert_after": "pd_custom_tax_base_amount"
            },
            # Right Column Fields
            {
                "fieldname": "pd_custom_apply_withholding_tax",
                "fieldtype": "Check",
                "label": "Apply Withholding Tax",
                "insert_after": "pd_custom_column_break_thai_tax",
                "description": "Apply withholding tax to this invoice"
            },
            {
                "fieldname": "pd_custom_wht_certificate_no",
                "fieldtype": "Data",
                "label": "WHT Certificate No",
                "insert_after": "pd_custom_apply_withholding_tax",
                "depends_on": "pd_custom_apply_withholding_tax",
                "description": "Withholding tax certificate number"
            },
            {
                "fieldname": "pd_custom_wht_certificate_date",
                "fieldtype": "Date",
                "label": "WHT Certificate Date",
                "insert_after": "pd_custom_wht_certificate_no",
                "depends_on": "pd_custom_apply_withholding_tax",
                "description": "Withholding tax certificate date"
            },
            {
                "fieldname": "pd_custom_withholding_tax_rate",
                "fieldtype": "Percent",
                "label": "Withholding Tax Rate",
                "insert_after": "pd_custom_wht_certificate_date",
                "depends_on": "pd_custom_apply_withholding_tax",
                "description": "Withholding tax rate percentage"
            },
            {
                "fieldname": "pd_custom_withholding_tax_amount",
                "fieldtype": "Currency",
                "label": "Withholding Tax Amount",
                "insert_after": "pd_custom_withholding_tax_rate",
                "depends_on": "pd_custom_apply_withholding_tax",
                "description": "Withholding tax amount"
            },
            {
                "fieldname": "pd_custom_net_payment_amount",
                "fieldtype": "Currency",
                "label": "Net Payment Amount",
                "insert_after": "pd_custom_withholding_tax_amount",
                "depends_on": "pd_custom_apply_withholding_tax",
                "description": "Net amount after withholding tax deduction"
            }
        ]
    }

    print("🔧 Installing Thai Tax Compliance fields for Purchase Invoice...")

    try:
        # Create the custom fields
        create_custom_fields(thai_tax_fields, ignore_validate=True)
        frappe.db.commit()
        print("✅ Successfully installed Thai Tax Compliance fields for Purchase Invoice")
        print("📋 Fields added:")
        for field in thai_tax_fields["Purchase Invoice"]:
            if field["fieldtype"] != "Tab Break" and field["fieldtype"] != "Column Break":
                print(f"   - {field['fieldname']}: {field['label']}")

    except Exception as e:
        print(f"❌ Error installing fields: {str(e)}")
        frappe.db.rollback()
        raise e

def remove_purchase_invoice_thai_tax_fields():
    """Remove Thai Tax Compliance fields from Purchase Invoice"""

    field_names = [
        "thai_tax_compliance_section",
        "pd_custom_tax_invoice_number",
        "pd_custom_tax_invoice_date",
        "pd_custom_income_type",
        "pd_custom_tax_base_amount",
        "pd_custom_column_break_thai_tax",
        "pd_custom_apply_withholding_tax",
        "pd_custom_wht_certificate_no",
        "pd_custom_wht_certificate_date",
        "pd_custom_withholding_tax_rate",
        "pd_custom_withholding_tax_amount",
        "pd_custom_net_payment_amount"
    ]

    print("🗑️ Removing Thai Tax Compliance fields from Purchase Invoice...")

    removed_count = 0
    for fieldname in field_names:
        try:
            custom_field = frappe.db.get_value(
                "Custom Field",
                {"dt": "Purchase Invoice", "fieldname": fieldname},
                "name"
            )

            if custom_field:
                frappe.delete_doc("Custom Field", custom_field, force=True)
                print(f"✅ Removed: {fieldname}")
                removed_count += 1
            else:
                print(f"⚠️ Not found: {fieldname}")
        except Exception as e:
            print(f"❌ Error removing {fieldname}: {str(e)}")

    frappe.db.commit()
    print(f"📊 Total removed: {removed_count} fields")

if __name__ == '__main__':
    frappe.init()
    frappe.connect()
    install_purchase_invoice_thai_tax_fields()