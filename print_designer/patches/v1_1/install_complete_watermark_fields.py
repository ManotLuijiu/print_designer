import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """
    Migration patch to ensure complete watermark fields installation.
    This installs both Print Format and Print Settings watermark fields for existing users.
    """
    try:
        # Import the complete custom fields configuration
        from print_designer.custom_fields import CUSTOM_FIELDS
        
        # Filter only watermark-related fields for Print Format and Print Settings
        watermark_custom_fields = {}
        
        # Add Print Format watermark fields
        if "Print Format" in CUSTOM_FIELDS:
            print_format_fields = []
            for field in CUSTOM_FIELDS["Print Format"]:
                if field.get("fieldname") == "watermark_settings":
                    print_format_fields.append(field)
            if print_format_fields:
                watermark_custom_fields["Print Format"] = print_format_fields
        
        # Add Print Settings watermark fields  
        if "Print Settings" in CUSTOM_FIELDS:
            print_settings_fields = []
            for field in CUSTOM_FIELDS["Print Settings"]:
                if "watermark" in field.get("fieldname", "").lower() or field.get("fieldname") in [
                    "copy_settings_section", "enable_multiple_copies", "show_copy_controls_in_toolbar", 
                    "watermark_settings_section"
                ]:
                    print_settings_fields.append(field)
            if print_settings_fields:
                watermark_custom_fields["Print Settings"] = print_settings_fields
        
        # Install the watermark custom fields
        if watermark_custom_fields:
            create_custom_fields(watermark_custom_fields, update=True)
            print("✅ Complete watermark custom fields installed successfully")
        
        # Also install document-level watermark fields
        _install_document_watermark_fields()
        
        # Set default values
        _set_watermark_defaults()
        
        frappe.db.commit()
        print("✅ Watermark fields migration completed successfully")
        
    except Exception as e:
        frappe.log_error(f"Error installing complete watermark fields: {str(e)}")
        print(f"❌ Error installing complete watermark fields: {str(e)}")


def _install_document_watermark_fields():
    """Install watermark_text fields on document types"""
    try:
        from print_designer.watermark_fields import get_watermark_custom_fields
        
        # Install document watermark fields 
        custom_fields = get_watermark_custom_fields()
        create_custom_fields(custom_fields, update=True)
        print("✅ Document watermark fields installed successfully")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not install document watermark fields: {str(e)}")


def _set_watermark_defaults():
    """Set default values for watermark fields in Print Settings"""
    try:
        print_settings = frappe.get_single("Print Settings")
        
        # Set defaults for watermark fields
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
            print("✅ Watermark default values set successfully")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not set watermark defaults: {str(e)}")