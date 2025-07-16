"""
WeasyPrint integration for Print Designer
Provides better PDF generation than wkhtmltopdf with modern CSS support
"""

import frappe
from frappe.utils.weasyprint import get_pdf as weasyprint_get_pdf


def get_pdf_with_weasyprint(html, options=None):
	"""
	Generate PDF using WeasyPrint for Print Designer formats
	This provides better CSS support than wkhtmltopdf
	"""
	try:
		# WeasyPrint handles modern CSS better than wkhtmltopdf
		# No need for extensive CSS cleaning
		return weasyprint_get_pdf(html, options)
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
		# Check if WeasyPrint is available and enabled in Print Settings
		from weasyprint import HTML
		
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
	Minimal CSS cleaning for WeasyPrint (it supports modern CSS better)
	"""
	if not css_content:
		return css_content
	
	# WeasyPrint supports most modern CSS, minimal cleaning needed
	import re
	
	# Remove only truly problematic properties
	problematic_properties = [
		r'user-select\s*:\s*[^;]+;?',  # Not supported in print
		r'-webkit-[^:]*\s*:\s*[^;]+;?',  # Remove webkit prefixes
		r'-moz-[^:]*\s*:\s*[^;]+;?',     # Remove moz prefixes
		r'-ms-[^:]*\s*:\s*[^;]+;?',      # Remove ms prefixes
	]
	
	for prop in problematic_properties:
		css_content = re.sub(prop, '', css_content, flags=re.IGNORECASE | re.MULTILINE)
	
	return css_content.strip()