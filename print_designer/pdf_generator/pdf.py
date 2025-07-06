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
				frappe.get_cached_value("Print Format", frappe.request.args.get("format"), "pdf_generator"),
			)
			or "wkhtmltopdf"
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
		# Not Heavy operation as if proccess is not available it returns
		if not FrappePDFGenerator().USE_PERSISTENT_CHROMIUM:
			FrappePDFGenerator()._close_browser()


@measure_time
def get_pdf(print_format, html, options, output, pdf_generator=None):
	if pdf_generator != "chrome":
		# Use the default pdf generator
		return
	
	# Extract copy parameters from form_dict (URL parameters)
	copy_count = cint(frappe.form_dict.get("copy_count", 0))
	copy_labels = frappe.form_dict.get("copy_labels", "")
	copy_watermark = frappe.form_dict.get("copy_watermark", "true").lower() == "true"
	
	# Debug logging
	frappe.logger().info(f"PDF Generation Debug - copy_count: {copy_count}, copy_labels: {copy_labels}, pdf_generator: {pdf_generator}")
	frappe.logger().info(f"Form dict keys: {list(frappe.form_dict.keys())}")
	frappe.logger().info(f"Options: {options}")
	
	# Add copy parameters to options
	if not options:
		options = {}
	
	if copy_count > 1:
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
