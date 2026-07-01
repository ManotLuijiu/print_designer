"""
Export and Import functionality for Print Designer formats
"""

import importlib.util
import json
import re

# pyright: reportMissingImports=false
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, cast

import frappe
from frappe import _

from print_designer.utils.convert_print_format_to_designer_export import create_designer_export_dict

# Phase 1 MVP: bridge contract version for the export bundle.
# Bump only when the bundle shape (keys/meaning) changes in a breaking way.
BRIDGE_CONTRACT_VERSION = "1.0.0"

# Reuse the production render pipeline's schema/version + footer-anchor helpers
# so the export stays in sync with what Print Designer actually prints.
_pdf_spec = importlib.util.find_spec("print_designer.pdf")
_pdf_module = __import__("print_designer.pdf", fromlist=["*"]) if _pdf_spec else None
_anchor_footer_to_bottom = getattr(_pdf_module, "_anchor_footer_to_bottom", None)
_pdf_is_older_schema = getattr(_pdf_module, "is_older_schema", None)

if callable(_pdf_is_older_schema):
    _callable_is_older_schema = cast(Callable[[Any, Any], Any], _pdf_is_older_schema)

    def is_older_schema(settings, current_version):
        return bool(_callable_is_older_schema(settings, current_version))

else:

    def is_older_schema(settings, current_version):
        format_version = (settings or {}).get("schema_version", "1.0.0")
        fv = str(format_version).split(".")
        cv = str(current_version).split(".")
        for f, c in zip(fv, cv):
            try:
                fi = int(f)
            except (TypeError, ValueError):
                fi = 0
            try:
                ci = int(c)
            except (TypeError, ValueError):
                ci = 0
            if fi < ci:
                return True
            if fi > ci:
                return False
        return False


def _safe_json_loads(value, default):
    """Parse a JSON value with a typed fallback.

    Print Designer stores its structured fields as JSON strings; if any of
    them are missing, malformed, or not strings at all, we degrade to the
    supplied default rather than crashing the export.
    """
    if not value:
        try:
            return json.loads(default)
        except (json.JSONDecodeError, TypeError):
            return {}
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        try:
            return json.loads(default)
        except (json.JSONDecodeError, TypeError):
            return {}


def safe_get_attr(obj, attr_name, default=None):
    """Safe attribute getter that handles missing attributes gracefully"""
    try:
        if hasattr(obj, attr_name):
            return getattr(obj, attr_name, default)
        else:
            return default
    except (AttributeError, TypeError):
        return default


@frappe.whitelist()
def export_print_format(print_format_name):
    """
    Export a Print Designer format as JSON for backup purposes.

    Args:
        print_format_name: Name of the print format to export

    Returns:
        JSON string containing all print designer data
    """
    if not frappe.has_permission("Print Format", "read", print_format_name):
        frappe.throw(_("You don't have permission to export this Print Format"))

    print_format = frappe.get_doc("Print Format", print_format_name)

    # Check if it's a Print Designer format
    if not print_format.print_designer:
        frappe.throw(_("This is not a Print Designer format"))

    # Prepare export data with safe attribute access for PDPrintFormat compatibility
    export_data = {
        "export_date": datetime.now().isoformat(),
        "frappe_version": frappe.__version__,
        "print_designer_version": "1.7.8",  # You can get this from app version
        "print_format": {
            "name": print_format.name,
            "doc_type": print_format.doc_type,
            "module": safe_get_attr(print_format, "module", None),
            "standard": safe_get_attr(print_format, "standard", 0),
            "custom": safe_get_attr(print_format, "custom", 0),
            "disabled": safe_get_attr(print_format, "disabled", 0),
            "print_format_type": safe_get_attr(print_format, "print_format_type", "Standard"),
            "raw_printing": safe_get_attr(print_format, "raw_printing", 0),
            "raw_commands": safe_get_attr(print_format, "raw_commands", None),
            "margin_top": safe_get_attr(print_format, "margin_top", None),
            "margin_right": safe_get_attr(print_format, "margin_right", None),
            "margin_bottom": safe_get_attr(print_format, "margin_bottom", None),
            "margin_left": safe_get_attr(print_format, "margin_left", None),
            "default_print_language": safe_get_attr(print_format, "default_print_language", None),
            "font": safe_get_attr(print_format, "font", None),
            "font_size": safe_get_attr(print_format, "font_size", None),
            "page_number": safe_get_attr(print_format, "page_number", None),
            "align_labels_right": safe_get_attr(print_format, "align_labels_right", 0),
            "show_section_headings": safe_get_attr(print_format, "show_section_headings", 0),
            "line_breaks": safe_get_attr(print_format, "line_breaks", 0),
            "absolute_value": safe_get_attr(print_format, "absolute_value", 0),
            # Print Designer specific fields
            "print_designer": safe_get_attr(print_format, "print_designer", 0),
            "print_designer_header": safe_get_attr(print_format, "print_designer_header", None),
            "print_designer_body": safe_get_attr(print_format, "print_designer_body", None),
            "print_designer_footer": safe_get_attr(print_format, "print_designer_footer", None),
            "print_designer_after_table": safe_get_attr(
                print_format, "print_designer_after_table", None
            ),
            "print_designer_settings": safe_get_attr(print_format, "print_designer_settings", None),
            "print_designer_print_format": safe_get_attr(
                print_format, "print_designer_print_format", None
            ),
            "css": safe_get_attr(print_format, "css", None),
            "custom_css": safe_get_attr(print_format, "custom_css", None),
        },
    }

    # Add metadata
    export_data["metadata"] = {
        "exported_by": frappe.session.user,
        "original_name": print_format.name,
        "description": f"Export of Print Designer format: {print_format.name}",
    }

    return export_data


@frappe.whitelist()
def import_print_format(export_data, new_name=None, overwrite=False):
    """
    Import a Print Designer format from exported JSON data.

    Args:
        export_data: JSON string or dict containing exported print format data
        new_name: Optional new name for the imported format (to avoid conflicts)
        overwrite: If True, overwrite existing format with same name

    Returns:
        Name of the imported print format
    """
    if not frappe.has_permission("Print Format", "create"):
        frappe.throw(_("You don't have permission to import Print Formats"))

    # Parse JSON if string
    if isinstance(export_data, str):
        try:
            export_data = json.loads(export_data)
        except json.JSONDecodeError as e:
            frappe.throw(_("Invalid JSON data: {0}").format(str(e)))

    if not isinstance(export_data, dict):
        frappe.throw(_("Invalid export data: expected an object"))
    export_data_dict = cast(dict[str, Any], export_data)

    # Validate export data structure
    if "print_format" not in export_data_dict:
        frappe.throw(_("Invalid export data: missing print_format"))

    format_data = export_data_dict["print_format"]
    if not isinstance(format_data, dict):
        frappe.throw(_("Invalid export data: print_format must be an object"))
    format_data = cast(dict[str, Any], format_data)

    # Determine the name for the new format
    if new_name:
        format_name = new_name
    else:
        format_name = format_data.get("name")

    # Check if format already exists
    if frappe.db.exists("Print Format", format_name):
        if not overwrite:
            # Generate a unique name
            base_name = format_name
            counter = 1
            while frappe.db.exists("Print Format", format_name):
                format_name = f"{base_name} ({counter})"
                counter += 1
            frappe.msgprint(_("Print Format renamed to {0} to avoid conflict").format(format_name))
        else:
            # Delete existing format if overwrite is True
            if not frappe.has_permission("Print Format", "delete", format_name):
                frappe.throw(_("You don't have permission to overwrite this Print Format"))
            frappe.delete_doc("Print Format", format_name, force=True)

    # Create new Print Format document
    new_format = frappe.new_doc("Print Format")

    # Copy all fields from export data with safe assignment
    fields_to_copy = [
        "doc_type",
        "module",
        "standard",
        "custom",
        "disabled",
        "print_format_type",
        "raw_printing",
        "raw_commands",
        "margin_top",
        "margin_right",
        "margin_bottom",
        "margin_left",
        "default_print_language",
        "font",
        "font_size",
        "page_number",
        "align_labels_right",
        "show_section_headings",
        "line_breaks",
        "absolute_value",
        "print_designer",
        "print_designer_header",
        "print_designer_body",
        "print_designer_footer",
        "print_designer_after_table",
        "print_designer_settings",
        "print_designer_print_format",
        "css",
        "custom_css",
    ]

    for field in fields_to_copy:
        if field in format_data and format_data[field] is not None:
            # Safe attribute setting for PDPrintFormat compatibility
            try:
                setattr(new_format, field, format_data[field])
            except AttributeError:
                # Skip fields that don't exist in PDPrintFormat class
                frappe.log_error(
                    f"Field '{field}' not available in Print Format class, skipping",
                    "Print Format Import Warning",
                )

    # Set the name
    new_format.name = format_name

    # Set standard to 0 for imported formats (unless explicitly importing a standard format)
    if not frappe.conf.developer_mode:
        new_format.standard = 0

    # Set custom to 0 for imported formats
    new_format.custom = 0

    try:
        new_format.insert()

        # Add import metadata as a comment
        if "metadata" in export_data_dict and isinstance(export_data_dict["metadata"], dict):
            metadata = cast(dict[str, Any], export_data_dict["metadata"])
            comment = f"Imported from: {metadata.get('original_name', 'Unknown')}"
            if metadata.get("exported_by"):
                comment += f" (exported by {metadata['exported_by']})"
            export_date = export_data_dict.get("export_date")
            if export_date:
                comment += f" on {export_date}"

            frappe.get_doc(
                {
                    "doctype": "Comment",
                    "comment_type": "Info",
                    "reference_doctype": "Print Format",
                    "reference_name": new_format.name,
                    "content": comment,
                }
            ).insert(ignore_permissions=True)

        frappe.msgprint(
            _("Print Format {0} imported successfully").format(format_name), indicator="green"
        )
        return new_format.name

    except Exception as e:
        frappe.log_error(f"Error importing Print Format: {str(e)}", "Print Format Import Error")
        frappe.throw(_("Error importing Print Format: {0}").format(str(e)))


@frappe.whitelist()
def duplicate_print_format(source_name, new_name):
    """
    Duplicate a Print Designer format with a new name.

    Args:
        source_name: Name of the print format to duplicate
        new_name: Name for the duplicated format

    Returns:
        Name of the duplicated print format
    """
    if not frappe.has_permission("Print Format", "create"):
        frappe.throw(_("You don't have permission to duplicate Print Formats"))

    if not frappe.has_permission("Print Format", "read", source_name):
        frappe.throw(_("You don't have permission to read the source Print Format"))

    # Export the source format
    export_data = export_print_format(source_name)

    # Import with new name
    return import_print_format(export_data, new_name=new_name, overwrite=False)


@frappe.whitelist()
def validate_import_data(export_data):
    """
    Validate export data before import to provide early feedback.

    Args:
        export_data: JSON string or dict to validate

    Returns:
        Dict with validation results
    """
    try:
        # Parse JSON if string
        if isinstance(export_data, str):
            export_data = json.loads(export_data)

        # Check required fields
        if "print_format" not in export_data:
            return {"valid": False, "message": _("Missing print_format in export data")}

        format_data = export_data["print_format"]

        # Check essential fields
        required_fields = ["doc_type", "print_designer"]
        missing_fields = [f for f in required_fields if f not in format_data]

        if missing_fields:
            return {
                "valid": False,
                "message": _("Missing required fields: {0}").format(", ".join(missing_fields)),
            }

        # Check if doctype exists
        if not frappe.db.exists("DocType", format_data["doc_type"]):
            return {
                "valid": False,
                "message": _("DocType {0} does not exist in this system").format(
                    format_data["doc_type"]
                ),
            }

        # Check if it's a Print Designer format
        if not format_data.get("print_designer"):
            return {"valid": False, "message": _("This is not a Print Designer format")}

        # All validations passed
        return {
            "valid": True,
            "message": _("Export data is valid"),
            "format_name": format_data.get("name"),
            "doc_type": format_data.get("doc_type"),
            "export_date": export_data.get("export_date"),
            "exported_by": export_data.get("metadata", {}).get("exported_by"),
        }

    except json.JSONDecodeError as e:
        return {"valid": False, "message": _("Invalid JSON: {0}").format(str(e))}
    except Exception as e:
        return {"valid": False, "message": _("Validation error: {0}").format(str(e))}


@frappe.whitelist()
def convert_to_designer_export_format(print_format_name):
    """
    Convert a standard Print Format DocType JSON to Print Designer export format.
    This is useful for converting Print Formats downloaded from internet or exported
    as raw DocType JSON into the proper Print Designer import structure.

    Uses the shared conversion utility from:
    print_designer.utils.convert_print_format_to_designer_export.create_designer_export_dict()

    Args:
        print_format_name: Name of the print format to convert

    Returns:
        JSON dict with Print Designer export structure
    """
    if not frappe.has_permission("Print Format", "read", print_format_name):
        frappe.throw(_("You don't have permission to access this Print Format"))

    # Get the Print Format document
    print_format = frappe.get_doc("Print Format", print_format_name)

    # Convert to dictionary (same as DocType JSON export)
    format_dict = print_format.as_dict()

    # Remove system fields that shouldn't be in export
    system_fields = [
        "modified",
        "modified_by",
        "creation",
        "owner",
        "docstatus",
        "idx",
        "_liked_by",
        "_comments",
        "_assign",
        "_user_tags",
    ]
    for field in system_fields:
        format_dict.pop(field, None)

    # Use shared conversion function
    designer_export = create_designer_export_dict(
        print_format_dict=format_dict,
        exported_by=frappe.session.user,
        frappe_version=frappe.__version__,
    )

    return designer_export


@frappe.whitelist()
def convert_file_to_designer_export(source_file, target_file):
    """
    Convert a Print Format file to Designer Export format.
    This reads a Print Format DocType JSON file from disk, converts it to
    Print Designer export format, and saves it to a target file.

    Args:
        source_file: Absolute path to source .txt or .json file containing Print Format DocType JSON
        target_file: Absolute path where converted JSON will be saved

    Returns:
        Dict with success status and file details
    """
    import os

    # Validate source file exists
    if not os.path.exists(source_file):
        frappe.throw(_("Source file not found: {0}").format(source_file))

    # Validate source file extension
    if not source_file.lower().endswith((".txt", ".json")):
        frappe.throw(_("Source file must be .txt or .json file"))

    try:
        # Read the Print Format DocType JSON from source file
        with open(source_file, "r", encoding="utf-8") as f:
            print_format_dict = json.load(f)

        # Validate it's a Print Format
        if "doctype" not in print_format_dict or print_format_dict.get("doctype") != "Print Format":
            frappe.throw(_("Source file does not contain a valid Print Format DocType JSON"))

        # Extract format details for response
        name = print_format_dict.get("name", "Imported Print Format")
        doc_type = print_format_dict.get("doc_type", "")

        # Use shared conversion function
        designer_export = create_designer_export_dict(
            print_format_dict=print_format_dict,
            exported_by=frappe.session.user,
            frappe_version=frappe.__version__,
        )

        # Create target directory if it doesn't exist
        target_dir = os.path.dirname(target_file)
        if target_dir and not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        # Write the converted format to target file
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(designer_export, f, indent=2, ensure_ascii=False)

        return {"success": True, "name": name, "doc_type": doc_type, "output_file": target_file}

    except json.JSONDecodeError as e:
        frappe.throw(_("Invalid JSON in source file: {0}").format(str(e)))
    except IOError as e:
        frappe.throw(_("File operation error: {0}").format(str(e)))
    except Exception as e:
        frappe.log_error(f"Error converting file: {str(e)}", "Print Format File Conversion Error")
        frappe.throw(_("Error converting file: {0}").format(str(e)))


# ---------------------------------------------------------------------------
# Phase 1 MVP: Print Designer -> Jinja HTML + CSS bridge (export only)
#
# This is intentionally narrow:
#   * read-only — never mutates the source Print Format
#   * the exported `html` is a self-contained Jinja template SOURCE (not a
#     rendered snapshot) — Jinja expressions and userProvidedJinja stay as
#     source so the user can paste it into a standard Jinja Print Format
#     and have it render correctly against any doc of the right doctype
#   * for new-schema formats the supporting macros are inlined so the
#     template does not depend on Print Designer being installed at the
#     target site (Print Designer globals like convert_css / get_barcode /
#     render_user_text / convert_uom still need to be reachable — on the
#     same bench they come from print_designer hooks; on a foreign site
#     they would need to be re-defined manually)
#   * for old-schema formats macros are already inline in the main template
#     file, so only the data embedding block is prepended
#   * the exported `css` is RAW layout/wrapper CSS (style tags stripped)
#     plus the user's saved Print Format CSS — suitable for a Print Format's
#     CSS field
# ---------------------------------------------------------------------------


# Macros that need to be inlined for new-schema formats. The old schema keeps
# everything in one file so this list is unused for old schemas.
NEW_SCHEMA_MACRO_FILES = (
    "print_designer/page/print_designer/jinja/macros/render.html",
    "print_designer/page/print_designer/jinja/macros/relative_containers.html",
    "print_designer/page/print_designer/jinja/macros/render_element.html",
    "print_designer/page/print_designer/jinja/macros/statictext.html",
    "print_designer/page/print_designer/jinja/macros/dynamictext.html",
    "print_designer/page/print_designer/jinja/macros/spantag.html",
    "print_designer/page/print_designer/jinja/macros/image.html",
    "print_designer/page/print_designer/jinja/macros/barcode.html",
    "print_designer/page/print_designer/jinja/macros/rectangle.html",
    "print_designer/page/print_designer/jinja/macros/table.html",
    "print_designer/page/print_designer/jinja/macros/render_google_fonts.html",
    "print_designer/page/print_designer/jinja/macros/styles.html",
    "print_designer/page/print_designer/jinja/macros/styles_old.html",
)


@frappe.whitelist()
def export_print_format_as_jinja_bundle(print_format_name, doc_name=None):
    """
    Export a Print Designer format as a Jinja HTML + CSS bundle (source).

    Args:
        print_format_name: Name of the Print Designer Print Format to export.
        doc_name: Accepted for API stability but unused. The export is a Jinja
                  template SOURCE, not a rendered snapshot, so no specific doc
                  is needed at export time. ``doc`` is provided by the Print
                  Format rendering context when the exported template is used.

    Returns:
        Dict with keys:
            print_format_name  — echoed input
            html               — Jinja template source (macros inlined for
                                  new schema, data embedded, userProvidedJinja
                                  preserved as source). NO rendering happens.
            css                — RAW layout/wrapper CSS (no <style> tags)
                                  plus the user-saved Print Format CSS
            schema_version     — Print Designer schema version of the source
            bridge_contract_version — version of this export bundle shape
            source             — always "print_designer"

    Raises:
        frappe.ValidationError if the format is missing, not a Print Designer
        format, or empty.
    """
    if not print_format_name:
        frappe.throw(_("print_format_name is required"))

    if not frappe.has_permission("Print Format", "read", print_format_name):
        frappe.throw(_("You don't have permission to export this Print Format"))

    print_format = frappe.get_doc("Print Format", print_format_name)

    if not print_format.print_designer:
        frappe.throw(_("'{0}' is not a Print Designer format").format(print_format_name))

    if not print_format.print_designer_body:
        frappe.throw(_("Print Designer format '{0}' has no body content").format(print_format_name))

    # Parse settings JSON safely (malformed settings degrade gracefully)
    try:
        settings = json.loads(print_format.print_designer_settings or "{}")
    except (json.JSONDecodeError, TypeError):
        settings = {}

    if not isinstance(settings, dict):
        settings = {}

    schema_version = settings.get("schema_version") or "1.0.0"
    use_old_schema = is_older_schema(settings, "1.1.0")

    # Build the Jinja template SOURCE (no rendering). This is the exportable
    # artifact: macros inlined, data embedded, userProvidedJinja preserved.
    html_source = _build_exported_template_source(print_format, settings, use_old_schema)

    # Layout/wrapper CSS — raw CSS only (no <style> tags), so it is suitable
    # for a Print Format's `css` field.
    layout_css_raw = _render_layout_css_raw(settings, use_old_schema)
    saved_css = (print_format.css or "").strip()
    combined_css = layout_css_raw + ("\n\n" + saved_css if saved_css else "")

    return {
        "print_format_name": print_format.name,
        "html": html_source,
        "css": combined_css,
        "schema_version": schema_version,
        "bridge_contract_version": BRIDGE_CONTRACT_VERSION,
        "source": "print_designer",
    }


def _build_exported_template_source(print_format, settings, use_old_schema):
    """
    Build the self-contained Jinja template source for the export.

    The returned source has:
        * the Print Designer data (header/body/footer/settings/pd_format)
          embedded as a JSON blob parsed via ``frappe.parse_json`` so
          ``headerElement`` etc. are populated in the target Print Format
          context
        * for new-schema formats, the supporting macros are inlined so the
          template does not depend on Print Designer template files being
          available; old-schema formats already have macros inline in the
          main template file
        * ``userProvidedJinja`` substituted into the template placeholder
          AS-IS (not rendered), so it remains source
        * the trailing layout styles block stripped (rendered separately
          into ``css``)
    """
    if use_old_schema:
        main_template_path = "print_designer/page/print_designer/jinja/old_print_format.html"
        macros_source = ""
    else:
        main_template_path = "print_designer/page/print_designer/jinja/print_format.html"
        macros_source = _load_and_concat_macros(NEW_SCHEMA_MACRO_FILES)
        macros_source = _strip_jinja_from_imports(macros_source)

    main_template_source = _load_template_source(main_template_path)
    main_template_source = _strip_jinja_from_imports(main_template_source)
    main_template_source = _strip_trailing_styles(main_template_source, use_old_schema)

    # Preserve userProvidedJinja AS-IS — this is what makes the export a
    # reusable template rather than a one-shot render.
    user_provided_jinja = settings.get("userProvidedJinja") or ""
    main_template_source = main_template_source.replace(
        "<!-- user_generated_jinja_code -->",
        user_provided_jinja,
    )

    data_block = _build_data_embedding_block(print_format, settings, use_old_schema)

    if macros_source:
        return data_block + "\n\n" + macros_source + "\n\n" + main_template_source
    return data_block + "\n\n" + main_template_source


def _load_and_concat_macros(macro_paths):
    """Concatenate the macro source files in dependency order.

    Missing macro files are skipped rather than failing the whole export;
    the resulting template will reference an undefined macro and the user
    can see that clearly when they paste it.
    """
    parts = []
    for path in macro_paths:
        try:
            parts.append(_load_template_source(path))
        except Exception:
            continue
    return "\n".join(parts)


def _build_data_embedding_block(print_format, settings, use_old_schema):
    """
    Build the data embedding block that injects Print Designer data into
    the exported template via ``frappe.parse_json``.

    The block is plain Jinja that:
        1. parses the embedded JSON string
        2. assigns the components to the variable names the templates expect
        3. sets a few flags (pdf_generator, send_to_jinja, etc.) to match
           the production renderer defaults

    Single quotes inside the JSON are escaped so the JSON sits inside a
    Jinja single-quoted string literal without breaking out of it.
    """
    header_element = _safe_json_loads(print_format.print_designer_header, "[]")
    body_element = _safe_json_loads(print_format.print_designer_body, "[]")
    footer_element = _safe_json_loads(print_format.print_designer_footer, "[]")
    after_table_element = _safe_json_loads(print_format.print_designer_after_table, "[]")
    pd_format = _safe_json_loads(print_format.print_designer_print_format, "{}")

    # Anchor footer to wrapper bottom so the embedded data reflects what the
    # actual print would show. Same logic pdf.py uses.
    if _anchor_footer_to_bottom is not None:
        try:
            page = (settings or {}).get("page") or {}
            _anchor_footer_to_bottom(
                footer_element,
                page_height=page.get("height") or 0,
                footer_height=page.get("footerHeight") or 0,
            )
        except Exception:
            pass

    pd_data = {
        "header": header_element,
        "body": body_element,
        "footer": footer_element,
        "settings": settings,
        "pd_format": pd_format,
    }
    if use_old_schema:
        pd_data["afterTableElement"] = after_table_element

    # JSON encode and escape for a Jinja single-quoted string literal.
    # JSON already escapes backslashes/double-quotes; we additionally need
    # to escape single quotes so the Jinja string literal stays closed.
    data_json = json.dumps(pd_data, ensure_ascii=False)
    data_json_escaped = data_json.replace("\\", "\\\\").replace("'", "\\'")

    block_lines = [
        "{# ============================================================= #}",
        "{# Print Designer data — embedded JSON, parsed at render time.    #}",
        "{# DO NOT EDIT by hand. Re-export from Print Designer to refresh. #}",
        "{# ============================================================= #}",
        "{% set __pd_data = frappe.parse_json('" + data_json_escaped + "') %}",
        "{% set headerElement = __pd_data.header %}",
        "{% set bodyElement = __pd_data.body %}",
        "{% set footerElement = __pd_data.footer %}",
        "{% set settings = __pd_data.settings %}",
        "{% set pd_format = __pd_data.pd_format %}",
        "{% set send_to_jinja = true %}",
        "{% set pdf_generator = 'chrome' %}",
        "{% set effective_lang = frappe.local.lang or 'en' %}",
        "{% set is_thai = false %}",
    ]
    if use_old_schema:
        block_lines.append("{% set afterTableElement = __pd_data.afterTableElement %}")

    return "\n".join(block_lines)


def _load_template_source(template_path):
    """
    Load a Jinja template source by Print Designer path (e.g.
    ``print_designer/page/print_designer/jinja/print_format.html``).

    Tries Frappe's template loader first, then falls back to reading the
    file directly from the app path. The fallback joins
    ``frappe.get_app_path("print_designer")`` (= the python package root)
    with the template path itself — the python package root already ends
    with ``/print_designer``, so we DO NOT prepend another segment.
    """
    try:
        return frappe.get_template(template_path).source
    except Exception:
        pass

    abs_path = Path(frappe.get_app_path("print_designer")) / template_path
    if abs_path.exists():
        return abs_path.read_text(encoding="utf-8")

    frappe.throw(_("Template not found: {0}").format(template_path))


def _strip_jinja_from_imports(source):
    """
    Remove ``{% from '...' import ... %}`` statements from a template body.

    Used to flatten macro files into a single self-contained template — once
    all macros are inlined in one file, the cross-file imports are redundant.
    """
    return re.sub(
        r"\{%-?\s*from\s+['\"][^'\"]+['\"]\s+import\s+[^%]+?%\}",
        "",
        source,
    )


def _strip_trailing_styles(template_source, use_old_schema):
    """
    Remove the trailing styles block from the template source so we can
    render the layout CSS separately and return it as the ``css`` field.

    * old schema: single inline ``<style>...</style>`` block at the end
    * new schema: ``{%- if pdf_generator == "chrome" -%} ... {%- endif -%}``
      that calls ``render_styles(settings)`` or ``render_old_styles(settings)``
    """
    if use_old_schema:
        return re.sub(
            r"<style[^>]*>.*?</style>\s*$",
            "",
            template_source,
            flags=re.DOTALL,
        )

    return re.sub(
        r'\{%-?\s*if\s+pdf_generator\s*==\s*"chrome"\s*-?%\}.*?\{%-?\s*endif\s*-?%\}\s*$',
        "",
        template_source,
        flags=re.DOTALL,
    )


def _strip_style_tags(css_with_tags):
    """Strip ``<style>`` and ``</style>`` tags from rendered CSS so the
    return value is raw CSS suitable for a Print Format's ``css`` field."""
    if not css_with_tags:
        return ""
    cleaned = re.sub(r"<style[^>]*>", "", css_with_tags, flags=re.IGNORECASE)
    cleaned = re.sub(r"</style[^>]*>", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _render_layout_css_raw(settings, use_old_schema):
    """
    Render the layout/wrapper CSS macro against ``settings`` and strip the
    surrounding ``<style>`` tags so the result is raw CSS.

    Uses the new styles macro for non-old-schema formats (matches the
    ``pdf_generator = "chrome"`` path in the html template), and the old
    styles macro for legacy formats.
    """
    if use_old_schema:
        css_template = (
            "{% from 'print_designer/page/print_designer/jinja/macros/styles_old.html' "
            "import render_old_styles %}{{ render_old_styles(settings) }}"
        )
    else:
        css_template = (
            "{% from 'print_designer/page/print_designer/jinja/macros/styles.html' "
            "import render_styles %}{{ render_styles(settings) }}"
        )
    try:
        rendered = frappe.render_template(css_template, {"settings": settings})
    except Exception as e:
        frappe.log_error(
            title="Print Designer export CSS render failed",
            message=f"Error: {e}",
        )
        return ""
    return _strip_style_tags(rendered)


# ---------------------------------------------------------------------------
# Phase 1 MVP: Print Designer Import (template-first, validation before save)
#
# Three endpoints:
#   - download_print_designer_import_template
#       Returns a ready-to-use template string with required markers. No DB
#       writes; safe to call from anywhere.
#   - validate_print_designer_import_bundle
#       Parses the bundle, returns blockers + warnings + sections. No DB
#       writes; pure preview.
#   - import_print_designer_from_jinja_bundle
#       Re-validates, then writes back only the supported subset of fields
#       (print_designer_header / body / footer / print_designer_print_format /
#       settings / css). Refuses on blockers.
# ---------------------------------------------------------------------------

# Maximum bundle size we accept to prevent abuse (10 MB).
_IMPORT_MAX_BUNDLE_CHARS = 10 * 1024 * 1024

# Reusable template for download (kept as a function so we can read it
# from disk if someone wants to customise it later).
_IMPORT_TEMPLATE_DEFAULT = (
    "<!--\n"
    "Print Designer Import Bridge Template\n"
    "\n"
    "Fill the marker sections below. Do not remove the markers.\n"
    "Header / Content / Footer must be valid HTML supported by the\n"
    "MVP subset. CSS is stored separately on the Print Format.\n"
    "-->\n"
    "\n"
    "<!-- PD:METADATA:START -->\n"
    "{\n"
    '  "source": "print_designer_import_bridge_template",\n'
    '  "version": "1.0.0",\n'
    '  "notes": "Fill the sections below. Do not remove markers."\n'
    "}\n"
    "<!-- PD:METADATA:END -->\n"
    "\n"
    "<!-- PD:HEADER:START -->\n"
    "<!-- Paste HEADER HTML here. Use inline styles for layout. -->\n"
    "<!-- PD:HEADER:END -->\n"
    "\n"
    "<!-- PD:CONTENT:START -->\n"
    "<!-- Paste BODY/CONTENT HTML here. Use inline styles for layout. -->\n"
    "<!-- PD:CONTENT:END -->\n"
    "\n"
    "<!-- PD:FOOTER:START -->\n"
    "<!-- Paste FOOTER HTML here. Use inline styles for layout. -->\n"
    "<!-- PD:FOOTER:END -->\n"
    "\n"
    "<!-- PD:CSS:START -->\n"
    "/* Paste CSS here. This is stored verbatim in Print Format.css. */\n"
    "<!-- PD:CSS:END -->\n"
)


@frappe.whitelist()
def download_print_designer_import_template(print_format_name=None):
    """Return the import bridge template string.

    Optional: when ``print_format_name`` is provided, the template is
    lightly personalised with the format name in the metadata block. No
    DB writes; read-only.
    """
    template = _IMPORT_TEMPLATE_DEFAULT
    if print_format_name:
        # Inject the source format name into the metadata block
        meta = (
            "{\n"
            f'  "source": "print_designer_import_bridge_template",\n'
            f'  "version": "1.0.0",\n'
            f'  "source_format": {json.dumps(print_format_name)},\n'
            '  "notes": "Fill the sections below. Do not remove markers."\n'
            "}\n"
        )
        template = template.replace(
            '{\n  "source": "print_designer_import_bridge_template",\n  "version": "1.0.0",\n  "notes": "Fill the sections below. Do not remove markers."\n}\n',
            meta,
        )
    return template


@frappe.whitelist()
def validate_print_designer_import_bundle(bundle_text, print_format_name=None):
    """Parse a bundle text and return a validation report.

    No DB writes. Safe to call repeatedly.

    Returns:
        dict with keys: valid, blockers, warnings, sections,
        supported_subset, unsupported_detected.
    """
    if not bundle_text or not isinstance(bundle_text, str):
        frappe.throw(_("Bundle text is required"))
    if len(bundle_text) > _IMPORT_MAX_BUNDLE_CHARS:
        frappe.throw(_("Bundle too large (max {0} chars)").format(_IMPORT_MAX_BUNDLE_CHARS))

    # Local import keeps the helper isolated from circular import risk at
    # module load time (the helper does not import this file).
    from print_designer.utils.import_jinja_bridge import build_validation_report

    return build_validation_report(bundle_text)


@frappe.whitelist()
def import_print_designer_from_jinja_bundle(print_format_name, bundle_text, overwrite=None):
    """Validate then write back supported Print Designer fields.

    Refuses import if validation reports blockers. Only writes the
    supported subset: print_designer_header, print_designer_body,
    print_designer_footer, print_designer_print_format, print_designer_settings,
    css. Keeps ``print_designer = 1`` and does not touch unrelated fields.

    ``overwrite`` is ignored in the MVP and is accepted only for backward
    compatibility with older dialog code.
    """
    if not print_format_name:
        frappe.throw(_("print_format_name is required"))
    if not frappe.has_permission("Print Format", "write", print_format_name):
        frappe.throw(_("You don't have permission to import to this Print Format"))
    if not bundle_text or not isinstance(bundle_text, str):
        frappe.throw(_("Bundle text is required"))
    if len(bundle_text) > _IMPORT_MAX_BUNDLE_CHARS:
        frappe.throw(_("Bundle too large (max {0} chars)").format(_IMPORT_MAX_BUNDLE_CHARS))

    # Re-validate strictly before any write
    from print_designer.utils.import_jinja_bridge import (
        build_validation_report,
        reconstruct_from_bundle,
    )

    report = build_validation_report(bundle_text)
    if not report["valid"]:
        frappe.throw(_("Import blocked by validation: {0}").format(", ".join(report["blockers"])))

    print_format = frappe.get_doc("Print Format", print_format_name)
    # Read existing settings for merge
    try:
        existing_settings = json.loads(print_format.print_designer_settings or "{}")
    except (json.JSONDecodeError, TypeError):
        existing_settings = {}

    reconstruction = reconstruct_from_bundle(bundle_text, existing_settings=existing_settings)
    if not reconstruction["valid"]:
        # Should not happen since build_validation_report already passed
        frappe.throw(_("Reconstruction failed after validation"))

    fields = reconstruction["reconstruction"]
    print_format.print_designer_header = fields["print_designer_header"]
    print_format.print_designer_body = fields["print_designer_body"]
    print_format.print_designer_footer = fields["print_designer_footer"]
    print_format.print_designer_print_format = fields["print_designer_print_format"]
    print_format.print_designer_settings = fields["print_designer_settings"]
    print_format.css = fields["css"]
    print_format.print_designer = 1
    print_format.save()

    return {
        "print_format_name": print_format.name,
        "warnings": reconstruction["warnings"],
        "sections": report["sections"],
    }


# ---------------------------------------------------------------------------
# Phase 1 MVP (Slice A): PTG-driven import into the current Print Format
#
# Workflow: user opens print-designer/{form_name}, clicks "Import PTG" under
# the Import dropdown, picks a PTG Template record, the print_designer side
# calls into PTG's existing `code_generation.generate_template` over the
# public API to get {html, css}, and writes those onto the CURRENT Print
# Format (not a new one). Field binding UI is Slice B.
#
# Requires the print_template_generator app to be installed.
# ---------------------------------------------------------------------------

_PTG_REQUIRED_APP = "print_template_generator"


@frappe.whitelist()
def get_ptg_template_options(doctype=None, txt="", searchfield=None, page=1, start=0, page_len=20):
    """Return PTG Template names for the link field in the import dialog.

    Standard Frappe link-field autocomplete signature. Filters by name match
    and only returns templates that have a non-empty layout_json (i.e. have
    been generated at least once).
    """
    if "print_template_generator" not in frappe.get_installed_apps():
        frappe.throw(_("Print Template Generator app is not installed. PTG import is unavailable."))

    filters = [["layout_json", "is", "set"]]
    if txt:
        filters.append([searchfield or "name", "like", f"%{txt}%"])

    return frappe.get_all(
        "PTG Template",
        filters=filters,
        fields=["name", "target_doctype", "ai_conversion_status"],
        order_by="modified desc",
        limit_start=start,
        limit_page_length=page_len,
        as_list=1,
    )


@frappe.whitelist()
def get_ptg_preview_html(ptg_template):
    """Return a static preview HTML for the dialog iframe.

    Calls into PTG's existing code_generation.get_preview_html so the
    preview matches what PTG itself shows in its editor.
    """
    if "print_template_generator" not in frappe.get_installed_apps():
        frappe.throw(_("Print Template Generator app is not installed. PTG import is unavailable."))
    if not ptg_template:
        frappe.throw(_("ptg_template is required"))

    return frappe.call(
        "print_template_generator.print_template_generator.api.code_generation.get_preview_html",
        template_name=ptg_template,
    )


@frappe.whitelist()
def import_from_ptg_template(print_format_name, ptg_template):
    """Pull the generated html/css from a PTG Template into the current Print Format.

    Calls PTG's `code_generation.generate_template` to assemble html+css from
    the PTG layout_json, then writes ONLY `html` and `css` onto the existing
    Print Format. Does NOT create a new Print Format. Does NOT touch
    `doc_type`, `print_format_type`, `print_designer` flag, or any unrelated
    field on the Print Format.
    """
    if "print_template_generator" not in frappe.get_installed_apps():
        frappe.throw(_("Print Template Generator app is not installed. PTG import is unavailable."))
    if not print_format_name or not ptg_template:
        frappe.throw(_("print_format_name and ptg_template are required"))
    if not frappe.has_permission("Print Format", "write", print_format_name):
        frappe.throw(_("You don't have permission to import to this Print Format"))

    # 1) Pull fresh html + css from PTG
    generated = frappe.call(
        "print_template_generator.print_template_generator.api.code_generation.generate_template",
        template_name=ptg_template,
    )
    html = generated.get("html") or ""
    css = generated.get("css") or ""

    if not html.strip():
        frappe.throw(
            _("PTG Template '{0}' produced empty html. Re-generate it in PTG first.").format(
                ptg_template
            )
        )

    # 2) Write ONLY html + css to the current Print Format
    print_format = frappe.get_doc("Print Format", print_format_name)
    print_format.html = html
    print_format.css = css
    print_format.save()

    return {
        "print_format_name": print_format.name,
        "ptg_template": ptg_template,
        "html_length": len(html),
        "css_length": len(css),
        "status": "imported",
    }
