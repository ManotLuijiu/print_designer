import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """
    Migration patch to install watermark fields for existing Print Designer users.
    This ensures both fresh installs and existing users get watermark functionality.
    """
    try:
        # Import watermark fields configuration
        from print_designer.print_designer.watermark_fields import get_watermark_custom_fields
        
        # Install watermark custom fields across all configured DocTypes
        custom_fields = get_watermark_custom_fields()
        create_custom_fields(custom_fields, update=True)
        
        frappe.db.commit()
        print("✅ Watermark fields installed successfully via migration")
        
        # Also ensure watermark defaults are set in Print Settings
        _ensure_watermark_defaults()
        
    except Exception as e:
        frappe.log_error(f"Error installing watermark fields via migration: {str(e)}")
        print(f"❌ Error installing watermark fields: {str(e)}")


def _ensure_watermark_defaults():
    """Set defaults for watermark configuration fields in Print Settings"""
    try:
        print_settings = frappe.get_single("Print Settings")
        
        # Set defaults if fields are empty
        if not print_settings.get('watermark_font_size'):
            print_settings.watermark_font_size = 24
        
        if not print_settings.get('watermark_position'):
            print_settings.watermark_position = 'Top Right'
        
        if not print_settings.get('watermark_font_family'):
            print_settings.watermark_font_family = 'Arial'
        
        print_settings.save()
        frappe.db.commit()
        print("✅ Watermark field defaults set successfully")
        
    except Exception as e:
        frappe.log_error(f"Error setting watermark defaults via migration: {str(e)}")
        print(f"❌ Error setting watermark defaults: {str(e)}")