"""
Print Protection Utils for Print Designer
Protects against third-party app conflicts (like erpnext_thailand monkey patching)
"""

import frappe
from frappe.utils.pdf import get_pdf as original_get_pdf
from frappe import get_print as original_get_print

def safe_get_print(
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
    pdf_generator=None,
):
    """
    Safe wrapper around frappe.get_print that handles third-party app conflicts.
    
    This function ensures that print_designer works even when other apps
    (like erpnext_thailand) monkey patch frappe.get_print with functionality
    that might fail due to missing custom fields or other dependencies.
    """
    
    # First try the current frappe.get_print (which might be monkey patched)
    try:
        result = frappe.get_print(
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
        
        # If successful, return the result
        return result
        
    except Exception as e:
        # Check if this is likely a third-party app conflict
        error_msg = str(e)
        
        # Common error patterns from third-party apps
        third_party_error_patterns = [
            "add_comment_info",  # erpnext_thailand custom field
            "Unknown column",    # Database field missing
            "Custom Field",      # Custom field related errors
            "erpnext_thailand",  # Direct reference to the app
        ]
        
        is_third_party_conflict = any(pattern in error_msg for pattern in third_party_error_patterns)
        
        if is_third_party_conflict:
            # Log the conflict for debugging
            frappe.log_error(
                title="Print Designer - Third Party App Conflict",
                message=f"Third-party app conflict detected in get_print. "
                       f"Falling back to original frappe.get_print. "
                       f"Error: {error_msg}"
            )
            
            # Fallback to original frappe.get_print (before monkey patching)
            try:
                result = original_get_print(
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
                return result
                
            except Exception as fallback_error:
                # If even the fallback fails, log both errors
                frappe.log_error(
                    title="Print Designer - Fallback Also Failed",
                    message=f"Both monkey patched and original get_print failed. "
                           f"Original error: {error_msg}. "
                           f"Fallback error: {str(fallback_error)}"
                )
                # Re-raise the original error
                raise e
        else:
            # If not a third-party conflict, just re-raise
            raise e

def check_and_fix_third_party_conflicts():
    """
    Check for known third-party app conflicts and attempt to fix them.
    This is called during print_designer initialization.
    """
    
    conflicts_found = []
    
    # Check for erpnext_thailand monkey patching
    try:
        import erpnext_thailand.custom.print_utils as thailand_print_utils
        
        # Check if frappe.get_print is monkey patched
        if hasattr(frappe, 'get_print') and frappe.get_print == thailand_print_utils.get_print:
            conflicts_found.append("erpnext_thailand monkey patched frappe.get_print")
            
            # Check if the custom field exists
            try:
                field_exists = frappe.db.get_value(
                    "Custom Field", 
                    {"dt": "Print Format", "fieldname": "add_comment_info"}, 
                    "name"
                )
                if not field_exists:
                    conflicts_found.append("erpnext_thailand custom field 'add_comment_info' missing")
            except Exception:
                conflicts_found.append("erpnext_thailand custom field check failed")
                
    except ImportError:
        # erpnext_thailand not installed, no conflict
        pass
    except Exception as e:
        conflicts_found.append(f"erpnext_thailand conflict check failed: {str(e)}")
    
    # Log conflicts if found
    if conflicts_found:
        frappe.log_error(
            title="Print Designer - Third Party Conflicts Detected",
            message=f"The following third-party app conflicts were detected:\n" +
                   "\n".join(f"- {conflict}" for conflict in conflicts_found) +
                   "\n\nPrint Designer will use safe fallback methods to ensure PDF generation works."
        )
    
    return conflicts_found

def initialize_print_protection():
    """
    Initialize print protection for print_designer.
    This should be called when print_designer is loaded.
    """
    
    # Check for conflicts
    conflicts = check_and_fix_third_party_conflicts()
    
    if conflicts:
        # Store the original get_print function if not already stored
        if not hasattr(frappe, '_original_get_print'):
            frappe._original_get_print = original_get_print
        
        # Log initialization
        frappe.log_error(
            title="Print Designer - Protection Initialized",
            message=f"Print protection initialized. {len(conflicts)} conflicts detected and will be handled gracefully."
        )
    
    return len(conflicts) > 0