"""
Safe PDF API for Print Designer
Provides protected PDF generation endpoints that work regardless of third-party app conflicts
"""

import frappe
from frappe.utils.pdf import get_pdf as original_get_pdf
from frappe import get_print as original_get_print
from frappe.utils.print_format import download_pdf as original_download_pdf
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
    
    # Log the request for debugging
    frappe.log_error(
        title="Print Designer - Safe PDF Download Request",
        message=f"Request: doctype={doctype}, name={name}, format={format}, "
               f"pdf_generator={pdf_generator}, letterhead={letterhead}"
    )
    
    try:
        # First try the safe_get_print function
        html = safe_get_print(
            doctype=doctype,
            name=name,
            print_format=format,
            doc=doc,
            no_letterhead=no_letterhead,
            letterhead=letterhead,
            pdf_generator=pdf_generator,
            **kwargs
        )
        
        # If we get HTML, convert to PDF
        if html:
            # Use the original get_pdf function to avoid third-party conflicts
            pdf_data = original_get_pdf(html)
            
            # Set response headers for PDF download
            frappe.local.response.filename = f"{name}.pdf"
            frappe.local.response.filecontent = pdf_data
            frappe.local.response.type = "pdf"
            
            return
            
    except Exception as e:
        error_msg = str(e)
        
        # Check if this is a typical third-party conflict error
        if any(pattern in error_msg for pattern in ['add_comment_info', 'Unknown column', 'erpnext_thailand']):
            # This is definitely a third-party conflict, try bypass
            try:
                # Use the original frappe functions directly
                html = original_get_print(
                    doctype=doctype,
                    name=name,
                    print_format=format,
                    doc=doc,
                    no_letterhead=no_letterhead,
                    letterhead=letterhead,
                    pdf_generator=pdf_generator,
                    **kwargs
                )
                
                if html:
                    pdf_data = original_get_pdf(html)
                    
                    # Set response headers for PDF download
                    frappe.local.response.filename = f"{name}.pdf"
                    frappe.local.response.filecontent = pdf_data
                    frappe.local.response.type = "pdf"
                    
                    # Log successful bypass
                    frappe.log_error(
                        title="Print Designer - Third Party Conflict Bypassed",
                        message=f"Successfully bypassed third-party conflict: {error_msg}"
                    )
                    
                    return
                    
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
            return original_download_pdf(
                doctype=doctype,
                name=name,
                format=format,
                doc=doc,
                no_letterhead=no_letterhead,
                language=language,
                letterhead=letterhead,
                **kwargs
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
    
    try:
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
            **kwargs
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
                **kwargs
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