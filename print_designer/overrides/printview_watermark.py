import os

import frappe
from frappe.www.printview import get_html_and_style as original_get_html_and_style


def get_print_designer_html_for_browser(
    doc,
    print_format_doc,
    no_letterhead=None,
    letterhead=None,
    settings=None,
    is_print_mode=False,
):
    """
    Generate HTML for Print Designer formats optimized for browser printing.
    This includes proper page numbering and header/footer handling.
    """
    try:
        # Use the standard Frappe rendering system but with Print Designer enhancements
        from frappe.www.printview import get_rendered_template

        # Prepare the document
        if isinstance(doc, str):
            doc = frappe.parse_json(doc)

        # Get the document object
        if isinstance(doc, dict):
            doc_obj = frappe.get_doc(doc)
        else:
            doc_obj = doc

        # Try to use the standard Frappe rendering, but catch Chrome-related errors
        try:
            html = get_rendered_template(
                doc=doc_obj,
                print_format=print_format_doc,
                meta=doc_obj.meta,
                trigger_print=is_print_mode,
                no_letterhead=no_letterhead,
                letterhead=letterhead,
                settings=frappe.parse_json(settings) if settings else {},
            )
        except (BrokenPipeError, OSError, ConnectionError) as chrome_error:
            # If Chrome-related error occurs, fall back to simpler rendering
            log_to_print_designer(f"Chrome rendering failed, using fallback: {str(chrome_error)}")
            
            # Use the print format's HTML directly without Chrome processing
            if hasattr(print_format_doc, 'html'):
                from frappe.www.printview import get_context
                context = get_context(
                    doc=doc_obj,
                    print_format=print_format_doc,
                    meta=doc_obj.meta,
                    no_letterhead=no_letterhead,
                    letterhead=letterhead,
                    settings=frappe.parse_json(settings) if settings else {},
                )
                html = frappe.render_template(print_format_doc.html, context)
            else:
                # Final fallback - raise the error to be caught by outer exception handler
                raise chrome_error

        # Add browser-specific enhancements for page numbering and footer fixing
        enhanced_html = enhance_html_for_browser_printing(html, is_print_mode)

        # Get the style
        style = get_print_designer_style(print_format_doc)

        return {"html": enhanced_html, "style": style}

    except Exception as e:
        log_to_print_designer(f"Error in get_print_designer_html_for_browser: {str(e)}")
        frappe.log_error(f"Error in get_print_designer_html_for_browser: {str(e)}")
        # Fallback to standard method
        doc_str = doc if isinstance(doc, str) else frappe.as_json(doc)
        return original_get_html_and_style(
            doc=doc_str,
            print_format=print_format_doc.name,
            no_letterhead=no_letterhead,
            letterhead=letterhead,
            settings=settings,
        )


def enhance_html_for_browser_printing(html, is_print_mode=False):
    """
    Enhance HTML for browser printing by adding page numbering JavaScript
    and print-specific styles using Print Designer's actual page numbering system.
    """
    # Add Print Designer specific page numbering for browser printing
    browser_page_script = """
    <script>
        // Print Designer page numbering for browser printing
        document.addEventListener('DOMContentLoaded', function() {
            // Load Print Designer CSS if not already loaded
            loadPrintDesignerCSS();

            // Initialize page numbering immediately for preview
            initializePageNumbering();
        });

        window.addEventListener('beforeprint', function() {
            // Update page numbering before printing
            initializePageNumbering();
        });

        function loadPrintDesignerCSS() {
            // Check if Print Designer CSS is already loaded
            const existingLink = document.querySelector('link[href*="print_designer"]');
            if (existingLink) {
                return; // Already loaded
            }

            // Create and inject Print Designer CSS
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.type = 'text/css';
            link.href = '/assets/print_designer/css/print_designer.bundle.css';
            document.head.appendChild(link);

            console.log('Print Designer CSS loaded for browser printing');
        }

        function initializePageNumbering() {
            const dateObj = new Date();

            // Print Designer page numbering system
            function replaceText(parentEL, className, text) {
                const elements = parentEL.getElementsByClassName(className);
                for (let j = 0; j < elements.length; j++) {
                    elements[j].textContent = text;
                }
            }

            // Estimate total pages based on content height (rough approximation)
            const bodyHeight = document.body.scrollHeight;
            const pageHeight = 1056; // A4 page height in pixels (approximate)
            const totalPages = Math.max(1, Math.ceil(bodyHeight / pageHeight));

            // Update page info elements
            replaceText(document, "page_info_page", "1");
            replaceText(document, "page_info_topage", totalPages.toString());
            replaceText(document, "page_info_date", dateObj.toLocaleDateString());
            replaceText(document, "page_info_isodate", dateObj.toISOString());
            replaceText(document, "page_info_time", dateObj.toLocaleTimeString());

            console.log('Print Designer page numbering initialized:', {
                totalPages: totalPages,
                bodyHeight: bodyHeight
            });
        }
    </script>
    """

    # Add print-specific CSS with Print Designer compatibility
    print_css = """
    <style>
        /* Hide duplicate footers and headers for Print Designer formats */
        .hidden-pdf {
            display: none !important;
        }

        /* Hide standard Frappe print elements that conflict with Print Designer */
        .print-format-gutter {
            display: none !important;
        }

        /* Print Designer specific styles for browser printing */
        #__print_designer {
            width: 100%;
            margin: 0;
            padding: 0;
        }

        /* Ensure proper page layout for Print Designer */
        .print-format {
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Action banner styling for print preview */
        .action-banner {
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            padding: 10px;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 1000;
        }

        .action-banner a {
            display: inline-block;
            margin: 0 10px;
            padding: 8px 16px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-weight: 500;
        }

        .action-banner a:hover {
            background: #0056b3;
        }

        @media print {
            .no-print, .action-banner { display: none !important; }
            .page-break { page-break-before: always; }
            body { margin: 0; }

            /* Hide duplicate footers in print mode */
            .hidden-pdf {
                display: none !important;
            }

            /* Ensure headers and footers are positioned correctly for printing */
            .print-header {
                position: fixed;
                top: 0;
                width: 100%;
            }
            .print-footer {
                position: fixed;
                bottom: 0;
                width: 100%;
            }

            /* Print Designer specific print styles */
            #__print_designer {
                width: 100%;
                margin: 0;
                padding: 0;
            }
        }

        /* Ensure Print Designer footers are visible */
        #firstPageFooter,
        #otherPageFooter {
            display: block !important;
        }

        /* Print Designer page numbering elements */
        .page_info_page,
        .page_info_topage,
        .page_info_date,
        .page_info_time {
            font-family: inherit;
        }
    </style>
    """

    # Insert the enhancements before the closing body tag
    if "</body>" in html:
        html = html.replace("</body>", f"{browser_page_script}{print_css}</body>")
    else:
        html += browser_page_script + print_css

    return html


def get_print_designer_style(print_format_doc):
    """
    Get the CSS style for Print Designer formats.
    """
    try:
        # Get the print format CSS
        css = print_format_doc.css or ""

        # Add any additional Print Designer specific styles
        pd_css = """
        /* Print Designer specific styles */
        .print-designer-format {
            font-family: Arial, sans-serif;
            line-height: 1.4;
        }
        """

        return css + pd_css

    except Exception:
        return ""


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
            f.flush()  # Ensure data is written immediately
    except (OSError, IOError, BrokenPipeError) as e:
        # Silently fall back to frappe logger for file system errors
        try:
            frappe.logger("print_designer").info(
                f"[WATERMARK] [{level}] {message}"
            )
        except Exception:
            # If all logging fails, just ignore it to prevent blocking the main process
            pass
    except Exception as e:
        # For any other error, try frappe logger
        try:
            frappe.logger("print_designer").info(
                f"Log write failed: {e}, Original message: [{level}] {message}"
            )
        except Exception:
            # If all logging fails, just ignore it to prevent blocking the main process
            pass


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
    """Override of get_html_and_style that adds watermark support and Print Designer compatibility"""

    # Check if this is a Print Designer format
    print_format_doc = None
    if print_format:
        try:
            print_format_doc = frappe.get_doc("Print Format", print_format)
        except Exception:
            pass

    # For Print Designer formats, we need special handling to ensure proper rendering
    if (
        print_format_doc
        and hasattr(print_format_doc, "print_designer")
        and print_format_doc.print_designer
        and hasattr(print_format_doc, "print_designer_body")
        and print_format_doc.print_designer_body
    ):
        log_to_print_designer(
            f"Print Designer format detected for browser printing: {print_format}"
        )

        # For Print Designer formats, ALWAYS use the Print Designer rendering system
        # This ensures proper header/footer handling and page numbering for both preview and print

        log_to_print_designer(
            f"Using Print Designer rendering for format: {print_format}"
        )

        if trigger_print:
            # Add a flag to indicate this is for browser printing, not PDF
            frappe.local.form_dict["for_browser_print"] = "1"

        try:
            # Always use Print Designer rendering for Print Designer formats
            result = get_print_designer_html_for_browser(
                doc=doc,
                print_format_doc=print_format_doc,
                no_letterhead=no_letterhead,
                letterhead=letterhead,
                settings=settings,
                is_print_mode=trigger_print,
            )
            log_to_print_designer(
                f"Print Designer rendering successful: {len(result.get('html', '')) if result else 0} chars"
            )
        except Exception as e:
            log_to_print_designer(f"Print Designer rendering failed: {str(e)}")
            frappe.log_error(f"Print Designer rendering failed for {print_format}: {str(e)}")
            # Fallback to standard method
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
    else:
        # Not a Print Designer format, use standard method
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
