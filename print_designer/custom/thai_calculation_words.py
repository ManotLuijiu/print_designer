"""The wording of the calculated amounts of a Thai document.

The Sales Invoice, the Sales Order and the Quotation describe the same two
amounts in words: the net total after the withholding tax and the net total
after the withholding tax and the retention.  The helper keeps the wording of
the three in one place, so that a change reaches all of them.

The wording names the currency of the document.  Frappe's ``money_in_words``
falls back to the default currency of the site when no currency is given,
which describes the amount of a document in another currency in the wrong
currency.

The language of the wording is the language of the session, as it was before.
The print format decides the language of the printed document (see
:mod:`print_designer.utils.number_to_words_fields`); the stored wording is
the fallback for a print format without a configured number to words pair.
"""

import frappe
from frappe.utils import flt, money_in_words

#: The amount after the withholding tax.
NET_TOTAL_AFTER_WHT = "pd_custom_net_total_after_wht"

#: The amount after the withholding tax and the retention.
NET_AFTER_WHT_RETENTION = "pd_custom_net_after_wht_retention"

#: The field that carries the wording of the amount after the withholding tax.
NET_TOTAL_AFTER_WHT_WORDS = f"{NET_TOTAL_AFTER_WHT}_words"

#: The field that carries the wording of the amount after the retention.
NET_AFTER_WHT_RETENTION_WORDS = f"{NET_AFTER_WHT_RETENTION}_words"


def amount_in_words(doc, amount) -> str:
    """Return the wording of an amount in the currency of the document.

    An amount of zero has no wording, and a negative amount has none either -
    Frappe does not describe a negative amount in words.
    """
    if amount in (None, ""):
        return ""

    amount = flt(amount)
    if not amount:
        return ""

    currency = doc.get("currency") or None
    return money_in_words(amount, currency)


def _write(doc, field, value) -> None:
    """Write a field of the document, whatever kind of document it is."""
    setter = getattr(doc, "set", None)
    if callable(setter):
        setter(field, value)
        return

    doc[field] = value


def apply_amount_wording(doc, label="Thai Calc") -> None:
    """Describe the calculated amounts of the document in words.

    The two wording fields are only written when the document carries them.
    A document without a retention gets an empty wording of the retention.
    """
    try:
        net_total = doc.get(NET_TOTAL_AFTER_WHT)
        if net_total and hasattr(doc, NET_TOTAL_AFTER_WHT_WORDS):
            try:
                _write(
                    doc,
                    NET_TOTAL_AFTER_WHT_WORDS,
                    amount_in_words(doc, net_total),
                )
                print(
                    f"🔍 {label}: {NET_TOTAL_AFTER_WHT_WORDS} = "
                    f"{doc.get(NET_TOTAL_AFTER_WHT_WORDS)}"
                )
            except Exception as e:
                _write(doc, NET_TOTAL_AFTER_WHT_WORDS, "")
                print(f"🔍 {label}: Error converting {NET_TOTAL_AFTER_WHT} to words: {str(e)}")

        retention = doc.get(NET_AFTER_WHT_RETENTION)
        if (
            doc.get("pd_custom_subject_to_retention")
            and retention
            and hasattr(doc, NET_AFTER_WHT_RETENTION_WORDS)
        ):
            try:
                _write(
                    doc,
                    NET_AFTER_WHT_RETENTION_WORDS,
                    amount_in_words(doc, retention),
                )
                print(
                    f"🔍 {label}: {NET_AFTER_WHT_RETENTION_WORDS} = "
                    f"{doc.get(NET_AFTER_WHT_RETENTION_WORDS)}"
                )
            except Exception as e:
                _write(doc, NET_AFTER_WHT_RETENTION_WORDS, "")
                print(f"🔍 {label}: Error converting {NET_AFTER_WHT_RETENTION} to words: {str(e)}")
        elif hasattr(doc, NET_AFTER_WHT_RETENTION_WORDS):
            # A document without a retention has no wording of the retention.
            _write(doc, NET_AFTER_WHT_RETENTION_WORDS, "")
            print(f"🔍 {label}: Cleared {NET_AFTER_WHT_RETENTION_WORDS} (no retention)")

    except Exception as e:
        frappe.log_error(
            f"Error converting amounts to words for {doc.get('doctype')} "
            f"{doc.get('name')}: {str(e)}"
        )
        # Clear the wording fields on error
        if hasattr(doc, NET_TOTAL_AFTER_WHT_WORDS):
            _write(doc, NET_TOTAL_AFTER_WHT_WORDS, "")
        if hasattr(doc, NET_AFTER_WHT_RETENTION_WORDS):
            _write(doc, NET_AFTER_WHT_RETENTION_WORDS, "")
        print(f"🔍 {label}: Error in the wording of the calculated amounts: {str(e)}")
