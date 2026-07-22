import os

import frappe
from frappe.utils.print_format import download_pdf as original_download_pdf

from print_designer.overrides.printview_watermark import (
    build_pdf_watermark_html,
    get_watermark_position_css,
    inject_pdf_watermark_html,
    mm_to_px,
    resolve_basic_watermark_context,
)

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

OBSOLETE_INLINE_PDF_WATERMARK_NOTE = """
OBSOLETE: the legacy inline PDF watermark parsing/build/injection logic that used to live
inside download_pdf_with_signature_stamp was extracted to
print_designer.overrides.printview_watermark.

Use these shared helpers now:
- resolve_basic_watermark_context
- mm_to_px
- build_pdf_watermark_html
- inject_pdf_watermark_html

The exact old inline implementation is intentionally retired from the live path to avoid
preview/PDF drift. Recover it from git history if temporary rollback is ever needed.
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
        **watermark_config,
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

    try:
        log_to_print_designer(f"PDF download requested for {doctype}/{name} with kwargs: {kwargs}")
        log_to_print_designer(f"Form dict: {dict(frappe.form_dict)}")
    except Exception as e:
        print(f"Error in logging: {e}")
        frappe.log_error(f"PDF download debug error: {e}")

    # Get signature and stamp from form_dict if not provided
    digital_signature = digital_signature or frappe.form_dict.get("digital_signature")
    company_stamp = company_stamp or frappe.form_dict.get("company_stamp")

    # Add signature/stamp context to frappe.local for template access
    if digital_signature or company_stamp:
        signature_stamp_context = get_signature_and_stamp_context(digital_signature, company_stamp)

        # Store in frappe.local so templates can access it
        if not hasattr(frappe.local, "print_context"):
            frappe.local.print_context = {}
        frappe.local.print_context.update(signature_stamp_context)

    # Handle watermark settings for PDF generation
    # First check URL parameters for watermark_settings
    watermark_settings = frappe.form_dict.get("watermark_settings") or kwargs.get(
        "watermark_settings"
    )
    print(f"watermark_settings from URL: {watermark_settings}")

    # If not in URL, check settings parameter
    if not watermark_settings and settings:
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

        # Watermark-only logic has been extracted to printview_watermark.py so
        # preview and PDF paths share the same parsing/normalization rules.
        # OBSOLETE: the previous inline implementation has been removed from the
        # live code path and preserved in git history to avoid drift.
        watermark_context = resolve_basic_watermark_context(
            doctype=doctype,
            name=name,
            settings=settings,
            watermark_settings=watermark_settings,
        )
        pd_custom_watermark_text = watermark_context["watermark_text"]

        log_to_print_designer(
            f"[PDF WATERMARK] parsed_settings keys: {list(watermark_context['parsed_settings'].keys())}"
        )
        log_to_print_designer(
            "[PDF WATERMARK] resolved values: "
            f"mode={watermark_context['watermark_settings']}, "
            f"font_size={watermark_context['font_size']}, "
            f"position={watermark_context['position']}, "
            f"font_family={watermark_context['font_family']}, "
            f"top={watermark_context['margin_top']}, "
            f"right={watermark_context['margin_right']}, "
            f"bottom={watermark_context['margin_bottom']}, "
            f"left={watermark_context['margin_left']}"
        )

        if pd_custom_watermark_text:
            position_css = get_watermark_position_css(
                watermark_context["position"],
                margin_top=mm_to_px(watermark_context["margin_top"]),
                margin_right=mm_to_px(watermark_context["margin_right"]),
                margin_bottom=mm_to_px(watermark_context["margin_bottom"]),
                margin_left=mm_to_px(watermark_context["margin_left"]),
            )
            log_to_print_designer(
                f"[PDF WATERMARK] position_css={position_css}, text={pd_custom_watermark_text}"
            )

            watermark_html = build_pdf_watermark_html(
                pd_custom_watermark_text,
                position_css,
                watermark_context["font_size"],
                watermark_context["font_family"],
            )
            html_content = inject_pdf_watermark_html(
                html_content, watermark_html, pd_custom_watermark_text
            )

        # Now generate PDF from the modified HTML
        # Try wkhtmltopdf first, fallback to WeasyPrint if it fails
        pdf_file = None
        try:
            from frappe.utils.pdf import get_pdf

            pdf_file = get_pdf(html_content)
            log_to_print_designer("PDF generated with wkhtmltopdf (with watermark)")
        except Exception as wk_error:
            log_to_print_designer(f"wkhtmltopdf failed: {wk_error}, trying WeasyPrint fallback")
            try:
                from print_designer.weasyprint_integration import get_pdf_with_weasyprint

                pdf_file = get_pdf_with_weasyprint(html_content)
                log_to_print_designer("PDF generated with WeasyPrint fallback (with watermark)")
            except Exception as wp_error:
                log_to_print_designer(f"WeasyPrint also failed: {wp_error}")
                frappe.log_error(
                    f"Both PDF generators failed. wkhtmltopdf: {wk_error}, WeasyPrint: {wp_error}",
                    "PDF Generation",
                )
                frappe.throw(f"PDF generation failed: {str(wk_error)}")

        # Set response similar to original download_pdf
        if not doc:
            doc = frappe.get_doc(doctype, name)
        frappe.local.response.filename = "{name}.pdf".format(
            name=name.replace(" ", "-").replace("/", "-")
        )
        frappe.local.response.filecontent = pdf_file
        frappe.local.response.type = "pdf"

        log_to_print_designer(
            f"PDF generated successfully with watermark: {pd_custom_watermark_text}"
        )
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
    # If wkhtmltopdf fails, fallback to WeasyPrint
    try:
        result = original_download_pdf(**pdf_kwargs)
        log_to_print_designer("Original PDF function completed successfully")
        return result
    except Exception as e:
        log_to_print_designer(f"Error in original PDF function: {e}, trying WeasyPrint fallback")
        # Try WeasyPrint fallback
        try:
            from print_designer.weasyprint_integration import get_pdf_with_weasyprint

            # Get the HTML content for WeasyPrint
            html_content = frappe.get_print(
                doctype,
                name,
                format,
                doc=doc,
                no_letterhead=no_letterhead,
            )
            pdf_file = get_pdf_with_weasyprint(html_content)

            # Set response
            frappe.local.response.filename = "{name}.pdf".format(
                name=name.replace(" ", "-").replace("/", "-")
            )
            frappe.local.response.filecontent = pdf_file
            frappe.local.response.type = "pdf"

            log_to_print_designer("PDF generated with WeasyPrint fallback (no watermark)")
            return pdf_file
        except Exception as wp_error:
            log_to_print_designer(f"WeasyPrint fallback also failed: {wp_error}")
            frappe.log_error(
                f"Both PDF generators failed. wkhtmltopdf: {e}, WeasyPrint: {wp_error}",
                "PDF Generation",
            )
            frappe.throw(f"PDF generation failed: {str(e)}")


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
