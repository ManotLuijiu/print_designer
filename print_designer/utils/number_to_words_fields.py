from contextlib import contextmanager

import frappe
from frappe.utils import flt, money_in_words

from print_designer.utils.thai_amount_to_word import thai_money_in_words

NUMERIC_FIELD_TYPES = frozenset({"Currency", "Float", "Int", "Percent"})
TEXT_FIELD_TYPES = frozenset({"Data", "Small Text", "Text", "Long Text"})
THAI_LANGUAGES = frozenset({"th", "th-th", "thai", "ไทย"})

# Fallback order for the amount that the words fields describe when the
# Print Format does not declare a source field.
PRIMARY_AMOUNT_FALLBACKS = ("grand_total", "paid_amount", "received_amount", "total_amount")


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


def get_number_to_words_pairs(print_format):
    settings_value = _doc_value(print_format, "print_designer_settings") or "{}"
    settings = frappe.parse_json(settings_value) or {}
    pairs = settings.get("numberToWordsFieldPairs")
    return pairs if isinstance(pairs, list) else []


def merge_number_to_words_pair(settings, pair):
    pairs = settings.setdefault("numberToWordsFieldPairs", [])
    identity = (pair.get("source_field"), pair.get("target_field"))
    if not all(identity):
        return False
    if any(
        (current.get("source_field"), current.get("target_field")) == identity
        for current in pairs
        if isinstance(current, dict)
    ):
        return False
    pairs.append(dict(pair))
    return True


def resolve_print_language(
    print_format,
    explicit_language=None,
    document_language=None,
    user_language=None,
):
    normalized_explicit = normalize_language(explicit_language)
    normalized_user = normalize_language(user_language)
    if normalized_explicit and normalized_explicit == normalized_user:
        normalized_explicit = ""
    language = (
        normalized_explicit
        or _doc_value(print_format, "default_print_language")
        or document_language
        or normalized_user
        or "en"
    )
    return normalize_language(language)


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


def get_primary_amount(doc, meta, pairs):
    """Return the amount that the amount-in-words fields have to describe.

    The Print Format declares which field carries the amount it wants in
    words (the first configured pair).  That field is authoritative: on a
    Payment Entry it holds the amount **after** the withholding tax, while
    ``paid_amount`` is the gross amount that was paid.

    A source field without a value (or with a zero value) is ignored so a
    Payment Entry without a withholding tax still falls back to the amount
    that was actually paid.
    """
    for pair in validate_number_to_words_pairs(meta, pairs):
        value = _doc_value(doc, pair.get("source_field"))
        if value not in (None, "") and flt(value):
            return flt(value)

    for fieldname in PRIMARY_AMOUNT_FALLBACKS:
        value = _doc_value(doc, fieldname)
        if value not in (None, "") and flt(value):
            return flt(value)

    return 0


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
