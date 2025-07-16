"""
Immediate override for ERPNext Thailand - applies every time it's imported
"""

import frappe

# Apply the override immediately when this module is imported
def apply_immediate_override():
    """Apply the override immediately"""
    try:
        # Check if erpnext_thailand is installed and monkey patching
        import erpnext_thailand.custom.print_utils as thailand_print_utils
        
        # Check if frappe.get_print has been monkey patched by erpnext_thailand
        if hasattr(frappe, 'get_print') and frappe.get_print == thailand_print_utils.get_print:
            # Import our safe replacement
            from print_designer.utils.override_thailand import safe_thailand_get_print
            
            # Replace the monkey patch with our safe version
            frappe.get_print = safe_thailand_get_print
            
            # Log the override
            frappe.log_error(
                title="Print Designer - Immediate Override Applied",
                message="ERPNext Thailand override applied immediately to prevent 403 errors."
            )
            
            return True
            
    except ImportError:
        # erpnext_thailand not installed
        pass
    except Exception as e:
        # Error during override
        frappe.log_error(
            title="Print Designer - Immediate Override Failed",
            message=f"Failed to apply immediate override: {str(e)}"
        )
    
    return False

# Apply the override when this module is imported
if frappe.local and not getattr(frappe.local, 'thailand_override_applied', False):
    if apply_immediate_override():
        frappe.local.thailand_override_applied = True

@frappe.whitelist()
def force_override():
    """Force apply the override - can be called from API"""
    result = apply_immediate_override()
    
    if result:
        return {"status": "success", "message": "Override applied successfully"}
    else:
        return {"status": "info", "message": "Override not needed or already applied"}

@frappe.whitelist()
def test_override():
    """Test the override is working"""
    try:
        # Test with a simple print operation
        from print_designer.utils.override_thailand import check_thailand_override_status
        status = check_thailand_override_status()
        
        return {
            "status": "success",
            "override_status": status,
            "message": "Override test completed"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Override test failed: {str(e)}"
        }