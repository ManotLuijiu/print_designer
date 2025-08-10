#!/usr/bin/env python3

import click
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install_wht_rate_field():
    """Install the WHT rate field for Company DocType"""
    
    click.echo("Installing dynamic WHT rate field for Company...")
    
    # Check if field already exists
    if frappe.db.exists("Custom Field", {"dt": "Company", "fieldname": "default_wht_rate"}):
        click.echo("✅ Company default_wht_rate field already exists")
        return True
    
    # Define the field
    wht_rate_field = {
        "Company": [
            {
                "fieldname": "default_wht_rate",
                "fieldtype": "Percent",
                "label": "Default WHT Rate (%)",
                "insert_after": "thailand_service_business",
                "depends_on": "eval:doc.thailand_service_business",
                "description": "Default withholding tax rate for services (e.g., 3% for most services)",
                "default": 3.0,
                "precision": 2,
            }
        ]
    }
    
    try:
        create_custom_fields(wht_rate_field, update=False)
        frappe.db.commit()
        click.echo("✅ Company default_wht_rate field added successfully!")
        return True
    except Exception as e:
        click.echo(f"❌ Error adding WHT rate field: {str(e)}")
        frappe.log_error(f"Error installing WHT rate field: {str(e)}")
        return False


def check_wht_rate_field():
    """Check if the WHT rate field exists"""
    
    try:
        field_exists = frappe.db.exists("Custom Field", {"dt": "Company", "fieldname": "default_wht_rate"})
        
        if field_exists:
            click.echo("✅ Company default_wht_rate field found")
            return True
        else:
            click.echo("❌ Company default_wht_rate field not found")
            return False
            
    except Exception as e:
        click.echo(f"❌ Error checking WHT rate field: {str(e)}")
        return False


if __name__ == "__main__":
    check_wht_rate_field()
    if not check_wht_rate_field():
        install_wht_rate_field()