#!/usr/bin/env python3
"""
Install WHT Certificate Link Field Command

Adds pd_custom_wht_certificate link field to Payment Entry for linking to
generated Withholding Tax Certificate documents.
"""

import frappe
import click
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Main entry point for bench command"""
    install_wht_certificate_link_field()


@click.command()
def install_wht_certificate_link_field():
    """Install WHT Certificate link field in Payment Entry"""

    click.echo("🏗️  Installing WHT Certificate Link Field...")

    try:
        # Define the custom field
        custom_fields = {
            "Payment Entry": [
                {
                    "fieldname": "pd_custom_wht_certificate",
                    "fieldtype": "Link",
                    "options": "Withholding Tax Certificate",
                    "label": "WHT Certificate",
                    "description": "Link to generated Withholding Tax Certificate",
                    "insert_after": "pd_custom_thai_compliance_tab",
                    "depends_on": "eval:doc.payment_type=='Pay' && doc.pd_custom_has_thai_taxes",
                    "read_only": 1,
                    "no_copy": 1,
                    "allow_on_submit": 1,  # Allow updating even after submit
                },
                {
                    "fieldname": "pd_custom_needs_wht_certificate",
                    "fieldtype": "Check",
                    "label": "Needs WHT Certificate",
                    "description": "Internal flag to trigger WHT certificate creation",
                    "insert_after": "pd_custom_wht_certificate",
                    "depends_on": "eval:doc.payment_type=='Pay' && doc.pd_custom_has_thai_taxes",
                    "hidden": 1,  # Hidden field for internal use
                    "no_copy": 1,
                    "default": 0,
                }
            ]
        }

        # Create the custom fields
        create_custom_fields(custom_fields, update=True)

        click.echo("✅ WHT Certificate Link Field installed successfully!")

        # Verify installation
        field_exists = frappe.db.exists("Custom Field", {
            "dt": "Payment Entry",
            "fieldname": "pd_custom_wht_certificate"
        })

        if field_exists:
            click.echo("✅ Field verification: pd_custom_wht_certificate exists")
        else:
            click.echo("❌ Field verification: pd_custom_wht_certificate NOT found")

        flag_exists = frappe.db.exists("Custom Field", {
            "dt": "Payment Entry",
            "fieldname": "pd_custom_needs_wht_certificate"
        })

        if flag_exists:
            click.echo("✅ Field verification: pd_custom_needs_wht_certificate exists")
        else:
            click.echo("❌ Field verification: pd_custom_needs_wht_certificate NOT found")

    except Exception as e:
        click.echo(f"❌ Error installing WHT Certificate Link Field: {str(e)}")
        frappe.log_error(
            message=f"Error installing WHT Certificate Link Field: {str(e)}",
            title="WHT Certificate Link Field Installation Error"
        )


@click.command()
def check_wht_certificate_link_field():
    """Check if WHT Certificate link field is installed"""

    click.echo("🔍 Checking WHT Certificate Link Field status...")

    try:
        # Check main link field
        field_exists = frappe.db.exists("Custom Field", {
            "dt": "Payment Entry",
            "fieldname": "pd_custom_wht_certificate"
        })

        # Check internal flag field
        flag_exists = frappe.db.exists("Custom Field", {
            "dt": "Payment Entry",
            "fieldname": "pd_custom_needs_wht_certificate"
        })

        if field_exists and flag_exists:
            click.echo("✅ WHT Certificate Link Field: INSTALLED")

            # Get field details
            field_details = frappe.get_doc("Custom Field", {
                "dt": "Payment Entry",
                "fieldname": "pd_custom_wht_certificate"
            })

            click.echo(f"   - Field Type: {field_details.fieldtype}")
            click.echo(f"   - Options: {field_details.options}")
            click.echo(f"   - Dependencies: {field_details.depends_on}")
            click.echo(f"   - Read Only: {field_details.read_only}")

        else:
            click.echo("❌ WHT Certificate Link Field: NOT INSTALLED")
            if not field_exists:
                click.echo("   - Missing: pd_custom_wht_certificate")
            if not flag_exists:
                click.echo("   - Missing: pd_custom_needs_wht_certificate")

    except Exception as e:
        click.echo(f"❌ Error checking WHT Certificate Link Field: {str(e)}")


if __name__ == "__main__":
    execute()