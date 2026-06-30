from contextlib import contextmanager

import frappe
from frappe.utils import money_in_words

from print_designer.utils.thai_amount_to_word import thai_money_in_words


NUMERIC_FIELD_TYPES = frozenset({"Currency", "Float", "Int", "Percent"})
TEXT_FIELD_TYPES = frozenset({"Data", "Small Text", "Text", "Long Text"})
THAI_LANGUAGES = frozenset({"th", "th-th", "thai", "ไทย"})


def validate_number_to_words_pairs(meta, pairs):
    """Return field pairs that can safely convert a numeric source to text."""
    valid_pairs = []
    for pair in pairs or []:
        if not isinstance(pair, dict):
            continue

        source_field = pair.get("source_field")
        target_field = pair.get("target_field")
        source_df = meta.get_field(source_field) if source_field else None
        target_df = meta.get_field(target_field) if target_field else None

        if not (
            source_field
            and target_field
            and source_field != target_field
            and source_df
            and target_df
            and source_df.fieldtype in NUMERIC_FIELD_TYPES
            and target_df.fieldtype in TEXT_FIELD_TYPES
        ):
            continue

        valid_pairs.append(pair)

    return valid_pairs


def normalize_language(language):
    value = str(language or "").strip().lower()
    return "th" if value in THAI_LANGUAGES else value


@contextmanager
def _print_language(language):
    previous_language = getattr(frappe.local, "lang", None)
    try:
        if language:
            frappe.local.lang = language
        yield
    finally:
        frappe.local.lang = previous_language


def _doc_value(doc, fieldname, default=None):
    if not fieldname:
        return default
    if hasattr(doc, "get"):
        return doc.get(fieldname, default)
    return getattr(doc, fieldname, default)


def _resolve_currency(doc, currency_field=None):
    for fieldname in (
        currency_field,
        "currency",
        "paid_from_account_currency",
        "paid_to_account_currency",
    ):
        value = _doc_value(doc, fieldname)
        if value:
            return value

    return frappe.defaults.get_global_default("currency") or "THB"


def convert_amount_to_words(amount, language, currency="THB"):
    """Convert an amount under an explicit print-language context."""
    if amount in (None, ""):
        return ""

    normalized_language = normalize_language(language)
    if normalized_language == "th":
        return thai_money_in_words(amount)

    with _print_language(normalized_language):
        return money_in_words(amount, currency)


def apply_number_to_words_pairs(doc, meta, pairs, language):
    """Populate configured targets on a request-scoped document."""
    values = {}
    for pair in validate_number_to_words_pairs(meta, pairs):
        source_field = pair["source_field"]
        target_field = pair["target_field"]
        amount = _doc_value(doc, source_field)
        currency = _resolve_currency(doc, pair.get("currency_field"))
        value = convert_amount_to_words(amount, language, currency)
        setattr(doc, target_field, value)
        values[target_field] = value

    return values
