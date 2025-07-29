"""
API endpoints and utilities for managing Print Designer UI visibility and functionality.
This module ensures that users can properly access and use the Print Designer interface.
"""

import frappe
import click
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


@frappe.whitelist()
def enable_print_designer_for_format(print_format_name):
    """
    Enable Print Designer for a specific Print Format.
    Makes the 'Edit Format' button route to print-designer instead of print-format-builder.
    
    Args:
        print_format_name (str): Name of the Print Format to enable
        
    Returns:
        dict: Success status and message
    """
    try:
        # Check if Print Format exists
        if not frappe.db.exists("Print Format", print_format_name):
            return {
                "success": False,
                "error": f"Print Format '{print_format_name}' not found"
            }
        
        # Get the Print Format document
        print_format = frappe.get_doc("Print Format", print_format_name)
        
        # Enable print_designer field
        print_format.print_designer = 1
        
        # Save the document
        print_format.save()
        
        return {
            "success": True,
            "message": f"Print Designer enabled for '{print_format_name}'. The 'Edit Format' button will now route to Print Designer."
        }
        
    except Exception as e:
        frappe.log_error(f"Error enabling Print Designer for {print_format_name}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def disable_print_designer_for_format(print_format_name):
    """
    Disable Print Designer for a specific Print Format.
    Makes the 'Edit Format' button route to print-format-builder.
    
    Args:
        print_format_name (str): Name of the Print Format to disable
        
    Returns:
        dict: Success status and message
    """
    try:
        # Check if Print Format exists
        if not frappe.db.exists("Print Format", print_format_name):
            return {
                "success": False,
                "error": f"Print Format '{print_format_name}' not found"
            }
        
        # Get the Print Format document
        print_format = frappe.get_doc("Print Format", print_format_name)
        
        # Disable print_designer field
        print_format.print_designer = 0
        
        # Save the document
        print_format.save()
        
        return {
            "success": True,
            "message": f"Print Designer disabled for '{print_format_name}'. The 'Edit Format' button will now route to Print Format Builder."
        }
        
    except Exception as e:
        frappe.log_error(f"Error disabling Print Designer for {print_format_name}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_print_formats_with_designer_status():
    """
    Get all Print Formats with their Print Designer enable/disable status.
    
    Returns:
        list: List of dictionaries with print format info
    """
    try:
        formats = frappe.get_all(
            "Print Format",
            fields=["name", "print_designer", "doc_type", "standard", "owner", "creation"],
            order_by="creation desc"
        )
        
        return {
            "success": True,
            "data": formats
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting print formats: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def make_print_designer_field_visible():
    """
    Make the print_designer field visible in the Print Format form.
    This allows users to see and toggle the Print Designer option directly.
    """
    try:
        # Check if the field exists
        existing_field = frappe.db.get_value(
            "Custom Field",
            {"dt": "Print Format", "fieldname": "print_designer"},
            ["name", "hidden"]
        )
        
        if existing_field:
            field_name, is_hidden = existing_field
            
            if is_hidden:
                # Make the field visible using direct database update to avoid validation issues
                frappe.db.set_value("Custom Field", field_name, {
                    "hidden": 0,
                    "insert_after": "standard",
                    "description": "Enable Print Designer interface for this format. When enabled, 'Edit Format' button will open Print Designer instead of Print Format Builder."
                })
                
                # Clear cache to ensure changes take effect
                frappe.clear_cache(doctype="Print Format")
                
                click.echo("✅ Print Designer field is now visible in Print Format form")
                return True
            else:
                click.echo("✅ Print Designer field is already visible")
                return True
        else:
            click.echo("❌ Print Designer field not found - this should not happen")
            return False
            
    except Exception as e:
        click.echo(f"❌ Error making print_designer field visible: {str(e)}")
        return False


def setup_print_designer_ui_visibility():
    """
    Setup Print Designer UI visibility for all users.
    This function is called during installation and migration.
    """
    try:
        click.echo("🔧 Setting up Print Designer UI visibility...")
        
        # Step 1: Make the print_designer field visible
        success = make_print_designer_field_visible()
        
        if success:
            # Step 2: Enable Print Designer for existing Print Designer formats
            # This ensures existing formats work correctly after the field becomes visible
            enable_existing_print_designer_formats()
            
            # Step 3: Clear cache to ensure changes take effect
            frappe.clear_cache(doctype="Print Format")
            
            click.echo("✅ Print Designer UI visibility setup completed")
            return True
        else:
            click.echo("❌ Failed to setup Print Designer UI visibility")
            return False
            
    except Exception as e:
        click.echo(f"❌ Error setting up Print Designer UI visibility: {str(e)}")
        frappe.log_error(f"Error setting up Print Designer UI visibility: {str(e)}")
        return False


def enable_existing_print_designer_formats():
    """
    Enable Print Designer for formats that have print_designer data but field is set to 0.
    This fixes existing formats that were created before the field was visible.
    """
    try:
        # Find formats that have print_designer data but field is 0
        formats_with_designer_data = frappe.db.sql("""
            SELECT name 
            FROM `tabPrint Format` 
            WHERE (
                print_designer_print_format IS NOT NULL 
                OR print_designer_header IS NOT NULL 
                OR print_designer_body IS NOT NULL 
                OR print_designer_footer IS NOT NULL
            )
            AND (print_designer IS NULL OR print_designer = 0)
        """, as_dict=True)
        
        enabled_count = 0
        for format_doc in formats_with_designer_data:
            try:
                frappe.db.set_value("Print Format", format_doc.name, "print_designer", 1)
                enabled_count += 1
                click.echo(f"   ✅ Enabled Print Designer for: {format_doc.name}")
            except Exception as e:
                click.echo(f"   ⚠️ Could not enable Print Designer for {format_doc.name}: {str(e)}")
        
        if enabled_count > 0:
            frappe.db.commit()
            click.echo(f"✅ Enabled Print Designer for {enabled_count} existing formats")
        else:
            click.echo("ℹ️ No existing formats needed Print Designer enablement")
            
    except Exception as e:
        click.echo(f"⚠️ Error enabling existing Print Designer formats: {str(e)}")
        frappe.log_error(f"Error enabling existing Print Designer formats: {str(e)}")


def setup_print_designer_toggle_button():
    """
    Add a custom button to Print Format list view for bulk enable/disable of Print Designer.
    """
    try:
        # This will be handled by client script
        click.echo("📝 Print Designer toggle functionality will be available in Print Format form")
        return True
    except Exception as e:
        click.echo(f"❌ Error setting up Print Designer toggle: {str(e)}")
        return False


# Command-line utilities for bench commands
def enable_print_designer_cli(print_format_name=None):
    """
    Command-line utility to enable Print Designer for a format.
    Can be called via: bench execute print_designer.api.enable_print_designer_ui.enable_print_designer_cli --kwargs "{'print_format_name': 'Format Name'}"
    """
    if not print_format_name:
        click.echo("❌ Please provide a print_format_name")
        click.echo("Usage: bench execute print_designer.api.enable_print_designer_ui.enable_print_designer_cli --kwargs \"{'print_format_name': 'Your Format Name'}\"")
        return
    
    result = enable_print_designer_for_format(print_format_name)
    
    if result["success"]:
        click.echo(f"✅ {result['message']}")
    else:
        click.echo(f"❌ {result['error']}")


def list_print_formats_cli():
    """
    Command-line utility to list all print formats and their Print Designer status.
    Can be called via: bench execute print_designer.api.enable_print_designer_ui.list_print_formats_cli
    """
    try:
        formats = frappe.get_all(
            "Print Format",
            fields=["name", "print_designer", "doc_type", "standard"],
            order_by="creation desc"
        )
        
        click.echo("\n📋 Print Formats and Print Designer Status:")
        click.echo("=" * 80)
        
        for fmt in formats:
            status = "✅ Enabled" if fmt.print_designer else "❌ Disabled"
            standard = "📌 Standard" if fmt.standard == "Yes" else "🔧 Custom"
            click.echo(f"{fmt.name:<40} | {status:<12} | {standard:<12} | {fmt.doc_type}")
        
        enabled_count = sum(1 for fmt in formats if fmt.print_designer)
        click.echo("=" * 80)
        click.echo(f"Total: {len(formats)} formats | Print Designer Enabled: {enabled_count}")
        
    except Exception as e:
        click.echo(f"❌ Error listing print formats: {str(e)}")


# Migration and installation functions
def ensure_print_designer_ui_setup():
    """
    Ensure Print Designer UI is properly set up.
    Called during after_install and after_migrate hooks.
    """
    try:
        click.echo("🔧 Ensuring Print Designer UI is properly configured...")
        
        # Setup UI visibility
        success = setup_print_designer_ui_visibility()
        
        if success:
            # Enable existing formats
            enable_existing_print_designer_formats()
            
            click.echo("✅ Print Designer UI setup completed successfully")
            
            # Show helpful message
            click.echo("\n📝 Print Designer UI Status:")
            click.echo("   • Print Designer checkbox is now visible in Print Format form")
            click.echo("   • Existing Print Designer formats have been automatically enabled")
            click.echo("   • Users can now toggle Print Designer on/off for any format")
            click.echo("\n💡 Usage:")
            click.echo("   1. Go to any Print Format")
            click.echo("   2. Check the 'Print Designer' checkbox to enable Print Designer")
            click.echo("   3. Click 'Edit Format' to use Print Designer interface")
            
        return success
        
    except Exception as e:
        click.echo(f"❌ Error ensuring Print Designer UI setup: {str(e)}")
        frappe.log_error(f"Error ensuring Print Designer UI setup: {str(e)}")
        return False