import click

from print_designer.commands.emergency_fix_watermark import emergency_fix_watermark
from print_designer.commands.restructure_retention_fields import (
    restructure_retention_fields,
)

# OBSOLETE: install_watermark_fields - moved to install_print_settings_fields.py


@click.command("setup-chrome", help="setup chrome (server-side) for pdf generation")
def setup_chorme():
    from print_designer.install import setup_chromium

    setup_chromium()


@click.command("add-weasyprint-option", help="add WeasyPrint to PDF Generator dropdown")
def add_weasyprint_option():
    from print_designer.install import add_weasyprint_pdf_generator_option

    add_weasyprint_pdf_generator_option()


commands = [
    setup_chorme,
    add_weasyprint_option,
    emergency_fix_watermark,
    restructure_retention_fields,
]
