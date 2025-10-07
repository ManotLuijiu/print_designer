#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Install Company CoA CSV Import Fields

Adds custom fields to Company DocType for CSV-based Chart of Accounts import.
Integrates with thai_business_suite CoA mapper if available.
"""

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install_company_coa_csv_fields():
    """
    Install Company custom fields for CSV-based Chart of Accounts import.

    Fields added:
    - pd_coa_csv_section: Section break for CoA CSV import
    - pd_use_csv_coa: Checkbox to enable CSV-based CoA import
    - pd_coa_csv_file: Attach field for CSV file
    - pd_coa_mapping_template: Link to TBS CoA Mapping Template (if thai_business_suite installed)
    - pd_coa_import_status: Read-only status field
    """

    print("\n" + "=" * 80)
    print("📋 Installing Company CoA CSV Import Fields")
    print("=" * 80)

    custom_fields = {
        "Company": [
            {
                "fieldname": "pd_use_csv_coa",
                "label": _("Use CSV for Chart of Accounts"),
                "fieldtype": "Check",
                "insert_after": "chart_of_accounts",
                "default": "0",
                "description": _(
                    "Enable to import Chart of Accounts from CSV file instead of standard templates"
                ),
            },
            {
                "fieldname": "pd_coa_csv_file",
                "label": _("Chart of Accounts CSV File"),
                "fieldtype": "Attach",
                "insert_after": "pd_use_csv_coa",
                "depends_on": "eval:doc.pd_use_csv_coa",
                "mandatory_depends_on": "eval:doc.pd_use_csv_coa",
                "description": _("Upload your Chart of Accounts CSV file"),
            },
        ]
    }

    # Check if thai_business_suite is installed
    thai_business_suite_installed = False
    try:
        frappe.get_doc("DocType", "TBS CoA Mapping Template")
        thai_business_suite_installed = True
        print("✅ thai_business_suite detected - Adding mapping template field")
    except frappe.DoesNotExistError:
        print("ℹ️  thai_business_suite not installed - Skipping mapping template field")

    # Add mapping template field if thai_business_suite is available
    if thai_business_suite_installed:
        custom_fields["Company"].extend(
            [
                {
                    "fieldname": "pd_coa_mapping_template",
                    "label": _("CSV Mapping Template"),
                    "fieldtype": "Link",
                    "options": "TBS CoA Mapping Template",
                    "insert_after": "pd_coa_csv_file",
                    "depends_on": "eval:doc.pd_use_csv_coa",
                    "description": _("Select mapping template that matches your CSV format"),
                },
                {
                    "fieldname": "pd_coa_help",
                    "fieldtype": "HTML",
                    "options": """
					<div class="alert alert-info" style="margin-top: 10px;">
						<strong>How to use CSV Import:</strong>
						<ol>
							<li>Check "Use CSV for Chart of Accounts"</li>
							<li>Upload your Chart of Accounts CSV file</li>
							<li>Select appropriate mapping template (or create new one at <a href="/app/tbs-coa-mapping-template">Mapping Templates</a>)</li>
							<li>Save the Company - Chart of Accounts will be automatically imported</li>
						</ol>
						<p><a href="/app/coa-mapper" target="_blank">Test your CSV mapping</a> before creating the company.</p>
					</div>
				""",
                    "insert_after": "pd_coa_mapping_template",
                    "depends_on": "eval:doc.pd_use_csv_coa",
                },
            ]
        )
    else:
        # Add help text when thai_business_suite is not available
        custom_fields["Company"].extend(
            [
                {
                    "fieldname": "pd_coa_help",
                    "fieldtype": "HTML",
                    "options": """
					<div class="alert alert-warning" style="margin-top: 10px;">
						<strong>⚠️ Advanced CSV Import Not Available</strong>
						<p>Install <strong>thai_business_suite</strong> app to enable advanced CSV mapping features with template management.</p>
						<p>Without thai_business_suite, CSV files must follow the exact ERPNext standard format.</p>
					</div>
				""",
                    "insert_after": "pd_coa_csv_file",
                    "depends_on": "eval:doc.pd_use_csv_coa",
                },
            ]
        )

    # Add status field (common for both scenarios)
    custom_fields["Company"].append(
        {
            "fieldname": "pd_coa_import_status",
            "label": _("CoA Import Status"),
            "fieldtype": "Data",
            "insert_after": "pd_coa_help",
            "read_only": 1,
            "depends_on": "eval:doc.pd_use_csv_coa",
            "hidden": 1,  # Hidden by default, shown programmatically after import
        }
    )

    # Create custom fields
    print("\n📝 Creating custom fields...")
    create_custom_fields(custom_fields, update=True)

    print("✅ Company CoA CSV Import fields installed successfully")
    print("=" * 80 + "\n")

    return {
        "success": True,
        "fields_created": len(custom_fields["Company"]),
        "thai_business_suite_installed": thai_business_suite_installed,
    }


def uninstall_company_coa_csv_fields():
    """Remove Company CoA CSV import custom fields."""

    print("\n" + "=" * 80)
    print("🗑️  Uninstalling Company CoA CSV Import Fields")
    print("=" * 80)

    field_names = [
        "pd_use_csv_coa",
        "pd_coa_csv_file",
        "pd_coa_mapping_template",
        "pd_coa_help",
        "pd_coa_import_status",
    ]

    deleted_count = 0
    for fieldname in field_names:
        try:
            custom_field_name = f"Company-{fieldname}"
            if frappe.db.exists("Custom Field", custom_field_name):
                frappe.delete_doc("Custom Field", custom_field_name)
                deleted_count += 1
                print(f"✅ Deleted: {fieldname}")
        except Exception as e:
            print(f"⚠️  Failed to delete {fieldname}: {str(e)}")

    frappe.db.commit()

    print(f"\n✅ Uninstalled {deleted_count} custom fields")
    print("=" * 80 + "\n")

    return {"success": True, "fields_deleted": deleted_count}


# CLI interface
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall_company_coa_csv_fields()
    else:
        install_company_coa_csv_fields()
