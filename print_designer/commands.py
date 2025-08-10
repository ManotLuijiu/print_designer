import click
import frappe
from frappe.commands import pass_context


@click.command("install-watermark-fields")
@pass_context
def install_watermark_fields(context):
    """Install or reinstall Print Designer watermark fields"""
    
    for site in context.sites:
        try:
            frappe.init(site=site)
            frappe.connect()
            
            click.echo(f"Installing watermark fields for site: {site}")
            
            # Import and run the installation
            from print_designer.install import (
                override_erpnext_install,
                force_recreate_print_settings_fields
            )
            
            # Apply the override
            override_erpnext_install()
            
            # Force recreate fields
            force_recreate_print_settings_fields()
            
            # Commit changes
            frappe.db.commit()
            
            click.echo(f"✅ Successfully installed watermark fields for {site}")
            
        except Exception as e:
            click.echo(f"❌ Error installing watermark fields for {site}: {str(e)}")
            frappe.log_error(f"Error in install-watermark-fields command: {str(e)}")
            
        finally:
            frappe.destroy()


@click.command("check-print-settings-fields")
@pass_context  
def check_print_settings_fields(context):
    """Check which Print Settings custom fields are installed"""
    
    for site in context.sites:
        try:
            frappe.init(site=site)
            frappe.connect()
            
            click.echo(f"\nChecking Print Settings fields for site: {site}")
            
            # Check for watermark fields
            watermark_fields = [
                "watermark_settings_section",
                "watermark_settings", 
                "watermark_font_size",
                "watermark_position",
                "watermark_font_family"
            ]
            
            # Check for copy fields
            copy_fields = [
                "copy_settings_section",
                "enable_multiple_copies",
                "default_copy_count",
                "default_original_label",
                "default_copy_label"
            ]
            
            # Check for original ERPNext fields
            original_fields = [
                "compact_item_print",
                "print_uom_after_quantity",
                "print_taxes_with_zero_amount"
            ]
            
            all_fields = watermark_fields + copy_fields + original_fields
            
            click.echo("Field Status:")
            click.echo("-" * 50)
            
            for field in all_fields:
                exists = frappe.db.exists("Custom Field", {
                    "dt": "Print Settings", 
                    "fieldname": field
                })
                status = "✅ Installed" if exists else "❌ Missing"
                click.echo(f"{field:<30} {status}")
                
            # Check Print Settings values
            try:
                print_settings = frappe.get_single("Print Settings")
                watermark_setting = print_settings.get("watermark_settings", "Not Set")
                click.echo(f"\nCurrent watermark setting: {watermark_setting}")
            except:
                click.echo("\n❌ Could not read Print Settings")
                
        except Exception as e:
            click.echo(f"❌ Error checking fields for {site}: {str(e)}")
            
        finally:
            frappe.destroy()


commands = [
    install_watermark_fields,
    check_print_settings_fields
]

# Import Thai Form 50 ทวิ commands
try:
    from print_designer.commands.install_thai_form_50_twi import install_thai_form_50_twi
    commands.append(install_thai_form_50_twi)
except ImportError:
    pass
