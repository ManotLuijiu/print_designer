"""Regression tests for the Print Designer PDF download pipeline.

Frappe core's ``download_pdf`` endpoint defaults to ``wkhtmltopdf``.  The
Print Designer renders its documents with Chrome so that the designer header
and footer are merged as their own PDF pages, the page numbers are added and
the body keeps the designer page geometry.

Two things were missing:

1. the app never registered the ``before_request`` / ``after_request`` hooks,
   so ``frappe.local.form_dict.pdf_generator`` was never set to ``chrome`` and
   the endpoint fell back to wkhtmltopdf;
2. the watermark branch of ``download_pdf_with_signature_stamp`` generated the
   PDF with wkhtmltopdf, bypassing the Chrome pipeline completely.

Both paths produced a PDF without the designer header/footer and without the
page numbers.
"""

import unittest
from unittest.mock import patch

import frappe

from print_designer.utils import signature_stamp

DOWNLOAD_PDF_PATH = "/api/method/frappe.utils.print_format.download_pdf"


class RequestContextMixin:
    def set_request(self, path, args=None):
        """Install a fake request for the duration of the test."""
        request = frappe._dict(path=path, args=frappe._dict(args or {}))
        self.addCleanup(self.clear_request)
        frappe.local.request = request
        return request

    def clear_request(self):
        try:
            del frappe.local.request
        except AttributeError:
            pass


class TestDownloadPdfHooks(RequestContextMixin, unittest.TestCase):
    def test_hooks_are_registered(self):
        from print_designer import hooks

        self.assertIn("print_designer.pdf_generator.pdf.before_request", hooks.before_request)
        self.assertIn("print_designer.pdf_generator.pdf.after_request", hooks.after_request)

    def test_hooks_are_active_on_the_site(self):
        self.assertIn(
            "print_designer.pdf_generator.pdf.before_request",
            frappe.get_hooks("before_request"),
        )
        self.assertIn(
            "print_designer.pdf_generator.pdf.after_request",
            frappe.get_hooks("after_request"),
        )

    def test_before_request_selects_chrome_for_the_download_endpoint(self):
        from print_designer.pdf_generator import pdf as pd_pdf

        self.set_request(DOWNLOAD_PDF_PATH, {"doctype": "Payment Entry", "format": "Receipt"})
        frappe.local.form_dict = frappe._dict()

        with patch.object(pd_pdf, "FrappePDFGenerator"):
            pd_pdf.before_request()

        self.assertEqual(frappe.local.form_dict.pdf_generator, "chrome")

    def test_before_request_ignores_other_endpoints(self):
        from print_designer.pdf_generator import pdf as pd_pdf

        self.set_request("/api/method/frappe.client.get_list")
        frappe.local.form_dict = frappe._dict()

        with patch.object(pd_pdf, "FrappePDFGenerator"):
            pd_pdf.before_request()

        self.assertNotIn("pdf_generator", frappe.local.form_dict)

    def test_before_request_honours_an_explicit_generator_argument(self):
        from print_designer.pdf_generator import pdf as pd_pdf

        self.set_request(
            DOWNLOAD_PDF_PATH,
            {
                "doctype": "Payment Entry",
                "format": "Receipt",
                "pdf_generator": "wkhtmltopdf",
            },
        )
        frappe.local.form_dict = frappe._dict()

        with patch.object(pd_pdf, "FrappePDFGenerator"):
            pd_pdf.before_request()

        self.assertEqual(frappe.local.form_dict.pdf_generator, "wkhtmltopdf")


class TestPrintFormatNameResolution(unittest.TestCase):
    def test_explicit_format_wins(self):
        self.assertEqual(
            signature_stamp.resolve_print_format_name("Payment Entry", "Receipt"), "Receipt"
        )

    def test_default_print_format_is_used(self):
        expected = frappe.get_meta("Payment Entry").default_print_format or "Standard"

        self.assertEqual(
            signature_stamp.resolve_print_format_name("Payment Entry", None), expected
        )


class TestWatermarkBranchUsesChrome(RequestContextMixin, unittest.TestCase):
    def test_watermark_branch_generates_the_pdf_with_chrome(self):
        """The watermark branch must not fall back to wkhtmltopdf."""
        self.set_request(DOWNLOAD_PDF_PATH, {"watermark_settings": "Test Watermark"})
        frappe.local.form_dict = frappe._dict({"watermark_settings": "Test Watermark"})
        chrome_calls = []
        wkhtml_calls = []

        def fake_get_print(**kwargs):
            return "<html><body>receipt</body></html>"

        def fake_get_chrome_pdf(print_format, html, options, output, pdf_generator=None):
            chrome_calls.append(
                {"print_format": print_format, "pdf_generator": pdf_generator, "html": html}
            )
            return b"%PDF-1.4 chrome"

        def fake_get_pdf(html, options=None, output=None):
            wkhtml_calls.append(html)
            return b"%PDF-1.4 wkhtmltopdf"

        watermark_context = {
            "watermark_settings": "Text",
            "watermark_text": "DRAFT",
            "font_size": 24,
            "font_family": "Sarabun",
            "position": "Top Right",
            "margin_top": "0mm",
            "margin_right": "0mm",
            "margin_bottom": "0mm",
            "margin_left": "0mm",
            "parsed_settings": {},
        }

        with (
            patch("frappe.utils.print_utils.get_print", side_effect=fake_get_print),
            patch("frappe.utils.pdf.get_chrome_pdf", side_effect=fake_get_chrome_pdf),
            patch("frappe.utils.pdf.get_pdf", side_effect=fake_get_pdf),
            patch.object(
                signature_stamp,
                "resolve_basic_watermark_context",
                return_value=watermark_context,
            ),
            patch.object(signature_stamp, "build_pdf_watermark_html", return_value=""),
            patch.object(
                signature_stamp,
                "inject_pdf_watermark_html",
                side_effect=lambda html, wm, text: html,
            ),
        ):
            pdf_file = signature_stamp.download_pdf_with_signature_stamp(
                doctype="Payment Entry",
                name="ACC-PAY-2606-00001",
                format="Receipt",
            )

        self.assertEqual(pdf_file, b"%PDF-1.4 chrome")
        self.assertEqual(len(chrome_calls), 1)
        self.assertEqual(chrome_calls[0]["pdf_generator"], "chrome")
        self.assertEqual(chrome_calls[0]["print_format"], "Receipt")
        self.assertEqual(wkhtml_calls, [])


if __name__ == "__main__":
    unittest.main()
