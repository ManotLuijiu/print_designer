"""
Print Settings Custom Fields for Print Designer
============================================
Consolidates all Print Settings custom fields:
- Copy Settings (enable_multiple_copies, etc.)
- Watermark Settings (watermark_settings, position, font, margins)
- Page Number Settings (display, position, font)

Used by:
- after_install hook
- after_migrate hook (idempotent — safe to run multiple times)
- before_uninstall hook (cleanup)

CLI commands:
- bench --site <site> install-print-settings-fields
- bench --site <site> uninstall-print-settings-fields
"""

import click
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# =============================================================================
# FIELD CONFIGURATIONS
# =============================================================================

# All Print Settings custom fields for Print Designer
PRINT_SETTINGS_CUSTOM_FIELDS = {
    "Print Settings": [
        # Copy Settings Section
        {
            "label": "Copy Settings",
            "fieldname": "copy_settings_section",
            "fieldtype": "Section Break",
            "insert_after": "print_taxes_with_zero_amount",
            "collapsible": 1,
        },
        {
            "label": "Enable Multiple Copies",
            "fieldname": "enable_multiple_copies",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "copy_settings_section",
        },
        {
            "label": "Default Copy Count",
            "fieldname": "default_copy_count",
            "fieldtype": "Int",
            "default": "2",
            "insert_after": "enable_multiple_copies",
            "depends_on": "enable_multiple_copies",
            "description": "Default number of copies to generate",
        },
        {
            "label": "Copy Labels",
            "fieldname": "copy_labels_column",
            "fieldtype": "Column Break",
            "insert_after": "default_copy_count",
        },
        {
            "label": "Default Original Label",
            "fieldname": "default_original_label",
            "fieldtype": "Data",
            "default": "Original",
            "insert_after": "copy_labels_column",
            "depends_on": "enable_multiple_copies",
            "description": "Default label for original copy",
        },
        {
            "label": "Default Copy Label",
            "fieldname": "default_copy_label",
            "fieldtype": "Data",
            "default": "Copy",
            "insert_after": "default_original_label",
            "depends_on": "enable_multiple_copies",
            "description": "Default label for additional copies",
        },
        {
            "label": "Show Copy Controls in Toolbar",
            "fieldname": "show_copy_controls_in_toolbar",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "default_copy_label",
            "depends_on": "enable_multiple_copies",
            "description": "Show copy controls in print preview toolbar",
        },
        # Watermark Settings Section
        {
            "label": "Watermark Settings",
            "fieldname": "watermark_settings_section",
            "fieldtype": "Section Break",
            "insert_after": "show_copy_controls_in_toolbar",
            "collapsible": 1,
        },
        {
            "label": "Watermark per Page",
            "fieldname": "watermark_settings",
            "fieldtype": "Select",
            "options": "None\nOriginal on First Page\nCopy on All Pages\nOriginal,Copy on Sequence",
            "default": "None",
            "insert_after": "watermark_settings_section",
        },
        {
            "label": "Watermark Position",
            "fieldname": "watermark_position",
            "fieldtype": "Select",
            "options": "Top Left\nTop Center\nTop Right\nMiddle Left\nMiddle Center\nMiddle Right\nBottom Left\nBottom Center\nBottom Right",
            "default": "Top Right",
            "insert_after": "watermark_settings",
            "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
        },
        {
            "label": "Watermark Font Family",
            "fieldname": "watermark_font_family",
            "fieldtype": "Select",
            "options": "Kanit\nSarabun\nArial\nHelvetica\nTimes New Roman\nCourier New\nVerdana\nGeorgia\nTahoma\nCalibri",
            "default": "Kanit",
            "insert_after": "watermark_position",
            "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
        },
        {
            "label": "Watermark Font Size (px)",
            "fieldname": "watermark_font_size",
            "fieldtype": "Int",
            "default": "24",
            "insert_after": "watermark_font_family",
            "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
        },
        {
            "fieldname": "watermark_col_break",
            "fieldtype": "Column Break",
            "insert_after": "watermark_font_size",
        },
        {
            "label": "Margin Top (mm)",
            "fieldname": "watermark_margin_top",
            "fieldtype": "Int",
            "default": "0",
            "insert_after": "watermark_col_break",
            "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
        },
        {
            "label": "Margin Right (mm)",
            "fieldname": "watermark_margin_right",
            "fieldtype": "Int",
            "default": "0",
            "insert_after": "watermark_margin_top",
            "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
        },
        {
            "label": "Margin Bottom (mm)",
            "fieldname": "watermark_margin_bottom",
            "fieldtype": "Int",
            "default": "0",
            "insert_after": "watermark_margin_right",
            "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
        },
        {
            "label": "Margin Left (mm)",
            "fieldname": "watermark_margin_left",
            "fieldtype": "Int",
            "default": "0",
            "insert_after": "watermark_margin_bottom",
            "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
        },
        # Page Number Settings Section
        {
            "label": "Page Number Settings",
            "fieldname": "page_number_section",
            "fieldtype": "Section Break",
            "insert_after": "watermark_margin_left",
            "collapsible": 1,
        },
        {
            "label": "Page Number",
            "fieldname": "page_number_display",
            "fieldtype": "Select",
            "options": "None\nShow",
            "default": "Show",
            "insert_after": "page_number_section",
        },
        {
            "label": "Page Number Position",
            "fieldname": "page_number_position",
            "fieldtype": "Select",
            "options": "Bottom Center\nTop Right\nTop Left\nTop Center\nBottom Right\nBottom Left",
            "default": "Bottom Center",
            "insert_after": "page_number_display",
            "depends_on": "eval:doc.page_number_display == 'Show'",
        },
        {
            "label": "Page Number Font Family",
            "fieldname": "page_number_font_family",
            "fieldtype": "Select",
            "options": "Arial\nSarabun\nKanit\nNoto Sans Thai\nHelvetica\nTimes New Roman",
            "default": "Sarabun",
            "insert_after": "page_number_position",
            "depends_on": "eval:doc.page_number_display == 'Show'",
        },
        {
            "label": "Page Number Font Size (pt)",
            "fieldname": "page_number_font_size",
            "fieldtype": "Int",
            "default": "10",
            "insert_after": "page_number_font_family",
            "depends_on": "eval:doc.page_number_display == 'Show'",
        },
    ]
}

# All fieldnames for verification + uninstall
ALL_FIELDNAMES = [
    # Copy settings
    "copy_settings_section",
    "enable_multiple_copies",
    "default_copy_count",
    "copy_labels_column",
    "default_original_label",
    "default_copy_label",
    "show_copy_controls_in_toolbar",
    # Watermark settings
    "watermark_settings_section",
    "watermark_settings",
    "watermark_position",
    "watermark_font_family",
    "watermark_font_size",
    "watermark_col_break",
    "watermark_margin_top",
    "watermark_margin_right",
    "watermark_margin_bottom",
    "watermark_margin_left",
    # Page number settings
    "page_number_section",
    "page_number_display",
    "page_number_position",
    "page_number_font_family",
    "page_number_font_size",
]

# =============================================================================
# INSTALL FUNCTION
# =============================================================================


def install_print_settings_fields():
    """
    Install all Print Settings custom fields for Print Designer.

    Called from:
    - after_install hook
    - after_migrate hook (idempotent — safe to run multiple times)
    - CLI: install-print-settings-fields
    """
    try:
        print("Installing Print Settings custom fields for Print Designer...")

        # Skip if Print Settings DocType doesn't exist
        if not frappe.db.exists("DocType", "Print Settings"):
            print("   Skipping: Print Settings DocType not found")
            return True

        # Delete existing fields to ensure clean install with correct ordering
        _uninstall_existing_fields()

        # Create all fields fresh
        create_custom_fields(PRINT_SETTINGS_CUSTOM_FIELDS, update=True)

        # Apply Property Setters for Print Settings defaults
        _apply_property_setters()

        frappe.db.commit()

        print("   Print Settings custom fields installed:")
        for fn in ALL_FIELDNAMES:
            print(f"   - {fn}")

        # Set sensible defaults
        _set_defaults()

        print("Done!")
        return True

    except Exception as e:
        frappe.db.rollback()
        print(f"Error: {str(e)}")
        frappe.log_error("Print Settings Custom Fields Installation Error", str(e))
        return False


def _uninstall_existing_fields():
    """Delete existing Print Settings custom fields for clean reinstall."""
    for fieldname in ALL_FIELDNAMES:
        existing = frappe.db.exists(
            "Custom Field", {"dt": "Print Settings", "fieldname": fieldname}
        )
        if existing:
            frappe.delete_doc("Custom Field", existing, force=True)


def _apply_property_setters():
    """Apply Property Setters to set defaults for Print Settings standard fields."""
    from frappe.custom.doctype.property_setter.property_setter import (
        make_property_setter,
    )

    # Always set pdf_generator default to chrome
    make_property_setter(
        doctype="Print Settings",
        fieldname="pdf_generator",
        property="default",
        value="chrome",
        property_type="Data",
        for_doctype=False,
    )


def _fix_field_ordering():
    """Fix insert_after for existing fields that may have wrong ordering."""
    # Map of fieldname -> correct insert_after
    ordering_fixes = {
        # Page Number Settings (Page Number section should come AFTER Watermark margins)
        "page_number_section": "watermark_margin_left",
        "page_number_display": "page_number_section",
        "page_number_position": "page_number_display",
        "page_number_font_family": "page_number_position",
        "page_number_font_size": "page_number_font_family",
        # Watermark Settings (Per Page -> Position -> Font Family -> Font Size)
        "watermark_settings_section": "show_copy_controls_in_toolbar",
        "watermark_settings": "watermark_settings_section",
        "watermark_position": "watermark_settings",
        "watermark_font_family": "watermark_position",
        "watermark_font_size": "watermark_font_family",
        "watermark_col_break": "watermark_font_size",
        "watermark_margin_top": "watermark_col_break",
        "watermark_margin_right": "watermark_margin_top",
        "watermark_margin_bottom": "watermark_margin_right",
        "watermark_margin_left": "watermark_margin_bottom",
    }
    for fieldname, correct_insert_after in ordering_fixes.items():
        existing = frappe.db.get_value(
            "Custom Field",
            {"dt": "Print Settings", "fieldname": fieldname},
            ["name", "insert_after"],
            as_dict=True,
        )
        if existing and existing.insert_after != correct_insert_after:
            frappe.db.set_value(
                "Custom Field",
                existing.name,
                "insert_after",
                correct_insert_after,
            )
            print(
                f"   Fixed {fieldname}.insert_after: {existing.insert_after} -> {correct_insert_after}"
            )


def _set_defaults():
    """Set default values on the Print Settings singleton."""
    try:
        ps = frappe.get_single("Print Settings")

        defaults = {
            # Copy settings
            "enable_multiple_copies": 0,
            "default_copy_count": 2,
            "default_original_label": "Original",
            "default_copy_label": "Copy",
            "show_copy_controls_in_toolbar": 1,
            # Watermark settings
            "watermark_settings": "None",
            "watermark_position": "Top Right",
            "watermark_font_family": "Kanit",
            "watermark_font_size": 24,
            "watermark_margin_top": 0,
            "watermark_margin_right": 0,
            "watermark_margin_bottom": 0,
            "watermark_margin_left": 0,
            # Page number settings
            "page_number_display": "Show",
            "page_number_position": "Bottom Center",
            "page_number_font_size": 10,
            "page_number_font_family": "Sarabun",
        }

        updated = False
        for field, default_value in defaults.items():
            if not ps.get(field):
                ps.set(field, default_value)
                updated = True

        if updated:
            ps.save()
            print("   Default values set")

    except Exception as e:
        print(f"   Warning: Could not set defaults: {str(e)}")


# =============================================================================
# CHECK FUNCTION
# =============================================================================


def check_print_settings_fields():
    """
    Verify that all Print Settings custom fields are installed.

    Returns:
        dict: { 'installed': [...], 'missing': [...], 'all_installed': bool }
    """
    installed = []
    missing = []

    for fieldname in ALL_FIELDNAMES:
        exists = frappe.db.get_value(
            "Custom Field",
            {"dt": "Print Settings", "fieldname": fieldname},
            "name",
        )
        if exists:
            installed.append(fieldname)
        else:
            missing.append(fieldname)

    return {
        "installed": installed,
        "missing": missing,
        "all_installed": len(missing) == 0,
    }


# =============================================================================
# UNINSTALL FUNCTION
# =============================================================================


def uninstall_print_settings_fields():
    """
    Remove all Print Settings custom fields for Print Designer.

    Called from:
    - before_uninstall hook
    - CLI: uninstall-print-settings-fields
    """
    try:
        print("Removing Print Settings custom fields for Print Designer...")

        for fieldname in ALL_FIELDNAMES:
            existing = frappe.db.get_value(
                "Custom Field",
                {"dt": "Print Settings", "fieldname": fieldname},
                "name",
            )
            if existing:
                frappe.delete_doc("Custom Field", existing, ignore_permissions=True)
                print(f"   Removed {fieldname}")
            else:
                print(f"   {fieldname} not found (already removed)")

        frappe.db.commit()
        print("Done!")
        return True

    except Exception as e:
        frappe.db.rollback()
        print(f"Error: {str(e)}")
        frappe.log_error("Print Settings Custom Fields Removal Error", str(e))
        return False


# =============================================================================
# CLI COMMAND WRAPPERS
# =============================================================================


@click.command("install-print-settings-fields")
def install_print_settings_fields_cmd():
    """Install Print Settings custom fields for Print Designer."""
    install_print_settings_fields()


@click.command("check-print-settings-fields")
def check_print_settings_fields_cmd():
    """Check status of Print Settings custom fields."""
    status = check_print_settings_fields()
    click.echo(f"Installed: {status['installed']}")
    click.echo(f"Missing:   {status['missing']}")
    click.echo(f"All installed: {status['all_installed']}")


@click.command("uninstall-print-settings-fields")
def uninstall_print_settings_fields_cmd():
    """Uninstall Print Settings custom fields from Print Designer."""
    uninstall_print_settings_fields()


commands = [
    install_print_settings_fields_cmd,
    check_print_settings_fields_cmd,
    uninstall_print_settings_fields_cmd,
]
