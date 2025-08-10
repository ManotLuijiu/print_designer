"""
WeasyPrint integration for Print Designer
Provides better PDF generation than wkhtmltopdf with modern CSS support
"""

import frappe
from frappe.utils.weasyprint import import_weasyprint


def get_pdf_with_weasyprint(html, options=None):
	"""
	Generate PDF using WeasyPrint for Print Designer formats
	This provides better CSS support than wkhtmltopdf
	"""
	try:
		# Import WeasyPrint classes using Frappe's helper
		HTML, CSS = import_weasyprint()
		
		# Use WeasyPrint to generate PDF directly
		base_url = frappe.utils.get_url()
		html_doc = HTML(string=html, base_url=base_url)
		
		# Apply CSS if provided in options
		stylesheets = []
		if options and options.get('css'):
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


def should_use_weasyprint():
	"""
	Check if WeasyPrint should be used instead of wkhtmltopdf
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
	"""
	if not css_content:
		return css_content
	
	# Following original repository: minimal to no CSS cleaning
	# WeasyPrint supports most modern CSS including custom properties and flexbox
	# Only remove user-select which is not relevant for print
	import re
	
	css_content = re.sub(r'user-select\s*:\s*[^;]+;?', '', css_content, flags=re.IGNORECASE | re.MULTILINE)
	
	return css_content.strip()