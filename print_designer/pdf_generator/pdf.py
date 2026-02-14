import frappe
from frappe.utils.data import cint

from print_designer.pdf import measure_time
from print_designer.pdf_generator.browser import Browser
from print_designer.pdf_generator.generator import FrappePDFGenerator
from print_designer.pdf_generator.pdf_merge import PDFTransformer


def before_request():
    if frappe.request.path == "/api/method/frappe.utils.print_format.download_pdf":
        frappe.local.form_dict.pdf_generator = (
            frappe.request.args.get(
                "pdf_generator",
                frappe.get_cached_value(
                    "Print Format",
                    frappe.request.args.get("format") or "",
                    "pdf_generator",
                ),
            )
            or "chrome"
        )
        if frappe.local.form_dict.pdf_generator == "chrome":
            # Initialize the browser
            FrappePDFGenerator()
            return


def after_request():
    if (
        frappe.request.path == "/api/method/frappe.utils.print_format.download_pdf"
        and FrappePDFGenerator._instance
    ):
        # Not Heavy operation as if process is not available it returns
        if not FrappePDFGenerator().USE_PERSISTENT_CHROMIUM:
            FrappePDFGenerator()._close_browser()


@measure_time
def get_pdf(print_format, html, options, output, pdf_generator=None):
    print(f"pdf_generator {pdf_generator}")
    if pdf_generator == "chrome":
        # scrubbing url to expand url is not required as we have set url.
        # also, planning to remove network requests anyway 🤞
        generator = FrappePDFGenerator()
        browser = Browser(generator, print_format, html, options)
        transformer = PDFTransformer(browser)
        # transforms and merges header, footer into body pdf and returns merged pdf
        return transformer.transform_pdf(output=output)
    elif pdf_generator == "WeasyPrint":
        from print_designer.weasyprint_integration import get_pdf_with_weasyprint
        return get_pdf_with_weasyprint(html)
    # Use the default pdf generator (wkhtmltopdf)
    return
