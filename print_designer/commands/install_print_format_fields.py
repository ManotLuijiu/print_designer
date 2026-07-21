"""
Print Format Custom Fields for Print Designer
=============================================
Handles installation, verification, and removal of Print Format doctype
custom fields:
- Watermark per Page (per-format override of Print Settings watermark)

Used by:
- after_install hook
- after_migrate hook (idempotent — safe to run multiple times)
- before_uninstall hook (cleanup)

CLI commands:
- bench --site <site> install-print-format-fields
- bench --site <site> uninstall-print-format-fields
- bench --site <site> check-print-format-fields
"""

import click
import frappe
from frappe.commands import get_site, pass_context


def get_print_format_field_definitions():
    """Return the complete field definitions for Print Format doctype.

    Moved here from custom_fields.py (lines 112-121) to consolidate all
    Print Format field management in one place.
    """
    from frappe import _

    return [
        {
            "depends_on": "eval:doc.print_designer",
            "fieldname": "watermark_settings",
            "fieldtype": "Select",
            "label": _("Watermark per Page"),
            "options": "None\nOriginal on First Page\nCopy on All Pages\nOriginal,Copy on Sequence",
            "default": "None",
            "insert_after": "print_designer_template_app",
            "description": _(
                "Control watermark display: "
                "None=no watermarks, "
                "Original on First Page=first page shows 'Original', "
                "Copy on All Pages=all pages show 'Copy', "
                "Original,Copy on Sequence=pages alternate between 'Original' and 'Copy'"
            ),
        },
    ]


def install_print_format_fields():
    """Install Print Format custom fields and Property Setters (callable from hooks).

    Idempotent: safe to run multiple times.
    """
    if not frappe.db.exists("DocType", "Print Format"):
        return

    try:
        from frappe.custom.doctype.custom_field.custom_field import (
            create_custom_fields,
        )

        # Install custom fields
        create_custom_fields(
            {"Print Format": get_print_format_field_definitions()},
            update=True,
        )

        # Apply Property Setters for Print Format defaults
        _apply_property_setters()

        # Cleanup any legacy field that conflicts with the new schema
        _remove_legacy_fields()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(message=str(e), title="Print Format custom field install failed")


def _apply_property_setters():
    """Apply Property Setters to set defaults for Print Format standard fields."""
    from frappe.custom.doctype.property_setter.property_setter import (
        make_property_setter,
    )

    # Always set pdf_generator default to chrome
    make_property_setter(
        doctype="Print Format",
        fieldname="pdf_generator",
        property="default",
        value="chrome",
        property_type="Data",
        for_doctype=False,
    )

    # Set default_print_language to "th" if company is in Thailand
    if _is_thailand_company():
        make_property_setter(
            doctype="Print Format",
            fieldname="default_print_language",
            property="default",
            value="th",
            property_type="Data",
            for_doctype=False,
        )


def _is_thailand_company():
    """Check if any company in the site is in Thailand."""
    return frappe.db.exists("Company", {"country": ["like", "%Thailand%"]})


def _remove_legacy_fields():
    """Remove legacy/renamed Print Format fields so they can be recreated cleanly."""
    legacy = [
        "watermark_margin",  # old Int field, now replaced by Select watermark_settings
    ]
    for fieldname in legacy:
        existing = frappe.db.get_value(
            "Custom Field",
            {"dt": "Print Format", "fieldname": fieldname},
            "name",
        )
        if existing:
            frappe.delete_doc("Custom Field", existing, ignore_permissions=True)


def uninstall_print_format_fields():
    """Uninstall all Print Format custom fields created by print_designer."""
    if not frappe.db.exists("DocType", "Print Format"):
        return

    try:
        for field in get_print_format_field_definitions():
            existing = frappe.db.get_value(
                "Custom Field",
                {"dt": "Print Format", "fieldname": field["fieldname"]},
                "name",
            )
            if existing:
                frappe.delete_doc("Custom Field", existing, ignore_permissions=True)
        # Also remove legacy fields
        _remove_legacy_fields()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(message=str(e), title="Print Format custom field uninstall failed")


def check_print_format_fields():
    """Check status of Print Format custom fields. Returns dict for API/UI use."""
    result = {"installed": [], "missing": []}
    for field in get_print_format_field_definitions():
        fieldname = field["fieldname"]
        existing = frappe.db.get_value(
            "Custom Field",
            {"dt": "Print Format", "fieldname": fieldname},
            "name",
        )
        if existing:
            result["installed"].append(f"Print Format.{fieldname}")
        else:
            result["missing"].append(f"Print Format.{fieldname}")
    result["all_installed"] = bool(len(result["missing"]) == 0)
    return result


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------


@click.command("install-print-format-fields")
@click.option("--site", help="Site name")
@pass_context
def install_print_format_fields_cmd(context, site=None):
    """Install Print Format custom fields for Print Designer."""
    if not site:
        site = get_site(context)

    with frappe.init_site(site):
        frappe.connect()

        installed_apps = frappe.get_installed_apps()
        if "print_designer" not in installed_apps:
            click.echo(f"❌ Error: print_designer app is not installed on site '{site}'")
            return

        try:
            install_print_format_fields()
            status = check_print_format_fields()
            click.echo(
                f"✅ Print Format fields installed! "
                f"Installed: {len(status['installed'])}, "
                f"Missing: {len(status['missing'])}"
            )
        except Exception as e:
            click.echo(f"❌ Error installing Print Format fields: {str(e)}")
            frappe.db.rollback()


@click.command("uninstall-print-format-fields")
@click.option("--site", help="Site name")
@pass_context
def uninstall_print_format_fields_cmd(context, site=None):
    """Uninstall Print Format custom fields for Print Designer."""
    if not site:
        site = get_site(context)

    with frappe.init_site(site):
        frappe.connect()

        try:
            uninstall_print_format_fields()
            click.echo("✅ Print Format fields uninstalled!")
        except Exception as e:
            click.echo(f"❌ Error uninstalling Print Format fields: {str(e)}")
            frappe.db.rollback()


@click.command("check-print-format-fields")
@click.option("--site", help="Site name")
@pass_context
def check_print_format_fields_cmd(context, site=None):
    """Check status of Print Format custom fields."""
    if not site:
        site = get_site(context)

    with frappe.init_site(site):
        frappe.connect()

        status = check_print_format_fields()
        click.echo(f"Installed: {status['installed']}")
        click.echo(f"Missing: {status['missing']}")
        click.echo(f"All installed: {status['all_installed']}")


commands = [
    install_print_format_fields_cmd,
    uninstall_print_format_fields_cmd,
    check_print_format_fields_cmd,
]
