import click
import frappe
from frappe.commands import pass_context

from print_designer.commands.emergency_fix_watermark import emergency_fix_watermark
from print_designer.commands.install_print_format_fields import (
    check_print_format_fields,
    install_print_format_fields,
    uninstall_print_format_fields,
)
from print_designer.commands.install_print_settings_fields import (
    check_print_settings_fields,
    install_print_settings_fields,
    uninstall_print_settings_fields,
)
from print_designer.commands.restructure_retention_fields import restructure_retention_fields


@click.command("setup-chrome", help="setup chrome (server-side) for pdf generation")
def setup_chorme():
    from print_designer.install import setup_chromium

    setup_chromium()


@click.command("add-weasyprint-option", help="add WeasyPrint to PDF Generator dropdown")
def add_weasyprint_option_cmd():
    from print_designer.install import add_weasyprint_pdf_generator_option

    add_weasyprint_pdf_generator_option()


# Print Format fields CLI commands
@click.command("install-print-format-fields")
@pass_context
def install_print_format_fields_cmd(ctx):
    site = ctx.sites[0] if ctx and ctx.sites else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        install_print_format_fields()
        frappe.destroy()


@click.command("uninstall-print-format-fields")
@pass_context
def uninstall_print_format_fields_cmd(ctx):
    site = ctx.sites[0] if ctx and ctx.sites else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        uninstall_print_format_fields()
        frappe.destroy()


@click.command("check-print-format-fields")
@pass_context
def check_print_format_fields_cmd(ctx):
    site = ctx.sites[0] if ctx and ctx.sites else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        check_print_format_fields()
        frappe.destroy()


# Print Settings fields CLI commands
@click.command("install-print-settings-fields")
@pass_context
def install_print_settings_fields_cmd(ctx):
    site = ctx.sites[0] if ctx and ctx.sites else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        install_print_settings_fields()
        frappe.destroy()


@click.command("uninstall-print-settings-fields")
@pass_context
def uninstall_print_settings_fields_cmd(ctx):
    site = ctx.sites[0] if ctx and ctx.sites else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        uninstall_print_settings_fields()
        frappe.destroy()


@click.command("check-print-settings-fields")
@pass_context
def check_print_settings_fields_cmd(ctx):
    site = ctx.sites[0] if ctx and ctx.sites else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        check_print_settings_fields()
        frappe.destroy()


commands = [
    setup_chorme,
    add_weasyprint_option_cmd,
    emergency_fix_watermark,
    restructure_retention_fields,
    install_print_format_fields_cmd,
    uninstall_print_format_fields_cmd,
    check_print_format_fields_cmd,
    install_print_settings_fields_cmd,
    uninstall_print_settings_fields_cmd,
    check_print_settings_fields_cmd,
]
