# install_sales_invoice_fields.py
# Enhanced Sales Invoice custom fields installation with comprehensive validation
# Following patterns established in Quotation and Sales Order
#
# =============================================================================
# APPROACH A: FIELD LIFECYCLE CLEANUP (For Future Custom Fields)
# =============================================================================
#
# CANONICAL PREFIX: pd_custom_ (e.g., pd_custom_wht_income_type)
#
# Orphan prefixes to clean up when migrating/renaming fields:
#   - thai_*       (e.g., thai_wht_preview_section, thai_cash_receipt)
#   - custom_*     (e.g., custom_net_total_after_wht_retention, custom_retention_*)
#   - wht_*        (e.g., wht_income_type, wht_description)
#   - No prefix    (e.g., vat_treatment, subject_to_wht, net_total_after_wht)
#
# Example cleanup function for future use:
#
# def cleanup_orphan_fields(doctype):
#     ORPHAN_PREFIXES = ['thai_', 'custom_', 'wht_']
#     ORPHAN_SPECIFIC = ['vat_treatment', 'subject_to_wht', 'net_total_after_wht']
#
#     existing = frappe.get_all("Custom Field", filters={"dt": doctype}, pluck="fieldname")
#
#     for prefix in ORPHAN_PREFIXES:
#         for fn in [f for f in existing if f.startswith(prefix)]:
#             frappe.delete_doc("Custom Field", fn, force=True)
#             print(f"  Deleted orphan: {fn}")
#
#     for fn in ORPHAN_SPECIFIC:
#         if fn in existing:
#             frappe.delete_doc("Custom Field", fn, force=True)
#             print(f"  Deleted orphan: {fn}")
#
#     frappe.db.commit()
#
# Usage in install function:
#     cleanup_orphan_fields("Sales Invoice")  # Call FIRST before create_custom_fields
#
# Full orphan list (deleted 2026-07-15):
#   thai_wht_preview_section, thai_cash_receipt, thai_compliance_section,
#   thai_customer_branch_code, thai_customer_tax_id, thai_export_eligible,
#   thai_invoice_type, thai_tax_information_section, thai_tax_invoice_date,
#   thai_tax_invoice_number, thai_vat_eligible,
#   custom_subject_to_retention, custom_net_total_after_wht_retention,
#   custom_net_total_after_wht_retention_in_words, custom_net_total_after_wht_and_retention_in_words,
#   custom_retention_note, custom_retention, custom_retention_amount,
#   custom_withholding_tax, custom_withholding_tax_amount, custom_payment_amount,
#   custom_invoice_qr_section, custom_show_qr_on_print, custom_invoice_qr_code,
#   custom_invoice_qr_image, custom_invoice_qr_url, custom_invoice_qr_column_break,
#   custom_invoice_qr_generated_on, custom_invoice_qr_data_version,
#   pd_custom_net_total_after_wht, pd_custom_approved_by_signature,
#   pd_custom_prepared_by_signature, pd_custom_watermark_text,
#   pd_custom_net_total_after_wht_words,
#   wht_amounts_column_break, vat_treatment, subject_to_wht, wht_income_type,
#   wht_description, wht_certificate_required, net_total_after_wht,
#   net_total_after_wht_in_words, wht_note, wht_preview_column_break
# =============================================================================

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def migrate_wht_income_type_field(doctype):
    """
    DEPRECATED: pd_custom_wht_income_type is no longer used on Sales Invoice header.
    WHT Income Type is now per-item using ERPNext's native tax_withholding_category field.
    This function is kept for historical reference.
    """
    pass


def install_sales_invoice_custom_fields():
    """
    Install custom fields for Sales Invoice DocType
    Enhanced with validation system and proper field dependencies
    """
    print("=== Installing Sales Invoice Custom Fields ===")

    # Check if fields are already installed
    status = check_sales_invoice_fields_status()
    if status.get("fields_installed") and not status.get("needs_installation"):
        print("✅ All Sales Invoice custom fields already installed and properly configured")
        return status

    custom_fields = get_sales_invoice_custom_fields_definition()

    try:
        print(f"📦 Installing {len(custom_fields['Sales Invoice'])} custom fields...")
        create_custom_fields(custom_fields, update=True)

        # Validate installation
        validation_result = validate_sales_invoice_fields_installation()

        if validation_result.get("success"):
            print("✅ Sales Invoice custom fields installed successfully!")
            print(f"📊 Total fields installed: {validation_result.get('field_count', 0)}")
            return validation_result
        else:
            print(f"⚠️ Installation completed with issues: {validation_result.get('message', '')}")
            return validation_result

    except Exception as e:
        error_msg = f"❌ Error installing Sales Invoice custom fields: {str(e)}"
        print(error_msg)
        return {"success": False, "error": error_msg}


def get_sales_invoice_custom_fields_definition():
    """
    Define all Sales Invoice custom fields with proper insertion chain
    Fixed circular dependency and field type issues
    """
    return {
        "Sales Invoice": [
            # Thai Compliance Tab - placed after title field
            {
                "fieldname": "pd_custom_thai_compliance_tab",
                "fieldtype": "Tab Break",
                "label": "Thai Tax Compliance",
                "insert_after": "loyalty_redemption_cost_center",
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
            },
            # Main WHT and Retention Preview Section
            {
                "fieldname": "pd_custom_wht_section",
                "fieldtype": "Section Break",
                "label": "Withholding Tax & Retention",
                "insert_after": "pd_custom_thai_compliance_tab",
                "no_copy": 1,
                "read_only": 1,
            },
            # WHT Column (Left side)
            {
                "fieldname": "pd_custom_wht_amounts_cb",
                "fieldtype": "Column Break",
                "insert_after": "pd_custom_wht_section",
                "no_copy": 1,
                "read_only": 1,
            },
            {
                "fieldname": "pd_custom_company_thailand_service_business",
                "fieldtype": "Check",
                "label": "Company Thailand Service Business",
                "fetch_from": "company.thailand_service_business",
                "insert_after": "pd_custom_wht_amounts_cb",
                "hidden": 0,
                "read_only": 1,
                "no_copy": 1,
            },
            # WHT Chain starts here
            {
                "fieldname": "pd_custom_wht_certificate_required",
                "fieldtype": "Check",
                "label": "WHT Certificate Required",
                "insert_after": "pd_custom_company_thailand_service_business",
                "description": "Customer will provide withholding tax certificate",
                "default": "1",
            },
            {
                "fieldname": "pd_custom_net_total_after_wht",
                "fieldtype": "Currency",
                "label": "Net Total (After WHT)",
                "insert_after": "pd_custom_wht_certificate_required",
                "description": "Net total after adding VAT (7%) and deducting WHT",
                "options": "Company:company:default_currency",
                "read_only": 1,
            },
            {
                "fieldname": "pd_custom_net_total_after_wht_words",
                "fieldtype": "Data",
                "label": "Net Total (After WHT) in Words",
                "insert_after": "pd_custom_net_total_after_wht",
                "description": "Net total amount in Thai words",
                "read_only": 1,
            },
            {
                "fieldname": "pd_custom_wht_note",
                "fieldtype": "Small Text",
                "label": "WHT Note",
                "insert_after": "pd_custom_net_total_after_wht_words",
                "description": "Important note about WHT deduction timing",
                "default": "Note: Withholding tax amount will be deducted upon payment",
                "no_copy": 0,
                "read_only": 1,
                "translatable": 1,
            },
            # Retention Column (Right side)
            {
                "fieldname": "pd_custom_wht_preview_cb",
                "fieldtype": "Column Break",
                "insert_after": "pd_custom_wht_note",
                "read_only": 1,
            },
            # Retention Chain starts here
            {
                "fieldname": "pd_custom_company_construction_service",
                "fieldtype": "Check",
                "label": "Company Construction Service",
                "fetch_from": "company.construction_service",
                "insert_after": "pd_custom_wht_preview_cb",
                "hidden": 0,
                "read_only": 1,
                "no_copy": 1,
            },
            {
                "fieldname": "pd_custom_subject_to_retention",
                "fieldtype": "Check",
                "label": "Subject to Retention",
                "insert_after": "pd_custom_company_construction_service",
                "description": "This invoice is for construction subject to retention deduct.",
            },
            {
                "fieldname": "pd_custom_net_after_wht_retention",
                "fieldtype": "Currency",
                "label": "Net Total (After WHT & Retention)",
                "insert_after": "pd_custom_subject_to_retention",
                "description": "Net total after adding VAT (7%) and deducting WHT&Retention",
            },
            {
                "fieldname": "pd_custom_net_after_wht_retention_words",
                "fieldtype": "Data",
                "label": "Net Total (After WHT and Retention) in Words",
                "insert_after": "pd_custom_net_after_wht_retention",
                "description": "Net total amount in Thai words (After WHT & Retention)",
                "translatable": 1,
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_retention_note",
                "fieldtype": "Small Text",
                "label": "Retention Note",
                "insert_after": "pd_custom_net_after_wht_retention_words",
                "description": "Important note about Retention deduction timing",
                "default": "หมายเหตุ: จำนวนเงินประกันผลงาน  จะถูกหักเมื่อชำระเงิน\\nNote: Retention amount will be deducted upon payment",
                "translatable": 1,
            },
            # Tax calculation fields (outside preview section)
            {
                "fieldname": "pd_custom_retention_pct",
                "fieldtype": "Percent",
                "label": "Retention (%)",
                "insert_after": "base_in_words",
                "description": "Retention percentage to be withheld from payment",
            },
            {
                "fieldname": "pd_custom_retention_amount",
                "fieldtype": "Currency",
                "label": "Retention Amount",
                "insert_after": "pd_custom_retention_pct",
                "description": "Calculated retention amount",
            },
            {
                "fieldname": "pd_custom_withholding_tax_pct",
                "fieldtype": "Percent",
                "label": "Withholding Tax (%)",
                "insert_after": "pd_custom_retention_amount",
                "description": "Withholding tax percentage",
            },
            {
                "fieldname": "pd_custom_withholding_tax_amount",
                "fieldtype": "Currency",
                "label": "Withholding Tax Amount",
                "insert_after": "pd_custom_withholding_tax_pct",
                "description": "Calculated withholding tax amount",
            },
            {
                "fieldname": "pd_custom_payment_amount",
                "fieldtype": "Currency",
                "label": "Payment Amount",
                "insert_after": "pd_custom_withholding_tax_amount",
                "description": "Final payment amount after all deductions",
            },
            # Signature fields
            {
                "fieldname": "pd_custom_prepared_by_signature",
                "fieldtype": "Attach Image",
                "label": "Prepared By Signature",
                "insert_after": "sales_team",
                "description": "Signature of person who prepared the invoice",
            },
            {
                "fieldname": "pd_custom_approved_by_signature",
                "fieldtype": "Attach Image",
                "label": "Approved By Signature",
                "insert_after": "pd_custom_prepared_by_signature",
                "description": "Signature of person who approved the invoice",
            },
            # =============================================
            # Invoice QR Code Fields (Thai e-Tax Format)
            # For B2B document exchange - scan to import
            # =============================================
            {
                "fieldname": "pd_custom_qr_section",
                "fieldtype": "Section Break",
                "label": "Invoice QR Code",
                "insert_after": "language",
                "collapsible": 1,
            },
            {
                "fieldname": "pd_custom_show_qr_on_print",
                "fieldtype": "Check",
                "label": "Show QR on Print",
                "insert_after": "pd_custom_qr_section",
                "default": "1",
                "description": "Enable QR code display on printed invoices",
            },
            {
                "fieldname": "pd_custom_qr_code",
                "fieldtype": "Long Text",
                "label": "Invoice QR Code",
                "insert_after": "pd_custom_show_qr_on_print",
                "read_only": 1,
                "hidden": 1,
                "description": "Base64 encoded PNG QR code image (internal use)",
            },
            {
                "fieldname": "pd_custom_qr_image",
                "fieldtype": "Long Text",
                "label": "Invoice QR Image",
                "insert_after": "pd_custom_qr_code",
                "read_only": 1,
                "hidden": 0,
                "description": "QR code image for Print Designer (drag & drop)",
            },
            {
                "fieldname": "pd_custom_qr_url",
                "fieldtype": "Data",
                "label": "Invoice QR URL",
                "insert_after": "pd_custom_qr_image",
                "read_only": 1,
                "hidden": 1,
                "description": "Verification URL for this invoice",
            },
            {
                "fieldname": "pd_custom_qr_cb",
                "fieldtype": "Column Break",
                "label": "",
                "insert_after": "pd_custom_qr_url",
            },
            {
                "fieldname": "pd_custom_qr_generated_on",
                "fieldtype": "Datetime",
                "label": "QR Generated On",
                "insert_after": "pd_custom_qr_cb",
                "read_only": 1,
            },
            {
                "fieldname": "pd_custom_qr_data_version",
                "fieldtype": "Data",
                "label": "QR Data Version",
                "insert_after": "pd_custom_qr_generated_on",
                "read_only": 1,
                "default": "1.0",
            },
            # Document watermark field
            {
                "fieldname": "pd_custom_watermark_text",
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
        ]
    }


def check_sales_invoice_fields_status():
    """
    Check current status of Sales Invoice custom fields
    Returns comprehensive status information
    """
    try:
        current_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Sales Invoice"},
            fields=["fieldname", "fieldtype", "insert_after", "label"],
        )

        expected_fields = get_sales_invoice_custom_fields_definition()["Sales Invoice"]

        print(f"📊 Current fields: {len(current_fields)}")
        print(f"📊 Expected fields: {len(expected_fields)} (from definition)")

        return {
            "current_count": len(current_fields),
            "expected_count": len(expected_fields),
            "fields_installed": len(current_fields) >= len(expected_fields),
            "needs_installation": len(current_fields) < len(expected_fields),
        }

    except Exception as e:
        return {
            "error": str(e),
            "current_count": 0,
            "expected_count": 0,
            "fields_installed": False,
            "needs_installation": True,
        }


def validate_sales_invoice_fields_installation():
    """
    Validate that all Sales Invoice custom fields were installed correctly
    """
    try:
        # Get all current custom fields for Sales Invoice
        current_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Sales Invoice"},
            fields=["fieldname", "fieldtype", "insert_after", "label"],
            order_by="idx",
        )

        expected_fields = get_sales_invoice_custom_fields_definition()["Sales Invoice"]

        print("\n📋 Current Field Order:")
        for i, field in enumerate(current_fields, 1):
            print(
                f"{i:2d}. {field.fieldname:<35} | {field.fieldtype:<15} | after: {field.insert_after or 'None'}"
            )

        return {
            "success": True,
            "field_count": len(current_fields),
            "expected_count": len(expected_fields),
            "validation_passed": len(current_fields) >= len(expected_fields),
        }

    except Exception as e:
        return {"success": False, "error": str(e), "field_count": 0}


def reinstall_sales_invoice_custom_fields():
    """
    Reinstall all Sales Invoice custom fields (useful for updates/fixes)

    This will update existing fields and add any missing ones.
    Forces update even if fields already exist.

    Returns:
        dict: Reinstallation results
    """
    try:
        print("=== Reinstalling Sales Invoice Custom Fields ===")

        # Get current status
        status = check_sales_invoice_fields_status()
        print(f"Current status: {status['current_count']}/{status['expected_count']} fields")

        # Get field definitions and force installation with update=True
        custom_fields = get_sales_invoice_custom_fields_definition()

        print(f"📦 Reinstalling {len(custom_fields['Sales Invoice'])} custom fields...")
        create_custom_fields(custom_fields, update=True)

        # Validate installation
        validation_result = validate_sales_invoice_fields_installation()

        if validation_result.get("success"):
            print("✅ Sales Invoice custom fields reinstallation completed successfully!")
            print(f"📊 Total fields: {validation_result.get('field_count', 0)}")
            return {
                "success": True,
                "fields_installed": validation_result.get("field_count", 0),
                "validation": validation_result,
            }
        else:
            print(
                f"⚠️ Reinstallation completed with issues: {validation_result.get('message', '')}"
            )
            return {
                "success": False,
                "error": validation_result.get("message", "Unknown validation error"),
                "validation": validation_result,
            }

    except Exception as e:
        error_msg = f"Error reinstalling Sales Invoice custom fields: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}


if __name__ == "__main__":
    install_sales_invoice_custom_fields()
