"""
Print Settings API for Print Designer
=====================================
Handles installation and migration of Print Settings custom fields.

This module consolidates all Print Settings field logic that was previously
scattered across install.py.

Functions:
- setup_enhanced_print_settings() - Main entry point
- create_enhanced_print_settings_fields() - Fresh install
- migrate_existing_print_settings() - Existing installation migration
- setup_default_print_settings_values() - Set defaults
"""

import frappe


def setup_enhanced_print_settings():
    """
    Consolidated Print Settings setup - works with or without ERPNext.
    Safe for both fresh installations and existing user migrations.
    """
    if not frappe.db.exists("DocType", "Print Settings"):
        print("Print Settings DocType not found, skipping setup")
        return

    try:
        print("Setting up enhanced Print Settings...")

        # Check if this is a migration scenario
        is_migration = frappe.db.get_value(
            "Custom Field",
            {"dt": "Print Settings", "fieldname": "enable_multiple_copies"},
            "name",
        )

        if is_migration:
            print("Detected existing installation - performing safe migration...")
            migrate_existing_print_settings()
        else:
            print("Fresh installation detected - creating new fields...")
            create_enhanced_print_settings_fields()

        setup_default_print_settings_values()
        frappe.db.commit()
        print("Enhanced Print Settings configured successfully")

    except Exception as e:
        print(f"Error setting up enhanced Print Settings: {str(e)}")
        frappe.log_error(message=str(e), title="Print Settings setup failed")


def migrate_existing_print_settings():
    """Safe migration for existing users - updates field dependencies without recreating fields"""
    try:
        print("Updating existing Print Settings fields for compatibility...")

        # Import from consolidated command module
        from print_designer.commands.install_print_settings_fields import (
            install_print_settings_fields,
        )

        install_print_settings_fields()

    except Exception as e:
        print(f"Error migrating Print Settings: {str(e)}")
        frappe.log_error(message=str(e), title="Print Settings migration failed")


def create_enhanced_print_settings_fields():
    """Create Print Settings fields for fresh installations"""
    try:
        print("Creating enhanced Print Settings fields...")

        # Import from consolidated command module
        from print_designer.commands.install_print_settings_fields import (
            install_print_settings_fields,
        )

        install_print_settings_fields()

    except Exception as e:
        print(f"Error creating Print Settings fields: {str(e)}")
        frappe.log_error(message=str(e), title="Print Settings field creation failed")


def setup_default_print_settings_values():
    """Set default values for Print Settings fields"""
    try:
        print_settings = frappe.get_single("Print Settings")

        defaults = {
            "enable_multiple_copies": 0,
            "default_copy_count": 2,
            "default_original_label": "Original",
            "default_copy_label": "Copy",
            "show_copy_controls_in_toolbar": 1,
            "watermark_settings": "None",
            "watermark_position": "Top Right",
            "watermark_font_size": 24,
            "watermark_font_family": "Kanit",
            "watermark_margin_top": 0,
            "watermark_margin_right": 0,
            "watermark_margin_bottom": 0,
            "watermark_margin_left": 0,
            "page_number_display": "Show",
            "page_number_position": "Bottom Center",
            "page_number_font_size": 10,
            "page_number_font_family": "Sarabun",
        }

        updated = False
        for field, default_value in defaults.items():
            if not print_settings.get(field):
                print_settings.set(field, default_value)
                updated = True

        if updated:
            print_settings.save()
            print("Print Settings default values set")

    except Exception as e:
        print(f"Warning: Could not set Print Settings defaults: {str(e)}")


def ensure_custom_fields():
    """
    Ensure print_designer custom fields are installed after migration.
    This function runs after every migration to make sure that custom fields
    like 'print_designer_template_app' are always present.
    """
    try:
        from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

        from print_designer.custom_fields import CUSTOM_FIELDS

        # Check if print_designer_template_app field exists
        existing_field = frappe.db.get_value(
            "Custom Field", {"fieldname": "print_designer_template_app"}, "name"
        )

        if not existing_field:
            print("Installing missing print_designer custom fields...")
            create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)
            frappe.db.commit()
            print("✅ Print Designer custom fields installed successfully")

        # Enhanced Print Settings (includes watermark, copy, page number)
        setup_enhanced_print_settings()

    except Exception as e:
        frappe.log_error(f"Error ensuring print_designer custom fields: {str(e)}")
        print(f"⚠️  Warning: Could not install print_designer custom fields: {str(e)}")
