"""Regression tests for the amount that the amount-in-words fields describe.

The Payment Entry receipt used to convert ``paid_amount`` (the gross amount
that was paid) into words, while the receipt prints the amount **after** the
withholding tax.  The Print Format now declares the field that carries the
amount it wants in words and that field is authoritative.

    paid_amount                       = 105,000
    pd_custom_net_total_after_wht_details = 101,850  <- amount in words
"""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

WHT_PAIR = {
    "source_field": "pd_custom_net_total_after_wht_details",
    "target_field": "pd_custom_net_total_after_wht_words_details",
}


class FakeMeta:
    fields = {
        "pd_custom_net_total_after_wht_details": SimpleNamespace(fieldtype="Currency"),
        "pd_custom_net_total_after_wht_words_details": SimpleNamespace(fieldtype="Data"),
        "paid_amount": SimpleNamespace(fieldtype="Currency"),
        "received_amount": SimpleNamespace(fieldtype="Currency"),
        "grand_total": SimpleNamespace(fieldtype="Currency"),
    }

    def get_field(self, fieldname):
        return self.fields.get(fieldname)


class FakeDoc(SimpleNamespace):
    def get(self, fieldname, default=None):
        return getattr(self, fieldname, default)


def _payment_entry(**overrides):
    values = {
        "doctype": "Payment Entry",
        "name": "ACC-PAY-2606-00001",
        "paid_amount": 105000.0,
        "received_amount": 105000.0,
        "pd_custom_net_total_after_wht_details": 101850.0,
        "pd_custom_net_total_after_wht_words_details": "THB One Hundred And One Thousand, Eight Hundred And Fifty only.",
        "in_words": "THB One Hundred And Five Thousand only.",
        "currency": "THB",
    }
    values.update(overrides)
    return FakeDoc(**values)


def _print_format(pairs=(WHT_PAIR,), language="th"):
    return SimpleNamespace(
        name="Receipt",
        default_print_language=language,
        print_designer_settings=json.dumps({"numberToWordsFieldPairs": list(pairs)}),
    )


def _thai_words(amount):
    """Deterministic stand-in for the Thai amount in words."""
    return f"THAI_WORDS_{int(amount)}" if float(amount).is_integer() else f"THAI_WORDS_{amount}"


class TestPrimaryAmountSource(unittest.TestCase):
    def test_configured_source_field_wins_over_paid_amount(self):
        from print_designer.utils.number_to_words_fields import get_primary_amount

        doc = _payment_entry()

        self.assertEqual(get_primary_amount(doc, FakeMeta(), [WHT_PAIR]), 101850.0)

    def test_falls_back_to_paid_amount_without_configured_pairs(self):
        from print_designer.utils.number_to_words_fields import get_primary_amount

        doc = _payment_entry()

        self.assertEqual(get_primary_amount(doc, FakeMeta(), []), 105000.0)

    def test_falls_back_to_paid_amount_when_source_field_is_empty(self):
        from print_designer.utils.number_to_words_fields import get_primary_amount

        doc = _payment_entry(pd_custom_net_total_after_wht_details=0.0)

        self.assertEqual(get_primary_amount(doc, FakeMeta(), [WHT_PAIR]), 105000.0)


class TestThaiAmountEnhancement(unittest.TestCase):
    def _run(self, doc, print_format):
        from print_designer.pdf import _handle_thai_amount_enhancement

        args = {}
        with (
            patch("print_designer.pdf.get_effective_language", return_value="th"),
            patch("print_designer.pdf.frappe.get_meta", return_value=FakeMeta()),
            patch(
                "print_designer.utils.number_to_words_fields.thai_money_in_words",
                side_effect=_thai_words,
            ) as words,
            patch(
                "print_designer.utils.thai_amount_to_word.thai_money_in_words",
                side_effect=_thai_words,
            ) as legacy_words,
        ):
            _handle_thai_amount_enhancement(print_format, doc, args)
        return words, legacy_words

    def test_words_fields_use_the_amount_after_wht(self):
        doc = _payment_entry()

        words, legacy_words = self._run(doc, _print_format())

        self.assertEqual(doc.pd_custom_net_total_after_wht_words_details, "THAI_WORDS_101850")
        self.assertEqual(doc.in_words, "THAI_WORDS_101850")
        self.assertEqual(words.call_args_list[-1].args, (101850,))
        self.assertEqual(legacy_words.call_args_list[-1].args, (101850,))
        self.assertNotIn(
            105000,
            [call.args[0] for call in words.call_args_list + legacy_words.call_args_list],
        )

    def test_in_words_keeps_the_paid_amount_without_configured_pairs(self):
        doc = _payment_entry()

        _words, legacy_words = self._run(doc, _print_format(pairs=()))

        self.assertEqual(doc.in_words, "THAI_WORDS_105000")
        self.assertEqual(legacy_words.call_args_list[-1].args, (105000,))
        # nothing to populate without a configured pair
        self.assertEqual(
            doc.pd_custom_net_total_after_wht_words_details,
            "THB One Hundred And One Thousand, Eight Hundred And Fifty only.",
        )


if __name__ == "__main__":
    unittest.main()
