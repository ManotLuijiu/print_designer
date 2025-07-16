"""
PDF Generator Manager for Print Designer
Manages Chrome, WeasyPrint, and wkhtmltopdf PDF generation
"""

import frappe
from frappe.utils.data import cint
from .logger import get_logger

logger = get_logger()


class PDFGeneratorManager:
	"""Manages multiple PDF generators for Print Designer"""
	
	@staticmethod
	def get_available_generators():
		"""Get list of available PDF generators"""
		generators = ["wkhtmltopdf"]  # Always available in Frappe
		
		# Check WeasyPrint availability
		try:
			import weasyprint
			generators.append("WeasyPrint")
		except ImportError:
			pass
		
		# Chrome is available if dependencies are installed
		try:
			import websockets
			import distro
			generators.append("chrome")
		except ImportError:
			pass
		
		return generators
	
	@staticmethod
	def determine_generator(requested_generator=None):
		"""Determine the best PDF generator to use"""
		available = PDFGeneratorManager.get_available_generators()
		
		# If specific generator requested and available, use it
		if requested_generator and requested_generator != 'auto' and requested_generator in available:
			return requested_generator
		
		# Auto-select priority: WeasyPrint > wkhtmltopdf > chrome
		if "WeasyPrint" in available:
			return "WeasyPrint"
		elif "wkhtmltopdf" in available:
			return "wkhtmltopdf"
		elif "chrome" in available:
			return "chrome"
		else:
			# Fallback (should never happen)
			return "wkhtmltopdf"
	
	@staticmethod
	def generate_pdf(print_format, html, options=None, output=None):
		"""Generate PDF using the appropriate generator"""
		requested_generator = frappe.form_dict.get("pdf_generator")
		generator = PDFGeneratorManager.determine_generator(requested_generator)
		
		logger.info(
			f"PDF Generation Request: "
			f"Format='{print_format.name}', "
			f"Requested='{requested_generator}', "
			f"Used='{generator}'"
		)
		
		if generator == "chrome":
			logger.info("Using Chrome PDF Generator")
			return PDFGeneratorManager._generate_with_chrome(print_format, html, options, output)
		elif generator == "WeasyPrint":
			logger.info("Using WeasyPrint PDF Generator")
			return PDFGeneratorManager._generate_with_weasyprint(html, options)
		else:
			logger.info("Falling back to Frappe's default PDF Generator (wkhtmltopdf)")
			# Default to wkhtmltopdf (handled by Frappe core)
			return None  # Let Frappe handle it
	
	@staticmethod
	def _generate_with_chrome(print_format, html, options, output):
		"""Generate PDF using Chrome"""
		from print_designer.pdf_generator.browser import Browser
		from print_designer.pdf_generator.generator import FrappePDFGenerator
		from print_designer.pdf_generator.pdf_merge import PDFTransformer
		
		# Extract copy parameters
		copy_count = cint(frappe.form_dict.get("copy_count", 0))
		copy_labels = frappe.form_dict.get("copy_labels", "")
		copy_watermark = frappe.form_dict.get("copy_watermark", "true").lower() == "true"
		
		if not options:
			options = {}
		
		# Handle copy functionality
		if copy_count > 1:
			options["copy_count"] = copy_count
			if copy_labels:
				options["copy_labels"] = copy_labels.split(",")
			else:
				options["copy_labels"] = [frappe._("Original"), frappe._("Copy")]
			options["copy_watermark"] = copy_watermark
		
		# Generate PDF with Chrome
		generator = FrappePDFGenerator()
		browser = Browser(generator, print_format, html, options)
		transformer = PDFTransformer(browser)
		return transformer.transform_pdf(output=output)
	
	@staticmethod
	def _generate_with_weasyprint(html, options):
		"""Generate PDF using WeasyPrint"""
		try:
			from print_designer.weasyprint_integration import get_pdf_with_weasyprint
			return get_pdf_with_weasyprint(html, options)
		except Exception as e:
			logger.error(f"WeasyPrint PDF Generation Failed: {str(e)}", exc_info=True)
			frappe.log_error(
				title="WeasyPrint PDF Generation Failed",
				message=f"Error: {str(e)}\nFalling back to wkhtmltopdf"
			)
			# Return None to let Frappe handle with wkhtmltopdf
			return None
	
	@staticmethod
	def get_generator_info():
		"""Get information about available generators"""
		available = PDFGeneratorManager.get_available_generators()
		current = PDFGeneratorManager.determine_generator()
		
		return {
			"available": available,
			"current": current,
			"count": len(available)
		}
