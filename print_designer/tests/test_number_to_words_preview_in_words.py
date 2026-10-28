"""Regression tests for the Design View amount-in-words preview.

The Design View (`/app/print-designer/<format>`) has to show the same text as
the generated PDF.  The PDF computes the amount-in-words fields from the
source field that the Print Format declares
(`numberToWordsFieldPairs`), and it uses the same amount for the legacy
`in_words` field.  The preview endpoint used to compute only the declared
targets, so `in_words` kept the stored value (the gross amount of a Payment
Entry) and the Design View disagreed with the printed document.
"""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

PAIRS = [{"source_field": "amount", "target_field": "amount_words"}]


class FakeMeta:
    def __init__(self, with_in_words=True):
        self.fields = {
            "amount": SimpleNamespace(fieldtype="Currency"),
            "amount_words": SimpleNamespace(fieldtype="Small Text"),
        }
        if with_in_words:
            self.fields["in_words"] = SimpleNamespace(fieldtype="Small Text")

    def get_field(self, fieldname):
        return self.fields.get(fieldname)


class FakeDoc(SimpleNamespace):
    def get(self, fieldname, default=None):
        return getattr(self, fieldname, default)

    def check_permission(self, *args, **kwargs):
        return None


def _print_format(language="th"):
    return SimpleNamespace(
        doc_type="Payment Entry",
        default_print_language=language,
        print_designer_settings=json.dumps({"numberToWordsFieldPairs": PAIRS}),
    )


class TestPreviewInWords(unittest.TestCase):
    def _call(self, doc, print_format, meta, language=None):
        from print_designer.print_designer.page.print_designer import print_designer

        with (
            patch.object(
                print_designer.frappe,
                "get_doc",
                side_effect=[doc, print_format],
            ),
            patch.object(print_designer.frappe, "get_meta", return_value=meta),
            patch(
                "print_designer.utils.number_to_words_fields.thai_money_in_words",
                side_effect=lambda amount: f"THAI_WORDS_{int(amount)}",
            ),
            patch(
                "print_designer.utils.number_to_words_fields.money_in_words",
                side_effect=lambda amount, currency="THB": f"EN_WORDS_{int(amount)}",
            ),
        ):
            return print_designer.get_number_to_words_preview(
                doctype="Payment Entry",
                docname="ACC-PAY-2606-00001",
                print_format="Receipt",
                language=language,
            )

    def test_in_words_describes_the_configured_amount(self):
        doc = FakeDoc(
            amount=101850,
            amount_words=None,
            in_words="THB One Hundred And Five Thousand only.",
            currency="THB",
        )

        values = self._call(doc, _print_format(), FakeMeta())

        self.assertEqual(values["amount_words"], "THAI_WORDS_101850")
        self.assertEqual(
            values["in_words"],
            "THAI_WORDS_101850",
            "The legacy in_words field must describe the same amount as the "
            "configured pair, exactly like the print pipeline does.",
        )

    def test_in_words_is_not_recomputed_for_other_languages(self):
        doc = FakeDoc(
            amount=101850,
            amount_words=None,
            in_words="THB One Hundred And Five Thousand only.",
            currency="THB",
        )

        values = self._call(doc, _print_format(language="en"), FakeMeta(), language="en")

        self.assertNotIn("in_words", values)
        self.assertEqual(values["amount_words"], "EN_WORDS_101850")

    def test_documents_without_in_words_are_unaffected(self):
        doc = FakeDoc(amount=101850, amount_words=None, currency="THB")

        values = self._call(doc, _print_format(), FakeMeta(with_in_words=False))

        self.assertEqual(list(values.keys()), ["amount_words"])

    def test_preview_does_not_write_to_the_database(self):
        doc = MagicMock()
        doc.get.return_value = None

        from print_designer.print_designer.page.print_designer import print_designer

        with (
            patch.object(
                print_designer.frappe,
                "get_doc",
                side_effect=[doc, _print_format()],
            ),
            patch.object(print_designer.frappe, "get_meta", return_value=FakeMeta()),
            patch.object(
                print_designer,
                "apply_number_to_words_pairs",
                return_value={"amount_words": "หนึ่งร้อยบาทถ้วน"},
                create=True,
            ),
        ):
            print_designer.get_number_to_words_preview(
                doctype="Payment Entry",
                docname="ACC-PAY-2606-00001",
                print_format="Receipt",
            )

        doc.save.assert_not_called()
        doc.db_set.assert_not_called()


if __name__ == "__main__":
    unittest.main()
