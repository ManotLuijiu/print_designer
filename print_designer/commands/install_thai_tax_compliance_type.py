"""
Add 'Thai Tax Compliance' to charge_type options in Sales Taxes and Charges.

This allows users to select Thai WHT type directly in the tax table,
showing negative amounts (e.g., -1,800 instead of 1,800).

Usage:
    bench --site <site> execute print_designer.print_designer.commands.install_thai_tax_compliance_type.execute
"""

import frappe
from frappe.custom.doctype.property_setter.property_setter import delete_property_setter


def execute():
    """Add 'Thai Tax Compliance' to charge_type options."""
    
    # Add to Sales Taxes and Charges
    add_thai_tax_type_to_charge_type("Sales Taxes and Charges")
    
    # Add to Purchase Taxes and Charges
    add_thai_tax_type_to_charge_type("Purchase Taxes and Charges")
    
    frappe.clear_cache()


def add_thai_tax_type_to_charge_type(doctype):
    """Add Thai Tax Compliance option to charge_type field."""
    
    field_name = "charge_type"
    new_option = "Thai Tax Compliance"
    
    # Get current options
    current_options = frappe.get_value(
        "DocField",
        {"parent": doctype, "fieldname": field_name},
        "options"
    ) or ""
    
    # Check if already exists
    if new_option in current_options:
        print(f"⏭️ {doctype}.charge_type already has '{new_option}'")
        return
    
    # Add new option (at the beginning, after newline)
    updated_options = current_options.strip() + f"\n{new_option}"
    
    # Update DocField
    frappe.db.set_value(
        "DocField",
        {"parent": doctype, "fieldname": field_name},
        "options",
        updated_options
    )
    
    print(f"✅ Added '{new_option}' to {doctype}.charge_type")


def remove_thai_tax_type_from_charge_type(doctype):
    """Remove Thai Tax Compliance option from charge_type field."""
    
    field_name = "charge_type"
    option_to_remove = "Thai Tax Compliance"
    
    # Get current options
    current_options = frappe.get_value(
        "DocField",
        {"parent": doctype, "fieldname": field_name},
        "options"
    ) or ""
    
    # Remove the option
    lines = current_options.split("\n")
    updated_lines = [line for line in lines if line.strip() != option_to_remove]
    updated_options = "\n".join(updated_lines)
    
    # Update DocField
    frappe.db.set_value(
        "DocField",
        {"parent": doctype, "fieldname": field_name},
        "options",
        updated_options
    )
    
    print(f"✅ Removed '{option_to_remove}' from {doctype}.charge_type")


def remove():
    """Remove Thai Tax Compliance from charge_type options."""
    
    remove_thai_tax_type_from_charge_type("Sales Taxes and Charges")
    remove_thai_tax_type_from_charge_type("Purchase Taxes and Charges")
    
    frappe.clear_cache()
