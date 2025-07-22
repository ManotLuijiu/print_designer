import json

import frappe
from frappe import _
from frappe.utils.print_format import download_pdf as original_download_pdf

"""
#    Digital Signature
#    * `title`: Title (Data)
#    * `signature_image`: Signature Image (Attach Image)
#    * `description`: Description (Small Text)
#    * `is_active`: Is Active (Check)
#    * `company`: Company (Link to Company)
#    * `department`: Department (Link to Department)
#    * `designation`: Designation (Link to Designation)

"""


def boot_session(bootinfo):
    """Add print designer settings to boot info"""
    bootinfo.print_designer_settings = {
        "enable_digital_signatures": True,
        "enable_company_stamps": True,
        "default_signature_company_filter": True,
    }


@frappe.whitelist()
def get_signature_image(signature_name):
    """Get signature image and details from Digital Signature doctype"""
    if not signature_name:
        return None

    try:
        signature_doc = frappe.get_doc("Digital Signature", signature_name)
        print(f"signature_doc {signature_doc}")
        if signature_doc.get("is_active") and signature_doc.get("signature_image"):
            return {
                "image_url": signature_doc.get("signature_image"),
                "title": signature_doc.get("title"),
                "description": signature_doc.get("description"),
                "company": signature_doc.get("company"),
                "department": signature_doc.get("department"),
                "designation": signature_doc.get("designation"),
            }
    except frappe.DoesNotExistError:
        frappe.log_error(f"Digital Signature {signature_name} not found")

    return None


@frappe.whitelist()
def get_company_stamp_image(stamp_name):
    print(f"stamp_name {stamp_name}")
    """Get company stamp image URL from Company Stamp doctype"""
    if not stamp_name:
        return None

    try:
        stamp_doc = frappe.get_doc("Company Stamp", stamp_name)
        print(f"stamp_doc {stamp_doc}")
        if stamp_doc.get("is_active") and stamp_doc.get("stamp_image"):
            return {
                "image_url": stamp_doc.get("stamp_image"),
                "title": stamp_doc.get("title"),
                "description": stamp_doc.get("description"),
                "stamp_type": stamp_doc.get("stamp_type"),
                "company": stamp_doc.get("company"),
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
        print(f"signature_data {signature_data}")
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
        print(f"stamp_data {stamp_data}")
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
    settings=None,  # Now we'll handle watermark settings from this parameter
    digital_signature=None,
    company_stamp=None,
    language=None,
    pdf_generator=None,
    **kwargs,
):
    """Enhanced PDF download with signature, stamp, and watermark support"""

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

    # Handle watermark settings for PDF generation
    # Get watermark settings from Print Settings if not provided in settings parameter
    watermark_settings = None
    print(f"watermark_settings {watermark_settings}")
    if settings:
        # Parse settings if it's a JSON string
        if isinstance(settings, str):
            try:
                parsed_settings = frappe.parse_json(settings)
                watermark_settings = parsed_settings.get("watermark_settings")
            except Exception:
                pass
        elif isinstance(settings, dict):
            watermark_settings = settings.get("watermark_settings")

    # If no watermark settings in parameters, get from Print Settings
    if not watermark_settings:
        try:
            print_settings = frappe.get_single("Print Settings")
            watermark_settings = print_settings.get("watermark_settings", "None")
        except Exception:
            watermark_settings = "None"

    # Handle watermark settings for PDF generation
    if watermark_settings and watermark_settings != "None":
        # We need to override the HTML generation to include watermarks
        # First, get the HTML using frappe.get_print (without PDF)
        from frappe.utils.print_utils import get_print

        # Get the HTML content
        html_content = get_print(
            doctype=doctype,
            name=name,
            print_format=format,
            doc=doc,
            no_letterhead=no_letterhead,
            letterhead=letterhead,
            as_pdf=False,
        )

        # Get watermark configuration from Print Settings
        try:
            print_settings = frappe.get_single("Print Settings")
            font_size = print_settings.get("watermark_font_size", 24)
            position = print_settings.get("watermark_position", "Top Right")
            font_family = print_settings.get("watermark_font_family", "Sarabun")
        except Exception:
            font_size = 24
            position = "Top Right"
            font_family = "Sarabun"

        # Get watermark text from multiple sources
        watermark_text = ""

        print(f"watermark_settings: after print_settings {watermark_settings}")
        print(f"print_settings: after print_settings {print_settings}")

        # First, check the traditional watermark_settings from Print Settings
        if watermark_settings == "Original on First Page":
            watermark_text = frappe._("Original")
        elif watermark_settings == "Copy on All Pages":
            watermark_text = frappe._("Copy")
        elif watermark_settings == "Original,Copy on Sequence":
            watermark_text = frappe._("Original")  # For single page, use Original
            print(f"watermark_text {watermark_text}")

        # Then, check for dynamic watermark from document field (if available)
        if not watermark_text:
            try:
                doc = frappe.get_cached_doc(doctype, name)
                print(f"doc {doc}")
                dynamic_watermark = doc.get("watermark_text")
                if dynamic_watermark and dynamic_watermark != "None":
                    if isinstance(dynamic_watermark, (list, tuple)):
                        dynamic_watermark = ", ".join(
                            str(item) for item in dynamic_watermark
                        )
                    watermark_text = frappe._(str(dynamic_watermark))
            except Exception:
                pass

        if watermark_text:
            # Calculate position CSS based on selection (CSS 2.1 compatible only)
            # Use same positioning as print preview for consistency
            position_css = ""
            if position == "Top Right":
                position_css = "top: 70px; right: 20px;"  # Below page numbers, same as preview
            elif position == "Top Left":
                position_css = "top: 70px; left: 20px;"
            elif position == "Bottom Right":
                position_css = "bottom: 20px; right: 20px;"
            elif position == "Bottom Left":
                position_css = "bottom: 20px; left: 20px;"
            else:  # Center - use margin-based centering for CSS 2.1 compatibility
                position_css = "top: 45%; left: 45%; width: 100px; margin-left: -50px;"

            # Add watermark CSS and HTML (CSS 2.1 compatible only)
            watermark_html = f"""
            <style>
                .watermark {{
                    position: absolute;
                    {position_css}
                    font-size: {font_size}px;
                    color: #999999;
                    font-weight: bold;
                    font-family: {font_family}, sans-serif;
                }}
            </style>
            <div class="watermark">{watermark_text}</div>
            """

            # Insert watermark HTML inside header-html div where page numbers are located
            if isinstance(html_content, str):
                # Try to insert watermark inside header-html div where page numbers are located
                if '<div id="header-html">' in html_content:
                    # Insert watermark right after the header-html opening tag
                    html_content = html_content.replace(
                        '<div id="header-html">',
                        f'<div id="header-html">{watermark_html}'
                    )
                elif '<div class="print-format' in html_content:
                    # Fallback: insert before print-format div
                    html_content = html_content.replace(
                        '<div class="print-format',
                        f'{watermark_html}\n<div class="print-format',
                    )
                elif "</body>" in html_content:
                    # Last resort: before closing body tag
                    html_content = html_content.replace(
                        "</body>", f"{watermark_html}</body>"
                    )
                else:
                    # Final fallback: append at the end
                    html_content += watermark_html
            else:
                # If html_content is not a string, convert to string before appending watermark
                html_content = str(html_content) + watermark_html

        # Now generate PDF from the modified HTML
        from frappe.utils.pdf import get_pdf

        pdf_file = get_pdf(html_content)

        # Set response similar to original download_pdf
        if not doc:
            doc = frappe.get_doc(doctype, name)
        frappe.local.response.filename = "{name}.pdf".format(
            name=name.replace(" ", "-").replace("/", "-")
        )
        frappe.local.response.filecontent = pdf_file
        frappe.local.response.type = "pdf"

        return pdf_file

    # If no watermarks needed, use original function
    # Build parameters that match the current Frappe download_pdf signature
    pdf_kwargs = {
        "doctype": doctype,
        "name": name,
        "format": format,
        "doc": doc,
        "no_letterhead": no_letterhead,
        "letterhead": letterhead,
        "language": language,
        "pdf_generator": pdf_generator,
    }

    # Filter out any None values to avoid passing them to the original function
    pdf_kwargs = {k: v for k, v in pdf_kwargs.items() if v is not None}

    # Call the original download_pdf function with compatible parameters only
    return original_download_pdf(**pdf_kwargs)


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
