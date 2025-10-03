#!/usr/bin/env python3

import click
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install_item_service_field():
    """Install the Is Service field for Item DocType"""

    click.echo("Installing 'Is Service' field for Item DocType...")

    # Define the field
    item_service_field = {
        "Item": [
            {
                "fieldname": "pd_custom_is_service_item",
                "label": "Is Service",
                "fieldtype": "Check",
                "insert_after": "is_fixed_asset",
                "description": "Check if this item represents a service (subject to 3% WHT in Thailand)",
                "default": 0,
                "module": "Print Designer",
            }
        ]
    }

    try:
        # Check if field already exists (check both old and new field names)
        if frappe.db.exists(
            "Custom Field", {"dt": "Item", "fieldname": "pd_custom_is_service_item"}
        ):
            click.echo("✅ 'Is Service' field already exists")
            return True
        elif frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": "is_service_item"}):
            click.echo(
                "⚠️ Found old 'is_service_item' field - migrating to proper naming convention..."
            )
            # Remove old field
            frappe.db.delete("Custom Field", {"dt": "Item", "fieldname": "is_service_item"})
            frappe.db.commit()

        # Create the field
        create_custom_fields(item_service_field, update=False)
        frappe.db.commit()

        click.echo("✅ 'Is Service' field installed successfully!")
        return True

    except Exception as e:
        click.echo(f"❌ Error installing 'Is Service' field: {str(e)}")
        frappe.log_error(f"Error installing Item service field: {str(e)}")
        return False


def check_item_service_field():
    """Check if the Is Service field exists"""

    try:
        # Check for new field name first
        field_exists = frappe.db.exists(
            "Custom Field", {"dt": "Item", "fieldname": "pd_custom_is_service_item"}
        )

        if field_exists:
            click.echo("✅ 'Is Service' field found in Item DocType (pd_custom_is_service_item)")
            return True

        # Check for old field name
        old_field_exists = frappe.db.exists(
            "Custom Field", {"dt": "Item", "fieldname": "is_service_item"}
        )
        if old_field_exists:
            click.echo("⚠️ Old 'Is Service' field found (is_service_item) - needs migration")
            return False

        click.echo("❌ 'Is Service' field not found in Item DocType")
        return False

    except Exception as e:
        click.echo(f"❌ Error checking 'Is Service' field: {str(e)}")
        return False


def uninstall_item_service_field():
    """Remove Item Is Service field during app uninstall"""

    try:
        click.echo("Removing 'Is Service' field from Item DocType...")

        # Delete custom field
        frappe.db.delete("Custom Field", {"dt": "Item", "fieldname": "pd_custom_is_service_item"})

        # Also remove old field name if it exists
        frappe.db.delete("Custom Field", {"dt": "Item", "fieldname": "is_service_item"})

        # Clear cache
        frappe.clear_cache(doctype="Item")
        frappe.db.commit()

        click.echo("✅ Successfully removed 'Is Service' field from Item DocType")
        return True

    except Exception as e:
        frappe.db.rollback()
        click.echo(f"❌ Error removing 'Is Service' field: {str(e)}")
        frappe.log_error(f"Error removing Item service field: {str(e)}")
        return False


if __name__ == "__main__":
    check_item_service_field()
    if not check_item_service_field():
        install_item_service_field()
