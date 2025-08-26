# install_sales_invoice_fields.py
# File location: apps/custom_app/custom_app/install_sales_invoice_fields.py

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install_sales_invoice_custom_fields():
    """Install custom fields for Sales Invoice doctype"""

    custom_fields = {
        "Sales Invoice": [
            {
                "fieldname": "wht_certificate_required",
                "fieldtype": "Check",
                "label": "WHT Certificate Required",
                "insert_after": "wht_description",
                "description": "Customer will provide withholding tax certificate",
                "depends_on": "eval:doc.subject_to_wht",
                "default": "1",
            },
            {
                "fieldname": "watermark_text",
                "fieldtype": "Select",
                "label": "Document Watermark",
                "insert_after": "is_return",
                "description": "Watermark text to display on printed document",
                "options": "None\nOriginal\nCopy\nDraft\nCancelled\nPaid\nDuplicate",
                "default": "None",
                "allow_on_submit": 1,
                "print_hide": 1,
                "translatable": 1,
            },
            {
                "fieldname": "subject_to_wht",
                "fieldtype": "Check",
                "label": "Subject to Withholding Tax",
                "insert_after": "taxes_and_charges",
                "description": "This invoice is for services subject to withholding tax",
                "default": "0",
                "depends_on": "eval:doc.company",
            },
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
            {
                "fieldname": "wht_amounts_column_break",
                "fieldtype": "Column Break",
                "insert_after": "thai_wht_preview_section",
                "no_copy": 1,
                "read_only": 1,
            },
            {
                "fieldname": "vat_treatment",
                "fieldtype": "Select",
                "label": "VAT Treatment",
                "insert_after": "wht_amounts_column_break",
                "description": "Select VAT treatment: Standard 7% for regular sales, Exempt for fresh food/services, Zero-rated for export sales",
                "options": "\nStandard VAT (7%)\nExempt from VAT\nZero-rated for Export (0%)",
                "default": "Standard VAT (7%)",
                "in_list_view": 1,
                "in_standard_filter": 1,
                "translatable": 1,
            },
            {
                "fieldname": "wht_income_type",
                "fieldtype": "Select",
                "label": "WHT Income Type",
                "insert_after": "subject_to_wht",
                "description": "Type of income for WHT calculation",
                "depends_on": "eval:doc.subject_to_wht",
                "options": "\nprofessional_services\nrental\nservice_fees\nconstruction\nadvertising\nother_services",
                "no_copy": 1,
                "read_only": 1,
            },
            {
                "fieldname": "wht_description",
                "fieldtype": "Data",
                "label": "WHT Description",
                "insert_after": "wht_income_type",
                "description": "Thai description of WHT income type",
                "depends_on": "eval:doc.subject_to_wht",
                "no_copy": 1,
                "read_only": 1,
            },
            {
                "fieldname": "net_total_after_wht",
                "fieldtype": "Currency",
                "label": "Net Total (After WHT)",
                "insert_after": "wht_certificate_required",
                "description": "Net total after adding VAT (7%) and deducting WHT",
                "depends_on": "eval:doc.subject_to_wht",
                "options": "Company:company:default_currency",
                "read_only": 1,
            },
            {
                "fieldname": "net_total_after_wht_in_words",
                "fieldtype": "Small Text",
                "label": "Net Total (After WHT) in Words",
                "insert_after": "net_total_after_wht",
                "description": "Net total amount in Thai words",
                "depends_on": "eval:doc.subject_to_wht && doc.net_total_after_wht",
                "read_only": 1,
            },
            {
                "fieldname": "wht_note",
                "fieldtype": "Small Text",
                "label": "WHT Note",
                "insert_after": "net_total_after_wht_in_words",
                "description": "Important note about WHT deduction timing",
                "depends_on": "eval:doc.subject_to_wht",
                "default": "หมายเหตุ: จำนวนเงินภาษีหัก ณ ที่จ่าย จะถูกหักเมื่อชำระเงิน\\nNote: Withholding tax amount will be deducted upon payment",
                "no_copy": 1,
                "read_only": 1,
                "translatable": 1,
            },
            {
                "fieldname": "wht_preview_column_break",
                "fieldtype": "Column Break",
                "insert_after": "wht_note",
                "no_copy": 1,
                "read_only": 1,
            },
            {
                "fieldname": "custom_subject_to_retention",
                "fieldtype": "Check",
                "label": "Subject to Retention",
                "insert_after": "wht_preview_column_break",
                "description": "This invoice is for construction subject to retention deduct.",
            },
            {
                "fieldname": "custom_net_total_after_wht_retention",
                "fieldtype": "Currency",
                "label": "Net Total (After WHT & Retention)",
                "insert_after": "custom_subject_to_retention",
                "description": "Net total after adding VAT (7%) and deducting WHT&Retention",
                "depends_on": "eval:doc.custom_subject_to_retention",
            },
            {
                "fieldname": "custom_net_total_after_wht_and_retention_in_words",
                "fieldtype": "Data",
                "label": "Net Total (After WHT and Retention) in Words",
                "insert_after": "custom_net_total_after_wht_retention",
                "description": "Net total amount in Thai words (After WHT & Retention)",
                "translatable": 1,
            },
            {
                "fieldname": "custom_retention_note",
                "fieldtype": "Small Text",
                "label": "Retention Note",
                "insert_after": "custom_net_total_after_wht_and_retention_in_words",
                "description": "Important note about Retention deduction timing",
                "depends_on": "eval:doc.custom_subject_to_retention",
                "default": "หมายเหตุ: จำนวนเงินประกันผลงาน  จะถูกหักเมื่อชำระเงิน\\nNote: Retention amount will be deducted upon payment",
                "translatable": 1,
            },
            {
                "fieldname": "custom_retention",
                "fieldtype": "Percent",
                "label": "Retention (%)",
                "insert_after": "base_in_words",
                "description": "Retention percentage to be withheld from payment",
                "depends_on": "eval:doc.custom_subject_to_retention",
            },
            {
                "fieldname": "custom_retention_amount",
                "fieldtype": "Currency",
                "label": "Retention Amount",
                "insert_after": "custom_retention",
                "description": "Calculated retention amount",
                "depends_on": "eval:doc.custom_subject_to_retention",
            },
            {
                "fieldname": "custom_withholding_tax",
                "fieldtype": "Percent",
                "label": "Withholding Tax (%)",
                "insert_after": "custom_retention_amount",
                "description": "Withholding tax percentage",
                "depends_on": "eval:doc.subject_to_wht",
            },
            {
                "fieldname": "custom_withholding_tax_amount",
                "fieldtype": "Currency",
                "label": "Withholding Tax Amount",
                "insert_after": "custom_withholding_tax",
                "description": "Calculated withholding tax amount",
                "depends_on": "eval:doc.subject_to_wht",
            },
            {
                "fieldname": "custom_payment_amount",
                "fieldtype": "Currency",
                "label": "Payment Amount",
                "insert_after": "custom_withholding_tax_amount",
                "description": "Final payment amount after all deductions",
                "depends_on": "eval:doc.custom_subject_to_retention || doc.subject_to_wht",
            },
            {
                "fieldname": "prepared_by_signature",
                "fieldtype": "Attach Image",
                "label": "Prepared By Signature",
                "insert_after": "sales_team",
                "description": "Signature of person who prepared the invoice",
            },
            {
                "fieldname": "approved_by_signature",
                "fieldtype": "Attach Image",
                "label": "Approved By Signature",
                "insert_after": "prepared_by_signature",
                "description": "Signature of person who approved the invoice",
            },
        ]
    }

    print("Installing Sales Invoice custom fields...")
    create_custom_fields(custom_fields)
    print("Sales Invoice custom fields installed successfully!")


if __name__ == "__main__":
    install_sales_invoice_custom_fields()
