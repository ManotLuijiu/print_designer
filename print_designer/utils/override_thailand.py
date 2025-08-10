"""
Override erpnext_thailand monkey patching to prevent 403 errors
"""

import frappe
from frappe import get_print as original_get_print
from typing import Literal

def safe_thailand_get_print(
    doctype=None,
    name=None,
    print_format=None,
    style=None,
    as_pdf=False,
    doc=None,
    output=None,
    no_letterhead=0,
    password=None,
    pdf_options=None,
    letterhead=None,
    pdf_generator: Literal["wkhtmltopdf", "chrome"] | None = None,
):
    """
    Safe replacement for erpnext_thailand's get_print function.
    
    This function does the same thing as the original but with proper error handling
    for the missing add_comment_info field.
    """
    
    # Call the original frappe.get_print function
    res = original_get_print(
        doctype=doctype,
        name=name,
        print_format=print_format,
        style=style,
        as_pdf=as_pdf,
        doc=doc,
        output=output,
        no_letterhead=no_letterhead,
        password=password,
        pdf_options=pdf_options,
        letterhead=letterhead,
        pdf_generator=pdf_generator,
    )
    
    # Only try to add comment if both doc and print_format are available
    # and if the custom field actually exists
    if doc and print_format:
        try:
            # Check if the add_comment_info field exists before trying to access it
            field_exists = frappe.db.get_value(
                "Custom Field", 
                {"dt": "Print Format", "fieldname": "add_comment_info"}, 
                "name"
            )
            
            if field_exists:
                # Field exists, safe to proceed with original logic
                add_comment = frappe.get_value(
                    "Print Format", print_format, "add_comment_info"
                )
                if add_comment:
                    doc.add_comment(
                        comment_type="Info",
                        text="Printed: {}".format(print_format),
                    )
                    frappe.db.commit()
            else:
                # Field doesn't exist, log and continue without adding comment
                frappe.log_error(
                    title="Print Designer - ERPNext Thailand Override",
                    message=f"Custom field 'add_comment_info' not found for print format '{print_format}'. "
                           f"Comment not added but PDF generation continues normally."
                )
                
        except Exception as e:
            # Any error in the comment addition should not break PDF generation
            frappe.log_error(
                title="Print Designer - ERPNext Thailand Override Error",
                message=f"Error in comment addition for print format '{print_format}': {str(e)}. "
                       f"PDF generation continues normally."
            )
    
    return res

def override_thailand_monkey_patch(app_name=None):
    """
    Override the erpnext_thailand monkey patching with our safe version.
    
    This should be called during print_designer initialization to ensure
    our safe version is used instead of the problematic one.
    
    Args:
        app_name: The name of the app being installed (passed by Frappe hooks)
    """
    
    try:
        # Check if erpnext_thailand is installed and has monkey patched frappe.get_print
        import erpnext_thailand.custom.print_utils as thailand_print_utils
        
        # Check if frappe.get_print has been monkey patched by erpnext_thailand
        if hasattr(frappe, 'get_print') and frappe.get_print == thailand_print_utils.get_print:
            # Replace the monkey patch with our safe version
            frappe.get_print = safe_thailand_get_print
            
            frappe.log_error(
                title="Print Designer - ERPNext Thailand Override Applied",
                message="Successfully overrode erpnext_thailand monkey patching with safe version. "
                       "PDF generation should now work without 403 errors."
            )
            
            return True
            
        else:
            # Not monkey patched, no action needed
            return False
            
    except ImportError:
        # erpnext_thailand not installed, no action needed
        return False
        
    except Exception as e:
        # Error during override, log but don't break
        frappe.log_error(
            title="Print Designer - ERPNext Thailand Override Failed",
            message=f"Failed to override erpnext_thailand monkey patching: {str(e)}. "
                   f"PDF generation may still experience 403 errors."
        )
        return False

def check_thailand_override_status():
    """
    Check the current status of the thailand override.
    
    Returns information about whether the override is active and working.
    """
    
    status = {
        "thailand_installed": False,
        "thailand_monkey_patched": False,
        "override_active": False,
        "custom_field_exists": False,
        "safe_to_generate_pdf": False
    }
    
    try:
        # Check if erpnext_thailand is installed
        import erpnext_thailand.custom.print_utils as thailand_print_utils
        status["thailand_installed"] = True
        
        # Check if frappe.get_print is monkey patched
        if hasattr(frappe, 'get_print'):
            if frappe.get_print == thailand_print_utils.get_print:
                status["thailand_monkey_patched"] = True
                status["override_active"] = False
            elif frappe.get_print == safe_thailand_get_print:
                status["thailand_monkey_patched"] = True
                status["override_active"] = True
            else:
                status["thailand_monkey_patched"] = False
                status["override_active"] = False
        
        # Check if custom field exists
        try:
            field_exists = frappe.db.get_value(
                "Custom Field", 
                {"dt": "Print Format", "fieldname": "add_comment_info"}, 
                "name"
            )
            status["custom_field_exists"] = bool(field_exists)
        except Exception:
            status["custom_field_exists"] = False
            
    except ImportError:
        status["thailand_installed"] = False
    
    # Determine if it's safe to generate PDFs
    if not status["thailand_installed"]:
        status["safe_to_generate_pdf"] = True  # No thailand, no problem
    elif status["override_active"]:
        status["safe_to_generate_pdf"] = True  # Override is active
    elif status["thailand_monkey_patched"] and status["custom_field_exists"]:
        status["safe_to_generate_pdf"] = True  # Thailand patched but field exists
    else:
        status["safe_to_generate_pdf"] = False  # Thailand patched but field missing
    
    return status

@frappe.whitelist()
def get_thailand_override_status():
    """
    API endpoint to check thailand override status.
    
    Can be called from: /api/method/print_designer.utils.override_thailand.get_thailand_override_status
    """
    
    return check_thailand_override_status()