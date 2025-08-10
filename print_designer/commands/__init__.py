import click


@click.command("setup-chrome", help="setup chrome (server-side) for pdf generation")
def setup_chorme():
	from print_designer.install import setup_chromium

	setup_chromium()


@click.command("add-weasyprint-option", help="add WeasyPrint to PDF Generator dropdown")
def add_weasyprint_option():
	from print_designer.install import add_weasyprint_pdf_generator_option
	
	add_weasyprint_pdf_generator_option()


# Import watermark fields command
from print_designer.commands.install_watermark_fields import install_watermark_fields
from print_designer.commands.emergency_fix_watermark import emergency_fix_watermark

commands = [setup_chorme, add_weasyprint_option, install_watermark_fields, emergency_fix_watermark]
