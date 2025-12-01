"""
WeasyPrint integration for Print Designer
Provides better PDF generation than wkhtmltopdf with modern CSS support

This module provides reusable utilities for all Frappe apps to generate PDFs
using WeasyPrint with proper Thai font support.

Usage:
    from print_designer.weasyprint_integration import (
        get_pdf_with_weasyprint,
        get_thai_font_css,
        render_pdf_response
    )

    # Simple PDF generation
    pdf_bytes = get_pdf_with_weasyprint(html_content)

    # With Thai fonts and page options
    pdf_bytes = get_pdf_with_weasyprint(
        html_content,
        options={'page_size': 'A4', 'orientation': 'portrait'}
    )

    # Return as downloadable response
    render_pdf_response(pdf_bytes, "my_report.pdf")
"""

import frappe
import os
from frappe.utils.weasyprint import import_weasyprint


# Thai font CSS for local THSarabunNew fonts
THAI_FONT_CSS = """
@font-face {
    font-family: 'THSarabunNew';
    src: url('/assets/print_designer/fonts/thai/THSarabunNew/THSarabunNew.ttf') format('truetype');
    font-weight: normal;
    font-style: normal;
}
@font-face {
    font-family: 'THSarabunNew';
    src: url('/assets/print_designer/fonts/thai/THSarabunNew/THSarabunNew Bold.ttf') format('truetype');
    font-weight: bold;
    font-style: normal;
}
@font-face {
    font-family: 'THSarabunNew';
    src: url('/assets/print_designer/fonts/thai/THSarabunNew/THSarabunNew Italic.ttf') format('truetype');
    font-weight: normal;
    font-style: italic;
}
@font-face {
    font-family: 'THSarabunNew';
    src: url('/assets/print_designer/fonts/thai/THSarabunNew/THSarabunNew BoldItalic.ttf') format('truetype');
    font-weight: bold;
    font-style: italic;
}
"""


def get_thai_font_css():
	"""
	Return CSS @font-face declarations for Thai fonts (THSarabunNew)

	Use this to include Thai font support in your HTML templates:
		css = get_thai_font_css()
		html = f"<style>{css}</style>" + your_html

	Returns:
		str: CSS @font-face declarations for THSarabunNew fonts
	"""
	return THAI_FONT_CSS


def get_pdf_with_weasyprint(html, options=None):
	"""
	Generate PDF using WeasyPrint for Print Designer formats
	This provides better CSS support than wkhtmltopdf

	Args:
		html (str): HTML content to convert to PDF
		options (dict, optional): PDF generation options
			- css (str): Additional CSS to apply
			- page_size (str): Page size ('A4', 'Letter', etc.) Default: 'A4'
			- orientation (str): 'portrait' or 'landscape'. Default: 'portrait'
			- include_thai_fonts (bool): Include Thai font support. Default: True
			- margin_top (str): Top margin (e.g., '15mm'). Default: '15mm'
			- margin_bottom (str): Bottom margin. Default: '15mm'
			- margin_left (str): Left margin. Default: '15mm'
			- margin_right (str): Right margin. Default: '15mm'

	Returns:
		bytes: PDF content as bytes
	"""
	try:
		# Import WeasyPrint classes using Frappe's helper
		HTML, CSS = import_weasyprint()

		# Use WeasyPrint to generate PDF directly
		base_url = frappe.utils.get_url()
		html_doc = HTML(string=html, base_url=base_url)

		# Build stylesheets list
		stylesheets = []

		# Parse options with defaults
		if options is None:
			options = {}

		page_size = options.get('page_size', 'A4')
		orientation = options.get('orientation', 'portrait')
		include_thai_fonts = options.get('include_thai_fonts', True)
		margin_top = options.get('margin_top', '15mm')
		margin_bottom = options.get('margin_bottom', '15mm')
		margin_left = options.get('margin_left', '15mm')
		margin_right = options.get('margin_right', '15mm')

		# Add Thai fonts CSS if requested
		if include_thai_fonts:
			stylesheets.append(CSS(string=THAI_FONT_CSS))

		# Build page CSS
		page_css = f"""
			@page {{
				size: {page_size} {orientation};
				margin-top: {margin_top};
				margin-bottom: {margin_bottom};
				margin-left: {margin_left};
				margin-right: {margin_right};
			}}
		"""
		stylesheets.append(CSS(string=page_css))

		# Apply additional CSS if provided in options
		if options.get('css'):
			stylesheets.append(CSS(string=options['css']))

		# Render the PDF
		pdf_doc = html_doc.render(stylesheets=stylesheets)
		return pdf_doc.write_pdf()

	except Exception as e:
		frappe.log_error(
			title="WeasyPrint PDF Generation Failed",
			message=f"Error: {str(e)}\nFalling back to wkhtmltopdf"
		)
		# Fallback to wkhtmltopdf if WeasyPrint fails
		from frappe.utils.pdf import get_pdf
		return get_pdf(html, options)


def render_pdf_response(pdf_content, filename):
	"""
	Set Frappe response to return PDF as downloadable file

	This is a convenience function to return PDF content as a downloadable
	file in a Frappe API endpoint.

	Args:
		pdf_content (bytes): PDF content as bytes
		filename (str): Filename for the downloaded file (e.g., "report.pdf")

	Example:
		@frappe.whitelist()
		def download_my_report():
			html = render_my_report()
			pdf = get_pdf_with_weasyprint(html)
			render_pdf_response(pdf, "my_report.pdf")
	"""
	frappe.local.response.filename = filename
	frappe.local.response.filecontent = pdf_content
	frappe.local.response.type = "pdf"


def render_template_to_pdf(template_path, context, filename, options=None):
	"""
	Render a Jinja template to PDF and return as downloadable response

	This is a convenience function combining template rendering and PDF generation.

	Args:
		template_path (str): Path to Jinja template (e.g., "templates/print_formats/my_report.html")
		context (dict): Context variables for template rendering
		filename (str): Filename for the downloaded file
		options (dict, optional): PDF generation options (see get_pdf_with_weasyprint)

	Example:
		@frappe.whitelist()
		def download_loan_contract(loan_name):
			loan = frappe.get_doc("M Loan Application", loan_name)
			render_template_to_pdf(
				"templates/print_formats/loan_contract.html",
				{"doc": loan, "company": frappe.get_doc("Company", loan.company)},
				f"Loan_Contract_{loan_name}.pdf"
			)

	Returns:
		str: Filename (for reference)
	"""
	# Render template using Frappe's render_template
	html = frappe.render_template(template_path, context)

	# Generate PDF with WeasyPrint
	pdf_content = get_pdf_with_weasyprint(html, options)

	# Return as downloadable response
	render_pdf_response(pdf_content, filename)

	return filename


def should_use_weasyprint():
	"""
	Check if WeasyPrint should be used instead of wkhtmltopdf

	Returns:
		bool: True if WeasyPrint is available and should be used
	"""
	try:
		# Check if WeasyPrint is available using Frappe's helper
		from frappe.utils.weasyprint import import_weasyprint
		HTML, CSS = import_weasyprint()

		# Check Print Settings for PDF generation method
		print_settings = frappe.get_single("Print Settings")

		if hasattr(print_settings, 'pdf_generation_method'):
			return print_settings.pdf_generation_method == "WeasyPrint"

		# Default to WeasyPrint if available (better CSS support)
		return True

	except ImportError:
		# WeasyPrint not available, fallback to wkhtmltopdf
		return False
	except Exception:
		# Any other error, fallback to wkhtmltopdf
		return False


def clean_css_for_weasyprint(css_content):
	"""
	Minimal CSS cleaning for WeasyPrint - following original repository approach
	WeasyPrint supports modern CSS well, so minimal cleaning needed

	Args:
		css_content (str): CSS content to clean

	Returns:
		str: Cleaned CSS content
	"""
	if not css_content:
		return css_content

	# Following original repository: minimal to no CSS cleaning
	# WeasyPrint supports most modern CSS including custom properties and flexbox
	# Only remove user-select which is not relevant for print
	import re

	css_content = re.sub(r'user-select\s*:\s*[^;]+;?', '', css_content, flags=re.IGNORECASE | re.MULTILINE)

	return css_content.strip()


# Convenience alias for backwards compatibility and shorter imports
generate_pdf = get_pdf_with_weasyprint