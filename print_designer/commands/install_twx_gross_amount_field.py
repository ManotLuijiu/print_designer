#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Install TBS Custom Fields for Tax Withholding Entry.

Adds:
- pd_custom_gross_amount: Gross amount before WHT (for Thai gross-up calculation)
  This field stores the calculated gross amount (before tax) so that:
  - taxable_amount = gross_amount (displayed as "Base Taxable Amount")
  - withholding_amount = gross_amount × tax_rate

Usage:
    bench execute print_designer.commands.install_twx_gross_amount_field.execute
"""

import click
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


TWX_CUSTOM_FIELDS = {
    "Tax Withholding Entry": [
        {
            "fieldname": "pd_custom_gross_amount",
            "fieldtype": "Currency",
            "label": "Gross Amount",
            "translatable": 0,
            "insert_after": "tax_withholding_group",
            "description": "Gross amount before WHT deduction. For Thai gross-up: if net=9700 and rate=3%, gross=10000, WHT=300.",
            "in_list_view": 1,
            "module": "Print Designer",
            "precision": 2,
        },
    ]
}


def execute():
    """Main installation function."""
    print("Installing Tax Withholding Entry custom fields...")
    create_twx_custom_fields()
    frappe.clear_cache()
    print("✓ Tax Withholding Entry custom fields installed successfully")
    print("   - pd_custom_gross_amount (Gross Amount)")


def create_twx_custom_fields():
    """Create the custom fields on Tax Withholding Entry."""
    create_custom_fields(TWX_CUSTOM_FIELDS, update=True)


def check_fields_exist():
    """Check if fields are installed."""
    fields = ["pd_custom_gross_amount"]
    all_exist = True
    for fieldname in fields:
        exists = frappe.db.exists(
            "Custom Field",
            {"dt": "Tax Withholding Entry", "fieldname": fieldname}
        )
        status = "✓" if exists else "✗"
        print(f"  {status} {fieldname}: {'Installed' if exists else 'Missing'}")
        if not exists:
            all_exist = False
    if all_exist:
        print("All Tax Withholding Entry custom fields are installed.")
        return True
    else:
        print("Some fields are missing.")
        return False


def remove_twx_custom_fields():
    """Remove custom fields."""
    print("Removing Tax Withholding Entry custom fields...")
    fields = [
        {"dt": "Tax Withholding Entry", "fieldname": "pd_custom_gross_amount"},
    ]
    for field in fields:
        custom_field = frappe.db.exists("Custom Field", field)
        if custom_field:
            frappe.delete_doc("Custom Field", custom_field, force=True)
            print(f"  ✓ Removed {field['fieldname']}")
    frappe.clear_cache()
    print("✓ Tax Withholding Entry custom fields removed")


@click.command("install-twx-gross-amount-field")
@click.option("--site", help="Site name")
def install_twx_gross_amount_cmd(site):
    """CLI: Install pd_custom_gross_amount field on Tax Withholding Entry"""
    frappe.init(site=site)
    frappe.connect()
    try:
        create_twx_custom_fields()
    finally:
        frappe.destroy()


@click.command("check-twx-gross-amount-field")
@click.option("--site", help="Site name")
def check_twx_gross_amount_cmd(site):
    """CLI: Verify pd_custom_gross_amount field is installed"""
    frappe.init(site=site)
    frappe.connect()
    try:
        check_fields_exist()
    finally:
        frappe.destroy()


@click.command("uninstall-twx-gross-amount-field")
@click.option("--site", help="Site name")
def uninstall_twx_gross_amount_cmd(site):
    """CLI: Remove pd_custom_gross_amount field from Tax Withholding Entry"""
    frappe.init(site=site)
    frappe.connect()
    try:
        remove_twx_custom_fields()
    finally:
        frappe.destroy()


commands = [
    install_twx_gross_amount_cmd,
    check_twx_gross_amount_cmd,
    uninstall_twx_gross_amount_cmd,
]