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
                "fieldname": "is_service_item",
                "label": "Is Service",
                "fieldtype": "Check",
                "insert_after": "is_fixed_asset",
                "description": "Check if this item represents a service (subject to 3% WHT in Thailand)",
                "default": 0,
            }
        ]
    }
    
    try:
        # Check if field already exists
        if frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": "is_service_item"}):
            click.echo("✅ 'Is Service' field already exists")
            return True
            
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
        field_exists = frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": "is_service_item"})
        
        if field_exists:
            click.echo("✅ 'Is Service' field found in Item DocType")
            return True
        else:
            click.echo("❌ 'Is Service' field not found in Item DocType")
            return False
            
    except Exception as e:
        click.echo(f"❌ Error checking 'Is Service' field: {str(e)}")
        return False


if __name__ == "__main__":
    check_item_service_field()
    if not check_item_service_field():
        install_item_service_field()