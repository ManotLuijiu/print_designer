# Copyright (c) 2026, Print Designer
# For license information, please see license.txt

"""
Override DocField options for charge_type to add "Thai Tax Compliance".

This ensures the new tax type is available across all installations,
not just those where the migration was run.

The actual options are set in the JSON schema files:
- erpnext/accounts/doctype/sales_taxes_and_charges/sales_taxes_and_charges.json
- erpnext/accounts/doctype/purchase_taxes_and_charges/purchase_taxes_and_charges.json
"""

import os
import frappe


def patch_charge_type_options():
    """
    Patch the JSON schema files to add Thai Tax Compliance option.
    This runs during app installation to ensure the option exists.
    """
    frappe_path = frappe.get_app_path("erpnext")
    
    # Files to patch
    files_to_patch = [
        os.path.join(
            frappe_path, 
            "accounts/doctype/sales_taxes_and_charges/sales_taxes_and_charges.json"
        ),
        os.path.join(
            frappe_path,
            "accounts/doctype/purchase_taxes_and_charges/purchase_taxes_and_charges.json"
        ),
    ]
    
    for json_file in files_to_patch:
        if os.path.exists(json_file):
            patch_file(json_file)


def patch_file(json_file):
    """Patch a single JSON file to add Thai Tax Compliance option."""
    import json
    
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Find and update the charge_type field
    for field in data.get("fields", []):
        if field.get("fieldname") == "charge_type":
            current_options = field.get("options", "")
            
            # Check if already patched
            if "Thai Tax Compliance" in current_options:
                print(f"⏭️ {json_file} already has 'Thai Tax Compliance'")
                return
            
            # Add the new option
            field["options"] = current_options.strip() + "\nThai Tax Compliance"
            
            # Write back
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=1, ensure_ascii=False)
            
            print(f"✅ Patched {json_file} with 'Thai Tax Compliance'")


def execute():
    """Called during app installation."""
    patch_charge_type_options()
