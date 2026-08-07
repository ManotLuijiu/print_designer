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
        # PDF Settings Section
        {
            "label": "Page Orientation",
            "fieldname": "page_orientation",
            "fieldtype": "Select",
            "options": "Portrait\nLandscape",
            "default": "Portrait",
            "insert_after": "pdf_page_size",
        },
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
            "label": "Copy Count",
            "fieldname": "default_copy_count",
            "fieldtype": "Int",
            "default": "2",
            "insert_after": "enable_multiple_copies",
            "depends_on": "enable_multiple_copies",
        },
        {
            "label": "Copy Labels",
            "fieldname": "copy_labels_column",
            "fieldtype": "Column Break",
            "insert_after": "default_copy_count",
        },
        {
            "label": "Original Label",
            "fieldname": "default_original_label",
            "fieldtype": "Data",
            "default": "Original",
            "insert_after": "copy_labels_column",
            "depends_on": "enable_multiple_copies",
        },
        {
            "label": "Copy Label",
            "fieldname": "default_copy_label",
            "fieldtype": "Data",
            "default": "Copy",
            "insert_after": "default_original_label",
            "depends_on": "enable_multiple_copies",
        },
        {
            "label": "Show Copy Controls in Toolbar",
            "fieldname": "show_copy_controls_in_toolbar",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "default_copy_label",
            "depends_on": "enable_multiple_copies",
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
            "default": "Original on First Page",
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
            "label": "Top (mm)",
            "fieldname": "watermark_top",
            "fieldtype": "Int",
            "default": "0",
            "insert_after": "watermark_col_break",
            "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
        },
        {
            "label": "Right (mm)",
            "fieldname": "watermark_right",
            "fieldtype": "Int",
            "default": "0",
            "insert_after": "watermark_top",
            "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
        },
        {
            "label": "Bottom (mm)",
            "fieldname": "watermark_bottom",
            "fieldtype": "Int",
            "default": "0",
            "insert_after": "watermark_right",
            "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
        },
        {
            "label": "Left (mm)",
            "fieldname": "watermark_left",
            "fieldtype": "Int",
            "default": "0",
            "insert_after": "watermark_bottom",
            "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
        },
        # Page Number Settings Section
        {
            "label": "Page Number Settings",
            "fieldname": "page_number_section",
            "fieldtype": "Section Break",
            "insert_after": "watermark_left",
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
            "options": "Top Right\nTop Left\nTop Center\nBottom Center\nBottom Right\nBottom Left",
            "default": "Top Right",
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
            "fieldname": "page_number_col_break",
            "fieldtype": "Column Break",
            "insert_after": "page_number_font_family",
        },
        {
            "label": "Page Number Font Size (pt)",
            "fieldname": "page_number_font_size",
            "fieldtype": "Int",
            "default": "8",
            "insert_after": "page_number_col_break",
            "depends_on": "eval:doc.page_number_display == 'Show'",
        },
        {
            "label": "Page Number Font Color",
            "fieldname": "page_number_font_color",
            "fieldtype": "Color",
            "default": "#4463F0",
            "insert_after": "page_number_font_size",
            "depends_on": "eval:doc.page_number_display == 'Show'",
        },
        {
            "label": "Page Number Border",
            "fieldname": "page_number_border",
            "fieldtype": "Select",
            "options": "None\nSolid\nDashed\nDotted",
            "default": "None",
            "insert_after": "page_number_font_color",
            "depends_on": "eval:doc.page_number_display == 'Show'",
        },
        {
            "fieldname": "page_number_col_break_02",
            "fieldtype": "Column Break",
            "insert_after": "page_number_border",
        },
        {
            "label": "Top (mm)",
            "fieldname": "page_number_top",
            "fieldtype": "Int",
            "default": "0",
            "insert_after": "page_number_col_break_02",
            "depends_on": "eval:doc.page_number_display && doc.page_number_display != 'None'",
        },
        {
            "label": "Right (mm)",
            "fieldname": "page_number_right",
            "fieldtype": "Int",
            "default": "0",
            "insert_after": "page_number_top",
            "depends_on": "eval:doc.page_number_display && doc.page_number_display != 'None'",
        },
        {
            "label": "Bottom (mm)",
            "fieldname": "page_number_bottom",
            "fieldtype": "Int",
            "default": "0",
            "insert_after": "page_number_right",
            "depends_on": "eval:doc.page_number_display && doc.page_number_display != 'None'",
        },
        {
            "label": "Left (mm)",
            "fieldname": "page_number_left",
            "fieldtype": "Int",
            "default": "0",
            "insert_after": "page_number_bottom",
            "depends_on": "eval:doc.page_number_display && doc.page_number_display != 'None'",
        },
    ]
}

# All fieldnames for verification + uninstall
ALL_FIELDNAMES = [
    # PDF Settings
    "page_orientation",
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
    "watermark_top",
    "watermark_right",
    "watermark_bottom",
    "watermark_left",
    # Page number settings
    "page_number_section",
    "page_number_display",
    "page_number_position",
    "page_number_font_family",
    "page_number_font_size",
    "page_number_font_color",
    "page_number_border",
    "page_number_col_break_02",
    "page_number_top",
    "page_number_right",
    "page_number_bottom",
    "page_number_left",
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
    """
    Apply Property Setters to override Print Settings standard field behavior.

    Property Setters can modify:
    - default: Set default value for a field
    - options: Add/modify Select field options
    - hidden: Hide/show fields
    - read_only: Make fields read-only
    - reqd: Make fields required
    - field_order: Reorder fields (on DocType level)

    Note: Field ordering for standard fields is controlled via field_order in DocType JSON.
    Custom field ordering is controlled via insert_after property.
    """
    from frappe.custom.doctype.property_setter.property_setter import (  # pyright: ignore[reportMissingImports]
        make_property_setter,
    )

    # 1. Add WeasyPrint option to pdf_generator in Print Settings
    # This extends the standard wkhtmltopdf/chrome options with WeasyPrint
    make_property_setter(
        doctype="Print Settings",
        fieldname="pdf_generator",
        property="options",
        value="wkhtmltopdf\nWeasyPrint\nchrome",
        property_type="Text",
        for_doctype=False,
    )

    # 2. Set pdf_generator default to chrome (future-proof, no letterhead dependency)
    make_property_setter(
        doctype="Print Settings",
        fieldname="pdf_generator",
        property="default",
        value="chrome",
        property_type="Data",
        for_doctype=False,
    )

    # 3. Create 3-column layout for PDF Settings (like Page Number Settings)
    _apply_pdf_settings_3column_layout()


def _apply_pdf_settings_3column_layout():
    """
    Add Column Break to PDF Settings section to create 3 columns.

    Layout:
    - Column 1: send_print_as_pdf, repeat_header_footer
    - Column 2: pdf_page_size, page_orientation, pdf_page_height
    - Column 3: pdf_generator, pdf_page_width
    """
    import json

    # 1. Create Column Break custom field if not exists
    existing_cf = frappe.db.exists(
        "Custom Field", {"dt": "Print Settings", "fieldname": "pdf_generator_column_break"}
    )
    if not existing_cf:
        cf = frappe.get_doc(
            {
                "doctype": "Custom Field",
                "dt": "Print Settings",
                "fieldname": "pdf_generator_column_break",
                "fieldtype": "Column Break",
                "label": "",  # No label for Column Break fields
                "insert_after": "pdf_page_height",
            }
        )
        cf.insert()
        print("   Created: pdf_generator_column_break")
    else:
        print("   pdf_generator_column_break already exists")

    # 2. Update field_order to include column break
    meta = frappe.get_meta("Print Settings")
    current_order = [df.fieldname for df in meta.fields]

    if "pdf_generator_column_break" not in current_order:
        # Insert column break after pdf_page_height, before pdf_generator
        if "pdf_page_height" in current_order and "pdf_generator" in current_order:
            height_idx = current_order.index("pdf_page_height")
            current_order.insert(height_idx + 1, "pdf_generator_column_break")
            print("   Inserted pdf_generator_column_break in field_order")

    # 3. Update field_order Property Setter
    existing_ps = frappe.db.exists(
        "Property Setter", {"doc_type": "Print Settings", "property": "field_order"}
    )
    if existing_ps:
        frappe.delete_doc("Property Setter", existing_ps, force=True)

    ps = frappe.get_doc(
        {
            "doctype": "Property Setter",
            "doctype_or_field": "DocType",
            "doc_type": "Print Settings",
            "field_name": None,
            "property": "field_order",
            "value": json.dumps(current_order),
            "property_type": "Text",
            "is_system_generated": 1,
        }
    )
    ps.flags.ignore_permissions = True
    ps.insert()
    print("   Updated field_order with 3-column PDF Settings layout")


def _fix_field_ordering():
    """Fix insert_after for existing fields that may have wrong ordering."""
    # Map of fieldname -> correct insert_after
    ordering_fixes = {
        # Page Number Settings (Page Number section should come AFTER Watermark margins)
        "page_number_section": "watermark_left",
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
        "watermark_top": "watermark_col_break",
        "watermark_right": "watermark_top",
        "watermark_bottom": "watermark_right",
        "watermark_left": "watermark_bottom",
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
            # PDF Settings
            "page_orientation": "Portrait",
            # Copy settings
            "enable_multiple_copies": 0,
            "default_copy_count": 2,
            "default_original_label": "Original",
            "default_copy_label": "Copy",
            "show_copy_controls_in_toolbar": 1,
            # Watermark settings
            "watermark_settings": "Original on First Page",
            "watermark_position": "Top Right",
            "watermark_font_family": "Kanit",
            "watermark_font_size": 24,
            "watermark_top": 0,
            "watermark_right": 0,
            "watermark_bottom": 0,
            "watermark_left": 0,
            # Page number settings
            "page_number_display": "Show",
            "page_number_position": "Top Right",
            "page_number_font_size": 10,
            "page_number_font_family": "Sarabun",
            "page_number_font_color": "000000",
            "page_number_border": "None",
        }

        updated = False
        for field, default_value in defaults.items():
            if not ps.get(field):
                ps.set(field, default_value)
                updated = True

        legacy_default_migrations = {
            "page_number_position": ("Bottom Center", "Top Right"),
        }
        for field, (legacy_value, new_value) in legacy_default_migrations.items():
            if ps.get(field) == legacy_value:
                ps.set(field, new_value)
                updated = True
                print(f"   Migrated {field}: {legacy_value} -> {new_value}")

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
