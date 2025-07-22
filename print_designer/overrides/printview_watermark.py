import os
import frappe
from frappe.www.printview import get_html_and_style as original_get_html_and_style
from frappe.utils.print_format import download_pdf


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
            f.write(f"[{timestamp}] [WATERMARK] [{level}] {message}\n")
    except Exception as e:
        # Fallback to frappe logger if file logging fails
        frappe.logger("print_designer").info(
            f"Log write failed: {e}, Original message: {message}"
        )


@frappe.whitelist()
def get_html_and_style_with_watermark(
    doc,
    name=None,
    print_format=None,
    no_letterhead=None,
    letterhead=None,
    trigger_print=False,
    style=None,
    settings=None,
):
    """Override of get_html_and_style that adds watermark support"""

    # Get original HTML and style
    result = original_get_html_and_style(
        doc=doc,
        name=name,
        print_format=print_format,
        no_letterhead=no_letterhead,
        letterhead=letterhead,
        trigger_print=trigger_print,
        style=style,
        settings=settings,
    )

    # Parse settings to check for watermark configuration
    settings_dict = frappe.parse_json(settings) if settings else {}
    watermark_settings = settings_dict.get("watermark_settings", "None")

    log_to_print_designer(
        f"Print preview watermark request - settings: {watermark_settings}"
    )

    # Add watermark HTML if configured
    if watermark_settings and watermark_settings != "None" and result.get("html"):
        # Get watermark configuration from Print Settings
        try:
            print_settings = frappe.get_single("Print Settings")
            font_size = print_settings.get("watermark_font_size", 12)
            font_family = print_settings.get("watermark_font_family", "Sarabun")
        except Exception:
            font_size = 12
            font_family = "Sarabun"

        # Get watermark text from multiple sources
        watermark_text = ""

        # First, check the traditional watermark_settings from Print Settings
        if watermark_settings == "Original on First Page":
            watermark_text = frappe._("Original")
        elif watermark_settings == "Copy on All Pages":
            watermark_text = frappe._("Copy")
        elif watermark_settings == "Original,Copy on Sequence":
            # For print preview, show "Original" only since preview shows single page
            # The actual sequence watermarking (Original on page 1, Copy on page 2)
            # is handled by the Chrome PDF generator for multi-page PDFs
            watermark_text = frappe._("Original")

        # Then, check for dynamic watermark from document fields (if available)
        if not watermark_text and settings_dict:
            doc_data = settings_dict.get("doc", {})
            log_to_print_designer(f"Document data for dynamic watermark: {doc_data}")
            doctype = settings_dict.get("doctype", "")
            docname = settings_dict.get("name", "")

            # Try to get watermark from document field
            if doctype and docname:
                try:
                    doc = frappe.get_cached_doc(doctype, docname)
                    dynamic_watermark = doc.get("watermark_text")
                    log_to_print_designer(
                        f"Dynamic watermark from {doctype}/{docname}: {dynamic_watermark}"
                    )
                    if dynamic_watermark and dynamic_watermark != "None":
                        if not isinstance(dynamic_watermark, str):
                            dynamic_watermark = str(dynamic_watermark)
                        watermark_text = frappe._(dynamic_watermark)
                        log_to_print_designer(
                            f"Using dynamic watermark for preview: {watermark_text}"
                        )
                except Exception as e:
                    log_to_print_designer(
                        f"Error getting dynamic watermark for preview: {e}"
                    )

        watermark_html = ""
        if watermark_text:
            # Calculate position CSS based on selection (CSS 2.1 compatible only)
            # Position it below page numbers with consistent positioning for both preview and PDF
            log_to_print_designer(
                f"Creating watermark HTML with text: {watermark_text}, font: {font_family}"
            )
            watermark_html = f"""
            <style>
            	@font-face {{
					font-family: 'Sarabun';
    				src: url('/assets/print_designer/fonts/thai/Sarabun/Sarabun-Regular.ttf') format('truetype');
				}}

				body {{
					font-family: 'Sarabun', sans-serif;
				}}

                .watermark {{
                    position: absolute;
                    top: 70px;
                    right: 70px;
                    font-size: 12px;
                    color: #000000;
                    font-weight: normal;
                    font-family: Sarabun, sans-serif;
                    z-index: 1000;
                }}
            </style>
            <div class="watermark">{watermark_text}</div>
            """

        # Insert watermark HTML if any watermark was generated
        if watermark_html:
            html = result["html"]

            # Try to insert watermark inside header-html div where page numbers are located
            if '<div id="header-html">' in html:
                # Insert watermark right after the header-html opening tag
                html = html.replace(
                    '<div id="header-html">', f'<div id="header-html">{watermark_html}'
                )
            elif '<div class="print-format' in html:
                # Fallback: insert before print-format div
                html = html.replace(
                    '<div class="print-format',
                    f'{watermark_html}\n<div class="print-format',
                )
            else:
                # Last resort: append at the end
                html += watermark_html

            result["html"] = html
            log_to_print_designer(
                f"Watermark added to print preview HTML. Final watermark text: {watermark_text}"
            )

    return result
