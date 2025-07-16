import frappe
from frappe.utils.data import cint

from print_designer.pdf import measure_time
from print_designer.pdf_generator.browser import Browser
from print_designer.pdf_generator.generator import FrappePDFGenerator
from print_designer.pdf_generator.pdf_merge import PDFTransformer


def before_request():
	if frappe.request.path == "/api/method/frappe.utils.print_format.download_pdf":
		original_pdf_generator = (
			frappe.request.args.get(
				"pdf_generator",
				frappe.get_cached_value("Print Format", frappe.request.args.get("format"), "pdf_generator"),
			)
			or "wkhtmltopdf"
		)
		
		# Use wkhtmltopdf for Print Designer formats
		frappe.local.form_dict.pdf_generator = "wkhtmltopdf"
>>>>>>> develop


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
	# Chrome PDF generation is disabled - Print Designer now uses wkhtmltopdf
	return
	
	# Extract copy parameters from form_dict (URL parameters)
	copy_count = cint(frappe.form_dict.get("copy_count", 0))
	copy_labels = frappe.form_dict.get("copy_labels", "")
	copy_watermark = frappe.form_dict.get("copy_watermark", "true").lower() == "true"
	
	
	# Get watermark settings from Print Format if available
	watermark_settings = None
	if print_format:
		try:
			pf_doc = frappe.get_cached_doc("Print Format", print_format)
			watermark_settings = pf_doc.get("watermark_settings")
		except:
			pass
	
	# Debug logging
	frappe.logger().info(f"PDF Generation Debug - copy_count: {copy_count}, copy_labels: {copy_labels}, watermark_settings: {watermark_settings}")
	
	# Add copy parameters to options
	if not options:
		options = {}
	
	# Apply watermark settings from Print Format
	if watermark_settings and watermark_settings != "None":
		if watermark_settings == "Original on First Page":
			options["watermark_mode"] = "first_page_only"
			options["watermark_labels"] = [frappe._("Original")]
			options["copy_watermark"] = True
		elif watermark_settings == "Copy on All Pages":
			options["watermark_mode"] = "all_pages"
			options["watermark_labels"] = [frappe._("Copy")]
			options["copy_watermark"] = True
		elif watermark_settings == "Original,Copy on Sequence":
			options["watermark_mode"] = "sequence"
			options["watermark_labels"] = [frappe._("Original"), frappe._("Copy")]
			options["copy_watermark"] = True
		else:
			options["copy_watermark"] = False
		
		# Watermark functionality disabled - chrome support removed
	elif copy_count > 1:
		# Legacy multiple copies behavior
		options["copy_count"] = copy_count
		# Use translated labels if no custom labels provided
		if copy_labels:
			options["copy_labels"] = copy_labels.split(",")
		else:
			# Use Frappe's translation system for default labels
			options["copy_labels"] = [
				frappe._("Original"),
				frappe._("Copy")
			]
		options["copy_watermark"] = copy_watermark
	
	# scrubbing url to expand url is not required as we have set url.
	# also, planning to remove network requests anyway 🤞
	generator = FrappePDFGenerator()
	browser = Browser(generator, print_format, html, options)
	transformer = PDFTransformer(browser)
	# transforms and merges header, footer into body pdf and returns merged pdf
	return transformer.transform_pdf(output=output)
