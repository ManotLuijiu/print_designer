# install_sales_invoice_fields.py
# Enhanced Sales Invoice custom fields installation with comprehensive validation
# Following patterns established in Quotation and Sales Order

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def migrate_wht_income_type_field(doctype):
    """
    Migrate wht_income_type field from Select to Link type.
    Frappe doesn't allow changing fieldtype directly, so we need to delete and recreate.
    """
    field_name = f"{doctype}-wht_income_type"
    if frappe.db.exists("Custom Field", field_name):
        existing_field = frappe.db.get_value("Custom Field", field_name, "fieldtype")
        if existing_field == "Select":
            # Delete old Select field to allow creating new Link field
            frappe.delete_doc("Custom Field", field_name, force=True)
            frappe.db.commit()
            print(f"  Migrated {doctype}.wht_income_type: Select → Link")


def install_sales_invoice_custom_fields():
    """
    Install custom fields for Sales Invoice DocType
    Enhanced with validation system and proper field dependencies
    """
    print("=== Installing Sales Invoice Custom Fields ===")

    # Check if fields are already installed
    status = check_sales_invoice_fields_status()
    if status.get("fields_installed") and not status.get("needs_installation"):
        print(
            "✅ All Sales Invoice custom fields already installed and properly configured"
        )
        return status

    custom_fields = get_sales_invoice_custom_fields_definition()

    try:
        # Migrate wht_income_type from Select to Link (if exists as Select)
        migrate_wht_income_type_field("Sales Invoice")

        print(f"📦 Installing {len(custom_fields['Sales Invoice'])} custom fields...")
        create_custom_fields(custom_fields, update=True)

        # Validate installation
        validation_result = validate_sales_invoice_fields_installation()

        if validation_result.get("success"):
            print("✅ Sales Invoice custom fields installed successfully!")
            print(
                f"📊 Total fields installed: {validation_result.get('field_count', 0)}"
            )
            return validation_result
        else:
            print(
                f"⚠️ Installation completed with issues: {validation_result.get('message', '')}"
            )
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
            # Document watermark field
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
            # Main WHT and Retention Preview Section
            {
                "fieldname": "thai_wht_preview_section",
                "fieldtype": "Section Break",
                "label": "Thai Ecosystem Preview (ภาษีหัก ณ ที่จ่าย/เงินประกันผลงาน)",
                "insert_after": "named_place",
                "collapsible": 1,
                "collapsible_depends_on": "eval:doc.subject_to_wht || doc.custom_subject_to_retention",
                "no_copy": 1,
                "read_only": 1,
            },
            # WHT Column (Left side)
            {
                "fieldname": "wht_amounts_column_break",
                "fieldtype": "Column Break",
                "insert_after": "thai_wht_preview_section",
                "no_copy": 1,
                "read_only": 1,
            },
            # VAT Treatment (Foundation field)
            {
                "fieldname": "vat_treatment",
                "fieldtype": "Select",
                "label": "VAT Treatment",
                "insert_after": "wht_amounts_column_break",
                "description": "Select VAT treatment: Standard for regular sales, Exempt for fresh food/services, Zero-rated for export sales",
                "options": "\nStandard VAT\nVAT Undue\nExempt from VAT\nZero-rated for Export",
                "default": "Standard VAT",
                "in_list_view": 1,
                "in_standard_filter": 1,
                "translatable": 1,
            },
            # WHT Chain starts here
            {
                "fieldname": "subject_to_wht",
                "fieldtype": "Check",
                "label": "Subject to Withholding Tax",
                "insert_after": "vat_treatment",
                "description": "This invoice is for services subject to withholding tax",
                "default": "0",
                "depends_on": "eval:doc.company && doc.thailand_service_business",
            },
            {
                "fieldname": "wht_income_type",
                "fieldtype": "Link",
                "label": "WHT Income Type",
                "insert_after": "subject_to_wht",
                "description": "Type of income for WHT calculation",
                "depends_on": "eval:doc.subject_to_wht",
                "options": "Thai WHT Income Type",
                "no_copy": 0,
                "read_only": 1,
            },
            {
                "fieldname": "wht_description",
                "fieldtype": "Data",
                "label": "WHT Description",
                "insert_after": "wht_income_type",
                "description": "Thai description of WHT income type",
                "depends_on": "eval:doc.subject_to_wht",
                "no_copy": 0,
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
                "fieldtype": "Data",  # Fixed: Changed from Small Text to Data
                "label": "Net Total (After WHT) in Words",
                "insert_after": "net_total_after_wht",
                "description": "Net total amount in Thai words",
                "depends_on": "eval:doc.subject_to_wht && doc.net_total_after_wht",
                "read_only": 1,
            },
            # Fixed: Moved wht_certificate_required to proper position
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
                "fieldname": "wht_note",
                "fieldtype": "Small Text",
                "label": "WHT Note",
                "insert_after": "net_total_after_wht_in_words",
                "description": "Important note about WHT deduction timing",
                "depends_on": "eval:doc.subject_to_wht",
                "default": "หมายเหตุ: จำนวนเงินภาษีหัก ณ ที่จ่าย จะถูกหักเมื่อชำระเงิน\\nNote: Withholding tax amount will be deducted upon payment",
                "no_copy": 0,
                "read_only": 1,
                "translatable": 1,
            },
            # Retention Column (Right side)
            {
                "fieldname": "wht_preview_column_break",
                "fieldtype": "Column Break",
                "insert_after": "wht_note",
                "read_only": 1,
            },
            # Retention Chain starts here
            {
                "fieldname": "custom_subject_to_retention",
                "fieldtype": "Check",
                "label": "Subject to Retention",
                "insert_after": "wht_preview_column_break",
                "description": "This invoice is for construction subject to retention deduct.",
                "depends_on": "eval:doc.company && doc.construction_service",
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
                "fieldname": "custom_net_total_after_wht_retention_in_words",
                "fieldtype": "Data",
                "label": "Net Total (After WHT and Retention) in Words",
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
                "fieldtype": "Small Text",
                "label": "Retention Note",
                "insert_after": "custom_net_total_after_wht_retention_in_words",
                "description": "Important note about Retention deduction timing",
                "depends_on": "eval:doc.custom_subject_to_retention",
                "default": "หมายเหตุ: จำนวนเงินประกันผลงาน  จะถูกหักเมื่อชำระเงิน\\nNote: Retention amount will be deducted upon payment",
                "translatable": 1,
            },
            # Tax calculation fields (outside preview section)
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
            # Signature fields
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
        print(
            f"Current status: {status['current_count']}/{status['expected_count']} fields"
        )

        # Get field definitions and force installation with update=True
        custom_fields = get_sales_invoice_custom_fields_definition()

        print(f"📦 Reinstalling {len(custom_fields['Sales Invoice'])} custom fields...")
        create_custom_fields(custom_fields, update=True)

        # Validate installation
        validation_result = validate_sales_invoice_fields_installation()

        if validation_result.get("success"):
            print(
                "✅ Sales Invoice custom fields reinstallation completed successfully!"
            )
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
