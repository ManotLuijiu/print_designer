import html
import os
import re

import frappe
from frappe.translate import print_language
from frappe.www.printview import get_html_and_style as original_get_html_and_style

print("[DEBUG] printview_watermark.py module loaded!")


def get_print_designer_html_for_browser(
    doc,
    print_format_doc,
    no_letterhead=None,
    letterhead=None,
    settings=None,
    is_print_mode=False,
):
    """
    DEPRECATED: This function is no longer used after Print button fix.

    The fix was to let standard Frappe rendering handle Print Designer formats for browser printing,
    as the original frappe/print_designer only handles PDF generation, not browser printing.

    This function attempted to use Print Designer's PDF rendering system for browser printing,
    which caused conflicts. Now we use standard rendering + watermarks only.
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
            if hasattr(print_format_doc, "html"):
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
        
        /* Fix whitespace preservation for Print Designer text elements */
        .printDesignerElement[data-element-type="text"],
        .printDesignerElement .editable,
        #firstPageFooter,
        #otherPageFooter,
        #firstPageHeader,
        #otherPageHeader,
        .print-designer-text {
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
        }
        """

        return css + pd_css

    except Exception:
        return ""


def get_watermark_position_css(
    position,
    position_config=None,
    margin_top="10mm",
    margin_right="10mm",
    margin_bottom="10mm",
    margin_left="10mm",
):
    """
    Get CSS positioning styles based on Watermark Settings position configuration

    Args:
        position: Position string from Watermark Settings
        position_config: Dictionary containing custom position values
                        (position_top, position_right, position_bottom, position_left)
        margin_top/right/bottom/left: Independent edge offsets (default "0mm")

    Returns:
        str: CSS positioning properties
    """
    log_to_print_designer(
        f"get_watermark_position_css called with position='{position}', config={position_config}, margins=T{margin_top}/R{margin_right}/B{margin_bottom}/L{margin_left}"
    )
    # Check if custom positioning is requested (keeps px-based custom values as-is)
    if position == "Custom" and position_config:
        custom_css = []

        # Handle top/bottom positioning (top takes precedence)
        if position_config.get("position_top") is not None:
            custom_css.append(f"top: {position_config['position_top']}px;")
        elif position_config.get("position_bottom") is not None:
            custom_css.append(f"bottom: {position_config['position_bottom']}px;")
        else:
            custom_css.append(f"top: {margin_top};")

        # Handle left/right positioning (right takes precedence)
        if position_config.get("position_right") is not None:
            custom_css.append(f"right: {position_config['position_right']}px;")
        elif position_config.get("position_left") is not None:
            custom_css.append(f"left: {position_config['position_left']}px;")
        else:
            custom_css.append(f"right: {margin_right};")

        return " ".join(custom_css)

    # Use predefined positions with independent per-edge margins
    position_map = {
        "Top Left": f"top: {margin_top}; left: {margin_left};",
        "Top Center": f"top: {margin_top}; left: 50%; transform: translateX(-50%);",
        "Top Right": f"top: {margin_top}; right: {margin_right};",
        "Middle Left": f"top: 50%; left: {margin_left}; transform: translateY(-50%);",
        "Middle Center": "top: 50%; left: 50%; transform: translate(-50%, -50%);",
        "Middle Right": f"top: 50%; right: {margin_right}; transform: translateY(-50%);",
        "Bottom Left": f"bottom: {margin_bottom}; left: {margin_left};",
        "Bottom Center": f"bottom: {margin_bottom}; left: 50%; transform: translateX(-50%);",
        "Bottom Right": f"bottom: {margin_bottom}; right: {margin_right};",
    }

    result_css = position_map.get(position, position_map["Top Right"])
    log_to_print_designer(f"Position mapping result: '{position}' -> '{result_css}'")
    return result_css


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
    except (OSError, IOError, BrokenPipeError):
        # Silently fall back to frappe logger for file system errors
        try:
            frappe.logger("print_designer").info(f"[WATERMARK] [{level}] {message}")
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


def parse_watermark_settings_dict(settings):
    """Parse watermark settings payload from preview/PDF calls."""
    if not settings:
        return {}
    if isinstance(settings, str):
        try:
            return frappe.parse_json(settings) or {}
        except Exception:
            return {}
    if isinstance(settings, dict):
        return settings
    try:
        return dict(settings)
    except Exception:
        return {}


def normalize_watermark_measure(value, fallback="0mm", default_unit="mm"):
    """Normalize int/string spacing values into CSS-friendly unit strings."""
    if value is None or value == "":
        value = fallback

    value = str(value).strip()
    if not value:
        value = fallback or f"0{default_unit}"

    for unit in ["mm", "px", "cm", "in"]:
        doubled = unit + unit
        if value.endswith(doubled):
            value = value[: -len(unit)]
            break

    if not any(value.endswith(unit) for unit in ["mm", "px", "cm", "in"]):
        value += default_unit

    return value


def normalize_watermark_font_size(value, fallback=24):
    """Normalize font size values from sidebar/Print Settings into an int."""
    if value is None or value == "":
        value = fallback

    if isinstance(value, str) and value.endswith("px"):
        value = value[:-2]

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(fallback)


def resolve_basic_watermark_context(
    doctype=None, name=None, settings=None, watermark_settings=None
):
    """Resolve watermark settings/text shared by print preview and PDF paths."""
    parsed_settings = parse_watermark_settings_dict(settings)

    try:
        db_print_settings = frappe.get_single("Print Settings")
    except Exception:
        db_print_settings = {}

    effective_mode = (
        watermark_settings
        or parsed_settings.get("watermark_settings")
        or db_print_settings.get("watermark_settings", "None")
    )
    if not effective_mode:
        effective_mode = "None"

    font_size = normalize_watermark_font_size(
        parsed_settings.get("watermark_font_size"),
        db_print_settings.get("watermark_font_size", 24),
    )
    position = parsed_settings.get("watermark_position") or db_print_settings.get(
        "watermark_position", "Top Right"
    )
    font_family = parsed_settings.get("watermark_font_family") or db_print_settings.get(
        "watermark_font_family", "Kanit"
    )

    # Default margins: Top Right position uses 10mm margins
    margin_top = normalize_watermark_measure(
        parsed_settings.get("watermark_top"), db_print_settings.get("watermark_top", "10mm")
    )
    margin_right = normalize_watermark_measure(
        parsed_settings.get("watermark_right"), db_print_settings.get("watermark_right", "10mm")
    )
    margin_bottom = normalize_watermark_measure(
        parsed_settings.get("watermark_bottom"), db_print_settings.get("watermark_bottom", "10mm")
    )
    margin_left = normalize_watermark_measure(
        parsed_settings.get("watermark_left"), db_print_settings.get("watermark_left", "10mm")
    )

    watermark_text = ""
    custom_text = parsed_settings.get("custom_text")
    if custom_text:
        watermark_text = frappe._(str(custom_text))
    elif effective_mode == "Original on First Page":
        watermark_text = frappe._("Original")
    elif effective_mode == "Copy on All Pages":
        watermark_text = frappe._("Copy")
    elif effective_mode == "Original,Copy on Sequence":
        watermark_text = "sequence"

    if not watermark_text and effective_mode == "None" and doctype and name:
        try:
            doc = frappe.get_cached_doc(doctype, name)
            dynamic_watermark = doc.get("pd_custom_watermark_text")
            if dynamic_watermark and dynamic_watermark != "None":
                if isinstance(dynamic_watermark, (list, tuple)):
                    dynamic_watermark = ", ".join(str(item) for item in dynamic_watermark)
                watermark_text = frappe._(str(dynamic_watermark))
        except Exception as e:
            log_to_print_designer(f"Error getting dynamic watermark: {e}")

    return {
        "parsed_settings": parsed_settings,
        "watermark_settings": effective_mode,
        "font_size": font_size,
        "position": position,
        "font_family": font_family,
        "margin_top": margin_top,
        "margin_right": margin_right,
        "margin_bottom": margin_bottom,
        "margin_left": margin_left,
        "watermark_text": watermark_text,
    }


def mm_to_px(value):
    """Convert normalized CSS units into px for PDF watermark placement."""
    if value is None or value == "":
        return "0px"

    value = str(value).strip()
    if not value:
        return "0px"

    try:
        if value.endswith("mm"):
            return f"{int(float(value[:-2]) * 3.78)}px"
        if value.endswith("px"):
            return f"{int(float(value[:-2]))}px"
        if value.endswith("cm"):
            return f"{int(float(value[:-2]) * 37.8)}px"
        if value.endswith("in"):
            return f"{int(float(value[:-2]) * 96)}px"
        return f"{int(float(value))}px"
    except (TypeError, ValueError):
        return "0px"


def build_pdf_watermark_html(watermark_text, position_css, font_size, font_family):
    """Build watermark CSS/HTML for PDF generation."""
    if watermark_text == "sequence":
        return f"""
                <style>
                    .watermark-sequence {{
                        position: absolute;
                        {position_css}
                        font-size: {font_size}px;
                        color: #000000;
                        font-weight: normal;
                        font-family: {font_family}, sans-serif;
                        z-index: 1000;
                    }}
                </style>
                """

    return f"""
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


def normalize_checkbox_value(value, fallback=False):
    """Normalize Frappe checkbox-ish values into a bool."""
    if value is None:
        return fallback
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def normalize_copy_count(value, fallback=1):
    """Normalize copy count into an int >= 1."""
    try:
        fallback_int = max(1, int(float(fallback)))
    except (TypeError, ValueError):
        fallback_int = 1

    if value is None or value == "":
        return fallback_int
    try:
        return max(1, int(float(value)))
    except (TypeError, ValueError):
        return fallback_int


def get_copy_watermark_text(mode, copy_index):
    """Return the watermark text for a given generated copy/page index (1-based)."""
    if mode == "Original on First Page":
        return frappe._("Original") if copy_index == 1 else ""
    if mode == "Copy on All Pages":
        return frappe._("Copy")
    if mode == "Original,Copy on Sequence":
        return frappe._("Original") if copy_index % 2 == 1 else frappe._("Copy")
    return ""


def build_preview_copy_watermark_html(
    watermark_text,
    position_css,
    font_size,
    font_family,
    watermark_color,
    watermark_opacity,
):
    """Build per-copy preview watermark HTML using Watermark settings as source of truth."""
    if not watermark_text:
        return ""

    return f"""<div class="pd-preview-copy-watermark" style="position: absolute; {position_css} z-index: 1001; font-size: {font_size}px; color: {watermark_color}; opacity: {watermark_opacity}; font-weight: normal; font-family: {font_family}, sans-serif; text-transform: uppercase; pointer-events: none;">{html.escape(str(watermark_text))}</div>"""


def build_multi_copy_preview_html(
    base_html,
    copy_count,
    watermark_mode,
    watermark_position,
    margin_top,
    margin_right,
    margin_bottom,
    margin_left,
    font_size,
    font_family,
    watermark_color,
    watermark_opacity,
    position_config=None,
    page_number_html="",
):
    """Duplicate preview HTML into grouped copy sets using watermark mode/placement."""
    if copy_count <= 1 or not base_html:
        return base_html

    copies = []
    position_css = get_watermark_position_css(
        watermark_position,
        position_config or {},
        margin_top=margin_top,
        margin_right=margin_right,
        margin_bottom=margin_bottom,
        margin_left=margin_left,
    )
    separator_style = """
<style>
    .pd-preview-copy-separator {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 30px;
        padding: 0 24px;
        background-color: var(--gray-700) !important;
    }
    .pd-preview-copy-separator-label {
        display: flex;
        align-items: center;
        gap: 12px;
        width: min(960px, 100%);
        color: #fff;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .pd-preview-copy-separator-label::before,
    .pd-preview-copy-separator-label::after {
        content: "";
        flex: 1;
        border-top: 1px dashed #bdbdbd;
    }
    @media print {
        .pd-preview-copy-separator {
            display: none !important;
        }
    }
</style>
"""

    for idx in range(copy_count):
        watermark_text = get_copy_watermark_text(watermark_mode, idx + 1)
        copy_watermark_html = build_preview_copy_watermark_html(
            watermark_text,
            position_css,
            font_size,
            font_family,
            watermark_color,
            watermark_opacity,
        )
        separator_html = ""
        page_break = ""
        if idx > 0:
            page_break = " page-break-before: always; break-before: page;"
            separator_html = f'<div class="pd-preview-copy-separator"><div class="pd-preview-copy-separator-label">{html.escape(str(frappe._("Copy")))} {idx + 1}</div></div>'

        copies.append(
            f"""{separator_html}<div class="pd-preview-copy" data-copy-index="{idx + 1}" style="position: relative;{page_break}">
{copy_watermark_html}
{page_number_html}
{base_html}
</div>"""
        )

    return separator_style + "\n".join(copies)


def get_page_number_position_css(position, top="2mm", right="2mm", bottom="2mm", left="2mm"):
    """Map page number position to CSS using compact default offsets."""
    position_map = {
        "Top Right": f"top: {top}; right: {right};",
        "Top Left": f"top: {top}; left: {left};",
        "Top Center": f"top: {top}; left: 50%; transform: translateX(-50%);",
        "Bottom Right": f"bottom: {bottom}; right: {right};",
        "Bottom Left": f"bottom: {bottom}; left: {left};",
        "Bottom Center": f"bottom: {bottom}; left: 50%; transform: translateX(-50%);",
    }
    return position_map.get(position, position_map["Top Right"])


def normalize_preview_color(value, fallback="#000000"):
    """Normalize color values coming from Frappe Color fields into CSS colors."""
    color = str(value or fallback).strip()
    if not color:
        return fallback
    if (
        color.startswith("#")
        or color.startswith("rgb")
        or color.startswith("hsl")
        or color.startswith("var(")
    ):
        return color
    if re.fullmatch(r"[0-9a-fA-F]{3}([0-9a-fA-F]{3})?", color):
        return f"#{color}"
    return color


def get_page_number_border_css(border_style, border_color):
    """Convert page number border setting to CSS border declaration."""
    normalized_style = str(border_style or "Solid").strip().lower()
    if normalized_style == "none":
        return "border: none;"
    if normalized_style in {"solid", "dashed", "dotted"}:
        return f"border: 1px {normalized_style} {border_color};"
    return f"border: 1px solid {border_color};"


def build_preview_page_number_html(
    position,
    font_family,
    font_size,
    font_color="#000000",
    border_style="Solid",
    position_type="fixed",
    margin_top=2,
    margin_right=2,
    margin_bottom=2,
    margin_left=2,
):
    """Build preview page number overlay HTML/CSS."""
    position_css = get_page_number_position_css(
        position,
        top=f"{margin_top}mm",
        right=f"{margin_right}mm",
        bottom=f"{margin_bottom}mm",
        left=f"{margin_left}mm",
    )
    normalized_font_color = normalize_preview_color(font_color, "#000000")
    border_css = get_page_number_border_css(border_style, normalized_font_color)
    return f"""
<style>
    .pd-preview-page-number {{
        position: {position_type};
        {position_css}
        z-index: 1002;
        pointer-events: none;
        font-family: {font_family}, sans-serif;
        font-size: {font_size}pt;
        font-weight: 500;
        color: {normalized_font_color};
        background: rgba(255,255,255,0.92);
        padding: 2px 8px;
        border-radius: 999px;
        {border_css}
        line-height: 1.3;
    }}
</style>
<div class="pd-preview-page-number">{html.escape(str(frappe._("Page")))} <span class="page_info_page">1</span> / <span class="page_info_topage">1</span></div>
"""


def inject_preview_page_number_html(html_content, page_number_html):
    """Inject preview page number markup into repeating header when available."""
    if not isinstance(html_content, str):
        return str(html_content) + page_number_html

    if '<div id="header-html">' in html_content:
        return html_content.replace(
            '<div id="header-html">',
            f'<div id="header-html">{page_number_html}',
        )
    if '<div class="print-format' in html_content:
        return html_content.replace(
            '<div class="print-format',
            f'{page_number_html}\n<div class="print-format',
            1,
        )
    if "</body>" in html_content:
        return html_content.replace("</body>", f"{page_number_html}</body>")
    return html_content + page_number_html


def inject_pdf_watermark_html(html_content, watermark_html, watermark_text):
    """Inject regular or sequence watermark markup into PDF HTML."""
    if not isinstance(html_content, str):
        return str(html_content) + watermark_html

    if watermark_text == "sequence":
        if '<div id="header-html">' in html_content:
            html_content = html_content.replace(
                '<div id="header-html">',
                f'<div id="header-html">{watermark_html}',
            )
        elif "<head>" in html_content:
            html_content = html_content.replace("</head>", f"{watermark_html}</head>")
        elif "<body>" in html_content:
            html_content = html_content.replace("<body>", f"<body>{watermark_html}")
        else:
            html_content = watermark_html + html_content

        page_breaks = [
            "page-break-after: always;",
            "page-break-before: always;",
            "break-after: page;",
            "break-before: page;",
            '<div style="page-break-after:always">',
            '<div style="page-break-before:always">',
            'class="page-break"',
            'style="break-after: page"',
            'style="break-before: page"',
        ]

        first_watermark = f'<div class="watermark-sequence">{frappe._("Original")}</div>'
        if '<div class="print-format' in html_content:
            html_content = html_content.replace(
                '<div class="print-format',
                f'{first_watermark}\n<div class="print-format',
                1,
            )
        elif "<body>" in html_content:
            html_content = html_content.replace("<body>", f"<body>{first_watermark}", 1)

        copy_watermark = f'<div class="watermark-sequence">{frappe._("Copy")}</div>'
        for page_break in page_breaks:
            if page_break in html_content:
                matches = re.findall(re.escape(page_break), html_content)
                for _match in matches:
                    if "page-break-after" in page_break or "break-after" in page_break:
                        pattern = rf"({re.escape(page_break)}[^>]*>)"
                        replacement = rf"\1{copy_watermark}"
                        html_content = re.sub(pattern, replacement, html_content, count=1)
                    elif "page-break-before" in page_break or "break-before" in page_break:
                        pattern = rf"({re.escape(page_break)})"
                        replacement = rf"{copy_watermark}\1"
                        html_content = re.sub(pattern, replacement, html_content, count=1)
                break

        if not any(page_break in html_content for page_break in page_breaks):
            if "</table>" in html_content:
                if html_content.count("</table>") > 0:
                    html_content = html_content.replace("</table>", f"</table>{copy_watermark}", 1)
            elif '<div class="print-format' in html_content and html_content.count("<div") > 10:
                div_positions = [m.start() for m in re.finditer("<div", html_content)]
                if len(div_positions) > 5:
                    middle_pos = div_positions[len(div_positions) // 2]
                    html_content = (
                        html_content[:middle_pos] + copy_watermark + html_content[middle_pos:]
                    )

        return html_content

    if '<div id="header-html">' in html_content:
        return html_content.replace(
            '<div id="header-html">',
            f'<div id="header-html">{watermark_html}',
        )
    if '<div class="print-format' in html_content:
        return html_content.replace(
            '<div class="print-format',
            f'{watermark_html}\n<div class="print-format',
        )
    if "</body>" in html_content:
        return html_content.replace("</body>", f"{watermark_html}</body>")
    return html_content + watermark_html


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

    log_to_print_designer(
        f"Print preview override called: print_format={print_format}, settings={settings}, trigger_print={trigger_print}"
    )

    # Check if this is a Print Designer format
    print_format_doc = None
    if print_format:
        try:
            print_format_doc = frappe.get_doc("Print Format", print_format)
        except Exception:
            pass

    # Check if this is a Print Designer format and preserve its original rendering
    is_print_designer_format = print_format_doc and print_format_doc.get("print_designer") == 1

    # NEW: Get language from Print Format's default_print_language
    lang = None
    if print_format_doc and print_format_doc.get("default_print_language"):
        lang = print_format_doc.default_print_language
        log_to_print_designer(f"Using Print Format language: {lang}")

    if is_print_designer_format:
        # For Print Designer formats, we need to preserve the exact CSS and HTML structure
        # to maintain whitespace, fonts, and other styling that works in the designer
        with print_language(lang):
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

        # Ensure Print Designer CSS is preserved in the result
        if result.get("style") and print_format_doc and print_format_doc.css:
            # Preserve original Print Designer CSS which includes whitespace rules
            result["style"] = print_format_doc.css + "\n" + result.get("style", "")
    else:
        # For standard formats, use normal rendering
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

    # Log successful rendering
    log_to_print_designer(
        f"Standard rendering used: format={print_format}, trigger_print={trigger_print}, "
        f"html_length={len(result.get('html', '')) if result else 0}"
    )

    # Parse settings to check for watermark configuration
    settings_dict = parse_watermark_settings_dict(settings)
    log_to_print_designer(f"[DEBUG] settings_dict keys: {list(settings_dict.keys())}")
    log_to_print_designer(
        f"[DEBUG] watermark_top in settings_dict: {settings_dict.get('watermark_top')}"
    )
    print("[PAGE NUMBER DEBUG] ===== SETTINGS DICT RECEIVED =====")
    print(f"[PAGE NUMBER DEBUG] settings_dict: {settings_dict}")
    print(
        f"[PAGE NUMBER DEBUG] page_number_display in settings_dict: {settings_dict.get('page_number_display')}"
    )
    print(
        f"[PAGE NUMBER DEBUG] page_number_position in settings_dict: {settings_dict.get('page_number_position')}"
    )
    print(
        f"[PAGE NUMBER DEBUG] page_number_font_family in settings_dict: {settings_dict.get('page_number_font_family')}"
    )
    print(
        f"[PAGE NUMBER DEBUG] page_number_font_size in settings_dict: {settings_dict.get('page_number_font_size')}"
    )
    print(
        f"[PAGE NUMBER DEBUG] page_number_font_color in settings_dict: {settings_dict.get('page_number_font_color')}"
    )
    print(
        f"[PAGE NUMBER DEBUG] page_number_border in settings_dict: {settings_dict.get('page_number_border')}"
    )
    watermark_settings = settings_dict.get("watermark_settings")
    watermark_template = settings_dict.get("watermark_template")

    # Also check for new watermark fields from our Print Settings override
    watermark_font_size = settings_dict.get("watermark_font_size")
    watermark_position = settings_dict.get("watermark_position")
    watermark_font_family = settings_dict.get("watermark_font_family")
    watermark_top = settings_dict.get("watermark_top")
    watermark_right = settings_dict.get("watermark_right")
    watermark_bottom = settings_dict.get("watermark_bottom")
    watermark_left = settings_dict.get("watermark_left")

    # Read watermark and page_number from print_designer_settings JSON (per-format, saved from Design View)
    pd_watermark_settings = None
    pd_watermark_font_size = None
    pd_watermark_position = None
    pd_watermark_font_family = None
    pd_watermark_top = None
    pd_watermark_right = None
    pd_watermark_bottom = None
    pd_watermark_left = None
    pd_watermark = {}  # Initialize to empty dict for later use
    pd_page_number = {}  # Initialize to empty dict for page number settings
    if print_format_doc and print_format_doc.get("print_designer_settings"):
        try:
            pd_settings = frappe.parse_json(print_format_doc.get("print_designer_settings"))
            if pd_settings and isinstance(pd_settings, dict):
                pd_watermark = pd_settings.get("watermark", {})
                if pd_watermark and isinstance(pd_watermark, dict):
                    pd_watermark_settings = pd_watermark.get("mode")
                    pd_watermark_font_size = pd_watermark.get("font_size")
                    pd_watermark_position = pd_watermark.get("position")
                    pd_watermark_font_family = pd_watermark.get("font_family")
                    pd_watermark_top = pd_watermark.get("top")
                    pd_watermark_right = pd_watermark.get("right")
                    pd_watermark_bottom = pd_watermark.get("bottom")
                    pd_watermark_left = pd_watermark.get("left")
                    log_to_print_designer(
                        f"[WATERMARK] Read from print_designer_settings: mode={pd_watermark_settings}, "
                        f"font_size={pd_watermark_font_size}, position={pd_watermark_position}, "
                        f"font_family={pd_watermark_font_family}, "
                        f"top={pd_watermark_top}, right={pd_watermark_right}, "
                        f"bottom={pd_watermark_bottom}, left={pd_watermark_left}"
                    )
                # Read page_number from print_designer_settings
                pd_page_number = pd_settings.get("page_number", {})
                if pd_page_number and isinstance(pd_page_number, dict):
                    log_to_print_designer(
                        f"[PAGE NUMBER] Read from print_designer_settings: "
                        f"display={pd_page_number.get('display')}, "
                        f"position={pd_page_number.get('position')}"
                    )
        except Exception as e:
            log_to_print_designer(f"[WATERMARK] Error parsing print_designer_settings: {e}")

    # Frappe's print view JS sends "None" as string when watermark is disabled.
    # We should respect "None" from sidebar - don't fall back to Print Format doc values.
    # Only fall back to Print Format doc if sidebar didn't send watermark_settings at all (None).
    # Priority: settings_dict > print_designer_settings JSON > print_format_doc fields > Print Settings
    if watermark_settings is None:
        # Use per-format watermark from print_designer_settings
        if pd_watermark_settings:
            watermark_settings = pd_watermark_settings
            watermark_font_size = watermark_font_size or pd_watermark_font_size
            watermark_position = watermark_position or pd_watermark_position
            watermark_font_family = watermark_font_family or pd_watermark_font_family
            watermark_top = watermark_top or pd_watermark_top
            watermark_right = watermark_right or pd_watermark_right
            watermark_bottom = watermark_bottom or pd_watermark_bottom
            watermark_left = watermark_left or pd_watermark_left
            log_to_print_designer(
                f"Watermark settings read from print_designer_settings JSON: settings={watermark_settings}, "
                f"font_size={watermark_font_size}, position={watermark_position}, font_family={watermark_font_family}, "
                f"top={watermark_top}, right={watermark_right}, bottom={watermark_bottom}, left={watermark_left}"
            )
        elif print_format_doc:
            # Fall back to individual Print Format doc fields
            watermark_settings = print_format_doc.get("watermark_settings")
            watermark_font_size = watermark_font_size or print_format_doc.get("watermark_font_size")
            watermark_position = watermark_position or print_format_doc.get("watermark_position")
            watermark_font_family = watermark_font_family or print_format_doc.get(
                "watermark_font_family"
            )
            log_to_print_designer(
                f"Watermark settings read from Print Format doc: settings={watermark_settings}, "
                f"font_size={watermark_font_size}, position={watermark_position}, font_family={watermark_font_family}"
            )

    # Normalize None and "None" to "None" for consistent comparison
    if not watermark_settings:
        watermark_settings = "None"

    log_to_print_designer(
        f"Print preview watermark request - settings: {watermark_settings}, template: {watermark_template}, font_size: {watermark_font_size}, position: {watermark_position}, font_family: {watermark_font_family}"
    )

    try:
        print_settings = frappe.get_single("Print Settings")
        print("[PAGE NUMBER DEBUG] ===== PRINT SETTINGS LOADED =====")
        print(f"[PAGE NUMBER DEBUG] Full print_settings: {print_settings}")
        print(
            f"[PAGE NUMBER DEBUG] page_number_display: {print_settings.get('page_number_display')}"
        )
        print(
            f"[PAGE NUMBER DEBUG] page_number_position: {print_settings.get('page_number_position')}"
        )
        print(
            f"[PAGE NUMBER DEBUG] page_number_font_family: {print_settings.get('page_number_font_family')}"
        )
        print(
            f"[PAGE NUMBER DEBUG] page_number_font_size: {print_settings.get('page_number_font_size')}"
        )
        print(
            f"[PAGE NUMBER DEBUG] page_number_font_color: {print_settings.get('page_number_font_color')}"
        )
        print(f"[PAGE NUMBER DEBUG] page_number_border: {print_settings.get('page_number_border')}")
        print("[PAGE NUMBER DEBUG] settings_dict:", settings_dict)
    except Exception:
        print_settings = {}
        print("[PAGE NUMBER DEBUG] Failed to load Print Settings")

    copy_enabled = normalize_checkbox_value(
        settings_dict.get("enable_multiple_copies"),
        normalize_checkbox_value(print_settings.get("enable_multiple_copies"), False),
    )
    copy_count = normalize_copy_count(
        settings_dict.get("default_copy_count"),
        print_settings.get("default_copy_count", 1),
    )
    multi_copy_preview = copy_enabled and copy_count > 1

    effective_mode = watermark_settings or "None"
    position_config = {}

    # Fallback hierarchy: settings_dict > print_designer_settings > print_settings
    # watermark_font_size fallback chain
    font_size_raw = settings_dict.get("watermark_font_size") or pd_watermark_font_size
    font_size = normalize_watermark_font_size(
        font_size_raw,
        print_settings.get("watermark_font_size", 24),
    )

    # font_family fallback chain
    font_family = (
        settings_dict.get("watermark_font_family")
        or pd_watermark_font_family
        or print_settings.get("watermark_font_family", "Kanit")
    )

    # watermark_position fallback chain
    watermark_position = (
        settings_dict.get("watermark_position")
        or pd_watermark_position
        or print_settings.get("watermark_position", "Top Right")
    )

    # Margin fallback chain
    watermark_top = normalize_watermark_measure(
        settings_dict.get("watermark_top") or (pd_watermark.get("top") if pd_watermark else None),
        print_settings.get("watermark_top", "0mm"),
    )
    watermark_right = normalize_watermark_measure(
        settings_dict.get("watermark_right")
        or (pd_watermark.get("right") if pd_watermark else None),
        print_settings.get("watermark_right", "0mm"),
    )
    watermark_bottom = normalize_watermark_measure(
        settings_dict.get("watermark_bottom")
        or (pd_watermark.get("bottom") if pd_watermark else None),
        print_settings.get("watermark_bottom", "0mm"),
    )
    watermark_left = normalize_watermark_measure(
        settings_dict.get("watermark_left") or (pd_watermark.get("left") if pd_watermark else None),
        print_settings.get("watermark_left", "0mm"),
    )

    watermark_color = "#999999"
    watermark_opacity = 0.6
    custom_watermark_text = None

    # Add watermark HTML if configured (either via settings or template)
    # CRITICAL: Only show watermark if explicitly set and NOT "None"
    show_watermark = watermark_settings and watermark_settings != "None" and result.get("html")
    show_template_watermark = watermark_template and result.get("html")
    log_to_print_designer(
        f"Watermark condition check - show_watermark: {show_watermark}, show_template: {show_template_watermark}"
    )

    if show_watermark or show_template_watermark:
        context_doctype = settings_dict.get("doctype")
        context_name = settings_dict.get("name") or name
        if not context_doctype and isinstance(doc, dict):
            context_doctype = doc.get("doctype")
        elif not context_doctype and hasattr(doc, "doctype"):
            context_doctype = doc.doctype

        base_context = resolve_basic_watermark_context(
            doctype=context_doctype,
            name=context_name,
            settings=settings,
            watermark_settings=watermark_settings,
        )

        font_size = base_context["font_size"]
        font_family = base_context["font_family"]
        watermark_position = base_context["position"]
        watermark_top = base_context["margin_top"]
        watermark_right = base_context["margin_right"]
        watermark_bottom = base_context["margin_bottom"]
        watermark_left = base_context["margin_left"]
        watermark_color = "#999999"
        watermark_opacity = 0.6
        custom_watermark_text = None
        configured_mode = base_context["watermark_settings"]
        position_config = {}

        try:
            if watermark_template:
                log_to_print_designer(f"Using watermark template: {watermark_template}")
                from print_designer.api.watermark import get_watermark_template_config

                template_config = get_watermark_template_config(watermark_template)
                font_size = normalize_watermark_font_size(
                    settings_dict.get("watermark_font_size"),
                    template_config.get("font_size", font_size),
                )
                font_family = settings_dict.get("watermark_font_family") or template_config.get(
                    "font_family", font_family
                )
                watermark_color = template_config.get("color", "#999999")
                watermark_opacity = template_config.get("opacity", 0.6)
                watermark_position = settings_dict.get("watermark_position") or template_config.get(
                    "position", watermark_position
                )
                custom_watermark_text = template_config.get("custom_text")
                configured_mode = template_config.get("watermark_mode", configured_mode)
                position_config = {
                    "position_top": template_config.get("position_top"),
                    "position_right": template_config.get("position_right"),
                    "position_bottom": template_config.get("position_bottom"),
                    "position_left": template_config.get("position_left"),
                    "position_custom": template_config.get("position_custom"),
                }
                log_to_print_designer(
                    f"Template configuration loaded: mode={configured_mode}, text={custom_watermark_text}, position={watermark_position}, custom_pos={position_config}"
                )
            elif print_format:
                from print_designer.api.watermark import get_watermark_config_for_print_format

                watermark_config = get_watermark_config_for_print_format(print_format)
                if watermark_config.get("enabled"):
                    font_size = normalize_watermark_font_size(
                        settings_dict.get("watermark_font_size"),
                        watermark_config.get("font_size", font_size),
                    )
                    font_family = settings_dict.get(
                        "watermark_font_family"
                    ) or watermark_config.get("font_family", font_family)
                    watermark_color = watermark_config.get("color", "#999999")
                    watermark_opacity = watermark_config.get("opacity", 0.6)
                    watermark_position = settings_dict.get(
                        "watermark_position"
                    ) or watermark_config.get("position", watermark_position)
                    custom_watermark_text = watermark_config.get("custom_text")
                    configured_mode = watermark_config.get("watermark_mode", configured_mode)
                    position_config = {
                        "position_top": watermark_config.get("position_top"),
                        "position_right": watermark_config.get("position_right"),
                        "position_bottom": watermark_config.get("position_bottom"),
                        "position_left": watermark_config.get("position_left"),
                        "position_custom": watermark_config.get("position_custom"),
                    }
                else:
                    raise Exception(
                        f"No Watermark Settings configured for '{print_format}', using Print Settings fallback"
                    )
            else:
                raise Exception("No watermark configuration available")
        except Exception as e:
            log_to_print_designer(f"Failed to get Watermark Settings, using fallback: {str(e)}")
            log_to_print_designer(
                f"Using shared fallback context: font_size={font_size}, font_family={font_family}, position={watermark_position}, margins=T{watermark_top}/R{watermark_right}/B{watermark_bottom}/L{watermark_left}"
            )

        pd_custom_watermark_text = ""
        if custom_watermark_text:
            pd_custom_watermark_text = frappe._(custom_watermark_text)
            log_to_print_designer(
                f"Using custom watermark text from configuration: {pd_custom_watermark_text}"
            )
        elif configured_mode and configured_mode != "None":
            if configured_mode == "Original on First Page":
                pd_custom_watermark_text = frappe._("Original")
            elif configured_mode == "Copy on All Pages":
                pd_custom_watermark_text = frappe._("Copy")
            elif configured_mode == "Original,Copy on Sequence":
                pd_custom_watermark_text = frappe._("Original")
                log_to_print_designer(
                    "Sequence watermark detected - using 'Original' for preview, Chrome PDF will handle full sequence"
                )
        elif base_context["watermark_text"]:
            if base_context["watermark_text"] == "sequence":
                pd_custom_watermark_text = frappe._("Original")
                log_to_print_designer(
                    "Sequence watermark detected from base context - using 'Original' for preview"
                )
            else:
                pd_custom_watermark_text = base_context["watermark_text"]

        watermark_html = ""
        effective_mode = configured_mode or watermark_settings or "None"
        position_type = "absolute" if effective_mode == "Original on First Page" else "fixed"
        if pd_custom_watermark_text:
            # "Original on First Page" → position: absolute (document flow, page 1 only)
            # All other modes → position: fixed (repeats on every page via CSS)
            effective_mode = configured_mode or watermark_settings or "None"
            position_type = "absolute" if effective_mode == "Original on First Page" else "fixed"

            log_to_print_designer(
                f"Creating watermark HTML: text={pd_custom_watermark_text}, font={font_family}, "
                f"position_type={position_type}, margins=T{watermark_top}/R{watermark_right}/B{watermark_bottom}/L{watermark_left}mm"
            )

            # Ensure margins have proper unit (remove duplicate suffixes)
            def ensure_unit(val, default_unit="mm"):
                val = str(val).strip() if val else f"10{default_unit}"
                # Remove duplicate units
                for unit in ["mm", "px", "cm", "in"]:
                    if val.endswith(unit + unit):
                        val = val[: -(len(unit))] + unit
                # Add unit if missing
                if not any(val.endswith(u) for u in ["mm", "px", "cm", "in"]):
                    val += default_unit
                return val

            margin_top = ensure_unit(watermark_top)
            margin_right = ensure_unit(watermark_right)
            margin_bottom = ensure_unit(watermark_bottom)
            margin_left = ensure_unit(watermark_left)

            position_css = get_watermark_position_css(
                watermark_position,
                position_config,
                margin_top=margin_top,
                margin_right=margin_right,
                margin_bottom=margin_bottom,
                margin_left=margin_left,
            )
            log_to_print_designer(f"Watermark CSS: position={position_type}, {position_css}")
            log_to_print_designer(
                "Watermark style vars: "
                f"position_type={position_type}, "
                f"position_css={position_css}, "
                f"font_size={font_size}, "
                f"watermark_color={watermark_color}, "
                f"watermark_opacity={watermark_opacity}, "
                f"font_family={font_family}"
            )

            watermark_html = f"""
            <style>
            	@font-face {{
					font-family: 'Sarabun';
    				src: url('/assets/print_designer/fonts/thai/Sarabun/Sarabun-Regular.ttf') format('truetype');
				}}

                .watermark {{
                    position: {position_type};
                    {position_css}
                    font-size: {font_size}px;
                    color: {watermark_color};
                    opacity: {watermark_opacity};
                    font-weight: normal;
                    font-family: {font_family}, sans-serif;
                    z-index: 1000;
                    text-transform: uppercase;
                }}
            </style>
            <div id="print__preview__watermark__wrapper" class="watermark">{pd_custom_watermark_text}</div>
            """

        # Insert watermark HTML if any watermark was generated
        if watermark_html and not multi_copy_preview:
            html = result["html"]

            # Only insert into #header-html (Chrome CDP repeating header) when watermark
            # should appear on every page. "Original on First Page" must stay in body flow.
            use_header = (position_type == "fixed") and ('<div id="header-html">' in html)
            if use_header:
                html = html.replace(
                    '<div id="header-html">', f'<div id="header-html">{watermark_html}'
                )
            elif '<div class="print-format' in html:
                html = html.replace(
                    '<div class="print-format',
                    f'{watermark_html}\n<div class="print-format',
                )
            else:
                html += watermark_html

            result["html"] = html
            log_to_print_designer(
                f"Watermark added to print preview HTML. text={pd_custom_watermark_text}, mode={effective_mode}"
            )

    if result.get("html"):
        print("[PAGE NUMBER DEBUG] ===== PAGE NUMBER SETTINGS PARSING =====")
        print(
            f"[PAGE NUMBER DEBUG] settings_dict.get('page_number_display'): {settings_dict.get('page_number_display')}"
        )
        print(
            f"[PAGE NUMBER DEBUG] print_settings.page_number_display: {print_settings.get('page_number_display') if isinstance(print_settings, dict) else getattr(print_settings, 'page_number_display', None)}"
        )

        # Fallback chain: settings_dict > print_designer_settings > print_settings > defaults
        page_number_display = (
            settings_dict.get("page_number_display")
            or pd_page_number.get("display")
            or (
                print_settings.get("page_number_display")
                if isinstance(print_settings, dict)
                else getattr(print_settings, "page_number_display", None)
            )
            or "Show"
        )
        page_number_position = (
            settings_dict.get("page_number_position")
            or pd_page_number.get("position")
            or (
                print_settings.get("page_number_position")
                if isinstance(print_settings, dict)
                else getattr(print_settings, "page_number_position", None)
            )
            or "Top Right"
        )
        page_number_font_family = (
            settings_dict.get("page_number_font_family")
            or pd_page_number.get("font_family")
            or (
                print_settings.get("page_number_font_family")
                if isinstance(print_settings, dict)
                else getattr(print_settings, "page_number_font_family", None)
            )
            or "Sarabun"
        )
        page_number_font_size = normalize_copy_count(
            settings_dict.get("page_number_font_size"),
            pd_page_number.get("font_size")
            or (
                print_settings.get("page_number_font_size")
                if isinstance(print_settings, dict)
                else getattr(print_settings, "page_number_font_size", None)
            )
            or 10,
        )
        page_number_font_color = (
            settings_dict.get("page_number_font_color")
            or pd_page_number.get("font_color")
            or (
                print_settings.get("page_number_font_color")
                if isinstance(print_settings, dict)
                else getattr(print_settings, "page_number_font_color", None)
            )
            or "666666"
        )
        page_number_border = (
            settings_dict.get("page_number_border")
            or pd_page_number.get("border")
            or (
                print_settings.get("page_number_border")
                if isinstance(print_settings, dict)
                else getattr(print_settings, "page_number_border", None)
            )
            or "Solid"
        )
        # Page number margin values
        page_number_top = (
            settings_dict.get("page_number_top")
            or pd_page_number.get("top")
            or (
                print_settings.get("page_number_top")
                if isinstance(print_settings, dict)
                else getattr(print_settings, "page_number_top", None)
            )
            or 2
        )
        page_number_right = (
            settings_dict.get("page_number_right")
            or pd_page_number.get("right")
            or (
                print_settings.get("page_number_right")
                if isinstance(print_settings, dict)
                else getattr(print_settings, "page_number_right", None)
            )
            or 2
        )
        page_number_bottom = (
            settings_dict.get("page_number_bottom")
            or pd_page_number.get("bottom")
            or (
                print_settings.get("page_number_bottom")
                if isinstance(print_settings, dict)
                else getattr(print_settings, "page_number_bottom", None)
            )
            or 2
        )
        page_number_left = (
            settings_dict.get("page_number_left")
            or pd_page_number.get("left")
            or (
                print_settings.get("page_number_left")
                if isinstance(print_settings, dict)
                else getattr(print_settings, "page_number_left", None)
            )
            or 2
        )

        print("[PAGE NUMBER DEBUG] FINAL VALUES:")
        print(f"[PAGE NUMBER DEBUG]   page_number_display: {page_number_display}")
        print(f"[PAGE NUMBER DEBUG]   page_number_position: {page_number_position}")
        print(f"[PAGE NUMBER DEBUG]   page_number_font_family: {page_number_font_family}")
        print(f"[PAGE NUMBER DEBUG]   page_number_font_size: {page_number_font_size}")
        print(f"[PAGE NUMBER DEBUG]   page_number_font_color: {page_number_font_color}")
        print(f"[PAGE NUMBER DEBUG]   page_number_border: {page_number_border}")
        print(
            f"[PAGE NUMBER DEBUG]   page_number margins: top={page_number_top}, right={page_number_right}, bottom={page_number_bottom}, left={page_number_left}"
        )
        print(f"[PAGE NUMBER DEBUG]   multi_copy_preview: {multi_copy_preview}")

        multi_copy_page_number_html = ""
        if page_number_display == "Show" and multi_copy_preview:
            multi_copy_page_number_html = build_preview_page_number_html(
                page_number_position,
                page_number_font_family,
                page_number_font_size,
                font_color=page_number_font_color,
                border_style=page_number_border,
                position_type="absolute",
                margin_top=page_number_top,
                margin_right=page_number_right,
                margin_bottom=page_number_bottom,
                margin_left=page_number_left,
            )

        if multi_copy_preview:
            preview_watermark_mode = watermark_settings
            preview_watermark_position = watermark_position or print_settings.get(
                "watermark_position", "Top Right"
            )
            preview_watermark_font_size = normalize_watermark_font_size(
                settings_dict.get("watermark_font_size"),
                print_settings.get("watermark_font_size", 24),
            )
            preview_watermark_font_family = settings_dict.get(
                "watermark_font_family"
            ) or print_settings.get("watermark_font_family", "Kanit")
            preview_watermark_color = "#999999"
            preview_watermark_opacity = 0.6
            preview_watermark_top = normalize_watermark_measure(
                settings_dict.get("watermark_top"), print_settings.get("watermark_top", "0mm")
            )
            preview_watermark_right = normalize_watermark_measure(
                settings_dict.get("watermark_right"), print_settings.get("watermark_right", "0mm")
            )
            preview_watermark_bottom = normalize_watermark_measure(
                settings_dict.get("watermark_bottom"),
                print_settings.get("watermark_bottom", "0mm"),
            )
            preview_watermark_left = normalize_watermark_measure(
                settings_dict.get("watermark_left"), print_settings.get("watermark_left", "0mm")
            )

            if show_watermark or show_template_watermark:
                preview_watermark_mode = effective_mode
                preview_watermark_position = watermark_position
                preview_watermark_font_size = font_size
                preview_watermark_font_family = font_family
                preview_watermark_color = watermark_color
                preview_watermark_opacity = watermark_opacity
                preview_watermark_top = normalize_watermark_measure(watermark_top)
                preview_watermark_right = normalize_watermark_measure(watermark_right)
                preview_watermark_bottom = normalize_watermark_measure(watermark_bottom)
                preview_watermark_left = normalize_watermark_measure(watermark_left)

            result["html"] = build_multi_copy_preview_html(
                result["html"],
                copy_count,
                preview_watermark_mode,
                preview_watermark_position,
                preview_watermark_top,
                preview_watermark_right,
                preview_watermark_bottom,
                preview_watermark_left,
                preview_watermark_font_size,
                preview_watermark_font_family,
                preview_watermark_color,
                preview_watermark_opacity,
                position_config if (show_watermark or show_template_watermark) else {},
                page_number_html=multi_copy_page_number_html,
            )
            log_to_print_designer(
                f"Multi-copy preview applied: copy_count={copy_count}, mode={preview_watermark_mode}, position={preview_watermark_position}, page_number_display={page_number_display}"
            )
            print(
                f"[PAGE NUMBER DEBUG] Multi-copy page number HTML built with: position={page_number_position}, font_family={page_number_font_family}, font_size={page_number_font_size}, color={page_number_font_color}, border={page_number_border}"
            )
        elif page_number_display == "Show":
            page_number_html = build_preview_page_number_html(
                page_number_position,
                page_number_font_family,
                page_number_font_size,
                font_color=page_number_font_color,
                border_style=page_number_border,
                margin_top=page_number_top,
                margin_right=page_number_right,
                margin_bottom=page_number_bottom,
                margin_left=page_number_left,
            )
            print("[PAGE NUMBER DEBUG] ===== BUILDING PAGE NUMBER HTML =====")
            print("[PAGE NUMBER DEBUG] page_number_html generated:")
            print(page_number_html)
            print("[PAGE NUMBER DEBUG] ===== INJECTING PAGE NUMBER =====")
            result["html"] = inject_preview_page_number_html(result["html"], page_number_html)
            print(f"[PAGE NUMBER DEBUG] Page number injected! HTML length: {len(result['html'])}")
            log_to_print_designer(
                f"Preview page number applied: position={page_number_position}, font_family={page_number_font_family}, font_size={page_number_font_size}pt, font_color={page_number_font_color}, border={page_number_border}"
            )
        else:
            print(
                f"[PAGE NUMBER DEBUG] page_number_display = '{page_number_display}' - NOT showing page number"
            )

    return result
