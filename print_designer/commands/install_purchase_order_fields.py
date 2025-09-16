"""Install Thai tax custom fields for Purchase Order DocType."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Install custom Thai tax fields for Purchase Order."""

    custom_fields = {
        "Purchase Order": [
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
                "depends_on": "eval:doc.company && doc.construction_service",
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
                "options": "Company:company:default_currency",
                "read_only": 1,
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
                "read_only": 1,
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
                "read_only": 1,
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
                "depends_on": "eval:doc.custom_subject_to_retention",
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
                "options": "Company:company:default_currency",
                "read_only": 1,
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
                "options": "Company:company:default_currency",
                "read_only": 1,
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
                "options": "Company:company:default_currency",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
        ]
    }

    print("Creating custom fields for Purchase Order...")
    create_custom_fields(custom_fields, update=True)

    # Clear cache
    frappe.clear_cache(doctype="Purchase Order")

    print("✅ Successfully installed Thai tax custom fields for Purchase Order")
    print("✅ Added 19 custom fields:")
    print("   - Thai WHT Preview Section with VAT and WHT fields")
    print("   - Retention fields for construction services")
    print("   - Payment calculation fields")

    return True


@frappe.whitelist()
def check_purchase_order_fields():
    """Check if Purchase Order Thai tax fields are installed."""

    required_fields = [
        "thai_wht_preview_section",
        "vat_treatment",
        "subject_to_wht",
        "wht_income_type",
        "wht_description",
        "net_total_after_wht",
        "net_total_after_wht_in_words",
        "wht_note",
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
        WHERE dt = 'Purchase Order'
        AND fieldname IN ({})
    """.format(','.join(['%s'] * len(required_fields))), required_fields, as_dict=True)

    existing_field_names = [f.fieldname for f in existing_fields]
    missing_fields = [f for f in required_fields if f not in existing_field_names]

    if missing_fields:
        print(f"❌ Missing {len(missing_fields)} fields in Purchase Order:")
        for field in missing_fields:
            print(f"   - {field}")
        return False
    else:
        print("✅ All Purchase Order Thai tax fields are installed")
        return True


def uninstall_purchase_order_fields():
    """Remove all Purchase Order Thai tax fields during app uninstall."""

    fields_to_remove = [
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
        "custom_payment_amount",
    ]

    try:
        # Delete custom fields
        frappe.db.delete("Custom Field", {
            "dt": "Purchase Order",
            "fieldname": ("in", fields_to_remove)
        })

        # Clear cache
        frappe.clear_cache(doctype="Purchase Order")
        frappe.db.commit()

        print(f"✅ Successfully removed {len(fields_to_remove)} Purchase Order Thai tax fields")
        return True

    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error removing Purchase Order fields: {str(e)}")
        return False