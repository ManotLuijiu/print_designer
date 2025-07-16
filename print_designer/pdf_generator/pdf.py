from print_designer.pdf import measure_time
from print_designer.pdf_generator_manager import PDFGeneratorManager


@measure_time
def get_pdf(print_format, html, options, output, **kwargs):
	"""
	Generate a PDF using the appropriate generator.
	This function is called by Frappe's PDF generation workflow and delegates
	to the PDFGeneratorManager.
	"""
	return PDFGeneratorManager.generate_pdf(print_format, html, options, output)
