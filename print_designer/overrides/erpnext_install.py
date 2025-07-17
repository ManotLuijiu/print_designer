# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def create_print_setting_custom_fields():
    """Override ERPNext's create_print_setting_custom_fields to add copy-related fields"""
    
    # Create the original ERPNext fields plus our copy-related fields
    create_custom_fields(
        {
            "Print Settings": [
                # Original ERPNext fields
                {
                    "label": _("Compact Item Print"),
                    "fieldname": "compact_item_print",
                    "fieldtype": "Check",
                    "default": "1",
                    "insert_after": "with_letterhead",
                },
                {
                    "label": _("Print UOM after Quantity"),
                    "fieldname": "print_uom_after_quantity",
                    "fieldtype": "Check",
                    "default": "0",
                    "insert_after": "compact_item_print",
                },
                {
                    "label": _("Print taxes with zero amount"),
                    "fieldname": "print_taxes_with_zero_amount",
                    "fieldtype": "Check",
                    "default": "0",
                    "insert_after": "allow_print_for_cancelled",
                },
                # Print Designer copy-related fields
                {
                    "label": _("Copy Settings"),
                    "fieldname": "copy_settings_section",
                    "fieldtype": "Section Break",
                    "insert_after": "print_taxes_with_zero_amount",
                    "collapsible": 1,
                },
                {
                    "label": _("Enable Multiple Copies"),
                    "fieldname": "enable_multiple_copies",
                    "fieldtype": "Check",
                    "default": "0",
                    "insert_after": "copy_settings_section",
                    "description": _("Enable multiple copy generation for print formats"),
                },
                {
                    "label": _("Default Copy Count"),
                    "fieldname": "default_copy_count",
                    "fieldtype": "Int",
                    "default": "2",
                    "insert_after": "enable_multiple_copies",
                    "depends_on": "enable_multiple_copies",
                    "description": _("Default number of copies to generate"),
                },
                {
                    "label": _("Copy Labels"),
                    "fieldname": "copy_labels_column",
                    "fieldtype": "Column Break",
                    "insert_after": "default_copy_count",
                },
                {
                    "label": _("Default Original Label"),
                    "fieldname": "default_original_label",
                    "fieldtype": "Data",
                    "default": _("Original"),
                    "insert_after": "copy_labels_column",
                    "depends_on": "enable_multiple_copies",
                    "description": _("Default label for original copy"),
                },
                {
                    "label": _("Default Copy Label"),
                    "fieldname": "default_copy_label",
                    "fieldtype": "Data",
                    "default": _("Copy"),
                    "insert_after": "default_original_label",
                    "depends_on": "enable_multiple_copies",
                    "description": _("Default label for additional copies"),
                },
                {
                    "label": _("Show Copy Controls in Toolbar"),
                    "fieldname": "show_copy_controls_in_toolbar",
                    "fieldtype": "Check",
                    "default": "1",
                    "insert_after": "default_copy_label",
                    "depends_on": "enable_multiple_copies",
                    "description": _("Show copy controls in print preview toolbar"),
                },
            ]
        }
    )
    
    # Setup default values after creating fields
    setup_default_print_settings()


def setup_default_print_settings():
    """Setup default values for print settings"""
    
    try:
        # Get Print Settings single doctype
        print_settings = frappe.get_single("Print Settings")
        
        # Set default values if they don't exist
        if not hasattr(print_settings, 'enable_multiple_copies') or print_settings.enable_multiple_copies is None:
            print_settings.enable_multiple_copies = 1  # Enable by default
        
        if not hasattr(print_settings, 'default_copy_count') or not print_settings.default_copy_count:
            print_settings.default_copy_count = 2
        
        if not hasattr(print_settings, 'default_original_label') or not print_settings.default_original_label:
            print_settings.default_original_label = _("Original")
        
        if not hasattr(print_settings, 'default_copy_label') or not print_settings.default_copy_label:
            print_settings.default_copy_label = _("Copy")
        
        if not hasattr(print_settings, 'show_copy_controls_in_toolbar') or print_settings.show_copy_controls_in_toolbar is None:
            print_settings.show_copy_controls_in_toolbar = 1
        
        # Save the settings
        print_settings.flags.ignore_permissions = True
        print_settings.flags.ignore_mandatory = True
        print_settings.save()
        
        frappe.logger().info("Print Designer copy settings configured successfully")
        
    except Exception as e:
        frappe.logger().error(f"Error setting up Print Designer settings: {str(e)}")
        # Continue without failing the installation
        pass