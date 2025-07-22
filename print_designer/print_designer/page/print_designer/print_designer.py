import re
from typing import Literal

import frappe
from frappe.model.document import BaseDocument
from frappe.utils.jinja import get_jenv
from frappe import _


@frappe.whitelist()
def get_signature_image(signature_name):
    """Get signature image URL from Digital Signature doctype"""
    if not signature_name:
        return None

    try:
        signature_doc = frappe.get_doc("Digital Signature", signature_name)
        if signature_doc.is_active and signature_doc.signature_image:
            return {
                "image_url": signature_doc.signature_image,
                "title": signature_doc.title,
                "description": signature_doc.description,
            }
    except frappe.DoesNotExistError:
        frappe.log_error(f"Digital Signature {signature_name} not found")

    return None


@frappe.whitelist()
def get_company_stamp_image(stamp_name):
    """Get company stamp image URL from Company Stamp doctype"""
    if not stamp_name:
        return None

    try:
        stamp_doc = frappe.get_doc("Company Stamp", stamp_name)
        if stamp_doc.is_active and stamp_doc.stamp_image:
            return {
                "image_url": stamp_doc.stamp_image,
                "title": stamp_doc.title,
                "description": stamp_doc.description,
                "stamp_type": stamp_doc.stamp_type,
                "company": stamp_doc.company,
            }
    except frappe.DoesNotExistError:
        frappe.log_error(f"Company Stamp {stamp_name} not found")

    return None


@frappe.whitelist()
def get_signature_and_stamp_context(digital_signature=None, company_stamp=None):
    """Get both signature and stamp context for print templates"""
    context = {}

    # Add signature context
    if digital_signature:
        signature_data = get_signature_image(digital_signature)
        if signature_data:
            context.update(
                {
                    "signature_image": signature_data["image_url"],
                    "signature_title": signature_data["title"],
                    "signature_description": signature_data.get("description", ""),
                }
            )

    # Add stamp context
    if company_stamp:
        stamp_data = get_company_stamp_image(company_stamp)
        if stamp_data:
            context.update(
                {
                    "company_stamp_image": stamp_data["image_url"],
                    "company_stamp_title": stamp_data["title"],
                    "company_stamp_description": stamp_data.get("description", ""),
                    "company_stamp_type": stamp_data.get("stamp_type", ""),
                    "stamp_company": stamp_data.get("company", ""),
                }
            )

    return context


# Hook into the print context to inject signature and stamp data
def get_print_context(
    doctype,
    name,
    print_format=None,
    letterhead=None,
    digital_signature=None,
    company_stamp=None,
):
    """Enhanced print context with signature and stamp support"""

    # Get the standard print context
    from frappe.utils.print_format import (
        get_print_context as original_get_print_context,
    )

    context = original_get_print_context(doctype, name, print_format, letterhead)

    # Add signature and stamp context
    signature_stamp_context = get_signature_and_stamp_context(
        digital_signature, company_stamp
    )
    context.update(signature_stamp_context)

    return context


# Patch the original get_print_context function
import frappe.utils.print_format

frappe.utils.print_format.get_print_context = get_print_context


@frappe.whitelist(allow_guest=False)
def render_user_text_withdoc(
    string, doctype, docname=None, row=None, send_to_jinja=None
):
    if not row:
        row = {}
    if not send_to_jinja:
        send_to_jinja = {}

    if not docname or docname == "":
        return render_user_text(
            string=string, doc={}, row=row, send_to_jinja=send_to_jinja
        )
    doc = frappe.get_cached_doc(doctype, docname)
    doc.check_permission()
    return render_user_text(
        string=string, doc=doc, row=row, send_to_jinja=send_to_jinja
    )


@frappe.whitelist(allow_guest=False)
def get_meta(doctype):
    return frappe.get_meta(doctype).as_dict()


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
            {"doc": doc, "row": row, **jinja_vars}
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
    image_docfields = (
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
    ).run(as_dict=True)

    # Get custom image fields from Custom Field table (including signature fields)
    custom_image_fields = (
        frappe.qb.from_(customfield)
        .select(
            customfield.name,
            customfield.dt.as_("parent"),
            customfield.fieldname,
            customfield.fieldtype,
            customfield.label,
            customfield.options,
        )
        .where(
            (customfield.fieldtype == "Image")
            | (customfield.fieldtype == "Attach Image")
        )
        .orderby(customfield.dt)
    ).run(as_dict=True)

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
    watermark_docfields = (
        frappe.qb.from_(docfield)
        .select(
            docfield.name,
            docfield.parent,
            docfield.fieldname,
            docfield.fieldtype,
            docfield.label,
            docfield.options,
        )
        .where(
            (docfield.fieldtype == "Select") 
            & (docfield.fieldname.like("%watermark%"))
        )
        .orderby(docfield.parent)
    ).run(as_dict=True)

    # Get custom watermark fields from Custom Field table
    custom_watermark_fields = (
        frappe.qb.from_(customfield)
        .select(
            customfield.name,
            customfield.dt.as_("parent"),
            customfield.fieldname,
            customfield.fieldtype,
            customfield.label,
            customfield.options,
        )
        .where(
            (customfield.fieldtype == "Select")
            & (customfield.fieldname.like("%watermark%"))
        )
        .orderby(customfield.dt)
    ).run(as_dict=True)

    # Combine both lists
    all_watermark_fields = watermark_docfields + custom_watermark_fields

    # Filter to only include fields that have watermark-related options
    watermark_related_fields = []
    for field in all_watermark_fields:
        options = field.get('options', '')
        if options and any(keyword in options.lower() for keyword in ['original', 'copy', 'draft', 'duplicate']):
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
                "".join(
                    ["-" + i.lower() if i.isupper() else i for i in item[0]]
                ).lstrip("-")
                + ":"
                + str(
                    item[1]
                    if item[1] != "" or item[0] != "backgroundColor"
                    else "transparent"
                )
                + "!important;"
            )
    string_css += "user-select: all;"
    return string_css


def parse_float_and_unit(input_text, default_unit="px"):
    if isinstance(input_text, (int, float)):
        return {"value": input_text, "unit": default_unit}
    if not isinstance(input_text, str):
        return

    number = float(re.search(r"[+-]?([0-9]*[.])?[0-9]+", input_text).group())
    valid_units = [r"px", r"mm", r"cm", r"in"]
    unit = [match.group() for rx in valid_units if (match := re.search(rx, input_text))]

    return {"value": number, "unit": unit[0] if len(unit) == 1 else default_unit}


@frappe.whitelist()
def convert_uom(
    number: float,
    from_uom: Literal["px", "mm", "cm", "in"] = "px",
    to_uom: Literal["px", "mm", "cm", "in"] = "px",
    only_number: bool = False,
) -> float:
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
        return round(
            number * converstion_factor[0][f"from_{from_uom}"][0][f"to_{to_uom}"], 3
        )
    return f"{round(number * converstion_factor[0][f'from_{from_uom}'][0][f'to_{to_uom}'], 3)}{to_uom}"


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

    options = frappe.parse_json(options)

    if isinstance(barcode_value, str) and barcode_value.startswith("<svg"):
        import re

        barcode_value = re.search(r'data-barcode-value="(.*?)">', barcode_value).group(
            1
        )

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
            if not width:
                self._root.removeAttribute("width")
            else:
                self._root.setAttribute("width", f"{width * 3.7795275591}")
            if not height:
                self._root.removeAttribute("height")
            else:
                self._root.setAttribute("height", height)

            self._root.setAttribute(
                "viewBox", f"0 0 {vw * 3.7795275591} {vh * 3.7795275591}"
            )

    if barcode_format not in barcode.PROVIDED_BARCODES:
        return f"Barcode format {barcode_format} not supported. Valid formats are: {barcode.PROVIDED_BARCODES}"
    writer = ImageWriter() if png_base64 else PDSVGWriter()
    barcode_class = barcode.get_barcode_class(barcode_format)

    try:
        barcode = barcode_class(barcode_value, writer)
    except Exception:
        frappe.msgprint(
            f"Invalid barcode value <b>{barcode_value}</b> for format <b>{barcode_format}</b>",
            raise_exception=True,
            alert=True,
            indicator="red",
        )

    stream = BytesIO()
    barcode.write(stream, options)
    barcode_value = stream.getvalue().decode("utf-8")
    stream.close()

    if png_base64:
        import base64

        barcode_value = base64.b64encode(barcode_value)

    return {"type": "png_base64" if png_base64 else "svg", "value": barcode_value}


def get_qrcode(barcode_value, options=None, png_base64=False):
    from io import BytesIO

    import pyqrcode

    if not options:
        options = {}

    options = frappe.parse_json(options)
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
