import frappe
from frappe import _
import json
from frappe.utils.print_format import download_pdf as original_download_pdf


def boot_session(bootinfo):
    """Add print designer settings to boot info"""
    bootinfo.print_designer_settings = {
        "enable_digital_signatures": True,
        "enable_company_stamps": True,
        "default_signature_company_filter": True,
    }


@frappe.whitelist()
def get_signature_image(signature_name):
    """Get signature image URL from Digital Signature doctype"""
    if not signature_name:
        return None

    try:
        signature_doc = frappe.get_doc("Digital Signature", signature_name)
        if signature_doc.is_active and signature_doc.signature_image:
            return {
                "image_url": signature_doc.signature_image,
                "title": signature_doc.title,
                "description": signature_doc.description,
            }
    except frappe.DoesNotExistError:
        frappe.log_error(f"Digital Signature {signature_name} not found")

    return None


@frappe.whitelist()
def get_company_stamp_image(stamp_name):
    """Get company stamp image URL from Company Stamp doctype"""
    if not stamp_name:
        return None

    try:
        stamp_doc = frappe.get_doc("Company Stamp", stamp_name)
        if stamp_doc.is_active and stamp_doc.stamp_image:
            return {
                "image_url": stamp_doc.stamp_image,
                "title": stamp_doc.title,
                "description": stamp_doc.description,
                "stamp_type": stamp_doc.stamp_type,
                "company": stamp_doc.company,
            }
    except frappe.DoesNotExistError:
        frappe.log_error(f"Company Stamp {stamp_name} not found")

    return None


def get_signature_and_stamp_context(digital_signature=None, company_stamp=None):
    """Get both signature and stamp context for print templates - Jinja method"""
    context = {}

    # Add signature context
    if digital_signature:
        signature_data = get_signature_image(digital_signature)
        if signature_data:
            context.update(
                {
                    "signature_image": signature_data["image_url"],
                    "signature_title": signature_data["title"],
                    "signature_description": signature_data.get("description", ""),
                }
            )

    # Add stamp context
    if company_stamp:
        stamp_data = get_company_stamp_image(company_stamp)
        if stamp_data:
            context.update(
                {
                    "company_stamp_image": stamp_data["image_url"],
                    "company_stamp_title": stamp_data["title"],
                    "company_stamp_description": stamp_data.get("description", ""),
                    "company_stamp_type": stamp_data.get("stamp_type", ""),
                    "stamp_company": stamp_data.get("company", ""),
                }
            )

    return context


def get_signature_image_url(signature_name):
    """Jinja helper to get signature URL directly"""
    signature_data = get_signature_image(signature_name)
    return signature_data["image_url"] if signature_data else None


def get_company_stamp_url(stamp_name):
    """Jinja helper to get company stamp URL directly"""
    stamp_data = get_company_stamp_image(stamp_name)
    return stamp_data["image_url"] if stamp_data else None


@frappe.whitelist()
def download_pdf_with_signature_stamp(
    doctype,
    name,
    format=None,
    doc=None,
    no_letterhead=0,
    letterhead=None,
    settings=None,  # Keep for backward compatibility, but won't pass to original function
    digital_signature=None,
    company_stamp=None,
    language=None,
    pdf_generator=None,
    **kwargs,
):
    """Enhanced PDF download with signature and stamp support"""

    # Get signature and stamp from form_dict if not provided
    digital_signature = digital_signature or frappe.form_dict.get("digital_signature")
    company_stamp = company_stamp or frappe.form_dict.get("company_stamp")

    # Add signature/stamp context to frappe.local for template access
    if digital_signature or company_stamp:
        signature_stamp_context = get_signature_and_stamp_context(
            digital_signature, company_stamp
        )

        # Store in frappe.local so templates can access it
        if not hasattr(frappe.local, "print_context"):
            frappe.local.print_context = {}
        frappe.local.print_context.update(signature_stamp_context)

    # Build parameters that match the current Frappe download_pdf signature
    pdf_params = {
        "doctype": doctype,
        "name": name,
        "format": format,
        "doc": doc,
        "no_letterhead": no_letterhead,
        "letterhead": letterhead,
    }
    
    # Add optional parameters if they exist in current Frappe version
    if language is not None:
        pdf_params["language"] = language
    if pdf_generator is not None:
        pdf_params["pdf_generator"] = pdf_generator
    
    # Filter out any other kwargs that aren't supported by download_pdf
    # Call the original download_pdf function with compatible parameters only
    return original_download_pdf(**pdf_params)


def startup_patches():
    """Apply monkey patches at startup"""
    # Patch the get_print_context function to include signature/stamp data
    from frappe.utils import print_format

    # Store original function
    original_get_print_context = print_format.get_print_context

    def enhanced_get_print_context(
        doctype, name, print_format=None, letterhead=None, settings=None, **kwargs
    ):
        """Enhanced print context that includes signature and stamp data"""

        # Get standard context
        context = original_get_print_context(
            doctype, name, print_format, letterhead, settings
        )

        # Add signature and stamp from form_dict, local, or kwargs
        digital_signature = (
            kwargs.get("digital_signature")
            or frappe.form_dict.get("digital_signature")
            or getattr(frappe.local, "digital_signature", None)
        )
        company_stamp = (
            kwargs.get("company_stamp")
            or frappe.form_dict.get("company_stamp")
            or getattr(frappe.local, "company_stamp", None)
        )

        # Also check frappe.local.print_context if available
        if hasattr(frappe.local, "print_context"):
            digital_signature = digital_signature or frappe.local.print_context.get(
                "digital_signature"
            )
            company_stamp = company_stamp or frappe.local.print_context.get(
                "company_stamp"
            )

        if digital_signature or company_stamp:
            signature_stamp_context = get_signature_and_stamp_context(
                digital_signature, company_stamp
            )
            context.update(signature_stamp_context)

        return context

    # Apply the monkey patch
    print_format.get_print_context = enhanced_get_print_context

    # Also patch frappe.get_print to ensure signature/stamp context is available
    import frappe

    original_get_print = frappe.get_print

    def enhanced_get_print(
        doctype,
        name,
        print_format=None,
        doc=None,
        no_letterhead=0,
        password=None,
        letterhead=None,
        pdf=False,
        as_pdf=False,
        **kwargs,
    ):
        """Enhanced get_print with signature/stamp support"""

        # Extract signature/stamp parameters
        digital_signature = kwargs.pop(
            "digital_signature", None
        ) or frappe.form_dict.get("digital_signature")
        company_stamp = kwargs.pop("company_stamp", None) or frappe.form_dict.get(
            "company_stamp"
        )

        # Store in frappe.local for template access
        if digital_signature:
            frappe.local.digital_signature = digital_signature
        if company_stamp:
            frappe.local.company_stamp = company_stamp

        # Call original function
        result = original_get_print(
            doctype=doctype,
            name=name,
            print_format=print_format,
            doc=doc,
            no_letterhead=no_letterhead,
            password=password,
            letterhead=letterhead,
            pdf=pdf,
            as_pdf=as_pdf,
            **kwargs,
        )

        # Clean up
        if hasattr(frappe.local, "digital_signature"):
            delattr(frappe.local, "digital_signature")
        if hasattr(frappe.local, "company_stamp"):
            delattr(frappe.local, "company_stamp")

        return result

    # Apply the patch
    frappe.get_print = enhanced_get_print


# Optional: Auto-signature functionality
def auto_add_signature(doc, method):
    """Automatically add signature to documents based on rules"""
    # Example: Auto-add signature for certain roles or conditions
    if frappe.session.user != "Administrator":
        user_signature = frappe.db.get_value(
            "Digital Signature", {"user": frappe.session.user, "is_active": 1}, "name"
        )
        if user_signature:
            doc.digital_signature = user_signature
