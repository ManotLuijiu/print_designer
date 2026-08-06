"""
Custom Field Management Commands for Stock Entry DocType
Handles installation of receiver field for print format.
"""

import click
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Field configuration for Stock Entry DocType
STOCK_ENTRY_CUSTOM_FIELDS = {
    "Stock Entry": [
        {
            "fieldname": "pd_custom_receiver",
            "fieldtype": "Link",
            "label": "Receiver",
            "options": "Employee",
            "insert_after": "posting_time",
            "module": "Print Designer",
            "description": "Employee who receives the stock transfer",
        },
    ]
}


def create_stock_entry_fields():
    """Install Stock Entry custom fields."""
    try:
        print("Installing Stock Entry custom fields...")
        create_custom_fields(STOCK_ENTRY_CUSTOM_FIELDS, update=True)
        frappe.db.commit()
        print("Done!")
        return True
    except Exception as e:
        frappe.db.rollback()
        print(f"Error: {e}")
        return False


def execute():
    """Called from after_install and after_migrate hooks"""
    create_stock_entry_fields()
    frappe.clear_cache()


# Click CLI Commands
@click.command("install-stock-entry-fields")
@click.pass_context
def install_stock_entry_fields_cmd(context):
    """Install Stock Entry custom fields"""
    site = context.obj["sites"][0] if context.obj.get("sites") else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        create_stock_entry_fields()
        frappe.destroy()
