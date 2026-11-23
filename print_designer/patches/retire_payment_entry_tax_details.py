import json
import re

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from pypika.functions import Trim

from print_designer.commands.install_payment_entry_fields import (
    get_payment_entry_custom_fields_definition,
)

FIELDS = {
    f"pd_custom_{field}_details": f"pd_custom_{field}"
    for field in (
        "net_after_wht_retention",
        "net_after_wht_retention_words",
        "retention_note",
        "net_total_after_wht",
        "net_total_after_wht_words",
        "wht_description",
        "wht_certificate_required",
        "wht_certificate",
        "wht_note",
    )
}

def execute():
    return retire_fields(FIELDS)


def retire_fields(replacements, layout_fields=()):
    field_pattern = re.compile(r"\b(?:" + "|".join(replacements) + r")\b")
    legacy_fields = frappe.get_all(
        "Custom Field",
        filters={"dt": "Payment Entry", "fieldname": ["in", tuple(replacements)]},
        fields=["name", "fieldname", "fieldtype", "options"],
    )
    if legacy_fields:
        original_columns = set(frappe.db.get_table_columns("Payment Entry"))
        _install_replacements(replacements, layout_fields)
        for field in legacy_fields:
            if field.fieldname in original_columns:
                _copy_values(field, replacements[field.fieldname], original_columns)
        _update_field_order(replacements, field_pattern)

    _update_print_formats(replacements, field_pattern)

    for field in legacy_fields:
        # Frappe keeps the SQL column. Retain values that differ from the canonical
        # field and historical certificate names that cannot be resolved.
        frappe.delete_doc("Custom Field", field.name)
    frappe.clear_cache(doctype="Payment Entry")
    return len(legacy_fields)


def _install_replacements(replacements, layout_fields):
    meta = frappe.get_meta("Payment Entry", cached=False)
    existing = {field.fieldname for field in meta.fields}
    fields = get_payment_entry_custom_fields_definition()["Payment Entry"]
    targets = set(replacements.values())
    if targets <= existing:
        return
    targets.update(layout_fields)
    if "pd_custom_wht_certificate" in targets and not meta.has_field("pd_custom_wht_certificate"):
        targets.add("pd_custom_wht_certificate_doctype")

    # Preserve each site's existing layout. Walk backwards through the installer
    # layout when the preferred anchor has yet to be installed or is retiring.
    anchors = {field["fieldname"]: field["insert_after"] for field in fields}
    missing = []
    for field in fields:
        name = field["fieldname"]
        if name not in targets or name in existing:
            continue
        anchor = field["insert_after"]
        while anchor in anchors and (anchor not in existing or anchor in replacements):
            anchor = anchors[anchor]
        if anchor not in existing:
            anchor = "remarks"
        missing.append({**field, "insert_after": anchor})
        existing.add(name)

    if missing:
        create_custom_fields({"Payment Entry": missing}, update=False)


def _copy_values(field, target, original_columns):
    payment = frappe.qb.DocType("Payment Entry")
    old_value = payment[field.fieldname]
    new_value = payment[target]
    query = frappe.qb.update(payment).set(new_value, old_value).where(old_value.isnotnull())

    if field.fieldtype == "Check":
        if field.fieldname == "pd_custom_apply_withholding_tax":
            # A previously enabled deduction remains enabled on the surviving checkbox.
            query = query.where(old_value == 1)
        elif target in original_columns:
            query = query.where(new_value.isnull())
    elif field.fieldtype in ("Currency", "Float", "Int", "Percent"):
        query = query.where(old_value != 0)
        if target in original_columns:
            query = query.where(new_value.isnull() | (new_value == 0))
    else:
        query = query.where(Trim(old_value) != "")
        if target in original_columns:
            query = query.where(new_value.isnull() | (Trim(new_value) == ""))

    if target == "pd_custom_wht_certificate":
        definition = frappe.get_meta("Payment Entry").get_field(target)
        certificate_doctype = field.options
        if not certificate_doctype or not frappe.db.table_exists(certificate_doctype):
            return
        certificate = frappe.qb.DocType(certificate_doctype)
        valid_certificates = frappe.qb.from_(certificate).select(certificate.name).where(certificate.docstatus != 2)
        query = query.where(old_value.isin(valid_certificates))
        if definition.fieldtype == "Dynamic Link":
            controller = payment[definition.options]
            query = query.where(
                controller.isnull() | (controller == "") | (controller == certificate_doctype)
            ).set(controller, certificate_doctype)
        elif definition.options != certificate_doctype:
            return

    query.run()


def _update_field_order(replacements, field_pattern):
    fields = frappe.get_all(
        "Custom Field",
        filters={"dt": "Payment Entry", "insert_after": ["in", tuple(replacements)]},
        fields=["name", "fieldname", "insert_after"],
    )
    legacy_anchors = {field.fieldname: field.insert_after for field in fields if field.fieldname in replacements}
    for field in fields:
        if field.fieldname in replacements:
            continue
        anchor = replacements[field.insert_after]
        # A field following a retired field should stay in its original
        # section when the replacement moved to Details.
        if field.fieldname == anchor or anchor.endswith("_details"):
            anchor = frappe.db.get_value(
                "Custom Field", {"dt": "Payment Entry", "fieldname": field.insert_after}, "insert_after"
            )
            seen = {field.insert_after}
            while anchor in legacy_anchors and anchor not in seen:
                seen.add(anchor)
                anchor = legacy_anchors[anchor]
            if not anchor or anchor in replacements or anchor == field.fieldname:
                anchor = "remarks"
        frappe.db.set_value("Custom Field", field.name, "insert_after", anchor, update_modified=False)

    for setter in frappe.get_all(
        "Property Setter",
        filters={"doc_type": "Payment Entry", "property": "field_order"},
        fields=["name", "value"],
    ):
        if not field_pattern.search(setter.value or ""):
            continue
        order = json.loads(setter.value)
        migrated = list(dict.fromkeys(
            replacements.get(name, name)
            for name in order
            if name not in replacements
            or (replacements[name] not in order and not replacements[name].endswith("_details"))
        ))
        frappe.db.set_value("Property Setter", setter.name, "value", json.dumps(migrated), update_modified=False)


def _update_print_formats(replacements, field_pattern):
    columns = set(frappe.db.get_table_columns("Print Format"))
    fields = [field for field in ("html", "format_data", "print_designer_settings") if field in columns]
    for print_format in frappe.get_all("Print Format", filters={"doc_type": "Payment Entry"}, fields=["name", *fields]):
        updates = {}
        for field in fields:
            value = print_format.get(field)
            if not isinstance(value, str) or not field_pattern.search(value):
                continue
            migrated = field_pattern.sub(lambda match: replacements[match.group()], value)
            if field == "print_designer_settings":
                settings = json.loads(migrated)
                pairs = settings.get("numberToWordsFieldPairs")
                if isinstance(pairs, list):
                    settings["numberToWordsFieldPairs"] = [
                        pair for index, pair in enumerate(pairs) if pair not in pairs[:index]
                    ]
                migrated = json.dumps(settings, ensure_ascii=False)
            updates[field] = migrated
        if updates:
            frappe.db.set_value("Print Format", print_format.name, updates, update_modified=False)
            frappe.clear_document_cache("Print Format", print_format.name)
