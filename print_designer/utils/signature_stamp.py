import json
import os

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

def log_to_print_designer(message, level="INFO"):
    """Log messages to Print Designer specific log file"""
    try:
        log_dir = os.path.join(frappe.get_site_path(), "logs", "print_designer")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, "print_designer.log")
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")
    except Exception as e:
        # Fallback to frappe logger if file logging fails
        frappe.logger("print_designer").info(f"Log write failed: {e}, Original message: {message}")


def boot_session(bootinfo):
    """Add print designer settings to boot info"""
    
    # Get Print Settings to include watermark configuration
    try:
        print_settings = frappe.get_single("Print Settings")
        
        # Extract watermark settings
        watermark_config = {
            "watermark_settings": print_settings.get("watermark_settings", "None"),
            "watermark_font_size": print_settings.get("watermark_font_size", 12),
            "watermark_position": print_settings.get("watermark_position", "Top Right"),
            "watermark_font_family": print_settings.get("watermark_font_family", "Arial"),
            "enable_multiple_copies": print_settings.get("enable_multiple_copies", 0),
            "default_copy_count": print_settings.get("default_copy_count", 2),
            "default_original_label": print_settings.get("default_original_label", "Original"),
            "default_copy_label": print_settings.get("default_copy_label", "Copy"),
            "show_copy_controls_in_toolbar": print_settings.get("show_copy_controls_in_toolbar", 1),
        }
        
        log_to_print_designer(f"Boot session watermark config: {watermark_config}")
        
    except Exception as e:
        # Fallback to default values if Print Settings cannot be accessed
        watermark_config = {
            "watermark_settings": "None",
            "watermark_font_size": 12,
            "watermark_position": "Top Right", 
            "watermark_font_family": "Arial",
            "enable_multiple_copies": 0,
            "default_copy_count": 2,
            "default_original_label": "Original",
            "default_copy_label": "Copy",
            "show_copy_controls_in_toolbar": 1,
        }
        log_to_print_designer(f"Boot session watermark fallback due to error: {e}")
    
    bootinfo.print_designer_settings = {
        "enable_digital_signatures": True,
        "enable_company_stamps": True,
        "default_signature_company_filter": True,
        # Add watermark settings for frontend availability
        **watermark_config
    }


@frappe.whitelist()
def get_signature_image(signature_name):
    """Get signature image and details from Digital Signature doctype"""
    if not signature_name:
        return None

    try:
        signature_doc = frappe.get_doc("Digital Signature", signature_name)
        log_to_print_designer(f"Retrieved signature doc: {signature_doc.name}")
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
    """Get company stamp image URL from Company Stamp doctype"""
    log_to_print_designer(f"Getting company stamp: {stamp_name}")
    if not stamp_name:
        return None

    try:
        stamp_doc = frappe.get_doc("Company Stamp", stamp_name)
        log_to_print_designer(f"Retrieved stamp doc: {stamp_doc.name}")
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
        log_to_print_designer(f"Signature data: {signature_data}")
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
        log_to_print_designer(f"Stamp data: {stamp_data}")
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
            font_size = print_settings.get("watermark_font_size", 12)
            position = print_settings.get("watermark_position", "Top Right")
            font_family = print_settings.get("watermark_font_family", "Sarabun")
        except Exception:
            font_size = 12
            position = "Top Right"
            font_family = "Sarabun"

        # Get watermark text from multiple sources
        watermark_text = ""

        log_to_print_designer(f"Watermark settings: {watermark_settings}")
        log_to_print_designer(f"Print settings loaded: font_size={font_size}, position={position}, font_family={font_family}")

        # First, check the traditional watermark_settings from Print Settings
        if watermark_settings == "Original on First Page":
            watermark_text = _("Original")
            # watermark_text = "Original"
        elif watermark_settings == "Copy on All Pages":
            watermark_text = _("Copy")
            # watermark_text = "Copy"
        elif watermark_settings == "Original,Copy on Sequence":
            # For sequence watermarks, we need to delegate to the Chrome PDF generator
            # which handles multiple copies with different watermarks properly.
            # This HTML-based approach can't handle per-page watermarks correctly.
            # Return None here so the Chrome PDF generator takes over.
            watermark_text = None
            log_to_print_designer("Sequence watermarks detected - delegating to Chrome PDF generator")

        # Then, check for dynamic watermark from document field (if available)
        if not watermark_text:
            try:
                doc = frappe.get_cached_doc(doctype, name)
                log_to_print_designer(f"Checking document {doctype}/{name} for dynamic watermark")
                dynamic_watermark = doc.get("watermark_text")
                if dynamic_watermark and dynamic_watermark != "None":
                    if isinstance(dynamic_watermark, (list, tuple)):
                        dynamic_watermark = ", ".join(
                            str(item) for item in dynamic_watermark
                        )
                    watermark_text = frappe._(str(dynamic_watermark))
                    log_to_print_designer(f"Using dynamic watermark: {watermark_text}")
            except Exception as e:
                log_to_print_designer(f"Error getting dynamic watermark: {e}")

        if watermark_text:
            # Calculate position CSS based on selection (CSS 2.1 compatible only)
            # Use same positioning as print preview for consistency
            position_css = ""
            if position == "Top Right":
                position_css = (
                    "top: 70px; right: 70px;"  # Below page numbers, same as preview
                )
            elif position == "Top Left":
                position_css = "top: 70px; left: 20px;"
            elif position == "Bottom Right":
                position_css = "bottom: 20px; right: 70px;"
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
                    color: #000000;
                    font-weight: normal;
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
                        f'<div id="header-html">{watermark_html}',
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
        
        log_to_print_designer(f"PDF generated successfully with watermark: {watermark_text}")
        return pdf_file

    # If no watermarks needed, use original function
    log_to_print_designer(f"No watermarks needed, using original PDF function for {doctype}/{name}")
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
