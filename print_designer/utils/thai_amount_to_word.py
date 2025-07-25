"""
Thai Amount to Word Conversion Utility for Print Designer

This module provides Thai language amount to word conversion functionality.
It integrates with the existing Frappe money_in_words function but adds
Thai language support when the print format uses Thai as the default language.
"""

import frappe
from frappe import _
from frappe.utils import flt
from num2words import num2words


def thai_money_in_words(
    number,
    main_currency=None,
    fraction_currency=None,
    currency_symbol="บาท",
    fraction_symbol="สตางค์",
    zero_text="ศูนย์",
    only_text="ถ้วน",
    and_text="",
):
    """
    Convert amount to Thai words with proper currency formatting.

    Args:
        number: Amount to convert
        main_currency: Main currency name (defaults to บาท)
        fraction_currency: Fraction currency name (defaults to สตางค์)
        currency_symbol: Currency symbol for display
        fraction_symbol: Fraction symbol for display
        zero_text: Text for zero amount
        only_text: Text for "only" (ถ้วน)
        and_text: Text for "and" (empty in Thai)

    Returns:
        str: Amount in Thai words
    """

    try:
        # Convert to float, return empty string if invalid
        number = float(number)
    except (ValueError, TypeError):
        return ""

    # Return empty string for negative numbers
    if number < 0:
        return ""

    # Handle zero case
    if number == 0:
        return f"{zero_text}{currency_symbol}{only_text}"

    # Split into main currency and fraction
    number_str = f"{number:.2f}"
    parts = number_str.split(".")
    main_part = int(parts[0])
    fraction_part = int(parts[1]) if len(parts) > 1 else 0

    result_parts = []

    # Convert main currency part
    if main_part > 0:
        try:
            main_words = num2words(main_part, lang="th")
            result_parts.append(f"{main_words}{currency_symbol}")
        except Exception:
            # Fallback to English if Thai conversion fails
            main_words = num2words(main_part, lang="en")
            result_parts.append(f"{main_words} {currency_symbol}")

    # Convert fraction part
    if fraction_part > 0:
        try:
            fraction_words = num2words(fraction_part, lang="th")
            result_parts.append(f"{fraction_words}{fraction_symbol}")
        except Exception:
            # Fallback to English if Thai conversion fails
            fraction_words = num2words(fraction_part, lang="en")
            result_parts.append(f"{fraction_words} {fraction_symbol}")

    # Join parts
    if len(result_parts) == 1:
        if main_part > 0:
            return f"{result_parts[0]}{only_text}"
        else:
            return result_parts[0]
    elif len(result_parts) == 2:
        return f"{result_parts[0]}{result_parts[1]}"
    else:
        return f"{main_part}{currency_symbol}{only_text}"


def is_thai_format(print_format_name=None, doc=None):
    """
    Check if the current print format should use Thai language.

    IMPORTANT: This function now uses the new language priority system.
    Priority: URL _lang parameter > Print Format language > Local language > Legacy logic

    Args:
        print_format_name: Name of the print format
        doc: Document being printed

    Returns:
        bool: True if Thai language should be used
    """

    # Use the new centralized language detection from pdf.py
    try:
        from print_designer.pdf import get_effective_language, is_thai_language

        effective_lang = get_effective_language(print_format_name)
        result = is_thai_language(effective_lang)

        if result:
            print(
                f"Using Thai formatting based on effective language: {effective_lang}"
            )
        else:
            print(
                f"NOT using Thai formatting - effective language is: {effective_lang}"
            )

        return result

    except ImportError:
        # Fallback to old logic if pdf.py is not available
        pass

    # Legacy logic (kept for backward compatibility)
    # Check URL parameter directly (supports both th and ไทย)
    lang_param = frappe.form_dict.get("_lang")
    if lang_param and lang_param.lower() in ["th", "ไทย", "thai"]:
        print(f"Using Thai formatting based on URL parameter: {lang_param}")
        return True

    # Check if the current language is Thai
    if frappe.local.lang == "th":
        print(f"Using Thai formatting based on local language: {frappe.local.lang}")
        return True

    # Check if the print format is configured for Thai
    if print_format_name:
        try:
            print_format = frappe.get_doc("Print Format", print_format_name)

            print(f"print_format {print_format}")

            # Check if print format has Thai language setting
            if getattr(print_format, "language", None) == "th":
                print("Using Thai formatting based on print format language")
                return True

            # Check if print format name contains Thai indicators
            thai_indicators = ["thai", "ไทย", "th_", "_th", "form_50", "tax_invoice"]
            for indicator in thai_indicators:
                if indicator.lower() in print_format_name.lower():
                    print(
                        f"Using Thai formatting based on format name indicator: {indicator}"
                    )
                    return True
        except Exception:
            pass

    # Check document for Thai language indicators
    if doc:
        try:
            # Check if document has Thai language field
            if getattr(doc, "language", None) == "th":
                print(
                    f"Using Thai formatting based on document language {getattr(doc, 'language')}"
                )
                return True

            # Check if company has Thai settings
            if hasattr(doc, "company"):
                company = frappe.get_doc("Company", doc.company)
                print(f"company {company}")
                if getattr(company, "country", None) == "Thailand":
                    print(
                        f"Using Thai formatting based on company country: Thailand {getattr(company, 'country')}"
                    )
                    return True
        except Exception:
            pass

    print("NOT using Thai formatting - no Thai indicators found")
    return False


@frappe.whitelist()
def get_amount_in_words(
    amount, currency="THB", print_format=None, doctype=None, docname=None
):
    """
    API endpoint to get amount in words with Thai language support.

    Args:
        amount: Amount to convert
        currency: Currency code (defaults to THB)
        print_format: Print format name
        doctype: Document type
        docname: Document name

    Returns:
        str: Amount in words
    """

    try:
        # Get document if available
        doc = None
        if doctype and docname:
            doc = frappe.get_doc(doctype, docname)

        # Check if Thai language should be used
        if is_thai_format(print_format, doc):
            return thai_money_in_words(amount)
        else:
            # Use standard Frappe money_in_words function
            from frappe.utils import money_in_words

            return money_in_words(amount, currency)

    except Exception as e:
        frappe.log_error(
            title="Thai Amount to Word Error",
            message=f"Error converting amount to words: {str(e)}",
        )
        # Fallback to standard function
        try:
            from frappe.utils import money_in_words

            return money_in_words(amount, currency)
        except Exception:
            return str(amount)


def enhance_in_words_field(doc, print_format_name=None, method=None):
    """
    Enhance the in_words field with Thai language support.

    This function can be called from print format hooks to automatically
    set Thai amount in words when appropriate.

    Args:
        doc: Document with in_words field
        print_format_name: Name of the print format
        method: Hook method (for Frappe document event compatibility)
    """

    if not hasattr(doc, "in_words") or not hasattr(doc, "grand_total"):
        return

    # Get print format from form_dict if not provided
    if not print_format_name:
        print_format_name = frappe.form_dict.get("format")

    # Only enhance if Thai format is detected
    if is_thai_format(print_format_name, doc):
        try:
            # Set Thai amount in words
            doc.in_words = thai_money_in_words(doc.grand_total or 0)

            if frappe.conf.developer_mode:
                frappe.logger().info(
                    f"Enhanced Thai amount in words for {doc.doctype} {doc.name}: {doc.in_words}"
                )
        except Exception as e:
            frappe.log_error(
                title="Thai Amount Enhancement Error",
                message=f"Error enhancing in_words field for {doc.doctype} {doc.name}: {str(e)}",
            )


def smart_money_in_words(amount, main_currency="", print_format=None):
    """
    Smart money in words that automatically detects Thai language context.

    This function can be used in Jinja templates as a replacement for frappe.utils.money_in_words.
    Usage: {{ smart_money_in_words(doc.grand_total, doc.currency, format) }}

    Args:
        amount: Amount to convert
        main_currency: Currency (unused for Thai, kept for compatibility)
        print_format: Print format name (optional)

    Returns:
        str: Amount in words (Thai or English based on context)
    """
    # If Thai context is detected, use Thai conversion
    if is_thai_format(print_format):
        return thai_money_in_words(amount or 0)

    # Otherwise, use Frappe's default function
    from frappe.utils import money_in_words as frappe_money_in_words

    return frappe_money_in_words(amount, main_currency)


def get_smart_in_words(doc):
    """
    Get smart in_words field that automatically uses Thai when appropriate.
    This can be used as: {{ get_smart_in_words(doc) }}
    """
    # Check if we should use Thai format
    if is_thai_format(frappe.form_dict.get("format"), doc):
        return thai_money_in_words(getattr(doc, "grand_total", 0) or 0)

    # Return original in_words field
    return getattr(doc, "in_words", "")


@frappe.whitelist()
def get_thai_in_words_for_print(doc, print_format_name=None):
    """
    Get Thai amount in words for use in print templates.

    This function can be called directly from Jinja templates in print formats.
    Usage in template: {{ frappe.call('print_designer.utils.thai_amount_to_word.get_thai_in_words_for_print', doc, format) }}

    Args:
        doc: Document object
        print_format_name: Print format name

    Returns:
        str: Thai amount in words or original in_words if not Thai format
    """
    # Check if we should use Thai format
    if is_thai_format(print_format_name, doc):
        try:
            return thai_money_in_words(getattr(doc, "grand_total", 0) or 0)
        except Exception:
            pass

    # Return original in_words field as fallback
    return getattr(doc, "in_words", "")


@frappe.whitelist()
def test_thai_conversion(amount=1234.56):
    """
    Test function for Thai amount to word conversion.

    Args:
        amount: Amount to test (defaults to 1234.56)

    Returns:
        dict: Test results
    """

    # Convert amount to float if it's a string
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        amount = 1234.56

    results = {
        "amount": amount,
        "thai_words": None,
        "english_words": None,
        "error": None,
    }

    try:
        # Test Thai conversion
        results["thai_words"] = thai_money_in_words(amount)

        # Test English conversion for comparison
        from frappe.utils import money_in_words

        results["english_words"] = money_in_words(amount, "THB")

    except Exception as e:
        results["error"] = str(e)

    return results
