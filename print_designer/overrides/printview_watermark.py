import frappe
from frappe.www.printview import get_html_and_style as original_get_html_and_style


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

    # Add watermark HTML if configured
    if watermark_settings and watermark_settings != "None" and result.get("html"):
        # Get watermark configuration from Print Settings
        try:
            print_settings = frappe.get_single("Print Settings")
            font_size = print_settings.get("watermark_font_size", 24)
            font_family = print_settings.get("watermark_font_family", "Sarabun")
        except Exception:
            font_size = 24
            font_family = "Sarabun"

        # Get watermark text from multiple sources
        watermark_text = ""

        # First, check the traditional watermark_settings from Print Settings
        if watermark_settings == "Original on First Page":
            watermark_text = frappe._("Original")
        elif watermark_settings == "Copy on All Pages":
            watermark_text = frappe._("Copy")
        elif watermark_settings == "Original,Copy on Sequence":
            watermark_text = frappe._(
                "Original"
            )  # Default to Original for single page preview

        # Then, check for dynamic watermark from document fields (if available)
        if not watermark_text and settings_dict:
            doc_data = settings_dict.get("doc", {})
            frappe.logger().debug(f"doc_data {doc_data}")
            print(f"doc_data {doc_data}")
            doctype = settings_dict.get("doctype", "")
            docname = settings_dict.get("name", "")

            # Try to get watermark from document field
            if doctype and docname:
                try:
                    doc = frappe.get_cached_doc(doctype, docname)
                    dynamic_watermark = doc.get("watermark_text")
                    frappe.logger().debug(f"dynamic_watermark {dynamic_watermark}")
                    print(f"dynamic_watermark {dynamic_watermark}")
                    if dynamic_watermark and dynamic_watermark != "None":
                        if not isinstance(dynamic_watermark, str):
                            dynamic_watermark = str(dynamic_watermark)
                        watermark_text = frappe._(dynamic_watermark)
                except Exception:
                    pass

        if watermark_text:
            # Calculate position CSS based on selection (CSS 2.1 compatible only)
            # (position_css variable removed as it was unused)
            # You may add logic here if you want to use position_css in the future.

            # Add watermark CSS and HTML (CSS 2.1 compatible only)
            watermark_html = f"""
            <style>
                .watermark {{
                    position: fixed;
                    top: 20mm;
                    right: 20mm;
                    font-size: {font_size}px;
                    color: #999;
                    font-weight: bold;
                    font-family: {font_family}, sans-serif;
                    opacity: 0.1;
                    z-index: 9999;
                }}
            </style>
            <div class="watermark">{watermark_text}</div>
            """

        # Insert watermark HTML if any watermark was generated
        if watermark_html:
            # html = result["html"]
            # if "</body>" in html:
            #     html = html.replace("</body>", f"{watermark_html}</body>")
            # else:
            #     # If no body tag, append at the end
            #     html += watermark_html

            # result["html"] = html
            result["html"] = result["html"].replace(
                '<div class="print-format',
                f'{watermark_html}\n<div class="print-format',
            )
            frappe.logger().debug(f"result {result}")
            print(f"result {result}")

    return result
