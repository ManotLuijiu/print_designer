"""
Print Designer startup hooks
"""

import frappe

def apply_thailand_override():
    """
    Apply the erpnext_thailand override during system startup.
    
    This ensures our safe version is always used instead of the problematic one.
    """
    
    try:
        from print_designer.utils.override_thailand import override_thailand_monkey_patch
        
        # Apply the override
        override_applied = override_thailand_monkey_patch()
        
        if override_applied:
            frappe.log_error(
                title="Print Designer - Startup Override Applied",
                message="ERPNext Thailand override successfully applied during system startup."
            )
        
    except Exception as e:
        frappe.log_error(
            title="Print Designer - Startup Override Failed",
            message=f"Failed to apply ERPNext Thailand override during startup: {str(e)}"
        )

def initialize_print_designer():
    """
    Initialize print designer components during system startup.
    """
    
    # Apply thailand override
    apply_thailand_override()
    
    # Initialize print protection
    try:
        from print_designer.utils.print_protection import initialize_print_protection
        initialize_print_protection()
    except Exception as e:
        frappe.log_error(
            title="Print Designer - Startup Protection Failed",
            message=f"Failed to initialize print protection during startup: {str(e)}"
        )