#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Install TBS Custom Fields for Tax Withholding Account Child Table.

Adds:
- tbs_wht_liability_account: Separate WHT Liability Account (for credit entries)

This allows Thai companies to configure separate Asset WHT and Liability WHT accounts
at the Tax Withholding Category level, reducing duplicate configuration.

Usage:
    bench execute print_designer.commands.install_wht_account_child_fields.execute
"""

import click
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


WHT_ACCOUNT_CHILD_CUSTOM_FIELDS = {
    "Tax Withholding Account": [
        {
            "fieldname": "pd_custom_wht_liability_account",
            "fieldtype": "Link",
            "label": "WHT Liability Account",
            "translatable": 0,
            "insert_after": "account",
            "options": "Account",
            "description": "Separate WHT Liability Account for credit (remittance) entries. Falls back to Company.default_wht_debt_account if not set.",
            "in_list_view": 1,
            "module": "Print Designer",
        },
    ]
}


def execute():
    """Main installation function."""
    print("Installing Tax Withholding Account child table custom fields...")
    create_wht_account_child_fields()
    frappe.clear_cache()
    print("✓ Tax Withholding Account custom fields installed successfully")
    print("   - tbs_wht_liability_account (WHT Liability Account)")


def create_wht_account_child_fields():
    """Create the custom fields on Tax Withholding Account child table."""
    create_custom_fields(WHT_ACCOUNT_CHILD_CUSTOM_FIELDS, update=True)


def check_wht_account_child_fields():
    """Check if fields are installed."""
    fields = ["pd_custom_wht_liability_account"]
    all_exist = True
    for fieldname in fields:
        exists = frappe.db.exists(
            "Custom Field",
            {"dt": "Tax Withholding Account", "fieldname": fieldname}
        )
        status = "✓" if exists else "✗"
        print(f"  {status} {fieldname}: {'Installed' if exists else 'Missing'}")
        if not exists:
            all_exist = False
    if all_exist:
        print("All Tax Withholding Account custom fields are installed.")
        return True
    else:
        print("Some fields are missing.")
        return False


def remove_wht_account_child_fields():
    """Remove custom fields."""
    print("Removing Tax Withholding Account child table custom fields...")
    fields = [
        {"dt": "Tax Withholding Account", "fieldname": "pd_custom_wht_liability_account"},
    ]
    for field in fields:
        custom_field = frappe.db.exists("Custom Field", field)
        if custom_field:
            frappe.delete_doc("Custom Field", custom_field, force=True)
            print(f"  ✓ Removed {field['fieldname']}")
    frappe.clear_cache()
    print("✓ Tax Withholding Account custom fields removed")


# ── Click CLI commands (bench commands) ──────────────────────────────────────


@click.command("install-wht-account-child-fields")
@click.option("--site", help="Site name")
def install_wht_account_child_fields_cmd(site):
    """CLI: Install TBS custom fields on Tax Withholding Account child table"""
    frappe.init(site=site)
    frappe.connect()
    try:
        create_wht_account_child_fields()
    finally:
        frappe.destroy()


@click.command("check-wht-account-child-fields")
@click.option("--site", help="Site name")
def check_wht_account_child_fields_cmd(site):
    """CLI: Verify Tax Withholding Account child table custom fields are installed"""
    frappe.init(site=site)
    frappe.connect()
    try:
        check_wht_account_child_fields()
    finally:
        frappe.destroy()


@click.command("uninstall-wht-account-child-fields")
@click.option("--site", help="Site name")
def uninstall_wht_account_child_fields_cmd(site):
    """CLI: Remove TBS custom fields from Tax Withholding Account child table"""
    frappe.init(site=site)
    frappe.connect()
    try:
        remove_wht_account_child_fields()
    finally:
        frappe.destroy()


commands = [
    install_wht_account_child_fields_cmd,
    check_wht_account_child_fields_cmd,
    uninstall_wht_account_child_fields_cmd,
]
