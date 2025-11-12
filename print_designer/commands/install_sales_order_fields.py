"""
Programmatic Custom Field Installation for Sales Order
=====================================================

This module provides programmatic installation of custom fields for Sales Order DocType,
maintaining exact field definitions and comprehensive validation system.

Enhanced with validation, error handling, and status checking based on Quotation pattern.
"""

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import flt, cint


def install_sales_order_custom_fields():
    """
    Install all custom fields for Sales Order DocType programmatically

    This function creates custom fields with comprehensive validation
    and error handling.

    Returns:
            dict: Installation status and results
    """
    try:
        print("=== Installing Sales Order Custom Fields (Enhanced) ===")

        # Define custom fields
        custom_fields = get_sales_order_custom_fields_definition()

        # Install fields using Frappe's standard method
        create_custom_fields(custom_fields, update=True)

        # Validate installation
        validation_result = validate_sales_order_fields_installation()

        print("✅ Sales Order custom fields installation completed successfully")

        return {
            "success": True,
            "fields_installed": len(custom_fields["Sales Order"]),
            "validation": validation_result,
        }

    except Exception as e:
        error_msg = f"Error installing Sales Order custom fields: {str(e)}"
        print(f"❌ {error_msg}")
        frappe.log_error(error_msg, "Sales Order Fields Installation Error")
        return {"success": False, "error": error_msg}


def get_sales_order_custom_fields_definition():
    """
    Define all Sales Order custom fields with enhanced structure

    Returns:
            dict: Custom fields definition for create_custom_fields()
    """

    return {
        "Sales Order": [
            {
                "fieldname": "subject_to_wht",
                "fieldtype": "Check",
                "label": "Subject to Withholding Tax",
                "insert_after": "vat_treatment",
                "description": "This sales order is for services subject to 3% withholding tax",
                "default": "0",
                "depends_on": "eval:doc.company && doc.thailand_service_business",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "net_total_after_wht",
                "fieldtype": "Currency",
                "label": "Net Total (After WHT)",
                "insert_after": "wht_description",
                "description": "Net total after adding VAT (7%) and deducting WHT",
                "depends_on": "eval:doc.subject_to_wht",
                "options": "Company:company:default_currency",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "watermark_text",
                "fieldtype": "Select",
                "label": "Document Watermark",
                "insert_after": "order_type",
                "description": "Watermark text to display on printed document",
                "options": "None\nOriginal\nCopy\nDraft\nConfirmed\nCancelled\nDuplicate",
                "default": "None",
                "allow_on_submit": 1,
                "print_hide": 1,
                "translatable": 1,
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
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
                "hidden": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "wht_amounts_column_break",
                "fieldtype": "Column Break",
                "label": None,
                "insert_after": "thai_wht_preview_section",
                "no_copy": 1,
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
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
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "wht_income_type",
                "fieldtype": "Select",
                "label": "WHT Income Type",
                "insert_after": "subject_to_wht",
                "description": "Type of income for WHT calculation",
                "depends_on": "eval:doc.subject_to_wht",
                "options": "\nprofessional_services\nrental\nservice_fees\nconstruction\nadvertising\nother_services",
                "no_copy": 0,
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "wht_description",
                "fieldtype": "Data",
                "label": "WHT Description",
                "insert_after": "wht_income_type",
                "description": "Thai description of WHT income type",
                "depends_on": "eval:doc.wht_income_type",
                "no_copy": 0,
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "net_total_after_wht_in_words",
                "fieldtype": "Data",
                "label": "Net Total (After WHT) in Words",
                "insert_after": "net_total_after_wht",
                "description": "Net total amount in Thai words",
                "depends_on": "eval:doc.subject_to_wht && doc.net_total_after_wht",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "wht_note",
                "fieldtype": "Small Text",
                "label": "WHT Note",
                "insert_after": "net_total_after_wht_in_words",
                "description": "Important note about WHT deduction timing",
                "depends_on": "eval:doc.wht_income_type",
                "default": "หมายเหตุ: จำนวนเงินภาษีหัก ณ ที่จ่าย จะถูกหักเมื่อชำระเงิน\nNote: Withholding tax amount will be deducted upon payment",
                "no_copy": 0,
                "read_only": 1,
                "translatable": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "wht_preview_column_break",
                "fieldtype": "Column Break",
                "label": None,
                "insert_after": "wht_note",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "custom_subject_to_retention",
                "fieldtype": "Check",
                "label": "Subject to Retention",
                "insert_after": "wht_preview_column_break",
                "description": "This SO is for construction subject to retention deduct.",
                "depends_on": "eval:doc.company && doc.construction_service",
                "in_list_view": 1,
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "custom_net_total_after_wht_retention",
                "fieldtype": "Currency",
                "label": "Net Total (After WHT & Retention)",
                "insert_after": "custom_subject_to_retention",
                "description": "Net total after adding VAT (7%) and deducting WHT&Retention",
                "depends_on": "eval:doc.custom_subject_to_retention",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
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
                "default": "หมายเหตุ: จำนวนเงินประกันผลงาน  จะถูกหักเมื่อชำระเงิน\nNote: Retention amount will be deducted upon payment",
                "translatable": 1,
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "custom_retention",
                "fieldtype": "Percent",
                "label": "Retention (%)",
                "insert_after": "base_in_words",
                "description": "Retention percentage to be withheld from payment",
                "depends_on": "eval:doc.custom_subject_to_retention",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "custom_retention_amount",
                "fieldtype": "Currency",
                "label": "Retention Amount",
                "insert_after": "custom_retention",
                "description": "Calculated retention amount",
                "depends_on": "eval:doc.custom_subject_to_retention",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "custom_withholding_tax",
                "fieldtype": "Percent",
                "label": "Withholding Tax (%)",
                "insert_after": "custom_retention_amount",
                "description": "Withholding tax percentage",
                "depends_on": "eval:doc.subject_to_wht",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "custom_withholding_tax_amount",
                "fieldtype": "Currency",
                "label": "Withholding Tax Amount",
                "insert_after": "custom_withholding_tax",
                "description": "Calculated withholding tax amount",
                "depends_on": "eval:doc.subject_to_wht",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "custom_payment_amount",
                "fieldtype": "Currency",
                "label": "Payment Amount",
                "insert_after": "custom_withholding_tax_amount",
                "description": "Final payment amount after all deductions",
                "depends_on": "eval:doc.subject_to_wht || doc.custom_subject_to_retention",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "section_break_o8q38",
                "fieldtype": "Section Break",
                "label": "Deposit",
                "insert_after": "payment_schedule",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "has_deposit",
                "fieldtype": "Check",
                "label": "Deposit on 1st Invoice",
                "insert_after": "section_break_o8q38",
                "description": "If checked, the 1st invoice from this order should be a deposit invoice.",
                "allow_on_submit": 1,
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "deposit_invoice",
                "fieldtype": "Data",
                "label": "Deposit Invoice",
                "insert_after": "has_deposit",
                "no_copy": 1,
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "column_break_euapx",
                "fieldtype": "Column Break",
                "label": None,
                "insert_after": "deposit_invoice",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "percent_deposit",
                "fieldtype": "Percent",
                "label": "Percent Deposit",
                "insert_after": "column_break_euapx",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "deposit_deduction_method",
                "fieldtype": "Select",
                "label": "Deposit Deduction Method",
                "insert_after": "percent_deposit",
                "description": "Deposit deduction (return of deposit) on following invoice(s).",
                "options": "Percent\nFull Amount",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "prepared_by_signature",
                "fieldtype": "Attach Image",
                "label": "Prepared By Signature",
                "insert_after": "sales_team",
                "description": "Signature of person who prepared the sales order",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "approved_by_signature",
                "fieldtype": "Attach Image",
                "label": "Approved By Signature",
                "insert_after": "prepared_by_signature",
                "description": "Signature of person who approved the sales order",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
        ]
    }


def validate_sales_order_fields_installation():
    """
    Validate that all Sales Order custom fields are properly installed

    Returns:
            dict: Validation results
    """
    try:
        print("\n=== Validating Sales Order Fields Installation ===")

        # Get installed fields from database
        installed_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Sales Order"},
            fields=["fieldname", "fieldtype", "label", "insert_after", "depends_on"],
            order_by="idx asc, modified asc",
        )

        # Expected fields from definition
        expected_fields_def = get_sales_order_custom_fields_definition()
        expected_fields = expected_fields_def["Sales Order"]

        # Create lookup for validation
        installed_lookup = {field["fieldname"]: field for field in installed_fields}
        expected_lookup = {field["fieldname"]: field for field in expected_fields}

        # Validation checks
        missing_fields = []
        field_mismatches = []

        for field_def in expected_fields:
            fieldname = field_def["fieldname"]

            if fieldname not in installed_lookup:
                missing_fields.append(fieldname)
            else:
                # Check key properties match
                installed_field = installed_lookup[fieldname]

                # Compare essential properties
                essential_props = ["fieldtype", "label", "insert_after"]
                for prop in essential_props:
                    expected_val = field_def.get(prop)
                    installed_val = installed_field.get(prop)

                    if expected_val and expected_val != installed_val:
                        field_mismatches.append(
                            {
                                "fieldname": fieldname,
                                "property": prop,
                                "expected": expected_val,
                                "installed": installed_val,
                            }
                        )

        # Report results
        print(f"📊 Expected fields: {len(expected_fields)} (from definition)")
        print(f"📊 Installed fields: {len(installed_fields)}")
        print(f"📊 Missing fields: {len(missing_fields)}")
        print(f"📊 Field mismatches: {len(field_mismatches)}")

        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")

        if field_mismatches:
            print(f"⚠️  Field mismatches found:")
            for mismatch in field_mismatches:
                print(
                    f"   {mismatch['fieldname']}.{mismatch['property']}: expected='{mismatch['expected']}', installed='{mismatch['installed']}'"
                )

        if not missing_fields and not field_mismatches:
            print("✅ All fields validated successfully!")

        return {
            "expected_count": len(expected_fields),
            "installed_count": len(installed_fields),
            "missing_fields": missing_fields,
            "field_mismatches": field_mismatches,
            "validation_passed": len(missing_fields) == 0
            and len(field_mismatches) == 0,
        }

    except Exception as e:
        error_msg = f"Error validating Sales Order fields: {str(e)}"
        print(f"❌ {error_msg}")
        return {"validation_passed": False, "error": error_msg}


def check_sales_order_fields_status():
    """
    Check current status of Sales Order custom fields installation

    Returns:
            dict: Current status information
    """
    try:
        print("=== Checking Sales Order Fields Status ===")

        # Get current fields
        current_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Sales Order"},
            fields=["fieldname", "fieldtype", "label", "insert_after"],
            order_by="idx asc, modified asc",
        )

        # Expected fields count
        expected_def = get_sales_order_custom_fields_definition()
        expected_count = len(expected_def["Sales Order"])

        print(f"📊 Current fields: {len(current_fields)}")
        print(f"📊 Expected fields: {expected_count} (from definition)")

        # Show field summary
        if current_fields:
            print("\n📋 Current Field Order:")
            for i, field in enumerate(current_fields, 1):
                insert_after = (
                    f" | after: {field['insert_after']}"
                    if field["insert_after"]
                    else ""
                )
                print(
                    f"{i:2d}. {field['fieldname']:<40} | {field['fieldtype']:<15}{insert_after}"
                )
        else:
            print("❌ No Sales Order custom fields found")

        return {
            "current_count": len(current_fields),
            "expected_count": expected_count,
            "fields_installed": len(current_fields) > 0,
            "needs_installation": len(current_fields) != expected_count,
        }

    except Exception as e:
        error_msg = f"Error checking Sales Order fields status: {str(e)}"
        print(f"❌ {error_msg}")
        return {"error": error_msg, "fields_installed": False}


def reinstall_sales_order_custom_fields():
    """
    Reinstall all Sales Order custom fields (useful for updates/fixes)

    This will update existing fields and add any missing ones.

    Returns:
            dict: Reinstallation results
    """
    try:
        print("=== Reinstalling Sales Order Custom Fields ===")

        # Get current status
        status = check_sales_order_fields_status()
        print(
            f"Current status: {status['current_count']}/{status['expected_count']} fields"
        )

        # Perform installation (with update=True to modify existing fields)
        result = install_sales_order_custom_fields()

        if result["success"]:
            print("✅ Sales Order custom fields reinstallation completed")
        else:
            print(f"❌ Reinstallation failed: {result.get('error')}")

        return result

    except Exception as e:
        error_msg = f"Error reinstalling Sales Order custom fields: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}


# Convenience functions for command execution
def main():
    """Main execution function for command line usage"""
    return install_sales_order_custom_fields()


if __name__ == "__main__":
    main()
