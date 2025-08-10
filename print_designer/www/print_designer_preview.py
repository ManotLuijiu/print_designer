import json

import frappe
from frappe import _
from frappe.utils import cint


def get_context(context):
    """
    Print Designer Preview endpoint that uses the same rendering system as PDF generation
    but outputs HTML optimized for browser printing.
    """
    # Get parameters from URL
    doctype = frappe.form_dict.get("doctype")
    name = frappe.form_dict.get("name")
    print_format = frappe.form_dict.get("format")
    letterhead = frappe.form_dict.get("letterhead")
    no_letterhead = cint(frappe.form_dict.get("no_letterhead", 0))
    settings = frappe.form_dict.get("settings", "{}")
    trigger_print = cint(frappe.form_dict.get("trigger_print", 0))

    if not doctype or not name:
        frappe.throw(_("Document type and name are required"))

    # Get the document
    try:
        doc = frappe.get_doc(doctype, name)
        doc.check_permission("read")
    except Exception as e:
        frappe.throw(_("Error loading document: {0}").format(str(e)))

    # Get print format
    if not print_format:
        print_format = "Standard"

    try:
        print_format_doc = frappe.get_doc("Print Format", print_format)
    except Exception:
        frappe.throw(_("Print format not found: {0}").format(print_format))

    # Check if this is a Print Designer format
    is_print_designer = (
        hasattr(print_format_doc, "print_designer")
        and print_format_doc.print_designer
        and hasattr(print_format_doc, "print_designer_body")
        and print_format_doc.print_designer_body
    )

    if not is_print_designer:
        # For non-Print Designer formats, redirect to standard printview
        redirect_url = f"/printview?doctype={doctype}&name={name}&format={print_format}"
        if letterhead:
            redirect_url += f"&letterhead={letterhead}"
        if no_letterhead:
            redirect_url += f"&no_letterhead={no_letterhead}"
        if trigger_print:
            redirect_url += f"&trigger_print={trigger_print}"
        if settings != "{}":
            redirect_url += f"&settings={settings}"

        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = redirect_url
        return

    # Generate Print Designer HTML using the same system as PDF generation
    try:
        # Use the same approach as the PDF generation but for HTML output
        from frappe.www.printview import get_rendered_template

        # Get the rendered HTML using Frappe's standard method which will
        # call Print Designer hooks for Print Designer formats
        html_content = get_rendered_template(
            doc=doc,
            print_format=print_format_doc,
            meta=doc.meta,
            trigger_print=trigger_print,
            no_letterhead=no_letterhead,
            letterhead=letterhead,
            settings=json.loads(settings) if settings else {},
        )

        # Get Print Designer CSS
        css_content = get_print_designer_css(print_format_doc)

        # Enhance HTML for browser printing
        enhanced_html = enhance_for_browser_printing(html_content, trigger_print)

    except Exception as e:
        frappe.log_error(f"Error generating Print Designer preview: {str(e)}")
        frappe.throw(_("Error generating print preview: {0}").format(str(e)))

    # Set context for the template
    context.update(
        {
            "body": enhanced_html,
            "print_style": css_content,
            "title": f"{doctype}: {name}",
            "doctype": doctype,
            "name": name,
            "print_format": print_format,
            "letterhead": letterhead,
            "no_letterhead": no_letterhead,
            "trigger_print": trigger_print,
            "lang": frappe.local.lang,
            "layout_direction": "rtl"
            if frappe.local.lang in ["ar", "he", "fa"]
            else "ltr",
        }
    )


def get_print_designer_css(print_format_doc):
    """Get CSS for Print Designer format"""
    try:
        css = print_format_doc.css or ""

        # Add Print Designer specific CSS for browser printing
        browser_css = """
        /* Print Designer Browser Printing Styles */
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }

        #__print_designer {
            width: 100%;
            margin: 0;
            padding: 0;
        }

        /* Hide duplicate elements */
        .hidden-pdf {
            display: none !important;
        }

        /* Print styles */
        @media print {
            .no-print, .action-banner {
                display: none !important;
            }

            body {
                margin: 0;
            }

            .hidden-pdf {
                display: none !important;
            }
        }

        /* Action banner */
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
        """

        return css + browser_css

    except Exception:
        return ""


def enhance_for_browser_printing(html, trigger_print=False):
    """Enhance HTML for browser printing with page numbering"""

    # Add page numbering script
    page_script = (
        """
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            initializePageNumbering();

            // Auto-print if trigger_print is set
            """
        + (
            """
            setTimeout(function() {
                window.print();
            }, 1000);
            """
            if trigger_print
            else ""
        )
        + """
        });

        window.addEventListener('beforeprint', function() {
            initializePageNumbering();
        });

        function initializePageNumbering() {
            const dateObj = new Date();

            function replaceText(parentEL, className, text) {
                const elements = parentEL.getElementsByClassName(className);
                for (let j = 0; j < elements.length; j++) {
                    elements[j].textContent = text;
                }
            }

            // Estimate total pages
            const bodyHeight = document.body.scrollHeight;
            const pageHeight = 1056; // A4 page height
            const totalPages = Math.max(1, Math.ceil(bodyHeight / pageHeight));

            // Update page info elements
            replaceText(document, "page_info_page", "1");
            replaceText(document, "page_info_topage", totalPages.toString());
            replaceText(document, "page_info_date", dateObj.toLocaleDateString());
            replaceText(document, "page_info_isodate", dateObj.toISOString());
            replaceText(document, "page_info_time", dateObj.toLocaleTimeString());
        }
    </script>
    """
    )

    # Insert script before closing body tag
    if "</body>" in html:
        html = html.replace("</body>", page_script + "</body>")
    else:
        html += page_script

    return html
