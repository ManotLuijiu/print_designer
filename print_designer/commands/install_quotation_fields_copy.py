import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Create custom fields for Quotation doctype"""

    custom_fields = {
        "Quotation": [
            # Prepared By Signature field
            {
                "fieldname": "prepared_by_signature",
                "fieldtype": "Attach Image",
                "label": "Prepared By Signature",
                "insert_after": "sales_team",
                "description": "Signature of person who prepared the quotation",
                "allow_on_submit": 0,
                "is_system_generated": 1,
            },
            # Subject to WHT field
            {
                "fieldname": "subject_to_wht",
                "fieldtype": "Check",
                "label": "Subject to Withholding Tax",
                "insert_after": "wht_section",
                "depends_on": "eval:doc.company && frappe.db.get_value('Company', doc.company, 'thailand_service_business')",
                "description": "This quotation is for services subject to 3% withholding tax",
                "default": "0",
                "allow_on_submit": 0,
                "is_system_generated": 1,
            },
            # Thai WHT Preview Section
            {
                "fieldname": "thai_wht_preview_section",
                "fieldtype": "Section Break",
                "label": "Thai Ecosystem Preview (ภาษีหัก ณ ที่จ่าย/เงินประกันผลงาน)",
                "insert_after": "named_place",
                "collapsible": 1,
                "collapsible_depends_on": "eval:doc.subject_to_wht",
                "no_copy": 1,
                "read_only": 1,
            },
            # WHT Amounts Column Break
            {
                "fieldname": "wht_amounts_column_break",
                "fieldtype": "Column Break",
                "insert_after": "thai_wht_preview_section",
                "no_copy": 1,
                "read_only": 1,
            },
            # VAT Treatment field
            {
                "fieldname": "vat_treatment",
                "fieldtype": "Select",
                "label": "VAT Treatment",
                "insert_after": "wht_amounts_column_break",
                "options": "\nStandard VAT (7%)\nExempt from VAT\nZero-rated for Export (0%)",
                "description": "Select VAT treatment: Standard 7% for regular sales, Exempt for fresh food/services, Zero-rated for export sales",
                "default": "Standard VAT (7%)",
                "in_list_view": 1,
                "in_standard_filter": 1,
                "translatable": 1,
                "is_system_generated": 1,
            },
            # WHT Income Type field
            {
                "fieldname": "wht_income_type",
                "fieldtype": "Select",
                "label": "WHT Income Type",
                "insert_after": "subject_to_wht",
                "options": "\nprofessional_services\nrental\nservice_fees\nconstruction\nadvertising\nother_services",
                "depends_on": "eval:doc.subject_to_wht",
                "description": "Type of income for WHT calculation",
                "no_copy": 1,
                "translatable": 1,
            },
            # WHT Description field
            {
                "fieldname": "wht_description",
                "fieldtype": "Data",
                "label": "WHT Description",
                "insert_after": "wht_income_type",
                "depends_on": "eval:doc.wht_income_type",
                "description": "Thai description of WHT income type",
                "read_only": 1,
                "no_copy": 1,
                "translatable": 1,
            },
            # Estimated WHT Rate field
            {
                "fieldname": "estimated_wht_rate",
                "fieldtype": "Percent",
                "label": "Estimated WHT Rate",
                "insert_after": "wht_description",
                "depends_on": "eval:doc.subject_to_wht",
                "description": "Withholding tax rate (e.g., 3% for services)",
                "precision": "2",
                "read_only": 1,
                "is_system_generated": 1,
            },
            # Estimated WHT Amount field
            {
                "fieldname": "estimated_wht_amount",
                "fieldtype": "Currency",
                "label": "Estimated WHT Amount",
                "insert_after": "estimated_wht_rate",
                "depends_on": "eval:doc.subject_to_wht",
                "description": "Estimated withholding tax amount (base amount × WHT rate)",
                "options": "Company:company:default_currency",
                "precision": "2",
                "read_only": 1,
                "is_system_generated": 1,
            },
            # Net Payment Amount field
            {
                "fieldname": "net_payment_amount",
                "fieldtype": "Currency",
                "label": "Net Payment Amount",
                "insert_after": "estimated_wht_amount",
                "depends_on": "eval:doc.subject_to_wht",
                "description": "Net payment amount after WHT deduction",
                "options": "Company:company:default_currency",
                "read_only": 1,
                "is_system_generated": 1,
            },
            # Net Total After WHT field
            {
                "fieldname": "net_total_after_wht",
                "fieldtype": "Currency",
                "label": "Net Total (After WHT)",
                "insert_after": "net_payment_amount",
                "depends_on": "eval:doc.subject_to_wht",
                "description": "Net total after adding VAT (7%) and deducting WHT",
                "options": "Company:company:default_currency",
                "read_only": 1,
                "is_system_generated": 1,
            },
            # Net Total After WHT in Words field
            {
                "fieldname": "net_total_after_wht_in_words",
                "fieldtype": "Small Text",
                "label": "Net Total (After WHT) in Words",
                "insert_after": "net_total_after_wht",
                "depends_on": "eval:doc.subject_to_wht && doc.net_total_after_wht",
                "description": "Net total amount in Thai words",
                "read_only": 1,
                "is_system_generated": 1,
            },
            # WHT Note field
            {
                "fieldname": "wht_note",
                "fieldtype": "Small Text",
                "label": "WHT Note",
                "insert_after": "net_total_after_wht_in_words",
                "depends_on": "eval:doc.wht_income_type",
                "description": "Important note about WHT deduction timing",
                "default": "หมายเหตุ: จำนวนเงินภาษีหัก ณ ที่จ่าย จะถูกหักเมื่อชำระเงิน\nNote: Withholding tax amount will be deducted upon payment",
                "read_only": 1,
                "no_copy": 1,
                "translatable": 1,
            },
            # WHT Preview Column Break
            {
                "fieldname": "wht_preview_column_break",
                "fieldtype": "Column Break",
                "insert_after": "wht_note",
                "no_copy": 1,
                "read_only": 1,
            },
            # Subject to Retention field
            {
                "fieldname": "custom_subject_to_retention",
                "fieldtype": "Check",
                "label": "Subject to Retention",
                "insert_after": "wht_preview_column_break",
                "description": "This quotation is for construction subject to retention deduct.",
                "in_list_view": 1,
            },
            # Retention Percentage field
            {
                "fieldname": "custom_retention",
                "fieldtype": "Percent",
                "label": "Retention (%)",
                "insert_after": "base_in_words",
                "depends_on": "eval:doc.custom_subject_to_retention",
                "description": "Retention percentage to be withheld from payment",
            },
            # Retention Amount field
            {
                "fieldname": "custom_retention_amount",
                "fieldtype": "Currency",
                "label": "Retention Amount",
                "insert_after": "custom_retention",
                "depends_on": "eval:doc.custom_subject_to_retention",
                "description": "Calculated retention amount",
            },
            # Withholding Tax Percentage field
            {
                "fieldname": "custom_withholding_tax",
                "fieldtype": "Percent",
                "label": "Withholding Tax (%)",
                "insert_after": "custom_retention_amount",
                "depends_on": "eval:doc.subject_to_wht",
                "description": "Withholding tax percentage",
            },
            # Withholding Tax Amount field
            {
                "fieldname": "custom_withholding_tax_amount",
                "fieldtype": "Currency",
                "label": "Withholding Tax Amount",
                "insert_after": "custom_withholding_tax",
                "depends_on": "eval:doc.subject_to_wht",
                "description": "Calculated withholding tax amount",
            },
            # Payment Amount field
            {
                "fieldname": "custom_payment_amount",
                "fieldtype": "Currency",
                "label": "Payment Amount",
                "insert_after": "custom_withholding_tax_amount",
                "depends_on": "eval:doc.subject_to_wht || doc.custom_subject_to_retention",
                "description": "Final payment amount after all deductions",
                "read_only": 1,
            },
            # Net Total After WHT & Retention field
            {
                "fieldname": "custom_net_total_after_wht_retention",
                "fieldtype": "Currency",
                "label": "Net Total (After WHT & Retention)",
                "insert_after": "custom_subject_to_retention",
                "depends_on": "eval:doc.custom_subject_to_retention",
                "description": "Net total after adding VAT (7%) and deducting WHT&Retention",
            },
            # Net Total After WHT & Retention in Words field
            {
                "fieldname": "custom_net_total_after_wht_and_retention_in_words",
                "fieldtype": "Data",
                "label": "Net Total (After WHT and Retention) in Words",
                "insert_after": "custom_net_total_after_wht_retention",
                "depends_on": "eval:doc.custom_subject_to_retention",
                "description": "Net total amount in Thai words (After WHT & Retention)",
                "translatable": 1,
            },
            # Retention Note field
            {
                "fieldname": "custom_retention_note",
                "fieldtype": "Small Text",
                "label": "Retention Note",
                "insert_after": "custom_net_total_after_wht_and_retention_in_words",
                "depends_on": "eval:doc.custom_subject_to_retention",
                "description": "Important note about Retention deduction timing",
                "default": "หมายเหตุ: จำนวนเงินประกันผลงาน  จะถูกหักเมื่อชำระเงิน\nNote: Retention amount will be deducted upon payment",
                "translatable": 1,
            },
            # Watermark Text field
            {
                "fieldname": "watermark_text",
                "fieldtype": "Select",
                "label": "Document Watermark",
                "insert_after": "quotation_to",
                "options": "None\nOriginal\nCopy\nDraft\nSubmitted\nOrdered\nExpired\nDuplicate",
                "description": "Watermark text to display on printed document",
                "default": "None",
                "allow_on_submit": 1,
                "print_hide": 1,
                "translatable": 1,
                "is_system_generated": 1,
            },
        ]
    }

    print("Creating custom fields for Quotation...")
    create_custom_fields(custom_fields, update=True)
    print("Custom fields for Quotation created successfully!")


if __name__ == "__main__":
    frappe.init(site="your-site-name")
    frappe.connect()
    execute()
    frappe.db.commit()
