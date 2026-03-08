"""
Programmatic Custom Field Installation for Quotation
====================================================

This module provides programmatic installation of custom fields for Quotation DocType,
maintaining exact field definitions from fixtures for production environment compatibility.

Updated to exactly match fixtures/custom_field.json definitions.
"""

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import flt, cint


def migrate_wht_income_type_field(doctype):
    """
    Migrate pd_custom_wht_income_type field from Select to Link type.
    Frappe doesn't allow changing fieldtype directly, so we need to delete and recreate.
    """
    field_name = f"{doctype}-pd_custom_wht_income_type"
    if frappe.db.exists("Custom Field", field_name):
        existing_field = frappe.db.get_value("Custom Field", field_name, "fieldtype")
        if existing_field == "Select":
            # Delete old Select field to allow creating new Link field
            frappe.delete_doc("Custom Field", field_name, force=True)
            frappe.db.commit()
            print(f"  Migrated {doctype}.pd_custom_wht_income_type: Select → Link")


def install_quotation_custom_fields():
    """
    Install all custom fields for Quotation DocType programmatically

    This function creates custom fields with the exact structure
    as defined in the custom_field.json fixture file.

    Returns:
            dict: Installation status and results
    """
    try:
        print("=== Installing Quotation Custom Fields (From Fixtures) ===")

        # Define custom fields exactly matching fixtures
        custom_fields = get_quotation_custom_fields_definition()

        # Migrate pd_custom_wht_income_type from Select to Link (if exists as Select)
        migrate_wht_income_type_field("Quotation")

        # Install fields using Frappe's standard method
        create_custom_fields(custom_fields, update=True)

        # Validate installation
        validation_result = validate_quotation_fields_installation()

        print("✅ Quotation custom fields installation completed successfully")

        return {
            "success": True,
            "fields_installed": len(custom_fields["Quotation"]),
            "validation": validation_result,
        }

    except Exception as e:
        error_msg = f"Error installing Quotation custom fields: {str(e)}"
        print(f"❌ {error_msg}")
        frappe.log_error(error_msg, "Quotation Fields Installation Error")
        return {"success": False, "error": error_msg}


def get_quotation_custom_fields_definition():
    """
    Define all Quotation custom fields exactly as in fixtures

    This maintains exact field definitions and properties from custom_field.json
    to ensure consistent behavior between fixture and programmatic installation.

    Returns:
            dict: Custom fields definition for create_custom_fields()
    """

    return {
        "Quotation": [
            {
                "fieldname": "pd_custom_net_after_wht_retention_words",
                "label": "Net Total (After WHT and Retention) in Words",
                "fieldtype": "Data",
                "insert_after": "pd_custom_net_after_wht_retention",
                "description": "Net total amount in Thai words (After WHT & Retention)",
                "depends_on": "eval:doc.pd_custom_subject_to_retention",
                "translatable": 1,
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_net_after_wht_retention",
                "label": "Net Total (After WHT & Retention)",
                "fieldtype": "Currency",
                "insert_after": "pd_custom_subject_to_retention",
                "depends_on": "eval:doc.pd_custom_subject_to_retention",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_payment_amount",
                "label": "Payment Amount",
                "fieldtype": "Currency",
                "insert_after": "pd_custom_withholding_tax_amount",
                "depends_on": "eval:doc.pd_custom_subject_to_wht || doc.pd_custom_subject_to_retention",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_retention_pct",
                "label": "Retention (%)",
                "fieldtype": "Percent",
                "insert_after": "base_in_words",
                "depends_on": "eval:doc.pd_custom_subject_to_retention",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_retention_amount",
                "label": "Retention Amount",
                "fieldtype": "Currency",
                "insert_after": "pd_custom_retention_pct",
                "depends_on": "eval:doc.pd_custom_subject_to_retention",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_retention_note",
                "label": "Retention Note",
                "fieldtype": "Small Text",
                "insert_after": "pd_custom_net_after_wht_retention_words",
                "depends_on": "eval:doc.pd_custom_subject_to_retention",
                "default": "หมายเหตุ: จำนวนเงินประกันผลงาน  จะถูกหักเมื่อชำระเงิน\nNote: Retention amount will be deducted upon payment",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_subject_to_retention",
                "label": "Subject to Retention",
                "fieldtype": "Check",
                "insert_after": "pd_custom_wht_preview_cb",
                "depends_on": "eval:doc.company && doc.construction_service",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "in_list_view": 1,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_withholding_tax_pct",
                "label": "Withholding Tax (%)",
                "fieldtype": "Percent",
                "insert_after": "pd_custom_retention_amount",
                "depends_on": "eval:doc.pd_custom_subject_to_wht",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_withholding_tax_amount",
                "label": "Withholding Tax Amount",
                "fieldtype": "Currency",
                "insert_after": "pd_custom_withholding_tax_pct",
                "depends_on": "eval:doc.pd_custom_subject_to_wht",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_net_total_after_wht",
                "label": "Net Total (After WHT)",
                "fieldtype": "Currency",
                "insert_after": "pd_custom_wht_description",
                "depends_on": "eval:doc.pd_custom_subject_to_wht",
                "options": "Company:company:default_currency",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_net_total_after_wht_words",
                "label": "Net Total (After WHT) in Words",
                "fieldtype": "Data",
                "insert_after": "pd_custom_net_total_after_wht",
                "depends_on": "eval:doc.pd_custom_subject_to_wht && doc.pd_custom_net_total_after_wht",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_prepared_by_signature",
                "label": "Prepared By Signature",
                "fieldtype": "Attach Image",
                "insert_after": "sales_team",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_subject_to_wht",
                "label": "Subject to Withholding Tax",
                "fieldtype": "Check",
                "insert_after": "pd_custom_vat_treatment",
                "depends_on": "eval:doc.company && doc.thailand_service_business",
                "default": "0",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_wht_preview_section",
                "label": "Thai Ecosystem (Withholding Tax & Retention)",
                "fieldtype": "Section Break",
                "insert_after": "named_place",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 1,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_vat_treatment",
                "label": "VAT Treatment",
                "fieldtype": "Select",
                "insert_after": "pd_custom_wht_amounts_cb",
                "default": "Standard VAT",
                "options": "\nStandard VAT\nVAT Undue\nExempt from VAT\nZero-rated for Export",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "in_list_view": 1,
                "in_standard_filter": 1,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_watermark_text",
                "label": "Document Watermark",
                "fieldtype": "Select",
                "insert_after": "quotation_to",
                "default": "None",
                "options": "None\nOriginal\nCopy\nDraft\nSubmitted\nOrdered\nExpired\nDuplicate",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_wht_amounts_cb",
                "label": None,
                "fieldtype": "Column Break",
                "insert_after": "pd_custom_wht_preview_section",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_wht_description",
                "label": "WHT Description",
                "fieldtype": "Data",
                "insert_after": "pd_custom_wht_income_type",
                "depends_on": "eval:doc.pd_custom_wht_income_type",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_wht_income_type",
                "label": "WHT Income Type",
                "fieldtype": "Link",
                "insert_after": "pd_custom_subject_to_wht",
                "depends_on": "eval:doc.pd_custom_subject_to_wht",
                "options": "Thai WHT Income Type",
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_wht_note",
                "label": "WHT Note",
                "fieldtype": "Small Text",
                "insert_after": "pd_custom_net_total_after_wht_words",
                "depends_on": "eval:doc.pd_custom_wht_income_type",
                "default": "หมายเหตุ: จำนวนเงินภาษีหัก ณ ที่จ่าย จะถูกหักเมื่อชำระเงิน\nNote: Withholding tax amount will be deducted upon payment",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "pd_custom_wht_preview_cb",
                "label": None,
                "fieldtype": "Column Break",
                "insert_after": "pd_custom_wht_note",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
        ]
    }


def validate_quotation_fields_installation():
    """
    Validate that all Quotation custom fields are properly installed

    Returns:
            dict: Validation results
    """
    try:
        print("\n=== Validating Quotation Fields Installation ===")

        # Get installed fields from database
        installed_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Quotation"},
            fields=["fieldname", "fieldtype", "label", "insert_after", "depends_on"],
            order_by="idx asc, modified asc",
        )

        # Expected fields from definition
        expected_fields_def = get_quotation_custom_fields_definition()
        expected_fields = expected_fields_def["Quotation"]

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
        print(f"📊 Expected fields: {len(expected_fields)} (from fixtures)")
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
        error_msg = f"Error validating Quotation fields: {str(e)}"
        print(f"❌ {error_msg}")
        return {"validation_passed": False, "error": error_msg}


def check_quotation_fields_status():
    """
    Check current status of Quotation custom fields installation

    Returns:
            dict: Current status information
    """
    try:
        print("=== Checking Quotation Fields Status ===")

        # Get current fields
        current_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Quotation"},
            fields=["fieldname", "fieldtype", "label", "insert_after"],
            order_by="idx asc, modified asc",
        )

        # Expected fields count
        expected_def = get_quotation_custom_fields_definition()
        expected_count = len(expected_def["Quotation"])

        print(f"📊 Current fields: {len(current_fields)}")
        print(f"📊 Expected fields: {expected_count} (matching fixtures)")

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
                    f"{i:2d}. {field['fieldname']:<35} | {field['fieldtype']:<15}{insert_after}"
                )
        else:
            print("❌ No Quotation custom fields found")

        return {
            "current_count": len(current_fields),
            "expected_count": expected_count,
            "fields_installed": len(current_fields) > 0,
            "needs_installation": len(current_fields) != expected_count,
        }

    except Exception as e:
        error_msg = f"Error checking Quotation fields status: {str(e)}"
        print(f"❌ {error_msg}")
        return {"error": error_msg, "fields_installed": False}


def reinstall_quotation_custom_fields():
    """
    Reinstall all Quotation custom fields (useful for updates/fixes)

    This will update existing fields and add any missing ones.

    Returns:
            dict: Reinstallation results
    """
    try:
        print("=== Reinstalling Quotation Custom Fields ===")

        # Get current status
        status = check_quotation_fields_status()
        print(
            f"Current status: {status['current_count']}/{status['expected_count']} fields"
        )

        # Perform installation (with update=True to modify existing fields)
        result = install_quotation_custom_fields()

        if result["success"]:
            print("✅ Quotation custom fields reinstallation completed")
        else:
            print(f"❌ Reinstallation failed: {result.get('error')}")

        return result

    except Exception as e:
        error_msg = f"Error reinstalling Quotation custom fields: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}


# Convenience functions for command execution
def main():
    """Main execution function for command line usage"""
    return install_quotation_custom_fields()


if __name__ == "__main__":
    main()
