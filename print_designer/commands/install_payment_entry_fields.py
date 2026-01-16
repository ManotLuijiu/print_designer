"""
Payment Entry Custom Fields Installation for Thai Tax Compliance
================================================================

This module provides programmatic installation of custom fields for Payment Entry DocType,
implementing Thai tax preview section based on Sales Invoice field structure.

Enhanced with validation, error handling, and comprehensive Thai tax integration.
"""

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import cint, flt


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


def install_payment_entry_custom_fields():
    """
    Install all custom fields for Payment Entry DocType programmatically
    Based on Sales Invoice Thai tax structure for accounting flow consistency

    Returns:
        dict: Installation status and results
    """
    try:
        print("=== Installing Payment Entry Custom Fields (Thai Tax Compliance) ===")

        # Define custom fields
        custom_fields = get_payment_entry_custom_fields_definition()

        # Migrate wht_income_type from Select to Link (if exists as Select)
        migrate_wht_income_type_field("Payment Entry")

        # Install fields using Frappe's standard method
        create_custom_fields(custom_fields, update=True)

        # Force remove depends_on conditions that might not be updated by create_custom_fields
        force_remove_depends_on_conditions()

        # Validate installation
        validation_result = validate_payment_entry_fields_installation()

        print("✅ Payment Entry custom fields installation completed successfully")

        return {
            "success": True,
            "fields_installed": len(custom_fields["Payment Entry"]),
            "validation": validation_result,
        }

    except Exception as e:
        error_msg = f"Error installing Payment Entry custom fields: {str(e)}"
        print(f"❌ {error_msg}")
        frappe.log_error(error_msg, "Payment Entry Fields Installation Error")
        return {"success": False, "error": error_msg}


def get_payment_entry_custom_fields_definition():
    """
    Define all Payment Entry custom fields based on Sales Invoice structure
    Implements thai_wht_preview_section after references field

    Returns:
        dict: Custom fields definition for create_custom_fields()
    """

    return {
        "Payment Entry": [
            # Main Thai WHT and Retention Preview Section
            {
                "fieldname": "thai_wht_preview_section",
                "fieldtype": "Section Break",
                "label": "Thai Ecosystem Preview (ภาษีหัก ณ ที่จ่าย/เงินประกันผลงาน)",
                "insert_after": "references",
                "collapsible": 1,
                "collapsible_depends_on": "eval:doc.subject_to_wht || doc.custom_subject_to_retention",
                "no_copy": 1,
                "read_only": 1,
                "hidden": 0,
                "length": 0,
                "bold": 0,
            },
            # Left Column - WHT (Withholding Tax) Fields (matches Sales Invoice structure)
            {
                "fieldname": "wht_amounts_column_break",
                "fieldtype": "Column Break",
                "insert_after": "thai_wht_preview_section",
                "no_copy": 1,
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            # VAT Treatment (Foundation field - matches Sales Invoice exactly)
            {
                "fieldname": "vat_treatment",
                "fieldtype": "Select",
                "label": "VAT Treatment",
                "insert_after": "wht_amounts_column_break",
                "description": "VAT treatment from invoices in this payment",
                "options": "\nStandard VAT\nVAT Undue\nExempt from VAT\nZero-rated for Export",
                "read_only": 1,
                "in_list_view": 1,
                "in_standard_filter": 1,
                "translatable": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            # WHT Chain (matches Sales Invoice exactly)
            {
                "fieldname": "subject_to_wht",
                "fieldtype": "Check",
                "label": "Subject to Withholding Tax",
                "insert_after": "vat_treatment",
                "description": "This payment includes invoices subject to withholding tax",
                "default": "0",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "wht_income_type",
                "fieldtype": "Link",
                "label": "WHT Income Type",
                "insert_after": "subject_to_wht",
                "description": "Type of income for WHT calculation",
                "options": "Thai WHT Income Type",
                "no_copy": 0,
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "wht_description",
                "fieldtype": "Data",
                "label": "WHT Description",
                "insert_after": "custom_withholding_tax_amount",
                "description": "Thai description of WHT income type",
                "no_copy": 0,
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "wht_certificate_required",
                "fieldtype": "Check",
                "label": "WHT Certificate Required",
                "insert_after": "wht_description",
                "description": "Customer will provide withholding tax certificate",
                "default": "1",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "net_total_after_wht",
                "fieldtype": "Currency",
                "label": "Net Total (After WHT)",
                "insert_after": "custom_withholding_tax_amount",
                "description": "Net total after deducting WHT",
                "options": "Company:company:default_currency",
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
                "read_only": 1,
                "translatable": 1,
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
                "default": "หมายเหตุ: จำนวนเงินภาษีหัก ณ ที่จ่าย จะถูกหักในการชำระเงินครั้งนี้\nNote: Withholding tax amount will be deducted in this payment",
                "no_copy": 0,
                "read_only": 1,
                "translatable": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            # Right Column - Retention Fields (matches Sales Invoice exactly)
            {
                "fieldname": "wht_preview_column_break",
                "fieldtype": "Column Break",
                "insert_after": "wht_note",
                "read_only": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            # Retention Chain (matches Sales Invoice exactly)
            {
                "fieldname": "custom_subject_to_retention",
                "fieldtype": "Check",
                "label": "Subject to Retention",
                "insert_after": "wht_preview_column_break",
                "description": "This payment includes invoices subject to retention deduction",
                "read_only": 1,
                "no_copy": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            {
                "fieldname": "custom_net_total_after_wht_retention",
                "fieldtype": "Currency",
                "label": "Net Total (After WHT & Retention)",
                "insert_after": "custom_retention_amount",
                "description": "Net total after deducting WHT and retention",
                "options": "Company:company:default_currency",
                "read_only": 1,
                "no_copy": 1,
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
                "translatable": 1,
                "read_only": 1,
                "no_copy": 1,
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
                "description": "Important note about retention deduction timing",
                "default": "หมายเหตุ: จำนวนเงินประกันผลงาน จะถูกหักในการชำระเงินครั้งนี้\nNote: Retention amount will be deducted in this payment",
                "translatable": 1,
                "read_only": 1,
                "no_copy": 1,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
            # Insert at Thai Ecosystem Preview (addon)
            {
                "fieldname": "custom_retention",
                "label": "Retention (%)",
                "fieldtype": "Percent",
                "insert_after": "custom_subject_to_retention",
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
                "insert_after": "wht_income_type",
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
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            },
        ]
    }


def force_remove_depends_on_conditions():
    """
    Force remove depends_on conditions from specific Payment Entry custom fields.

    This function ensures that fields remain visible even if create_custom_fields()
    doesn't properly update existing depends_on conditions.
    """
    try:
        print("🔧 Force removing depends_on conditions for field visibility...")

        # Fields that should NOT have depends_on conditions
        fields_to_fix = [
            "wht_income_type",
            "wht_description",
            "wht_certificate_required",
            "net_total_after_wht",
            "net_total_after_wht_in_words",
            "wht_note",
        ]

        updated_count = 0
        for fieldname in fields_to_fix:
            try:
                # Get the Custom Field record
                custom_field_name = frappe.db.get_value(
                    "Custom Field", {"dt": "Payment Entry", "fieldname": fieldname}, "name"
                )

                if custom_field_name:
                    # Check if it has a depends_on condition
                    current_depends_on = frappe.db.get_value(
                        "Custom Field", custom_field_name, "depends_on"
                    )

                    if current_depends_on:
                        # Force remove the depends_on condition
                        frappe.db.set_value("Custom Field", custom_field_name, "depends_on", "")
                        updated_count += 1
                        print(f"   ✅ Cleared depends_on for {fieldname}")
                    else:
                        print(f"   ✓ {fieldname} already clear")
                else:
                    print(f"   ⚠️ {fieldname} custom field not found")

            except Exception as e:
                print(f"   ❌ Error processing {fieldname}: {str(e)}")

        if updated_count > 0:
            frappe.db.commit()
            print(f"✅ Cleared depends_on conditions for {updated_count} fields")
        else:
            print("✓ No depends_on conditions needed clearing")

    except Exception as e:
        print(f"❌ Error in force_remove_depends_on_conditions: {str(e)}")


def validate_payment_entry_fields_installation():
    """
    Validate that all Payment Entry custom fields are properly installed

    Returns:
        dict: Validation results
    """
    try:
        print("\n=== Validating Payment Entry Fields Installation ===")

        # Get installed fields from database
        installed_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Payment Entry"},
            fields=["fieldname", "fieldtype", "label", "insert_after", "depends_on"],
            order_by="idx asc, modified asc",
        )

        # Expected fields from definition
        expected_fields_def = get_payment_entry_custom_fields_definition()
        expected_fields = expected_fields_def["Payment Entry"]

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
            "validation_passed": len(missing_fields) == 0 and len(field_mismatches) == 0,
        }

    except Exception as e:
        error_msg = f"Error validating Payment Entry fields: {str(e)}"
        print(f"❌ {error_msg}")
        return {"validation_passed": False, "error": error_msg}


def check_payment_entry_fields_status():
    """
    Check current status of Payment Entry custom fields installation

    Returns:
        dict: Current status information
    """
    try:
        print("=== Checking Payment Entry Fields Status ===")

        # Get current fields
        current_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Payment Entry"},
            fields=["fieldname", "fieldtype", "label", "insert_after"],
            order_by="idx asc, modified asc",
        )

        # Expected fields count
        expected_def = get_payment_entry_custom_fields_definition()
        expected_count = len(expected_def["Payment Entry"])

        print(f"📊 Current fields: {len(current_fields)}")
        print(f"📊 Expected fields: {expected_count} (from definition)")

        # Show field summary
        if current_fields:
            print("\n📋 Current Field Order:")
            for i, field in enumerate(current_fields, 1):
                insert_after = (
                    f" | after: {field['insert_after']}" if field["insert_after"] else ""
                )
                print(f"{i:2d}. {field['fieldname']:<45} | {field['fieldtype']:<15}{insert_after}")
        else:
            print("❌ No Payment Entry custom fields found")

        return {
            "current_count": len(current_fields),
            "expected_count": expected_count,
            "fields_installed": len(current_fields) > 0,
            "needs_installation": len(current_fields) != expected_count,
        }

    except Exception as e:
        error_msg = f"Error checking Payment Entry fields status: {str(e)}"
        print(f"❌ {error_msg}")
        return {"error": error_msg, "fields_installed": False}


def reinstall_payment_entry_custom_fields():
    """
    Reinstall all Payment Entry custom fields (useful for updates/fixes)

    Returns:
        dict: Reinstallation results
    """
    try:
        print("=== Reinstalling Payment Entry Custom Fields ===")

        # Get current status
        status = check_payment_entry_fields_status()
        print(f"Current status: {status['current_count']}/{status['expected_count']} fields")

        # Perform installation (with update=True to modify existing fields)
        result = install_payment_entry_custom_fields()

        if result["success"]:
            print("✅ Payment Entry custom fields reinstallation completed")
        else:
            print(f"❌ Reinstallation failed: {result.get('error')}")

        return result

    except Exception as e:
        error_msg = f"Error reinstalling Payment Entry custom fields: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}


# Convenience functions for command execution
def uninstall_payment_entry_custom_fields():
    """
    Remove all Payment Entry custom fields (for uninstallation)

    Returns:
        dict: Uninstallation results
    """
    try:
        print("=== Removing Payment Entry Thai Tax Preview Fields ===")

        # Get fields to remove
        fields_to_remove = get_payment_entry_custom_fields_definition()["Payment Entry"]
        field_names = [field["fieldname"] for field in fields_to_remove]

        removed_count = 0
        for fieldname in field_names:
            try:
                # Find and delete custom field
                custom_fields = frappe.get_all(
                    "Custom Field",
                    filters={"dt": "Payment Entry", "fieldname": fieldname},
                    fields=["name"],
                )

                for field in custom_fields:
                    frappe.delete_doc("Custom Field", field.name, ignore_permissions=True)
                    removed_count += 1
                    print(f"   🗑️ Removed: {fieldname}")

            except Exception as e:
                # Continue cleanup even if some fields fail
                print(f"   ⚠️ Could not remove {fieldname}: {str(e)}")
                pass

        if removed_count > 0:
            print(f"✅ Removed {removed_count} Payment Entry Thai tax preview fields")
            frappe.clear_cache()
        else:
            print("ℹ️ No Payment Entry Thai tax preview fields found to remove")

        return {"success": True, "removed_count": removed_count}

    except Exception as e:
        error_msg = f"Error removing Payment Entry Thai tax preview fields: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}


def check_and_fix_depends_on_issues():
    """
    Check and fix depends_on conditions that might be causing field visibility issues

    Returns:
        dict: Results of the check and fix operation
    """
    try:
        print("=== Checking Payment Entry Fields depends_on Issues ===")

        # Fields that should NOT have depends_on conditions
        problem_fields = [
            "wht_income_type",
            "wht_description",
            "wht_certificate_required",
            "net_total_after_wht",
            "net_total_after_wht_in_words",
            "wht_note",
        ]

        print("🔍 Checking Payment Entry custom fields depends_on in DATABASE:")

        # Get all Payment Entry custom fields
        custom_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Payment Entry"},
            fields=["fieldname", "depends_on", "name"],
            order_by="idx asc",
        )

        issues_found = []

        for field in custom_fields:
            fieldname = field.fieldname
            depends_on = field.depends_on or ""

            if fieldname in problem_fields:
                if depends_on:
                    print(f'   ❌ {fieldname}: depends_on = "{depends_on}" (SHOULD BE EMPTY)')
                    issues_found.append(
                        {"fieldname": fieldname, "depends_on": depends_on, "name": field.name}
                    )
                else:
                    print(f'   ✅ {fieldname}: depends_on = "" (CORRECT)')

        if issues_found:
            print(f"\n❌ Found {len(issues_found)} fields with problematic depends_on conditions")
            print("🔧 Fixing these fields...")

            for issue in issues_found:
                try:
                    # Update the Custom Field to remove depends_on
                    frappe.db.set_value("Custom Field", issue["name"], "depends_on", "")
                    print(f'   ✅ Fixed {issue["fieldname"]} - removed depends_on condition')
                except Exception as e:
                    print(f'   ❌ Error fixing {issue["fieldname"]}: {str(e)}')

            frappe.db.commit()
            print("✅ Database changes committed")

            return {
                "success": True,
                "issues_found": len(issues_found),
                "issues_fixed": len(issues_found),
                "fixed_fields": [issue["fieldname"] for issue in issues_found],
            }
        else:
            print("\n✅ All fields have correct depends_on conditions")
            return {"success": True, "issues_found": 0, "issues_fixed": 0, "fixed_fields": []}

    except Exception as e:
        error_msg = f"Error checking depends_on issues: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}


def main():
    """Main execution function for command line usage"""
    return install_payment_entry_custom_fields()


if __name__ == "__main__":
    main()
