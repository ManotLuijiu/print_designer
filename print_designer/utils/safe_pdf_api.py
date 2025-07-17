"""
Safe PDF API for Print Designer
Provides protected PDF generation endpoints that work regardless of third-party app conflicts
"""

import frappe
from frappe.utils.pdf import get_pdf as original_get_pdf
from frappe import get_print as original_get_print
from frappe.utils.print_format import download_pdf as original_download_pdf
from frappe.www.printview import validate_print_permission
from frappe.translate import print_language
from print_designer.utils.print_protection import safe_get_print

@frappe.whitelist()
def safe_download_pdf(
    doctype,
    name,
    format=None,
    doc=None,
    no_letterhead=0,
    language=None,
    letterhead=None,
    pdf_generator=None,
    **kwargs
):
    """
    Safe PDF download endpoint that protects against third-party app conflicts.
    
    This endpoint is specifically designed for print_designer to ensure
    reliable PDF generation even when other apps monkey patch core functions.
    """
    
    # Get the document and validate permissions using Frappe's standard method
    try:
        doc = doc or frappe.get_doc(doctype, name)
        validate_print_permission(doc)
    except Exception as permission_error:
        frappe.log_error(
            title="Print Designer - Permission Validation Failed",
            message=f"Permission validation failed for {doctype} {name}: {str(permission_error)}"
        )
        frappe.throw("You don't have permission to access this document", frappe.PermissionError)
    
    # Handle HEAD requests - just return headers without body
    if frappe.request.method == "HEAD":
        frappe.local.response.headers = {
            'Content-Type': 'application/pdf',
            'Content-Disposition': f'attachment; filename="{name}.pdf"',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        return
    
    # Log the request for debugging
    frappe.log_error(
        title="Print Designer - Safe PDF Download Request",
        message=f"Request: doctype={doctype}, name={name}, format={format}, "
               f"pdf_generator={pdf_generator}, letterhead={letterhead}, "
               f"method={frappe.request.method}, user={frappe.session.user}"
    )
    
    try:
        # Log the attempt
        frappe.log_error(
            title="Print Designer - Safe PDF Generation Attempt",
            message=f"Attempting safe PDF generation for {doctype} {name} with format {format}"
        )
        
        # Filter out parameters that are not expected by safe_get_print
        allowed_params = {
            'style', 'as_pdf', 'output', 'password', 'pdf_options'
        }
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in allowed_params}
        
        # Handle language parameter - convert _lang to language if present
        if '_lang' in kwargs:
            language = kwargs['_lang']
        
        # Use print_language context manager like the standard Frappe function
        with print_language(language):
            # First try the safe_get_print function
            html = safe_get_print(
                doctype=doctype,
                name=name,
                print_format=format,
                doc=doc,
                no_letterhead=no_letterhead,
                letterhead=letterhead,
                pdf_generator=pdf_generator,
                **filtered_kwargs
            )
            
            # If we get HTML, convert to PDF
            if html:
                # Use the original get_pdf function to avoid third-party conflicts
                pdf_data = original_get_pdf(html)
                
                if pdf_data:
                    # Set response headers for PDF download
                    frappe.local.response.filename = f"{name}.pdf"
                    frappe.local.response.filecontent = pdf_data
                    frappe.local.response.type = "pdf"
                    
                    # Set additional headers for proper PDF handling
                    frappe.local.response.headers = {
                        'Content-Type': 'application/pdf',
                        'Content-Disposition': f'attachment; filename="{name}.pdf"',
                        'Cache-Control': 'no-cache, no-store, must-revalidate',
                        'Pragma': 'no-cache',
                        'Expires': '0'
                    }
                    
                    return pdf_data
                else:
                    frappe.throw("Failed to generate PDF from HTML")
            
    except Exception as e:
        error_msg = str(e)
        
        # Check if this is a typical third-party conflict error
        if any(pattern in error_msg for pattern in ['add_comment_info', 'Unknown column', 'erpnext_thailand']):
            # This is definitely a third-party conflict, try bypass
            try:
                # Use the original frappe functions directly with filtered kwargs
                html = original_get_print(
                    doctype=doctype,
                    name=name,
                    print_format=format,
                    doc=doc,
                    no_letterhead=no_letterhead,
                    letterhead=letterhead,
                    pdf_generator=pdf_generator,
                    **filtered_kwargs
                )
                
                if html:
                    pdf_data = original_get_pdf(html)
                    
                    if pdf_data:
                        # Set response headers for PDF download
                        frappe.local.response.filename = f"{name}.pdf"
                        frappe.local.response.filecontent = pdf_data
                        frappe.local.response.type = "pdf"
                        
                        # Set additional headers for proper PDF handling
                        frappe.local.response.headers = {
                            'Content-Type': 'application/pdf',
                            'Content-Disposition': f'attachment; filename="{name}.pdf"',
                            'Cache-Control': 'no-cache, no-store, must-revalidate',
                            'Pragma': 'no-cache',
                            'Expires': '0'
                        }
                        
                        # Log successful bypass
                        frappe.log_error(
                            title="Print Designer - Third Party Conflict Bypassed",
                            message=f"Successfully bypassed third-party conflict: {error_msg}"
                        )
                        
                        return pdf_data
                    else:
                        frappe.throw("Failed to generate PDF from HTML")
                    
            except Exception as bypass_error:
                # Log both errors
                frappe.log_error(
                    title="Print Designer - Bypass Also Failed",
                    message=f"Both safe and bypass methods failed. "
                           f"Original error: {error_msg}. "
                           f"Bypass error: {str(bypass_error)}"
                )
        
        # Log the error
        frappe.log_error(
            title="Print Designer - Safe PDF Download Failed",
            message=f"Safe PDF download failed: {error_msg}"
        )
        
        # Try direct original download_pdf as last resort
        try:
            # Filter kwargs for original_download_pdf function
            original_download_kwargs = {k: v for k, v in kwargs.items() if k not in ['_lang']}
            return original_download_pdf(
                doctype=doctype,
                name=name,
                format=format,
                doc=doc,
                no_letterhead=no_letterhead,
                language=language,
                letterhead=letterhead,
                **original_download_kwargs
            )
        except Exception as fallback_error:
            frappe.log_error(
                title="Print Designer - All PDF Methods Failed",
                message=f"Both safe and original PDF methods failed. "
                       f"Original error: {error_msg}. "
                       f"Fallback error: {str(fallback_error)}"
            )
            frappe.throw(f"PDF generation failed: {error_msg}")

@frappe.whitelist()
def safe_get_print_html(
    doctype,
    name,
    print_format=None,
    style=None,
    no_letterhead=0,
    letterhead=None,
    language=None,
    pdf_generator=None,
    **kwargs
):
    """
    Safe HTML generation endpoint for print preview.
    
    Returns HTML instead of PDF for preview purposes.
    """
    
    # Get the document and validate permissions using Frappe's standard method
    doc = frappe.get_doc(doctype, name)
    validate_print_permission(doc)
    
    try:
        # Filter out parameters that are not expected by safe_get_print
        allowed_params = {
            'output', 'password', 'pdf_options'
        }
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in allowed_params}
        
        # Handle language parameter - convert _lang to language if present
        if '_lang' in kwargs:
            language = kwargs['_lang']
        
        # Use print_language context manager like the standard Frappe function
        with print_language(language):
            # Use the safe_get_print function
            html = safe_get_print(
                doctype=doctype,
                name=name,
                print_format=print_format,
                style=style,
                as_pdf=False,
                no_letterhead=no_letterhead,
                letterhead=letterhead,
                pdf_generator=pdf_generator,
                **filtered_kwargs
            )
            
            return {"html": html}
        
    except Exception as e:
        frappe.log_error(
            title="Print Designer - Safe HTML Generation Failed",
            message=f"Safe HTML generation failed: {str(e)}"
        )
        
        # Try original get_print as fallback
        try:
            html = original_get_print(
                doctype=doctype,
                name=name,
                print_format=print_format,
                style=style,
                as_pdf=False,
                no_letterhead=no_letterhead,
                letterhead=letterhead,
                pdf_generator=pdf_generator,
                **filtered_kwargs
            )
            return {"html": html}
            
        except Exception as fallback_error:
            frappe.log_error(
                title="Print Designer - All HTML Methods Failed",
                message=f"Both safe and original HTML methods failed. "
                       f"Original error: {str(e)}. "
                       f"Fallback error: {str(fallback_error)}"
            )
            frappe.throw(f"HTML generation failed: {str(e)}")

@frappe.whitelist()
def check_third_party_conflicts():
    """
    Check for third-party app conflicts and return status.
    
    This can be called from client-side to determine if safe endpoints should be used.
    """
    
    from print_designer.utils.print_protection import check_and_fix_third_party_conflicts
    
    conflicts = check_and_fix_third_party_conflicts()
    
    return {
        "conflicts_found": len(conflicts) > 0,
        "conflicts": conflicts,
        "safe_endpoints_recommended": len(conflicts) > 0
    }

@frappe.whitelist()
def get_pdf_generation_info():
    """
    Get information about PDF generation capabilities and conflicts.
    """
    
    info = {
        "print_designer_version": frappe.get_attr("print_designer.__version__"),
        "frappe_version": frappe.__version__,
        "safe_endpoints_available": True,
        "third_party_conflicts": [],
        "recommended_pdf_generator": "wkhtmltopdf"
    }
    
    # Check for erpnext_thailand
    try:
        import erpnext_thailand
        info["erpnext_thailand_installed"] = True
        info["erpnext_thailand_version"] = getattr(erpnext_thailand, '__version__', 'unknown')
        
        # Check if it's monkey patching frappe.get_print
        try:
            import erpnext_thailand.custom.print_utils as thailand_print_utils
            if hasattr(frappe, 'get_print') and frappe.get_print == thailand_print_utils.get_print:
                info["third_party_conflicts"].append("erpnext_thailand monkey patched frappe.get_print")
        except Exception:
            pass
            
    except ImportError:
        info["erpnext_thailand_installed"] = False
    
    # Check for WeasyPrint availability
    try:
        from print_designer.weasyprint_integration import should_use_weasyprint
        if should_use_weasyprint():
            info["recommended_pdf_generator"] = "WeasyPrint"
    except Exception:
        pass
    
    return info