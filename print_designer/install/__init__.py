# Install package for Print Designer

# Import commonly used functions from the main install module
try:
    from ..install import (
        before_install,
        after_install,
        setup_enhanced_print_settings,
        ensure_watermark_fields_installed,
        emergency_watermark_fix_fallback,
        handle_erpnext_override,
    )
except ImportError as e:
    # Handle the case where the main install module can't be imported
    import frappe
    frappe.logger().error(f"Could not import functions from install module: {e}")
    
    # Define minimal stub functions to prevent import errors
    def before_install():
        pass
        
    def after_install():
        pass
        
    def setup_enhanced_print_settings():
        pass
        
    def ensure_watermark_fields_installed():
        pass
        
    def emergency_watermark_fix_fallback():
        pass
        
    def handle_erpnext_override():
        pass