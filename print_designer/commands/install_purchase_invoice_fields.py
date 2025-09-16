#!/usr/bin/env python3

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def install_purchase_invoice_thai_tax_fields():
    """Install Thai Tax Compliance fields for Purchase Invoice in print_designer app"""

    # Thai Tax Compliance fields for Purchase Invoice
    thai_tax_fields = {
        "Purchase Invoice": [
            # Thai WHT Compliance - Independent system
            {
                "fieldname": "apply_thai_wht_compliance",
                "label": "Apply Thai Withholding Tax Compliance",
                "fieldtype": "Check",
                "insert_after": "tax_withholding_category",
                "description": "TDS enabled: VAT Treatment will be auto-set to \"VAT Undue (7%)\" for compliance",
                "default": "0",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
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
            },
            # Thai Ecosystem Preview (ภาษีหัก ณ ที่จ่าย/เงินประกันผลงาน)
             {
                "fieldname": "thai_wht_preview_section",
                "label": "Thai Ecosystem Preview (ภาษีหัก ณ ที่จ่าย/เงินประกันผลงาน)",
                "fieldtype": "Section Break",
                "insert_after": "named_place",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 1,
                "length": 0,
                "bold": 0,
            },
            # Left Column
            {
                "fieldname": "wht_amounts_column_break",
                "label": None,
                "fieldtype": "Column Break",
                "insert_after": "thai_wht_preview_section",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
             {
                "fieldname": "vat_treatment",
                "label": "VAT Treatment",
                "fieldtype": "Select",
                "insert_after": "wht_amounts_column_break",
                "default": "Standard VAT (7%)",
                "options": "\nStandard VAT (7%)\nVAT Undue (7%)\nExempt from VAT\nZero-rated for Export (0%)",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "in_list_view": 1,
                "in_standard_filter": 1,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "subject_to_wht",
                "label": "Subject to Withholding Tax",
                "fieldtype": "Check",
                "insert_after": "vat_treatment",
                "depends_on": "eval:doc.company && doc.thailand_service_business",
                "default": "0",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "wht_income_type",
                "label": "WHT Income Type",
                "fieldtype": "Select",
                "insert_after": "subject_to_wht",
                "depends_on": "eval:doc.subject_to_wht",
                "options": "\nprofessional_services\nrental\nservice_fees\nconstruction\nadvertising\nother_services",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "wht_description",
                "label": "WHT Description",
                "fieldtype": "Data",
                "insert_after": "wht_income_type",
                "depends_on": "eval:doc.wht_income_type",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "net_total_after_wht",
                "label": "Net Total (After WHT)",
                "fieldtype": "Currency",
                "insert_after": "wht_description",
                "depends_on": "eval:doc.subject_to_wht",
                "options": "Company:company:default_currency",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "net_total_after_wht_in_words",
                "label": "Net Total (After WHT) in Words",
                "fieldtype": "Data",
                "insert_after": "net_total_after_wht",
                "depends_on": "eval:doc.subject_to_wht && doc.net_total_after_wht",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
             {
                "fieldname": "wht_note",
                "label": "WHT Note",
                "fieldtype": "Small Text",
                "insert_after": "net_total_after_wht_in_words",
                "depends_on": "eval:doc.wht_income_type",
                "default": "หมายเหตุ: จำนวนเงินภาษีหัก ณ ที่จ่าย จะถูกหักเมื่อชำระเงิน\nNote: Withholding tax amount will be deducted upon payment",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            # Right Column
            {
                "fieldname": "wht_preview_column_break",
                "label": None,
                "fieldtype": "Column Break",
                "insert_after": "wht_note",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
             {
                "fieldname": "custom_subject_to_retention",
                "label": "Subject to Retention",
                "fieldtype": "Check",
                "insert_after": "wht_preview_column_break",
                "depends_on": "eval:doc.apply_thai_wht_compliance",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "in_list_view": 1,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "custom_net_total_after_wht_retention",
                "label": "Net Total (After WHT & Retention)",
                "fieldtype": "Currency",
                "insert_after": "custom_subject_to_retention",
                "depends_on": "eval:doc.custom_subject_to_retention",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "custom_net_total_after_wht_retention_in_words",
                "label": "Net Total (After WHT and Retention) in Words",
                "fieldtype": "Data",
                "insert_after": "custom_net_total_after_wht_retention",
                "description": "Net total amount in Thai words (After WHT & Retention)",
                "depends_on": "eval:doc.custom_subject_to_retention",
                "translatable": 1,
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
             {
                "fieldname": "custom_retention_note",
                "label": "Retention Note",
                "fieldtype": "Small Text",
                "insert_after": "custom_net_total_after_wht_retention_in_words",
                "depends_on": "eval:doc.custom_subject_to_retention",
                "default": "หมายเหตุ: จำนวนเงินประกันผลงาน  จะถูกหักเมื่อชำระเงิน\nNote: Retention amount will be deducted upon payment",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            # Insert at Totals Section
            {
                "fieldname": "custom_retention",
                "label": "Retention (%)",
                "fieldtype": "Percent",
                "insert_after": "base_in_words",
                "depends_on": "eval:doc.apply_thai_wht_compliance",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "custom_retention_amount",
                "label": "Retention Amount",
                "fieldtype": "Currency",
                "insert_after": "custom_retention",
                "depends_on": "eval:doc.custom_subject_to_retention",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "custom_withholding_tax",
                "label": "Withholding Tax (%)",
                "fieldtype": "Percent",
                "insert_after": "custom_retention_amount",
                "depends_on": "eval:doc.subject_to_wht",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "custom_withholding_tax_amount",
                "label": "Withholding Tax Amount",
                "fieldtype": "Currency",
                "insert_after": "custom_withholding_tax",
                "depends_on": "eval:doc.subject_to_wht",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
             {
                "fieldname": "custom_payment_amount",
                "label": "Payment Amount",
                "fieldtype": "Currency",
                "insert_after": "custom_withholding_tax_amount",
                "depends_on": "eval:doc.subject_to_wht || doc.custom_subject_to_retention",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
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
        "apply_thai_wht_compliance",
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
        "pd_custom_net_payment_amount",
        # WHT and Retention
        "thai_wht_preview_section",
        "wht_amounts_column_break",
        "vat_treatment",
        "subject_to_wht",
        "wht_income_type",
        "wht_description",
        "net_total_after_wht",
        "net_total_after_wht_in_words",
        "wht_note",
        "wht_preview_column_break",
        "custom_subject_to_retention",
        "custom_net_total_after_wht_retention",
        "custom_net_total_after_wht_retention_in_words",
        "custom_retention_note",
        "custom_retention",
        "custom_retention_amount",
        "custom_withholding_tax",
        "custom_withholding_tax_amount",
        "custom_payment_amount"
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

@frappe.whitelist()
def check_purchase_invoice_fields():
    """Check if Purchase Invoice Thai tax fields are installed."""

    required_fields = [
        # Thai WHT Compliance field
        "apply_thai_wht_compliance",
        # Thai Tax Compliance Tab fields
        "thai_tax_compliance_section",
        "pd_custom_tax_invoice_number",
        "pd_custom_tax_invoice_date",
        "pd_custom_income_type",
        "pd_custom_tax_base_amount",
        "pd_custom_apply_withholding_tax",
        "pd_custom_wht_certificate_no",
        "pd_custom_wht_certificate_date",
        "pd_custom_withholding_tax_rate",
        "pd_custom_withholding_tax_amount",
        "pd_custom_net_payment_amount",
        # Thai WHT Preview Section fields
        "thai_wht_preview_section",
        "vat_treatment",
        "subject_to_wht",
        "wht_income_type",
        "wht_description",
        "net_total_after_wht",
        "net_total_after_wht_in_words",
        "wht_note",
        # Retention fields
        "custom_subject_to_retention",
        "custom_net_total_after_wht_retention",
        "custom_net_total_after_wht_retention_in_words",
        "custom_retention_note",
        "custom_retention",
        "custom_retention_amount",
        "custom_withholding_tax",
        "custom_withholding_tax_amount",
        "custom_payment_amount",
    ]

    existing_fields = frappe.db.sql("""
        SELECT fieldname
        FROM `tabCustom Field`
        WHERE dt = 'Purchase Invoice'
        AND fieldname IN ({})
    """.format(','.join(['%s'] * len(required_fields))), required_fields, as_dict=True)

    existing_field_names = [f.fieldname for f in existing_fields]
    missing_fields = [f for f in required_fields if f not in existing_field_names]

    if missing_fields:
        print(f"❌ Missing {len(missing_fields)} fields in Purchase Invoice:")
        for field in missing_fields:
            print(f"   - {field}")
        return False
    else:
        print("✅ All Purchase Invoice Thai tax fields are installed")
        return True

if __name__ == '__main__':
    frappe.init()
    frappe.connect()
    install_purchase_invoice_thai_tax_fields()