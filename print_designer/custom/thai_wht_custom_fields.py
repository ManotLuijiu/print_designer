"""
Thai WHT Preview Custom Fields
==============================

This module defines custom fields for Thai Withholding Tax preview
on Quotation, Sales Order, and Sales Invoice documents.

These fields provide preview-only calculations and do not affect
ERPNext's payment-time WHT system.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field


# ==================================================
# CUSTOM FIELD DEFINITIONS
# ==================================================


def get_wht_preview_fields():
    """
    Get custom field definitions for WHT preview

    Returns:
        dict: Field definitions for each DocType
    """

    # Common field properties
    common_props = {
        "insert_after": "taxes_and_charges",
        "print_hide": 0,
        "read_only": 1,
        "no_copy": 1,
        "allow_on_submit": 0,
    }

    # Section break field
    # section_field = {
    #     "fieldname": "thai_wht_preview_section",
    #     "fieldtype": "Section Break",
    #     "label": "Thai Withholding Tax Preview (ภาษีหัก ณ ที่จ่าย - ข้อมูลเบื้องต้น)",
    #     "collapsible": 1,
    #     "collapsible_depends_on": "eval:doc.subject_to_wht",
    #     **common_props,
    # }

    # WHT preview fields
    wht_fields = [
        # Subject to WHT indicator
        {
            "fieldname": "subject_to_wht",
            "fieldtype": "Check",
            "label": "Subject to Withholding Tax",
            "default": 0,
            "description": "Indicates if this transaction is subject to WHT deduction",
            **common_props,
        },
        # Column break
        {
            "fieldname": "wht_preview_column_break",
            "fieldtype": "Column Break",
            **common_props,
        },
        # WHT Income Type
        {
            "fieldname": "wht_income_type",
            "fieldtype": "Select",
            "label": "WHT Income Type",
            "options": "\nprofessional_services\nrental\nservice_fees\nconstruction\nadvertising\nother_services",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Type of income for WHT calculation",
            **common_props,
        },
        # WHT Description
        {
            "fieldname": "wht_description",
            "fieldtype": "Data",
            "label": "WHT Description",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Thai description of WHT income type",
            **common_props,
        },
        # Section break for amounts
        {
            "fieldname": "wht_amounts_section",
            "fieldtype": "Section Break",
            "label": "WHT Amount Calculations",
            "depends_on": "eval:doc.subject_to_wht",
            **common_props,
        },
        # Base amount for WHT calculation
        {
            "fieldname": "wht_base_amount",
            "fieldtype": "Currency",
            "label": "WHT Base Amount",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Base amount used for WHT calculation (typically net total)",
            "precision": 2,
            **common_props,
        },
        # WHT Rate
        {
            "fieldname": "estimated_wht_rate",
            "fieldtype": "Percent",
            "label": "Estimated WHT Rate (%)",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "WHT rate based on income type and customer setup",
            "precision": 2,
            **common_props,
        },
        # Column break
        # {
        #     'fieldname': 'wht_amounts_column_break',
        #     'fieldtype': 'Column Break',
        #     **common_props
        # },
        # WHT Amount
        {
            "fieldname": "estimated_wht_amount",
            "fieldtype": "Currency",
            "label": "Estimated WHT Amount",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Estimated WHT amount (base amount × WHT rate)",
            "precision": 2,
            **common_props,
        },
        # Net payment amount
        {
            "fieldname": "net_payment_amount",
            "fieldtype": "Currency",
            "label": "Net Payment Amount",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Expected net payment after WHT deduction",
            "precision": 2,
            **common_props,
        },
        # Note section
        {
            "fieldname": "wht_note_section",
            "fieldtype": "Section Break",
            "label": "Important Note",
            "depends_on": "eval:doc.subject_to_wht",
            **common_props,
        },
        # WHT Note
        {
            "fieldname": "wht_note",
            "fieldtype": "Small Text",
            "label": "WHT Note",
            "default": "หมายเหตุ: จำนวนเงินภาษีหัก ณ ที่จ่าย จะถูกหักเมื่อชำระเงิน\nNote: Withholding tax amount will be deducted upon payment",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Important note about WHT deduction timing",
            **common_props,
        },
    ]

    # Prepare section field first, then other fields
    all_fields = [section_field] + wht_fields

    return {
        "Quotation": all_fields,
        "Sales Order": all_fields,
        "Sales Invoice": all_fields,
    }


# ==================================================
# FIELD INSTALLATION FUNCTIONS
# ==================================================


def install_wht_preview_fields():
    """
    Install WHT preview custom fields for sales documents
    """
    field_definitions = get_wht_preview_fields()

    for doctype, fields in field_definitions.items():
        print(f"\n📋 Installing WHT preview fields for {doctype}...")

        for field_def in fields:
            try:
                # Check if field already exists
                existing_field = frappe.db.get_value(
                    "Custom Field",
                    {"dt": doctype, "fieldname": field_def["fieldname"]},
                    "name",
                )

                if existing_field:
                    print(f"  ✅ Field '{field_def['fieldname']}' already exists")
                    continue

                # Create the custom field
                field_doc = frappe.get_doc(
                    {"doctype": "Custom Field", "dt": doctype, **field_def}
                )

                field_doc.insert(ignore_permissions=True)
                print(f"  ✅ Created field '{field_def['fieldname']}'")

            except Exception as e:
                print(f"  ❌ Error creating field '{field_def['fieldname']}': {str(e)}")

    # Clear cache to apply changes
    frappe.clear_cache()
    print("\n🔄 Cache cleared. Fields should now be visible in the forms.")


def check_wht_preview_fields():
    """
    Check if WHT preview fields are properly installed
    """
    field_definitions = get_wht_preview_fields()

    print("🔍 Checking WHT preview field installation...")

    for doctype, fields in field_definitions.items():
        print(f"\n📋 Checking {doctype}:")

        missing_fields = []
        for field_def in fields:
            existing_field = frappe.db.get_value(
                "Custom Field",
                {"dt": doctype, "fieldname": field_def["fieldname"]},
                "name",
            )

            if existing_field:
                print(f"  ✅ {field_def['fieldname']}")
            else:
                print(f"  ❌ {field_def['fieldname']} (MISSING)")
                missing_fields.append(field_def["fieldname"])

        if missing_fields:
            print(f"  ⚠️  Missing {len(missing_fields)} fields in {doctype}")
        else:
            print(f"  ✅ All WHT preview fields present in {doctype}")


def remove_wht_preview_fields():
    """
    Remove WHT preview custom fields (for testing/cleanup)
    """
    field_definitions = get_wht_preview_fields()

    print("🗑️  Removing WHT preview fields...")

    for doctype, fields in field_definitions.items():
        print(f"\n📋 Removing fields from {doctype}...")

        for field_def in fields:
            try:
                existing_field = frappe.db.get_value(
                    "Custom Field",
                    {"dt": doctype, "fieldname": field_def["fieldname"]},
                    "name",
                )

                if existing_field:
                    frappe.delete_doc("Custom Field", existing_field)
                    print(f"  🗑️  Removed field '{field_def['fieldname']}'")
                else:
                    print(f"  ℹ️  Field '{field_def['fieldname']}' not found")

            except Exception as e:
                print(f"  ❌ Error removing field '{field_def['fieldname']}': {str(e)}")

    # Clear cache
    frappe.clear_cache()
    print("\n🔄 Cache cleared. Fields should now be removed from forms.")


# ==================================================
# CUSTOMER WHT CONFIGURATION FIELDS
# ==================================================


def get_customer_wht_fields():
    """
    Get custom field definitions for Customer WHT configuration
    """

    return [
        # Section break
        {
            "fieldname": "thai_wht_section",
            "fieldtype": "Section Break",
            "label": "Thai Withholding Tax Configuration",
            "insert_after": "tax_withholding_category",
            "collapsible": 1,
        },
        # Subject to WHT
        {
            "fieldname": "subject_to_wht",
            "fieldtype": "Check",
            "label": "Subject to Withholding Tax",
            "default": 0,
            "description": "Check if this customer is subject to WHT deduction",
        },
        # Column break
        {"fieldname": "wht_config_column_break", "fieldtype": "Column Break"},
        # Juristic person indicator
        {
            "fieldname": "is_juristic_person",
            "fieldtype": "Check",
            "label": "Juristic Person (นิติบุคคล)",
            "default": 1,
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Check if customer is a juristic person (affects WHT rates)",
        },
        # Section break for WHT details
        {
            "fieldname": "wht_details_section",
            "fieldtype": "Section Break",
            "label": "WHT Details",
            "depends_on": "eval:doc.subject_to_wht",
        },
        # WHT Income Type
        {
            "fieldname": "wht_income_type",
            "fieldtype": "Select",
            "label": "Default WHT Income Type",
            "options": "\nprofessional_services\nrental\nservice_fees\nconstruction\nadvertising\nother_services",
            "default": "service_fees",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Default income type for WHT calculations",
        },
        # Custom WHT Rate
        {
            "fieldname": "custom_wht_rate",
            "fieldtype": "Percent",
            "label": "Custom WHT Rate (%)",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Override default WHT rate (leave blank to use standard rates)",
            "precision": 2,
        },
    ]


def install_customer_wht_fields():
    """
    Install WHT configuration fields for Customer DocType
    """
    print("📋 Installing WHT configuration fields for Customer...")

    fields = get_customer_wht_fields()

    for field_def in fields:
        try:
            # Check if field already exists
            existing_field = frappe.db.get_value(
                "Custom Field",
                {"dt": "Customer", "fieldname": field_def["fieldname"]},
                "name",
            )

            if existing_field:
                print(f"  ✅ Field '{field_def['fieldname']}' already exists")
                continue

            # Create the custom field
            field_doc = frappe.get_doc(
                {"doctype": "Custom Field", "dt": "Customer", **field_def}
            )

            field_doc.insert(ignore_permissions=True)
            print(f"  ✅ Created field '{field_def['fieldname']}'")

        except Exception as e:
            print(f"  ❌ Error creating field '{field_def['fieldname']}': {str(e)}")

    # Clear cache
    frappe.clear_cache()
    print("\n🔄 Cache cleared. Customer WHT fields should now be visible.")


def check_customer_wht_fields():
    """
    Check if Customer WHT fields are properly installed
    """
    print("🔍 Checking Customer WHT field installation...")

    fields = get_customer_wht_fields()
    missing_fields = []

    for field_def in fields:
        existing_field = frappe.db.get_value(
            "Custom Field",
            {"dt": "Customer", "fieldname": field_def["fieldname"]},
            "name",
        )

        if existing_field:
            print(f"  ✅ {field_def['fieldname']}")
        else:
            print(f"  ❌ {field_def['fieldname']} (MISSING)")
            missing_fields.append(field_def["fieldname"])

    if missing_fields:
        print(f"  ⚠️  Missing {len(missing_fields)} fields in Customer")
    else:
        print(f"  ✅ All Customer WHT fields present")


# ==================================================
# COMPLETE INSTALLATION FUNCTION
# ==================================================


def install_complete_wht_system():
    """
    Install complete WHT preview system fields
    """
    print("🚀 Installing complete Thai WHT preview system...\n")

    # Install customer configuration fields
    install_customer_wht_fields()

    print("\n" + "=" * 50)

    # Install sales document preview fields
    install_wht_preview_fields()

    print("\n✅ Thai WHT preview system installation complete!")
    print("\nNext steps:")
    print("1. Configure customer WHT settings in Customer forms")
    print("2. Test WHT preview calculations on sales documents")
    print("3. Customize print formats to show WHT information")


def check_complete_wht_system():
    """
    Check complete WHT preview system installation
    """
    print("🔍 Checking complete Thai WHT preview system...\n")

    # Check customer fields
    check_customer_wht_fields()

    print("\n" + "=" * 50)

    # Check sales document fields
    check_wht_preview_fields()

    print("\n📊 WHT preview system check complete!")
