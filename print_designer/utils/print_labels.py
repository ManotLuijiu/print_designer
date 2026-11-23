"""Translate print labels once in the selected output language."""

import re

import frappe

from print_designer.utils.number_to_words_fields import normalize_language

TABLE_COLUMN_LABELS = (
    ("Order", "ลำดับที่", ("No.", "เลขที่")),
    ("Receive", "รับชำระ", ("Allocated", "Allocated Amount", "จัดสรร", "จำนวนเงินที่จัดสรร")),
    ("Document Type", "ประเภทเอกสาร", ("Type", "ประเภท")),
    ("Document Number", "เลขที่เอกสาร", ("Name", "ชื่อ", "Document No.")),
)


def get_table_column_labels(language=None):
    language = normalize_language(language or getattr(frappe.local, "lang", None))
    return {
        alias: thai if language == "th" else english
        for english, thai, aliases in TABLE_COLUMN_LABELS
        for alias in (english, thai, *aliases)
    }


def translate_table_column_label(value, language=None):
    labels = get_table_column_labels(language)
    if value in labels:
        return labels[value]
    translated = translate_print_label(value, language)
    return labels.get(translated, translated)


def translate_print_label(value, language=None):
    text = str(value) if value is not None else ""
    language = normalize_language(language or getattr(frappe.local, "lang", None))
    # Some site dictionaries contain reverse entries (Thai -> English). A Thai
    # label is already in the requested output language; don't translate it twice.
    if language == "th" and re.search(r"[\u0e00-\u0e7f]", text):
        return text
    return frappe._(text, lang=language or None)
