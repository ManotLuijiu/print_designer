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


def _install_print_format_watermark_fields():
    """Install watermark fields for Print Format"""
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    
    custom_fields = {
        "Print Format": [
            {
                "depends_on": "eval:doc.print_designer",
                "fieldname": "watermark_settings",
                "fieldtype": "Select",
                "label": "Watermark per Page",
                "options": "None\nOriginal on First Page\nCopy on All Pages\nOriginal,Copy on Sequence",
                "default": "None",
                "insert_after": "print_designer_template_app",
                "description": "Control watermark display: None=no watermarks, Original on First Page=first page shows 'Original', Copy on All Pages=all pages show 'Copy', Original,Copy on Sequence=pages alternate between 'Original' and 'Copy'"
            }
        ]
    }
    
    create_custom_fields(custom_fields, update=True)
    click.echo("✅ Print Format watermark fields installed")


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
            {
                "label": "Watermark per Page",
                "fieldname": "watermark_settings",
                "fieldtype": "Select",
                "options": "None\nOriginal on First Page\nCopy on All Pages\nOriginal,Copy on Sequence",
                "default": "None",
                "insert_after": "watermark_settings_section",
                "description": "Control watermark display: None=no watermarks, Original on First Page=first page shows 'Original', Copy on All Pages=all pages show 'Copy', Original,Copy on Sequence=pages alternate between 'Original' and 'Copy'",
            },
            {
                "label": "Watermark Font Size (px)",
                "fieldname": "watermark_font_size",
                "fieldtype": "Int",
                "default": "24",
                "insert_after": "watermark_settings",
                "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
                "description": "Font size for watermark text in pixels (default: 24px)",
            },
            {
                "label": "Watermark Position",
                "fieldname": "watermark_position",
                "fieldtype": "Select",
                "options": "Top Left\nTop Center\nTop Right\nMiddle Left\nMiddle Center\nMiddle Right\nBottom Left\nBottom Center\nBottom Right",
                "default": "Top Right",
                "insert_after": "watermark_font_size",
                "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
                "description": "Position of watermark text on the page",
            },
            {
                "label": "Watermark Font Family",
                "fieldname": "watermark_font_family",
                "fieldtype": "Select",
                "options": "Arial\nHelvetica\nTimes New Roman\nCourier New\nVerdana\nGeorgia\nTahoma\nCalibri",
                "default": "Arial",
                "insert_after": "watermark_position",
                "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
                "description": "Font family for watermark text",
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
            'watermark_font_family': 'Arial',
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