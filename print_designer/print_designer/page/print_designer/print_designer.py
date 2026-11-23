import re
from typing import Any, Literal, cast

import frappe
import frappe.utils.print_format
from frappe import _
from frappe.model.document import BaseDocument
from frappe.utils.jinja import get_jenv

from print_designer.utils.number_to_words_fields import (
    _print_language,
    _resolve_currency,
    apply_number_to_words_pairs,
    convert_amount_to_words,
    get_number_to_words_pairs,
    get_primary_amount,
    normalize_language,
    resolve_print_language,
)

# The signature and the stamp helpers live in `print_designer.utils.signature_stamp`
# and are registered as Jinja methods in `hooks.py`. They are re-exported here
# so that the old paths of this module keep working.
from print_designer.utils.signature_stamp import (
    get_company_stamp_image,
    get_signature_and_stamp_context,
    get_signature_image,
)

__all__ = [
    "get_company_stamp_image",
    "get_signature_and_stamp_context",
    "get_signature_image",
]


def _query_rows(query: Any) -> list[dict[str, Any]]:
    """The rows of a query builder query.

    Frappe replaces the `run` method of the query builder with its own
    implementation when the framework starts (see
    `frappe.query_builder.utils`), so the type information of the stock
    package does not know the method.
    """
    return cast(Any, query).run(as_dict=True)


def _parse_barcode_options(options: Any) -> dict[str, Any]:
    """The options of a barcode or a qrcode as a dictionary.

    The options reach the server as a json string or as a dictionary,
    depending on the caller.
    """
    if not options:
        return {}

    if isinstance(options, str):
        parsed = frappe.parse_json(options)
        return parsed if isinstance(parsed, dict) else {}

    return options


@frappe.whitelist(allow_guest=False)
def render_user_text_withdoc(string, doctype, docname=None, row=None, send_to_jinja=None):
    if not row:
        row = {}
    if not send_to_jinja:
        send_to_jinja = {}

    if not docname or docname == "":
        return render_user_text(string=string, doc={}, row=row, send_to_jinja=send_to_jinja)
    doc = frappe.get_cached_doc(doctype, docname)
    doc.check_permission()
    return render_user_text(string=string, doc=doc, row=row, send_to_jinja=send_to_jinja)


@frappe.whitelist(allow_guest=False)
def get_number_to_words_preview(doctype, docname, print_format, language=None):
    doc = frappe.get_doc(doctype, docname)
    doc.check_permission("read")
    print_format_doc = frappe.get_doc("Print Format", print_format)
    # `getattr` and not `doc.doc_type`: the attribute of a real Document, but
    # the doubles that the tests use carry the value in the namespace only.
    if getattr(print_format_doc, "doc_type", None) != doctype:
        frappe.throw(_("Print Format does not belong to this document type"))

    effective_language = resolve_print_language(
        print_format_doc,
        explicit_language=language,
        document_language=doc.get("language"),
        # `getattr` and not `frappe.local.lang`: the language of the local is
        # absent when the request runs outside a session (a background job, a
        # command, a test), and the preview still has to answer.
        user_language=getattr(frappe.local, "lang", None),
    )
    meta = frappe.get_meta(doctype)
    pairs = get_number_to_words_pairs(print_format_doc)
    values = apply_number_to_words_pairs(doc, meta, pairs, effective_language)

    # Mirror the print pipeline: the legacy `in_words` field describes the
    # same amount as the configured pairs (the configured source field wins),
    # so the Design View shows the same text as the generated PDF.  For a
    # non-Thai print language the stored value is kept, exactly like
    # `_handle_thai_amount_enhancement` does when it renders the document.
    if meta.get_field("in_words") and normalize_language(effective_language) == "th":
        primary_amount = get_primary_amount(doc, meta, pairs)
        values["in_words"] = convert_amount_to_words(primary_amount, "th")

    return values


@frappe.whitelist()
def translate_in_words_fields(doctype, docname, language=None):
    """Translate in_words type fields when language changes.

    ERPNext stores in_words in English when document is saved.
    This function regenerates those fields in the requested language for
    print preview purposes (does not modify the database).
    """
    doc = frappe.get_doc(doctype, docname)
    doc.check_permission("read")
    meta = frappe.get_meta(doctype)
    values = {}
    normalized_lang = normalize_language(language) if language else "en"

    # Log fields found in meta for debugging
    _in_words_fields = [
        (df.fieldname, df.fieldtype)
        for df in meta.fields
        if df.fieldname and "_in_words" in df.fieldname
    ]
    frappe.logger().debug(
        f"[PD] translate_in_words_fields: doctype={doctype}, _in_words in meta: {_in_words_fields}"
    )

    # Find in_words and base_in_words fields in meta
    # NOTE: check for "in_words" (standalone) AND "*_in_words" (suffix)
    # "in_words".endswith("_in_words") is False, so we check separately
    in_words_field = None
    base_in_words_field = None
    for df in meta.fields:
        if df.fieldtype == "Small Text" and df.fieldname:
            if df.fieldname == "in_words":
                in_words_field = df
            elif df.fieldname == "base_in_words":
                base_in_words_field = df
            elif df.fieldname.endswith("_in_words"):
                # Generic _in_words suffix field - also translate
                pass  # Already handled via generic approach below

    # Helper to get primary amount field for in_words
    def get_primary_amount():
        for fname in [
            "rounded_total",
            "grand_total",
            "net_total",
            "total",
            "amount",
            "actual_total",
            "outstanding_amount",
        ]:
            val = doc.get(fname)
            if val is not None and val != 0:
                return val
        return None

    # Helper to get base amount field for base_in_words
    def get_base_amount():
        for fname in [
            "base_rounded_total",
            "base_grand_total",
            "base_net_total",
            "base_total",
            "base_amount",
        ]:
            val = doc.get(fname)
            if val is not None and val != 0:
                return val
        return None

    # Handle in_words (primary display currency)
    if in_words_field:
        amount = get_primary_amount()
        if amount is not None:
            currency = _resolve_currency(doc)
            if normalized_lang == "th":
                values["in_words"] = convert_amount_to_words(amount, "th", currency)
            else:
                with _print_language(normalized_lang):
                    values["in_words"] = convert_amount_to_words(amount, normalized_lang, currency)

    # Handle base_in_words
    if base_in_words_field:
        amount = get_base_amount()
        if amount is not None:
            currency = _resolve_currency(doc)
            if normalized_lang == "th":
                values["base_in_words"] = convert_amount_to_words(amount, "th", currency)
            else:
                with _print_language(normalized_lang):
                    values["base_in_words"] = convert_amount_to_words(
                        amount, normalized_lang, currency
                    )

    # CRITICAL: If doc has in_words value but field wasn't found in meta,
    # translate it anyway (some doctypes customize away the in_words field)
    if "in_words" not in values and doc.get("in_words"):
        amount = get_primary_amount()
        if amount is not None:
            currency = _resolve_currency(doc)
            if normalized_lang == "th":
                values["in_words"] = convert_amount_to_words(amount, "th", currency)
            else:
                with _print_language(normalized_lang):
                    values["in_words"] = convert_amount_to_words(amount, normalized_lang, currency)

    return values


@frappe.whitelist(allow_guest=False)
@frappe.whitelist(allow_guest=False)
def get_meta(doctype, _lang=None):
    from print_designer.utils.print_labels import get_table_column_labels

    meta = frappe.get_meta(doctype).as_dict()
    # Translate field labels if language is specified
    if _lang:
        old_lang = frappe.local.lang
        try:
            frappe.local.lang = _lang
            for field in meta.get("fields", []):
                if field.get("label"):
                    field["label"] = _(field["label"])
        finally:
            frappe.local.lang = old_lang
    meta["print_designer_column_labels"] = get_table_column_labels(_lang)
    return meta


@frappe.whitelist(allow_guest=False)
def render_user_text(string, doc, row=None, send_to_jinja=None):
    if not row:
        row = {}
    if not send_to_jinja:
        send_to_jinja = {}

    jinja_vars = {}
    if isinstance(send_to_jinja, dict):
        jinja_vars = send_to_jinja
    elif send_to_jinja != "" and isinstance(send_to_jinja, str):
        try:
            jinja_vars = frappe.parse_json(send_to_jinja)
        except Exception:
            pass

    if not (isinstance(row, dict) or issubclass(row.__class__, BaseDocument)):
        if isinstance(row, str):
            try:
                row = frappe.parse_json(row)
            except Exception:
                raise TypeError("row must be a dict")
        else:
            raise TypeError("row must be a dict")

    if not issubclass(doc.__class__, BaseDocument):
        # This is when we send doc from client side as a json string
        if isinstance(doc, str):
            try:
                doc = frappe.parse_json(doc)
            except Exception:
                raise TypeError("doc must be a dict or subclass of BaseDocument")

    jenv = get_jenv()
    result = {}
    try:
        result["success"] = 1
        result["message"] = jenv.from_string(string).render(
            {"doc": doc, "row": row, **(jinja_vars if isinstance(jinja_vars, dict) else {})}
        )
    except Exception as e:
        """
		string is provided by user and there is no way to know if it is correct or not so log the error from client side
		"""
        result["success"] = 0
        result["error"] = e
    return result


@frappe.whitelist(allow_guest=False)
def get_data_from_main_template(string, doctype, docname=None, settings=None):
    if not settings:
        settings = {}

    result = {}
    if string.find("send_to_jinja") == -1:
        result["success"] = 1
        result["message"] = ""
        return result
    string = string + "{{ send_to_jinja|tojson }}"
    if not isinstance(settings, dict):
        if isinstance(settings, str):
            try:
                settings = frappe.parse_json(settings)
            except Exception:
                raise TypeError("settings must be a dict")
        else:
            raise TypeError("settings must be a dict")
    if not docname or docname == "":
        doc = {}
    else:
        doc = frappe.get_cached_doc(doctype, docname)

    jenv = get_jenv()
    try:
        result["success"] = 1
        result["message"] = (
            jenv.from_string(string).render({"doc": doc, "settings": settings}).strip()
        )
    except Exception as e:
        """
		string is provided by user and there is no way to know if it is correct or not
		also doc is required if used in string else it is not required so there is no way
		for us to decide whether to run this or not if doc is not available
		"""
        result["success"] = 0
        result["error"] = e

    return result


@frappe.whitelist(allow_guest=False)
def get_image_docfields():
    docfield = frappe.qb.DocType("DocField")
    customfield = frappe.qb.DocType("Custom Field")

    # Get standard image fields from DocField table
    image_docfields = _query_rows(
        frappe.qb.from_(docfield)
        .select(
            docfield.name,
            docfield.parent,
            docfield.fieldname,
            docfield.fieldtype,
            docfield.label,
            docfield.options,
        )
        .where((docfield.fieldtype == "Image") | (docfield.fieldtype == "Attach Image"))
        .orderby(docfield.parent)
    )
    # Get custom image fields from Custom Field table (including signature fields)
    custom_image_fields = _query_rows(
        frappe.qb.from_(customfield)
        .select(
            customfield.name,
            customfield.dt.as_("parent"),
            customfield.fieldname,
            customfield.fieldtype,
            customfield.label,
            customfield.options,
        )
        .where((customfield.fieldtype == "Image") | (customfield.fieldtype == "Attach Image"))
        .orderby(customfield.dt)
    )
    # Combine both lists
    all_image_fields = image_docfields + custom_image_fields

    # Sort by parent (DocType name)
    all_image_fields.sort(key=lambda x: x.get("parent", ""))

    return all_image_fields


@frappe.whitelist(allow_guest=False)
def get_watermark_docfields():
    """Get all watermark fields (Select fields with watermark options) for dynamic watermark selection"""
    docfield = frappe.qb.DocType("DocField")
    customfield = frappe.qb.DocType("Custom Field")

    # Get standard watermark fields from DocField table
    watermark_docfields = _query_rows(
        frappe.qb.from_(docfield)
        .select(
            docfield.name,
            docfield.parent,
            docfield.fieldname,
            docfield.fieldtype,
            docfield.label,
            docfield.options,
        )
        .where((docfield.fieldtype == "Select") & (docfield.fieldname.like("%watermark%")))
        .orderby(docfield.parent)
    )
    # Get custom watermark fields from Custom Field table
    custom_watermark_fields = _query_rows(
        frappe.qb.from_(customfield)
        .select(
            customfield.name,
            customfield.dt.as_("parent"),
            customfield.fieldname,
            customfield.fieldtype,
            customfield.label,
            customfield.options,
        )
        .where((customfield.fieldtype == "Select") & (customfield.fieldname.like("%watermark%")))
        .orderby(customfield.dt)
    )
    # Combine both lists
    all_watermark_fields = watermark_docfields + custom_watermark_fields

    # Filter to only include fields that have watermark-related options
    watermark_related_fields = []
    for field in all_watermark_fields:
        options = field.get("options", "")
        if options and any(
            keyword in options.lower() for keyword in ["original", "copy", "draft", "duplicate"]
        ):
            watermark_related_fields.append(field)

    # Sort by parent (DocType name)
    watermark_related_fields.sort(key=lambda x: x.get("parent", ""))

    return watermark_related_fields


@frappe.whitelist()
def convert_css(css_obj):
    string_css = ""
    if css_obj:
        for item in css_obj.items():
            string_css += (
                "".join(["-" + i.lower() if i.isupper() else i for i in item[0]]).lstrip("-")
                + ":"
                + str(item[1] if item[1] != "" or item[0] != "backgroundColor" else "transparent")
                + "!important;"
            )
    string_css += "user-select: all;"
    return string_css


def parse_float_and_unit(input_text, default_unit="px"):
    if isinstance(input_text, (int, float)):
        return {"value": input_text, "unit": default_unit}
    if not isinstance(input_text, str):
        return
    number_match = re.search(r"[+-]?([0-9]*[.])?[0-9]+", input_text)
    if not number_match:
        return

    number = float(number_match.group())
    valid_units = [r"px", r"mm", r"cm", r"in"]
    unit = [match.group() for rx in valid_units if (match := re.search(rx, input_text))]

    return {"value": number, "unit": unit[0] if len(unit) == 1 else default_unit}


@frappe.whitelist()
def convert_uom(
    number: float,
    from_uom: Literal["px", "mm", "cm", "in"] = "px",
    to_uom: Literal["px", "mm", "cm", "in"] = "px",
    only_number: bool = False,
) -> float | str:
    unit_values = {
        "px": 1,
        "mm": 3.7795275591,
        "cm": 37.795275591,
        "in": 96,
    }
    from_px = (
        {
            "to_px": 1,
            "to_mm": unit_values["px"] / unit_values["mm"],
            "to_cm": unit_values["px"] / unit_values["cm"],
            "to_in": unit_values["px"] / unit_values["in"],
        },
    )
    from_mm = (
        {
            "to_mm": 1,
            "to_px": unit_values["mm"] / unit_values["px"],
            "to_cm": unit_values["mm"] / unit_values["cm"],
            "to_in": unit_values["mm"] / unit_values["in"],
        },
    )
    from_cm = (
        {
            "to_cm": 1,
            "to_px": unit_values["cm"] / unit_values["px"],
            "to_mm": unit_values["cm"] / unit_values["mm"],
            "to_in": unit_values["cm"] / unit_values["in"],
        },
    )
    from_in = {
        "to_in": 1,
        "to_px": unit_values["in"] / unit_values["px"],
        "to_mm": unit_values["in"] / unit_values["mm"],
        "to_cm": unit_values["in"] / unit_values["cm"],
    }
    converstion_factor = (
        {
            "from_px": from_px,
            "from_mm": from_mm,
            "from_cm": from_cm,
            "from_in": from_in,
        },
    )
    if only_number:
        return round(number * converstion_factor[0][f"from_{from_uom}"][0][f"to_{to_uom}"], 3)
    return (
        f"{round(number * converstion_factor[0][f'from_{from_uom}'][0][f'to_{to_uom}'], 3)}{to_uom}"
    )


@frappe.whitelist()
def get_barcode(
    barcode_format,
    barcode_value,
    options=None,
    width=None,
    height=None,
    png_base64=False,
):
    if not options:
        options = {}
    options = _parse_barcode_options(options)
    if isinstance(barcode_value, str) and barcode_value.startswith("<svg"):
        import re

        value_match = re.search(r'data-barcode-value="(.*?)">', barcode_value)
        if value_match:
            barcode_value = value_match.group(1)
    if barcode_value == "":
        fallback_html_string = """
			<div class="fallback-barcode">
				<div class="content">
					<span>No Value was Provided to Barcode</span>
				</div>
			</div>
		"""
        return {"type": "svg", "value": fallback_html_string}

    if barcode_format == "qrcode":
        return get_qrcode(barcode_value, options, png_base64)

    from io import BytesIO

    import barcode
    from barcode.writer import ImageWriter, SVGWriter

    class PDSVGWriter(SVGWriter):
        def __init__(self):
            SVGWriter.__init__(self)

        def calculate_viewbox(self, code):
            vw, vh = self.calculate_size(len(code[0]), len(code))
            return vw, vh

        def _init(self, code):
            SVGWriter._init(self, code)
            vw, vh = self.calculate_viewbox(code)
            root = self._root
            if root is None:
                return
            if not width:
                root.removeAttribute("width")
            else:
                root.setAttribute("width", f"{width * 3.7795275591}")
            if not height:
                root.removeAttribute("height")
            else:
                root.setAttribute("height", height)

            root.setAttribute("viewBox", f"0 0 {vw * 3.7795275591} {vh * 3.7795275591}")

    if barcode_format not in barcode.PROVIDED_BARCODES:
        return f"Barcode format {barcode_format} not supported. Valid formats are: {barcode.PROVIDED_BARCODES}"
    writer = ImageWriter() if png_base64 else PDSVGWriter()
    barcode_class = barcode.get_barcode_class(barcode_format)

    try:
        barcode_instance = barcode_class(barcode_value, writer)
    except Exception:
        frappe.msgprint(
            f"Invalid barcode value <b>{barcode_value}</b> for format <b>{barcode_format}</b>",
            raise_exception=True,
            alert=True,
            indicator="red",
        )
        raise
    stream = BytesIO()
    barcode_instance.write(stream, options)
    barcode_bytes = stream.getvalue()
    stream.close()

    if png_base64:
        import base64

        barcode_value = base64.b64encode(barcode_bytes).decode("ascii")
    else:
        barcode_value = barcode_bytes.decode("utf-8")
    return {"type": "png_base64" if png_base64 else "svg", "value": barcode_value}


def get_qrcode(barcode_value, options=None, png_base64=False):
    from io import BytesIO

    import pyqrcode

    if not options:
        options = {}
    options = _parse_barcode_options(options)
    options = {
        "scale": options.get("scale", 5),
        "module_color": options.get("module_color", "#000000"),
        "background": options.get("background", "#ffffff"),
        "quiet_zone": options.get("quiet_zone", 1),
    }
    qr = pyqrcode.create(barcode_value)
    stream = BytesIO()
    if png_base64:
        qrcode_svg = qr.png_as_base64_str(**options)
    else:
        options.update(
            {
                "svgclass": "print-qrcode",
                "lineclass": "print-qrcode-path",
                "omithw": True,
                "xmldecl": False,
            }
        )
        qr.svg(stream, **options)
        qrcode_svg = stream.getvalue().decode("utf-8")
        stream.close()

    return {"type": "png_base64" if png_base64 else "svg", "value": qrcode_svg}
