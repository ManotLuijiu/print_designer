import click
import frappe
from frappe.commands import get_site, pass_context


@click.command('install-watermark-fields')
@click.option('--site', help='Site name')
@pass_context
def install_watermark_fields(context, site=None):
    """Install watermark fields for Print Designer"""
    
    if not site:
        site = get_site(context)
    
    with frappe.init_site(site):
        frappe.connect()
        
        # Check if print_designer is installed
        installed_apps = frappe.get_installed_apps()
        if 'print_designer' not in installed_apps:
            click.echo(f"❌ Error: print_designer app is not installed on site '{site}'")
            click.echo(f"Install print_designer first with: bench --site {site} install-app print_designer")
            return
        
        try:
            # Migrate any type-mismatched fields from previous installs
            _migrate_legacy_fields()
            # Install Print Format and Print Settings watermark fields
            _install_print_format_watermark_fields()
            _install_print_settings_watermark_fields()
            _install_document_watermark_fields()
            _set_watermark_defaults()
            
            frappe.db.commit()
            click.echo("✅ Watermark fields installed successfully!")
            
        except Exception as e:
            click.echo(f"❌ Error installing watermark fields: {str(e)}")
            frappe.db.rollback()


def _migrate_legacy_fields():
    """Delete fields whose type changed since the previous install so they can be recreated."""
    # watermark_font_size was previously Data; now Int — delete to allow recreation
    mismatched = [
        ("Print Settings", "watermark_font_size", "Data"),
        # watermark_margin (single Int) replaced by 4 directional fields
        ("Print Settings", "watermark_margin", "Int"),
    ]
    for doctype, fieldname, old_type in mismatched:
        existing = frappe.db.get_value(
            "Custom Field",
            {"dt": doctype, "fieldname": fieldname},
            ["name", "fieldtype"],
            as_dict=True,
        )
        if existing and existing.fieldtype == old_type:
            frappe.delete_doc("Custom Field", existing.name, ignore_permissions=True)
            click.echo(f"  Removed legacy {doctype}.{fieldname} ({old_type}) for recreation")


def _install_print_format_watermark_fields():
    """Install watermark fields for Print Format (shown in print sidebar)"""
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    # Insert directly to avoid create_custom_fields re-validating unrelated Print Format fields
    # (print_designer_template_app is a Select with dynamic options that fail static validation).
    # Remove legacy single watermark_margin field from Print Format (replaced by Print Settings 4-field approach)
    existing = frappe.db.get_value("Custom Field", {"dt": "Print Format", "fieldname": "watermark_margin"}, "name")
    if existing:
        frappe.delete_doc("Custom Field", existing, ignore_permissions=True)
        click.echo("✅ Print Format watermark_margin (legacy) removed")
    else:
        click.echo("✅ Print Format watermark_margin already clean")


def _install_print_settings_watermark_fields():
    """Install watermark fields for Print Settings"""
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    
    custom_fields = {
        "Print Settings": [
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
                "description": "Enable multiple copy generation for print formats",
            },
            {
                "label": "Show Copy Controls in Toolbar",
                "fieldname": "show_copy_controls_in_toolbar",
                "fieldtype": "Check",
                "default": "1",
                "insert_after": "enable_multiple_copies",
                "depends_on": "enable_multiple_copies",
                "description": "Show copy controls in print preview toolbar",
            },
            {
                "label": "Watermark Settings",
                "fieldname": "watermark_settings_section",
                "fieldtype": "Section Break",
                "insert_after": "show_copy_controls_in_toolbar",
                "collapsible": 1,
            },
            # Left column
            {
                "label": "Watermark per Page",
                "fieldname": "watermark_settings",
                "fieldtype": "Select",
                "options": "None\nOriginal on First Page\nCopy on All Pages\nOriginal,Copy on Sequence",
                "default": "None",
                "insert_after": "watermark_settings_section",
                "description": "",
            },
            {
                "label": "Watermark Position",
                "fieldname": "watermark_position",
                "fieldtype": "Select",
                "options": "Top Left\nTop Center\nTop Right\nMiddle Left\nMiddle Center\nMiddle Right\nBottom Left\nBottom Center\nBottom Right",
                "default": "Top Right",
                "insert_after": "watermark_settings",
                "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
                "description": "Position of watermark text on the page",
            },
            # Right column
            {
                "fieldname": "watermark_col_break",
                "fieldtype": "Column Break",
                "insert_after": "watermark_position",
            },
            {
                "label": "Watermark Font Size (px)",
                "fieldname": "watermark_font_size",
                "fieldtype": "Int",
                "default": "24",
                "insert_after": "watermark_col_break",
                "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
                "description": "Font size in pixels",
            },
            {
                "label": "Watermark Font Family",
                "fieldname": "watermark_font_family",
                "fieldtype": "Select",
                "options": "Kanit\nSarabun\nArial\nHelvetica\nTimes New Roman\nCourier New\nVerdana\nGeorgia\nTahoma\nCalibri",
                "default": "Kanit",
                "insert_after": "watermark_font_size",
                "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
                "description": "Font family for watermark text",
            },
            {
                "label": "Margin Top (mm)",
                "fieldname": "watermark_margin_top",
                "fieldtype": "Int",
                "default": "0",
                "insert_after": "watermark_font_family",
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
        ]
    }
    
    create_custom_fields(custom_fields, update=True)
    click.echo("✅ Print Settings watermark fields installed")


def _install_document_watermark_fields():
    """Install watermark_text fields on document types"""
    try:
        from print_designer.watermark_fields import get_watermark_custom_fields
        from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
        
        custom_fields = get_watermark_custom_fields()
        create_custom_fields(custom_fields, update=True)
        click.echo("✅ Document watermark fields installed")
        
    except Exception as e:
        click.echo(f"⚠️  Warning: Could not install document watermark fields: {str(e)}")


def _set_watermark_defaults():
    """Set default values for watermark fields"""
    try:
        print_settings = frappe.get_single("Print Settings")
        
        defaults = {
            'watermark_font_size': 24,
            'watermark_position': 'Top Right',
            'watermark_margin_top': 0,
            'watermark_margin_right': 0,
            'watermark_margin_bottom': 0,
            'watermark_margin_left': 0,
            'watermark_font_family': 'Kanit',
            'watermark_settings': 'None',
            'enable_multiple_copies': 0,
            'show_copy_controls_in_toolbar': 1
        }
        
        updated = False
        for field, default_value in defaults.items():
            if not print_settings.get(field):
                print_settings.set(field, default_value)
                updated = True
        
        if updated:
            print_settings.save()
            click.echo("✅ Watermark default values set")
        
    except Exception as e:
        click.echo(f"⚠️  Warning: Could not set watermark defaults: {str(e)}")


commands = [install_watermark_fields]