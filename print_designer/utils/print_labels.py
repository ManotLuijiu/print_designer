"""Translate print labels once in the selected output language."""

import re

import frappe

from print_designer.utils.number_to_words_fields import normalize_language


def translate_print_label(value, language=None):
    text = str(value) if value is not None else ""
    language = normalize_language(language or getattr(frappe.local, "lang", None))
    # Some site dictionaries contain reverse entries (Thai -> English). A Thai
    # label is already in the requested output language; don't translate it twice.
    if language == "th" and re.search(r"[\u0e00-\u0e7f]", text):
        return text
    return frappe._(text, lang=language or None)
