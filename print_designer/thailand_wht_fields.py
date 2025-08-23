# Thailand Withholding Tax Fields Configuration for Print Designer
# This file defines withholding tax fields for Thai service businesses
# Following the same pattern as retention_fields.py for consistency
# Merged with Customer WHT configuration and preview fields

THAILAND_WHT_FIELDS = {
    # Company Configuration
    "Company": [
        {
            "fieldname": "thailand_service_business",
            "fieldtype": "Check",
            "label": "Thailand Service Business",
            "insert_after": "country",
            "description": "Enable Thailand withholding tax features for service businesses",
            "default": 0,
        },
        {
            "fieldname": "default_wht_rate",
            "fieldtype": "Percent",
            "label": "Default WHT Rate (%)",
            "insert_after": "thailand_service_business",
            "depends_on": "eval:doc.thailand_service_business",
            "description": "Default withholding tax rate for services (e.g., 3% for most services)",
            "default": 3.0,
            "precision": 2,
        },
        {
            "fieldname": "default_wht_account",
            "fieldtype": "Link",
            "label": "Default Withholding Tax Account",
            "options": "Account",
            "insert_after": "default_wht_rate",
            "depends_on": "eval:doc.thailand_service_business",
            "description": "Default account for withholding tax asset (e.g., Withholding Tax Assets)",
        },
    ],
    # Customer WHT Configuration
    "Customer": [
        {
            "fieldname": "subject_to_wht",
            "fieldtype": "Check",
            "label": "Subject to Withholding Tax",
            "insert_after": "tax_withholding_category",
            "default": 0,
            "description": "Check if this customer is subject to WHT deduction",
        },
        {
            "fieldname": "wht_config_column_break",
            "fieldtype": "Column Break",
            "insert_after": "subject_to_wht",
        },
        {
            "fieldname": "is_juristic_person",
            "fieldtype": "Check",
            "label": "Juristic Person (นิติบุคคล)",
            "insert_after": "wht_config_column_break",
            "default": 1,
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Check if customer is a juristic person (affects WHT rates)",
        },
        {
            "fieldname": "wht_income_type",
            "fieldtype": "Select",
            "label": "Default WHT Income Type",
            "insert_after": "is_juristic_person",
            "options": "\nprofessional_services\nrental\nservice_fees\nconstruction\nadvertising\nother_services",
            "default": "service_fees",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Default income type for WHT calculations",
        },
        {
            "fieldname": "custom_wht_rate",
            "fieldtype": "Percent",
            "label": "Custom WHT Rate (%)",
            "insert_after": "wht_income_type",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Override default WHT rate (leave blank to use standard rates)",
            "precision": 2,
        },
    ],
    # Sales Documents - Track WHT but don't calculate until payment
    "Quotation": [
        # Subject to WHT indicator
        {
            "fieldname": "subject_to_wht",
            "fieldtype": "Check",
            "label": "Subject to Withholding Tax",
            "insert_after": "taxes_and_charges",
            "description": "This quotation is for services subject to withholding tax",
            "depends_on": "eval:doc.company",
            "default": 0,
        },
        {
            "fieldname": "wht_preview_column_break",
            "fieldtype": "Column Break",
            "insert_after": "subject_to_wht",
        },
        # WHT Income Type
        {
            "fieldname": "wht_income_type",
            "fieldtype": "Select",
            "label": "WHT Income Type",
            "insert_after": "wht_preview_column_break",
            "options": "\nprofessional_services\nrental\nservice_fees\nconstruction\nadvertising\nother_services",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Type of income for WHT calculation",
        },
        # WHT Description
        {
            "fieldname": "wht_description",
            "fieldtype": "Data",
            "label": "WHT Description",
            "insert_after": "wht_income_type",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Thai description of WHT income type",
            "read_only": 1,
        },
        # Base amount for WHT calculation
        {
            "fieldname": "wht_base_amount",
            "fieldtype": "Currency",
            "label": "WHT Base Amount",
            "insert_after": "wht_description",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Base amount used for WHT calculation (typically net total)",
            "read_only": 1,
            "precision": 2,
            "options": "Company:company:default_currency",
        },
        # WHT Rate
        {
            "fieldname": "estimated_wht_rate",
            "fieldtype": "Percent",
            "label": "Estimated WHT Rate (%)",
            "insert_after": "wht_base_amount",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "WHT rate based on income type and customer setup",
            "read_only": 1,
            "precision": 2,
        },
        # WHT Amount
        {
            "fieldname": "estimated_wht_amount",
            "label": "Estimated WHT Amount",
            "fieldtype": "Currency",
            "insert_after": "estimated_wht_rate",
            "description": "Estimated withholding tax amount (base amount × WHT rate)",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht",
            "precision": 2,
            "options": "Company:company:default_currency",
        },
        # Net payment amount
        {
            "fieldname": "net_payment_amount",
            "fieldtype": "Currency",
            "label": "Net Payment Amount",
            "insert_after": "estimated_wht_amount",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Expected net payment after WHT deduction",
            "read_only": 1,
            "precision": 2,
            "options": "Company:company:default_currency",
        },
        # Legacy backward compatibility fields
        {
            "fieldname": "net_total_after_wht",
            "label": "Net Total (After WHT)",
            "fieldtype": "Currency",
            "insert_after": "net_payment_amount",
            "description": "Net total after adding VAT (7%) and deducting WHT",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht",
            "options": "Company:company:default_currency",
        },
        {
            "fieldname": "net_total_after_wht_in_words",
            "label": "Net Total (After WHT) in Words",
            "fieldtype": "Small Text",
            "insert_after": "net_total_after_wht",
            "description": "Net total amount in Thai words",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht && doc.net_total_after_wht",
        },
        # WHT Note
        {
            "fieldname": "wht_note",
            "fieldtype": "Small Text",
            "label": "WHT Note",
            "insert_after": "net_total_after_wht_in_words",
            "default": "หมายเหตุ: จำนวนเงินภาษีหัก ณ ที่จ่าย จะถูกหักเมื่อชำระเงิน\nNote: Withholding tax amount will be deducted upon payment",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Important note about WHT deduction timing",
            "read_only": 1,
        },
    ],
    "Item": [
        {
            "fieldname": "is_service_item",
            "label": "Is Service",
            "fieldtype": "Check",
            "insert_after": "is_fixed_asset",
            "description": "Check if this item represents a service (subject to WHT in Thailand)",
            "depends_on": "eval:1",
            "default": 0,
        },
    ],
    "Sales Order": [
        # Subject to WHT indicator
        {
            "fieldname": "subject_to_wht",
            "fieldtype": "Check",
            "label": "Subject to Withholding Tax",
            "insert_after": "taxes_and_charges",
            "description": "This sales order is for services subject to withholding tax",
            "depends_on": "eval:doc.company",
            "default": 0,
        },
        {
            "fieldname": "wht_preview_column_break",
            "fieldtype": "Column Break",
            "insert_after": "subject_to_wht",
        },
        # WHT Income Type
        {
            "fieldname": "wht_income_type",
            "fieldtype": "Select",
            "label": "WHT Income Type",
            "insert_after": "wht_preview_column_break",
            "options": "\nprofessional_services\nrental\nservice_fees\nconstruction\nadvertising\nother_services",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Type of income for WHT calculation",
        },
        # WHT Description
        {
            "fieldname": "wht_description",
            "fieldtype": "Data",
            "label": "WHT Description",
            "insert_after": "wht_income_type",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Thai description of WHT income type",
            "read_only": 1,
        },
        # Base amount for WHT calculation
        {
            "fieldname": "wht_base_amount",
            "fieldtype": "Currency",
            "label": "WHT Base Amount",
            "insert_after": "wht_description",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Base amount used for WHT calculation (typically net total)",
            "read_only": 1,
            "precision": 2,
            "options": "Company:company:default_currency",
        },
        # WHT Rate
        {
            "fieldname": "estimated_wht_rate",
            "fieldtype": "Percent",
            "label": "Estimated WHT Rate (%)",
            "insert_after": "wht_base_amount",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "WHT rate based on income type and customer setup",
            "read_only": 1,
            "precision": 2,
        },
        # WHT Amount
        {
            "fieldname": "estimated_wht_amount",
            "label": "Estimated WHT Amount",
            "fieldtype": "Currency",
            "insert_after": "estimated_wht_rate",
            "description": "Estimated withholding tax amount (base amount × WHT rate)",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht",
            "precision": 2,
            "options": "Company:company:default_currency",
        },
        # Net payment amount
        {
            "fieldname": "net_payment_amount",
            "fieldtype": "Currency",
            "label": "Net Payment Amount",
            "insert_after": "estimated_wht_amount",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Expected net payment after WHT deduction",
            "read_only": 1,
            "precision": 2,
            "options": "Company:company:default_currency",
        },
        # Legacy backward compatibility fields
        {
            "fieldname": "net_total_after_wht",
            "label": "Net Total (After WHT)",
            "fieldtype": "Currency",
            "insert_after": "net_payment_amount",
            "description": "Net total after adding VAT (7%) and deducting WHT",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht",
            "options": "Company:company:default_currency",
        },
        {
            "fieldname": "net_total_after_wht_in_words",
            "label": "Net Total (After WHT) in Words",
            "fieldtype": "Small Text",
            "insert_after": "net_total_after_wht",
            "description": "Net total amount in Thai words",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht && doc.net_total_after_wht",
        },
        # WHT Note
        {
            "fieldname": "wht_note",
            "fieldtype": "Small Text",
            "label": "WHT Note",
            "insert_after": "net_total_after_wht_in_words",
            "default": "หมายเหตุ: จำนวนเงินภาษีหัก ณ ที่จ่าย จะถูกหักเมื่อชำระเงิน\nNote: Withholding tax amount will be deducted upon payment",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Important note about WHT deduction timing",
            "read_only": 1,
        },
    ],
    "Sales Invoice": [
        # Subject to WHT indicator
        {
            "fieldname": "subject_to_wht",
            "label": "Subject to Withholding Tax",
            "fieldtype": "Check",
            "insert_after": "taxes_and_charges",
            "description": "This invoice is for services subject to withholding tax",
            "depends_on": "eval:doc.company",
            "default": 0,
        },
        # WHT Income Type
        {
            "fieldname": "wht_income_type",
            "fieldtype": "Select",
            "label": "WHT Income Type",
            "insert_after": "subject_to_wht",
            "options": "\nprofessional_services\nrental\nservice_fees\nconstruction\nadvertising\nother_services",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Type of income for WHT calculation",
        },
        # WHT Description
        {
            "fieldname": "wht_description",
            "fieldtype": "Data",
            "label": "WHT Description",
            "insert_after": "wht_income_type",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Thai description of WHT income type",
            "read_only": 1,
        },
        # Base amount for WHT calculation
        {
            "fieldname": "wht_base_amount",
            "fieldtype": "Currency",
            "label": "WHT Base Amount",
            "insert_after": "wht_description",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Base amount used for WHT calculation (typically net total)",
            "read_only": 1,
            "precision": 2,
            "options": "Company:company:default_currency",
        },
        # WHT Rate
        {
            "fieldname": "estimated_wht_rate",
            "fieldtype": "Percent",
            "label": "Estimated WHT Rate (%)",
            "insert_after": "wht_base_amount",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "WHT rate based on income type and customer setup",
            "read_only": 1,
            "precision": 2,
        },
        # WHT Amount
        {
            "fieldname": "estimated_wht_amount",
            "label": "Estimated WHT Amount",
            "fieldtype": "Currency",
            "insert_after": "estimated_wht_rate",
            "description": "Estimated withholding tax amount (base amount × WHT rate)",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht",
            "precision": 2,
            "options": "Company:company:default_currency",
        },
        # Net payment amount
        {
            "fieldname": "net_payment_amount",
            "fieldtype": "Currency",
            "label": "Net Payment Amount",
            "insert_after": "estimated_wht_amount",
            "depends_on": "eval:doc.subject_to_wht",
            "description": "Expected net payment after WHT deduction",
            "read_only": 1,
            "precision": 2,
            "options": "Company:company:default_currency",
        },
        # Legacy backward compatibility fields
        {
            "fieldname": "wht_certificate_required",
            "label": "WHT Certificate Required",
            "fieldtype": "Check",
            "insert_after": "net_payment_amount",
            "description": "Customer will provide withholding tax certificate",
            "depends_on": "eval:doc.subject_to_wht",
            "default": 1,
        },
        {
            "fieldname": "net_total_after_wht",
            "label": "Net Total (After WHT)",
            "fieldtype": "Currency",
            "insert_after": "wht_certificate_required",
            "description": "Net total after adding VAT (7%) and deducting WHT",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht",
            "options": "Company:company:default_currency",
        },
        {
            "fieldname": "net_total_after_wht_in_words",
            "label": "Net Total (After WHT) in Words",
            "fieldtype": "Small Text",
            "insert_after": "net_total_after_wht",
            "description": "Net total amount in Thai words",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht && doc.net_total_after_wht",
        },
        {
            "fieldname": "custom_retention",
            "label": "Apply Retention",
            "fieldtype": "Check",
            "insert_after": "net_total_after_wht_in_words",
            "description": "Apply retention amount (for construction/service contracts)",
            "depends_on": "eval:doc.company",
            "default": 0,
        },
        {
            "fieldname": "custom_retention_amount",
            "label": "Retention Amount",
            "fieldtype": "Currency",
            "insert_after": "custom_retention",
            "description": "Calculated retention amount",
            "read_only": 1,
            "depends_on": "eval:doc.custom_retention",
            "options": "Company:company:default_currency",
        },
        {
            "fieldname": "custom_withholding_tax",
            "label": "Apply Withholding Tax",
            "fieldtype": "Check",
            "insert_after": "custom_retention_amount",
            "description": "Apply withholding tax on payment",
            "depends_on": "eval:doc.company",
            "default": 0,
        },
        {
            "fieldname": "custom_withholding_tax_amount",
            "label": "Withholding Tax Amount",
            "fieldtype": "Currency",
            "insert_after": "custom_withholding_tax",
            "description": "Calculated withholding tax amount",
            "read_only": 1,
            "depends_on": "eval:doc.custom_withholding_tax",
            "options": "Company:company:default_currency",
        },
        {
            "fieldname": "custom_payment_amount",
            "label": "Payment Amount",
            "fieldtype": "Currency",
            "insert_after": "custom_withholding_tax_amount",
            "description": "Final payment amount after all deductions",
            "read_only": 1,
            "depends_on": "eval:doc.custom_retention || doc.custom_withholding_tax",
            "options": "Company:company:default_currency",
        },
    ],
    # Payment Entry - Where actual WHT is calculated and accounted
    # "Payment Entry": [
    #     {
    #         "fieldname": "wht_section",
    #         "label": "Thailand Withholding Tax",
    #         "fieldtype": "Section Break",
    #         "insert_after": "references",
    #         "depends_on": "eval:doc.company && doc.payment_type == 'Receive'",
    #         "collapsible": 1,
    #     },
    #     {
    #         "fieldname": "apply_wht",
    #         "label": "Apply Withholding Tax",
    #         "fieldtype": "Check",
    #         "insert_after": "wht_section",
    #         "description": "Apply withholding tax on this payment",
    #         "depends_on": "eval:doc.company && doc.payment_type == 'Receive'",
    #         "default": 0,
    #     },
    #     {
    #         "fieldname": "wht_rate",
    #         "label": "WHT Rate (%)",
    #         "fieldtype": "Percent",
    #         "insert_after": "apply_wht",
    #         "description": "Withholding tax rate (configurable per company)",
    #         "depends_on": "eval:doc.apply_wht",
    #         "default": 3.0,
    #         "precision": 2,
    #     },
    #     {
    #         "fieldname": "wht_amount",
    #         "label": "WHT Amount",
    #         "fieldtype": "Currency",
    #         "insert_after": "wht_rate",
    #         "description": "Calculated withholding tax amount",
    #         "read_only": 1,
    #         "depends_on": "eval:doc.apply_wht",
    #         "options": "Company:company:default_currency",
    #     },
    #     {
    #         "fieldname": "wht_account",
    #         "label": "Withholding Tax Account",
    #         "fieldtype": "Link",
    #         "options": "Account",
    #         "insert_after": "wht_amount",
    #         "description": "Account to record withholding tax asset",
    #         "depends_on": "eval:doc.apply_wht",
    #     },
    #     {
    #         "fieldname": "net_payment_amount",
    #         "label": "Net Payment Amount",
    #         "fieldtype": "Currency",
    #         "insert_after": "wht_account",
    #         "description": "Amount paid after withholding tax deduction",
    #         "read_only": 1,
    #         "depends_on": "eval:doc.apply_wht",
    #         "options": "Company:company:default_currency",
    #     },
    #     {
    #         "fieldname": "wht_certificate_no",
    #         "label": "WHT Certificate No.",
    #         "fieldtype": "Data",
    #         "insert_after": "net_payment_amount",
    #         "description": "Withholding tax certificate number",
    #         "depends_on": "eval:doc.apply_wht",
    #     },
    #     {
    #         "fieldname": "wht_certificate_date",
    #         "label": "WHT Certificate Date",
    #         "fieldtype": "Date",
    #         "insert_after": "wht_certificate_no",
    #         "description": "Date of withholding tax certificate",
    #         "depends_on": "eval:doc.apply_wht",
    #     },
    # ],
}


# Function to get all withholding tax fields for installation
def get_thailand_wht_fields():
    """
    Returns all Thailand withholding tax fields in the format expected by Frappe's custom fields system
    """
    return THAILAND_WHT_FIELDS


# Function to get withholding tax fields for a specific DocType
def get_wht_fields_for_doctype(doctype):
    """
    Returns withholding tax fields for a specific DocType
    """
    return THAILAND_WHT_FIELDS.get(doctype, [])


# Function to check if a DocType has withholding tax fields
def has_wht_fields(doctype):
    """
    Check if a DocType has withholding tax fields configured
    """
    return doctype in THAILAND_WHT_FIELDS


# Function to get all DocTypes with withholding tax fields
def get_doctypes_with_wht():
    """
    Returns list of all DocTypes that have withholding tax fields
    """
    return list(THAILAND_WHT_FIELDS.keys())


# Function to install withholding tax fields
def install_thailand_wht_fields():
    """
    Install Thailand withholding tax custom fields for all configured DocTypes
    """
    import frappe
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    try:
        custom_fields = get_thailand_wht_fields()

        # Try the standard bulk creation first
        try:
            # Validate all field values are strings to avoid formatting errors
            for doctype, fields in custom_fields.items():
                for field in fields:
                    for key, value in field.items():
                        if isinstance(value, (int, float)) and key not in [
                            "default",
                            "precision",
                            "read_only",
                            "collapsible",
                        ]:
                            field[key] = str(value)

            create_custom_fields(custom_fields, update=True)

        except Exception as bulk_error:
            print(f"⚠️  Bulk creation failed: {bulk_error}")
            print("🔄 Falling back to individual field creation...")

            # Fall back to individual field creation
            from frappe.custom.doctype.custom_field.custom_field import (
                create_custom_field,
            )

            for doctype, fields in custom_fields.items():
                print(f"  📋 Creating {doctype} fields...")

                for field_config in fields:
                    fieldname = field_config.get("fieldname", "unknown")

                    # Check if field already exists
                    if frappe.db.exists(
                        "Custom Field", {"dt": doctype, "fieldname": fieldname}
                    ):
                        print(f"    ✅ {doctype}.{fieldname} already exists")
                        continue

                    try:
                        field_config["dt"] = doctype
                        create_custom_field(doctype, field_config)
                        print(f"    ✅ Created {doctype}.{fieldname}")
                    except Exception as field_error:
                        print(
                            f"    ❌ Error creating {doctype}.{fieldname}: {field_error}"
                        )
                        frappe.log_error(
                            f"Failed to create {doctype}.{fieldname}: {str(field_error)}",
                            "WHT Fields Individual Creation",
                        )

        print("✅ Custom fields created successfully!")
        print("   - Company: thailand_service_business, default_wht_rate, default_wht_account")
        print("   - Customer: subject_to_wht, is_juristic_person, wht_income_type, custom_wht_rate")
        print("   - Item: is_service_item (checkbox for service items)")
        print("   - Quotation: subject_to_wht, wht_income_type, wht_base_amount, estimated_wht_rate,")
        print("     estimated_wht_amount, net_payment_amount, net_total_after_wht, wht_note")
        print("   - Sales Order: subject_to_wht, wht_income_type, wht_base_amount, estimated_wht_rate,")
        print("     estimated_wht_amount, net_payment_amount, net_total_after_wht, wht_note")
        print("   - Sales Invoice: subject_to_wht, wht_income_type, wht_base_amount, estimated_wht_rate,")
        print("     estimated_wht_amount, net_payment_amount, wht_certificate_required, net_total_after_wht,")
        print("     net_total_after_wht_in_words, custom_retention, custom_retention_amount,")
        print("     custom_withholding_tax, custom_withholding_tax_amount, custom_payment_amount")

        # Run migration to fix existing installations
        print("\n🔄 Running migration for existing installations...")
        migrate_sales_invoice_wht_fields()

        frappe.db.commit()
        print("✅ Thailand withholding tax custom fields installed successfully")
        return True
    except Exception as e:
        print(f"❌ Error installing Thailand withholding tax fields: {str(e)}")
        frappe.log_error(f"Thailand WHT Fields Installation Error: {str(e)}")
        try:
            frappe.db.rollback()
        except:
            pass
        return False


# Function to uninstall withholding tax fields
def uninstall_thailand_wht_fields():
    """
    Remove Thailand withholding tax custom fields from all configured DocTypes
    """
    import frappe

    try:
        for doctype, fields in THAILAND_WHT_FIELDS.items():
            for field_config in fields:
                fieldname = field_config["fieldname"]

                # Delete custom field if it exists
                if frappe.db.exists(
                    "Custom Field", {"dt": doctype, "fieldname": fieldname}
                ):
                    frappe.delete_doc(
                        "Custom Field",
                        frappe.db.get_value(
                            "Custom Field",
                            {"dt": doctype, "fieldname": fieldname},
                            "name",
                        ),
                    )

        print("✅ Thailand withholding tax custom fields removed successfully")
        return True
    except Exception as e:
        print(f"❌ Error removing Thailand withholding tax fields: {str(e)}")
        return False


# Migration function to update existing installations
def migrate_sales_invoice_wht_fields():
    """
    Migrate Sales Invoice WHT fields to remove wht_section and consolidate into taxes section.
    This function ensures existing installations are updated to the new field structure.
    """
    import frappe

    try:
        print("🔄 Migrating Sales Invoice WHT fields...")

        # Step 1: Check if wht_section exists
        wht_section_exists = frappe.db.exists(
            "Custom Field", {"dt": "Sales Invoice", "fieldname": "wht_section"}
        )

        if wht_section_exists:
            print("  📋 Found existing wht_section field - removing...")

            # Delete the wht_section field
            frappe.delete_doc(
                "Custom Field", wht_section_exists, ignore_permissions=True
            )
            print("  ✅ Removed wht_section field")
        else:
            print("  ℹ️  wht_section field not found - already removed")

        # Step 2: Update subject_to_wht to insert after taxes_and_charges
        subject_to_wht_exists = frappe.db.exists(
            "Custom Field", {"dt": "Sales Invoice", "fieldname": "subject_to_wht"}
        )

        if subject_to_wht_exists:
            subject_field = frappe.get_doc("Custom Field", subject_to_wht_exists)
            current_insert_after = subject_field.insert_after

            if current_insert_after != "taxes_and_charges":
                print(
                    f"  📝 Updating subject_to_wht position: '{current_insert_after}' → 'taxes_and_charges'"
                )
                subject_field.insert_after = "taxes_and_charges"
                subject_field.save(ignore_permissions=True)
                print("  ✅ Updated subject_to_wht field position")
            else:
                print("  ℹ️  subject_to_wht field already in correct position")
        else:
            print("  ⚠️  subject_to_wht field not found - may need full installation")

        # Step 3: Commit changes
        frappe.db.commit()
        print("✅ Sales Invoice WHT field migration completed successfully")
        return True

    except Exception as e:
        print(f"❌ Error during Sales Invoice WHT field migration: {str(e)}")
        frappe.log_error(
            f"Sales Invoice WHT Migration Error: {str(e)}", "WHT Field Migration"
        )
        try:
            frappe.db.rollback()
        except:
            pass
        return False


# Function to calculate withholding tax amount
def calculate_wht_amount(base_amount, wht_rate=3.0):
    """
    Calculate withholding tax amount based on base amount and rate
    """
    if not base_amount or not wht_rate:
        return 0
    return (base_amount * wht_rate) / 100


# Function to get net amount after WHT deduction
def get_net_amount_after_wht(gross_amount, wht_rate=3.0):
    """
    Calculate net amount after withholding tax deduction
    """
    if not gross_amount:
        return 0
    wht_amount = calculate_wht_amount(gross_amount, wht_rate)
    return gross_amount - wht_amount


# ==================================================
# COMPREHENSIVE FIELD CHECKING FUNCTIONS
# ==================================================


def check_thailand_wht_fields():
    """
    Check if Thailand WHT fields are properly installed across all DocTypes
    """
    import frappe

    print("🔍 Checking Thailand WHT field installation...")

    all_installed = True
    field_definitions = get_thailand_wht_fields()

    for doctype, fields in field_definitions.items():
        print(f"\n📋 Checking {doctype}:")

        missing_fields = []
        for field_def in fields:
            fieldname = field_def.get("fieldname", "unknown")
            existing_field = frappe.db.get_value(
                "Custom Field",
                {"dt": doctype, "fieldname": fieldname},
                "name",
            )

            if existing_field:
                print(f"  ✅ {fieldname}")
            else:
                print(f"  ❌ {fieldname} (MISSING)")
                missing_fields.append(fieldname)
                all_installed = False

        if missing_fields:
            print(f"  ⚠️  Missing {len(missing_fields)} fields in {doctype}")
        else:
            print(f"  ✅ All WHT fields present in {doctype}")

    print(f"\n📊 Overall status: {'✅ All fields installed' if all_installed else '❌ Some fields missing'}")
    return all_installed


def check_specific_doctype_wht_fields(doctype):
    """
    Check WHT fields for a specific DocType
    """
    import frappe

    print(f"🔍 Checking {doctype} WHT fields...")

    if doctype not in THAILAND_WHT_FIELDS:
        print(f"  ❌ {doctype} is not configured for WHT fields")
        return False

    fields = THAILAND_WHT_FIELDS[doctype]
    missing_fields = []

    for field_def in fields:
        fieldname = field_def.get("fieldname", "unknown")
        existing_field = frappe.db.get_value(
            "Custom Field",
            {"dt": doctype, "fieldname": fieldname},
            "name",
        )

        if existing_field:
            print(f"  ✅ {fieldname}")
        else:
            print(f"  ❌ {fieldname} (MISSING)")
            missing_fields.append(fieldname)

    if missing_fields:
        print(f"  ⚠️  Missing {len(missing_fields)} fields in {doctype}")
        return False
    else:
        print(f"  ✅ All WHT fields present in {doctype}")
        return True


def check_company_wht_fields():
    """
    Check specifically Company WHT configuration fields
    """
    return check_specific_doctype_wht_fields("Company")


def check_customer_wht_fields():
    """
    Check specifically Customer WHT configuration fields
    """
    return check_specific_doctype_wht_fields("Customer")


def check_sales_document_wht_fields():
    """
    Check WHT fields across all sales documents
    """
    print("🔍 Checking sales document WHT fields...")
    
    sales_doctypes = ["Quotation", "Sales Order", "Sales Invoice"]
    all_good = True
    
    for doctype in sales_doctypes:
        if not check_specific_doctype_wht_fields(doctype):
            all_good = False
    
    return all_good


# ==================================================
# COMPREHENSIVE INSTALLATION FUNCTIONS  
# ==================================================


def install_complete_thailand_wht_system():
    """
    Install complete Thailand WHT system with all fields and configurations
    """
    print("🚀 Installing complete Thailand WHT system...\n")

    try:
        # Install all WHT fields
        success = install_thailand_wht_fields()
        
        if not success:
            print("❌ Failed to install WHT fields")
            return False

        print("\n" + "=" * 60)
        print("🔍 Verifying installation...")
        
        # Verify installation
        all_installed = check_thailand_wht_fields()
        
        if all_installed:
            print("\n✅ Complete Thailand WHT system installation successful!")
            print("\nNext steps:")
            print("1. Configure Company settings (thailand_service_business, default_wht_rate, default_wht_account)")
            print("2. Set up Customer WHT configurations as needed")
            print("3. Test WHT calculations on sales documents")
            print("4. Customize print formats to show WHT information")
            print("5. Train users on WHT field usage")
        else:
            print("\n⚠️  Installation completed but some fields may be missing")
            print("   Run check_thailand_wht_fields() to see details")
        
        return all_installed

    except Exception as e:
        print(f"❌ Error during complete WHT system installation: {str(e)}")
        return False


def reinstall_thailand_wht_fields():
    """
    Reinstall Thailand WHT fields (useful for updates or fixes)
    """
    print("🔄 Reinstalling Thailand WHT fields...")
    
    try:
        # First remove existing fields
        print("🗑️  Removing existing WHT fields...")
        uninstall_thailand_wht_fields()
        
        print("\n📦 Installing fresh WHT fields...")
        # Then install fresh
        success = install_thailand_wht_fields()
        
        if success:
            print("✅ Thailand WHT fields reinstalled successfully")
        else:
            print("❌ Failed to reinstall WHT fields")
            
        return success
        
    except Exception as e:
        print(f"❌ Error during WHT fields reinstallation: {str(e)}")
        return False


# ==================================================
# UTILITY FUNCTIONS FOR WHT MANAGEMENT
# ==================================================


def get_wht_income_type_description(income_type):
    """
    Get Thai description for WHT income types
    """
    descriptions = {
        "professional_services": "ค่าบริการทางวิชาชีพ",
        "rental": "ค่าเช่า",
        "service_fees": "ค่าบริการ",
        "construction": "ค่าก่อสร้าง",
        "advertising": "ค่าโฆษณา",
        "other_services": "ค่าบริการอื่นๆ",
    }
    return descriptions.get(income_type, income_type)


def get_standard_wht_rates():
    """
    Get standard WHT rates for different income types
    """
    return {
        "professional_services": 5.0,  # Professional services: 5%
        "rental": 5.0,                  # Rental: 5%
        "service_fees": 3.0,            # Service fees: 3%
        "construction": 3.0,            # Construction: 3%
        "advertising": 2.0,             # Advertising: 2%
        "other_services": 3.0,          # Other services: 3%
    }


def get_wht_rate_for_income_type(income_type, is_juristic_person=True):
    """
    Get appropriate WHT rate based on income type and entity type
    """
    standard_rates = get_standard_wht_rates()
    base_rate = standard_rates.get(income_type, 3.0)
    
    # Individual rates may be different than juristic person rates
    if not is_juristic_person:
        # Individual rates might be higher for some categories
        individual_adjustments = {
            "professional_services": 5.0,
            "service_fees": 5.0,
        }
        return individual_adjustments.get(income_type, base_rate)
    
    return base_rate


def validate_wht_setup():
    """
    Validate that WHT system is properly configured
    """
    import frappe
    
    print("🔍 Validating Thailand WHT system setup...")
    
    issues = []
    
    # Check if fields are installed
    if not check_thailand_wht_fields():
        issues.append("❌ Some WHT fields are missing")
    
    # Check if any company has WHT enabled
    companies_with_wht = frappe.db.get_all(
        "Company", 
        filters={"thailand_service_business": 1}, 
        fields=["name", "default_wht_account"]
    )
    
    if not companies_with_wht:
        issues.append("⚠️  No companies have thailand_service_business enabled")
    else:
        for company in companies_with_wht:
            if not company.get("default_wht_account"):
                issues.append(f"⚠️  Company {company['name']} has no default_wht_account set")
    
    if not issues:
        print("✅ Thailand WHT system validation passed")
        return True
    else:
        print("❌ Thailand WHT system validation found issues:")
        for issue in issues:
            print(f"  {issue}")
        return False


def create_sample_wht_test_data():
    """
    Create sample test data for WHT system testing
    """
    import frappe
    
    print("🧪 Creating sample WHT test data...")
    
    try:
        # Enable WHT for first company if not already enabled
        company = frappe.get_doc("Company", frappe.get_all("Company", limit=1)[0].name)
        if not company.get("thailand_service_business"):
            company.thailand_service_business = 1
            company.default_wht_rate = 3.0
            # Note: default_wht_account should be set manually to existing account
            company.save()
            print(f"  ✅ Enabled WHT for company {company.name}")
        
        # Create a test customer with WHT configuration
        if not frappe.db.exists("Customer", "WHT Test Customer"):
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": "WHT Test Customer",
                "customer_type": "Company",
                "subject_to_wht": 1,
                "is_juristic_person": 1,
                "wht_income_type": "service_fees",
                "custom_wht_rate": 3.0,
            })
            customer.insert()
            print("  ✅ Created WHT Test Customer")
        
        print("✅ Sample WHT test data created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating sample WHT test data: {str(e)}")
        return False
