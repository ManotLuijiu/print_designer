import frappe
from frappe.utils.data import cint

from print_designer.pdf import measure_time
from print_designer.pdf_generator.browser import Browser
from print_designer.pdf_generator.generator import FrappePDFGenerator
from print_designer.pdf_generator.pdf_merge import PDFTransformer


def before_request():
	if frappe.request.path == "/api/method/frappe.utils.print_format.download_pdf":
		print_format_name = frappe.request.args.get("format")
		original_pdf_generator = (
			frappe.request.args.get("pdf_generator") or 
			frappe.get_cached_value("Print Format", print_format_name, "pdf_generator") or 
			"wkhtmltopdf"
		)
		
		# Store original generator for later use
		frappe.local.original_pdf_generator = original_pdf_generator
		
		# Check if this is a Print Designer format
		if print_format_name:
			try:
				is_print_designer = frappe.get_cached_value("Print Format", print_format_name, "print_designer")
				if is_print_designer:
					# For Print Designer formats, determine best generator
					pdf_generator = determine_best_pdf_generator(original_pdf_generator)
					frappe.local.form_dict.pdf_generator = pdf_generator
				else:
					# For non-Print Designer formats, use original generator
					frappe.local.form_dict.pdf_generator = original_pdf_generator
			except:
				# Fallback to wkhtmltopdf if any error
				frappe.local.form_dict.pdf_generator = "wkhtmltopdf"


def determine_best_pdf_generator(requested_generator):
	"""Determine the best PDF generator based on request and availability"""
	
	# If specific generator requested, try to honor it
	if requested_generator:
		if requested_generator.lower() == "chrome":
			return "chrome"
		elif requested_generator.lower() == "weasyprint":
			# Check if WeasyPrint is available
			try:
				import weasyprint
				return "WeasyPrint"
			except ImportError:
				pass
		elif requested_generator.lower() in ["wkhtmltopdf", "wkhtmltopdf"]:
			return "wkhtmltopdf"
	
	# Auto-select best available generator
	# Priority: WeasyPrint > wkhtmltopdf > Chrome
	try:
		import weasyprint
		return "WeasyPrint"
	except ImportError:
		pass
	
	# Fallback to wkhtmltopdf (most reliable)
	return "wkhtmltopdf"


def after_request():
	if (
		frappe.request.path == "/api/method/frappe.utils.print_format.download_pdf"
		and FrappePDFGenerator._instance
	):
		# Not Heavy operation as if proccess is not available it returns
		if not FrappePDFGenerator().USE_PERSISTENT_CHROMIUM:
			FrappePDFGenerator()._close_browser()


@measure_time
def get_pdf(print_format, html, options, output, pdf_generator=None):
	# Use PDF Generator Manager to handle all generators
	from print_designer.pdf_generator_manager import PDFGeneratorManager
	
	# Get the requested generator
	requested_generator = pdf_generator or frappe.form_dict.get("pdf_generator", "wkhtmltopdf")
	
	# Only handle Chrome generation here, let others fall through to Frappe
	if requested_generator.lower() != "chrome":
		return None
	
	# Use manager for Chrome PDF generation
	return PDFGeneratorManager.generate_pdf(print_format, html, options, output)
