"""Export a saved Print Designer format as an installer-ready default template.

A *default template* is a ``Print Format`` document that ships inside the
Print Designer app and that the missing-only installer
(:mod:`print_designer.default_templates_installer`) imports on a fresh site.

This module builds such a document from a saved Print Designer format.  The
result is a copy of the saved layout with everything that belongs to the
source site removed:

* the sample document selection (``print_designer_settings.currentDoc``),
* the source thumbnail (``print_designer_preview_img``),
* private ``File`` references of static images, and
* site-specific branding, which is replaced by the dynamic
  ``Company -> Company Logo`` binding.

The export never mutates the saved format and never writes to the app
folder.  The caller receives the document and is responsible for reviewing
and shipping the file.
"""

from __future__ import annotations

import json
import re
from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr

from print_designer.custom.print_format_profile import validate_profile

# The dynamic binding that replaces a site-specific branding image.  It
# mirrors the binding used by the bundled ``services_quotation`` template.
COMPANY_LOGO_BINDING = {
    "name": "",
    "doctype": "Company",
    "fieldname": "company_logo",
    "fieldtype": "Attach Image",
    "label": "Company Logo",
    "parentField": "company",
    "value": "",
    "file_name": "",
    "file_url": "",
    "modified": "",
}

# The design blobs that may hold elements.
DESIGN_BLOBS = (
    "print_designer_body",
    "print_designer_header",
    "print_designer_footer",
    "print_designer_after_table",
    "print_designer_print_format",
)

# The fields whose column carries a json_valid check constraint.  Their
# value must be valid JSON or NULL, never an empty string.
JSON_FIELDS = DESIGN_BLOBS + ("print_designer_settings",)

# The keys of an uploaded image that point at a private site file.
PRIVATE_FILE_KEYS = ("value", "name", "file_name", "file_url", "modified")

# A file reference that belongs to the site that saved the format.
PRIVATE_FILE_PATTERN = re.compile(r"(^|/)files/")

# The fields of the exported document that are copied from the saved format.
COPIED_FIELDS = (
    "doc_type",
    "module",
    "css",
    "custom_css",
    "font",
    "font_size",
    "margin_top",
    "margin_right",
    "margin_bottom",
    "margin_left",
    "page_size",
    "default_print_language",
    "raw_printing",
    "align_labels_right",
    "show_section_headings",
    "line_breaks",
    "absolute_value",
    "page_number",
    "print_format_type",
    "pdf_generator",
    "print_designer",
    "print_designer_template_app",
    "print_designer_header",
    "print_designer_body",
    "print_designer_footer",
    "print_designer_after_table",
    "print_designer_settings",
    "print_designer_print_format",
)


def _is_private_file(value: Any) -> bool:
    """True when ``value`` points at a file of the saving site."""
    if not isinstance(value, str) or not value.strip():
        return False

    return bool(PRIVATE_FILE_PATTERN.search(value))


def _strip_private_image(image: Any) -> None:
    """Remove the private file reference of a static image binding."""
    if not isinstance(image, dict):
        return

    for key in PRIVATE_FILE_KEYS:
        if key in image:
            image[key] = ""


def _replace_branding_with_company_logo(element: dict) -> bool:
    """Replace a static branding image with the dynamic company logo.

    Returns ``True`` when the element was changed.  A static image carries
    the file of the source site, so it cannot be shipped.  The company logo
    is the portable equivalent.
    """
    if element.get("type") != "image" or element.get("isDynamic"):
        return False

    image = element.get("image")
    if not isinstance(image, dict):
        return False

    if not _is_private_file(image.get("file_url")) and not _is_private_file(image.get("value")):
        return False

    element["isDynamic"] = True
    element["image"] = dict(COMPANY_LOGO_BINDING)
    return True


def _walk_elements(node: Any, visit) -> None:
    """Call ``visit`` for every dict of a parsed design payload."""
    if isinstance(node, dict):
        visit(node)
        for value in node.values():
            _walk_elements(value, visit)
    elif isinstance(node, list):
        for item in node:
            _walk_elements(item, visit)


def _clean_blob(value: Any) -> Any:
    """Remove the private file references of one design blob.

    A blob is either a JSON payload or plain text.  The result keeps the
    shape of the source: a design blob stays a JSON string, plain text
    stays plain text.
    """
    if not value:
        return value

    if isinstance(value, str):
        try:
            payload = json.loads(value)
        except ValueError:
            return value
    else:
        payload = value

    cleaned = _clean_payload(payload)

    if isinstance(cleaned, str):
        return cleaned

    return json.dumps(cleaned)


def _as_json_field(value: Any) -> str | None:
    """Return a value that a JSON custom field can store.

    The Print Designer design fields are JSON custom fields.  Their column
    carries a ``json_valid`` check constraint, so an empty string or a
    plain text payload cannot be stored: the insert fails with a
    constraint error.  A value that is not valid JSON therefore becomes
    ``None``, which the column accepts.
    """
    if value is None:
        return None

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None

        try:
            json.loads(text)
        except ValueError:
            return None

        return text

    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return None


def _clean_payload(payload: Any) -> Any:
    """Remove the private file references of a parsed design payload."""

    # The branding is replaced first: the replacement is detected by the
    # private file reference that the replacement itself removes.
    _walk_elements(payload, _replace_branding_with_company_logo)

    def visit(node: dict) -> None:
        if node.get("type") != "image" or not isinstance(node.get("image"), dict):
            return

        image = node["image"]
        if image.get("doctype") == "Company" and image.get("fieldname") == ("company_logo"):
            # The portable binding, keep it as it is.
            return

        _strip_private_image(image)

    _walk_elements(payload, visit)

    return payload


def _clean_settings(value: Any) -> Any:
    """Remove the sample document selection from the saved settings."""
    if not value:
        return value

    try:
        settings = json.loads(value) if isinstance(value, str) else value
    except ValueError:
        return value

    if not isinstance(settings, dict):
        return value

    # The sample document is a reference to a document of the source site.
    settings["currentDoc"] = None

    return json.dumps(settings)


def build_template_document(
    print_format: dict,
    template_name: str,
    transaction_type: str | None = None,
    transaction_direction: str | None = None,
) -> dict:
    """Build the installer-ready template document of a saved format.

    :param print_format: the saved Print Format as a plain dict.
    :param template_name: the public name of the template.  It determines
            the installation collisions, so it must be stable.
    :param transaction_type: the optional transaction type of the profile.
    :param transaction_direction: the optional direction of the profile.
    :returns: a ``Print Format`` document ready to be written as JSON.
    :raises frappe.ValidationError: when the profile does not belong to
            the DocType of the format.
    """
    # The profile is validated against the DocType of the format: a Sales
    # Invoice has no direction, and a format of another DocType has no
    # profile at all.
    validate_profile(
        print_format.get("doc_type"),
        direction=transaction_direction,
        transaction_type=transaction_type,
    )

    document: dict[str, Any] = {
        "doctype": "Print Format",
        "name": template_name,
        "standard": "No",
        "disabled": 0,
        "docstatus": 0,
        # The thumbnail belongs to the source site.
        "print_designer_preview_img": "",
    }

    for fieldname in COPIED_FIELDS:
        if fieldname not in print_format:
            continue

        value = print_format.get(fieldname)
        if fieldname in DESIGN_BLOBS:
            value = _clean_blob(value)
        elif fieldname == "print_designer_settings":
            value = _clean_settings(value)

        if fieldname in JSON_FIELDS:
            # The column of a JSON custom field carries a json_valid check
            # constraint, so the value has to be valid JSON or NULL.
            value = _as_json_field(value)

        document[fieldname] = value

    # The template belongs to the app that ships the templates.
    document["print_designer_template_app"] = "print_designer"

    if transaction_type:
        document["pd_custom_transaction_type"] = transaction_type

    if transaction_direction:
        document["pd_custom_transaction_direction"] = transaction_direction

    return document


@frappe.whitelist()
def get_categories() -> list[dict]:
    """The categories a template can be filed under.

    A category is a folder of the default templates folder.  The folders of
    the shipped app are the known categories.

    The Desk action of the export calls this over HTTP, so the function
    must be whitelisted, otherwise the request is refused before it
    starts.
    """
    from print_designer.default_templates_installer import get_templates_root

    root = get_templates_root("print_designer")
    categories: list[dict] = []

    if root.exists():
        for path in sorted(root.iterdir(), key=lambda item: item.name):
            if path.is_dir() and not path.name.startswith("."):
                categories.append({"value": path.name, "label": path.name})

    return categories


@frappe.whitelist()
def export_as_default_template(
    print_format_name: str,
    template_name: str | None = None,
    category: str | None = None,
    transaction_type: str | None = None,
    transaction_direction: str | None = None,
):
    """Export a saved Print Designer format as an installer-ready template.

    :param print_format_name: the saved Print Format to export.
    :param template_name: the public name of the template.  Defaults to the
            name of the saved format.
    :param category: the destination category.  It is reported back so the
            reviewer knows where the file belongs.
    :param transaction_type: the optional transaction type of the profile.
    :param transaction_direction: the optional direction of the profile.
    :returns: the template document and the metadata of the export.
    """
    if not frappe.has_permission("Print Format", "read", print_format_name):
        frappe.throw(
            _("You don't have permission to export this Print Format"),
            frappe.PermissionError,
        )

    print_format = frappe.get_doc("Print Format", print_format_name)

    if not print_format.get("print_designer"):
        frappe.throw(_("This is not a Print Designer format"))

    name = cstr(template_name).strip() or cstr(print_format.name).strip()
    if not name:
        frappe.throw(_("The template needs a name"))

    source = print_format.as_dict()
    document = build_template_document(
        source,
        name,
        transaction_type=cstr(transaction_type).strip() or None,
        transaction_direction=cstr(transaction_direction).strip() or None,
    )

    known_categories = {item["value"] for item in get_categories()}
    destination = cstr(category).strip()
    if destination and destination not in known_categories:
        frappe.throw(_("Unknown category: {0}").format(destination))

    return {
        "template": document,
        "filename": "{0}.json".format(_slugify(name)),
        "category": destination,
        "source": print_format.name,
    }


def _slugify(value: str) -> str:
    """A file system friendly name for a template."""
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")

    return slug or "template"
