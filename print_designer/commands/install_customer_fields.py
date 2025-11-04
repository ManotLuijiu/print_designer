"""
Custom Field Management Commands for Customer DocType
Handles installation, verification, and removal of Print Designer-specific Customer custom fields.

Features:
- Branch Code for Thai tax invoice compliance (00000 default for head office)
"""

import click
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Field configuration for Customer DocType
CUSTOMER_CUSTOM_FIELDS = {
    "Customer": [
        {
            "fieldname": "pd_custom_branch_code",
            "label": "Branch Code",
            "fieldtype": "Data",
            "insert_after": "tax_id",
            "default": "00000",
            "module": "Print Designer",
            "description": "Branch code for Thai tax invoice compliance (00000 = head office)",
        },
    ]
}


def create_customer_fields():
    """
    Install Customer custom fields for Print Designer.

    Returns:
        bool: True if installation successful, False otherwise
    """
    try:
        print("🚀 Installing Print Designer Customer custom fields...")
        create_custom_fields(CUSTOMER_CUSTOM_FIELDS, update=True)
        frappe.db.commit()
        print("✅ Customer custom fields installed successfully!")
        print("   - pd_custom_branch_code (Branch Code for Thai tax invoices)")
        return True
    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error installing Customer custom fields: {str(e)}")
        frappe.log_error("Customer Custom Fields Installation Error", str(e))
        return False


def check_customer_fields():
    """
    Verify that all Customer custom fields are properly installed.

    Returns:
        bool: True if all fields exist, False otherwise
    """
    try:
        print("🔍 Checking Customer custom fields...")
        missing_fields = []

        for field_config in CUSTOMER_CUSTOM_FIELDS["Customer"]:
            fieldname = field_config["fieldname"]
            if not frappe.db.exists("Custom Field", {"dt": "Customer", "fieldname": fieldname}):
                missing_fields.append(fieldname)

        if missing_fields:
            print(f"❌ Missing {len(missing_fields)} field(s) in Customer:")
            for field in missing_fields:
                print(f"   - {field}")
            return False
        else:
            print(
                f"✅ All {len(CUSTOMER_CUSTOM_FIELDS['Customer'])} Customer custom fields are installed!"
            )
            return True

    except Exception as e:
        print(f"❌ Error checking Customer custom fields: {str(e)}")
        frappe.log_error("Customer Custom Fields Check Error", str(e))
        return False


def uninstall_customer_fields():
    """
    Remove all Customer custom fields created by Print Designer.

    Returns:
        bool: True if removal successful, False otherwise
    """
    try:
        print("🗑️  Removing Customer custom fields...")
        removed_count = 0

        for field_config in CUSTOMER_CUSTOM_FIELDS["Customer"]:
            fieldname = field_config["fieldname"]
            custom_field = frappe.db.exists(
                "Custom Field", {"dt": "Customer", "fieldname": fieldname}
            )

            if custom_field:
                frappe.delete_doc("Custom Field", custom_field, force=1)
                removed_count += 1
                print(f"   ✓ Removed {fieldname}")

        frappe.db.commit()
        print(f"✅ Successfully removed {removed_count} Customer custom field(s)!")
        return True

    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error removing Customer custom fields: {str(e)}")
        frappe.log_error("Customer Custom Fields Uninstall Error", str(e))
        return False


# Click CLI Commands for bench integration


@click.command("install-pd-customer-fields")
@click.pass_context
def install_customer_fields_cmd(context):
    """Install Customer custom fields for Print Designer"""
    site = context.obj["sites"][0] if context.obj.get("sites") else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        create_customer_fields()
        frappe.destroy()


@click.command("check-pd-customer-fields")
@click.pass_context
def check_customer_fields_cmd(context):
    """Verify Print Designer Customer custom fields installation"""
    site = context.obj["sites"][0] if context.obj.get("sites") else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        check_customer_fields()
        frappe.destroy()


@click.command("uninstall-pd-customer-fields")
@click.pass_context
def uninstall_customer_fields_cmd(context):
    """Remove Print Designer Customer custom fields"""
    site = context.obj["sites"][0] if context.obj.get("sites") else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        uninstall_customer_fields()
        frappe.destroy()


# Commands are registered in hooks.py as string paths
