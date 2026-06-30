import unittest
from types import SimpleNamespace
from unittest.mock import patch


class FakeMeta:
    fields = {
        "amount": SimpleNamespace(fieldtype="Currency"),
        "amount_words": SimpleNamespace(fieldtype="Small Text"),
        "tax": SimpleNamespace(fieldtype="Float"),
        "tax_words": SimpleNamespace(fieldtype="Data"),
        "notes": SimpleNamespace(fieldtype="Small Text"),
    }

    def get_field(self, fieldname):
        return self.fields.get(fieldname)


class FakeDoc(SimpleNamespace):
    def get(self, fieldname, default=None):
        return getattr(self, fieldname, default)


PAIRS = [{"source_field": "amount", "target_field": "amount_words"}]


class TestNumberToWordsFieldPairs(unittest.TestCase):
    def test_validates_multiple_declarative_pairs(self):
        from print_designer.utils.number_to_words_fields import (
            validate_number_to_words_pairs,
        )

        pairs = [
            {"source_field": "amount", "target_field": "amount_words"},
            {"source_field": "tax", "target_field": "tax_words"},
        ]

        self.assertEqual(validate_number_to_words_pairs(FakeMeta(), pairs), pairs)

    def test_rejects_invalid_field_pairs(self):
        from print_designer.utils.number_to_words_fields import (
            validate_number_to_words_pairs,
        )

        pairs = [
            {"source_field": "missing", "target_field": "amount_words"},
            {"source_field": "amount", "target_field": "missing"},
            {"source_field": "amount", "target_field": "amount"},
            {"source_field": "notes", "target_field": "amount_words"},
            {"source_field": "amount", "target_field": "tax"},
        ]

        self.assertEqual(validate_number_to_words_pairs(FakeMeta(), pairs), [])

    @patch("print_designer.utils.number_to_words_fields.thai_money_in_words")
    def test_thai_render_replaces_stored_english_on_temporary_doc(self, thai_words):
        from print_designer.utils.number_to_words_fields import (
            apply_number_to_words_pairs,
        )

        thai_words.return_value = "หนึ่งร้อยบาทถ้วน"
        doc = FakeDoc(
            amount=100,
            amount_words="THB One Hundred only.",
            currency="THB",
        )

        values = apply_number_to_words_pairs(
            doc,
            FakeMeta(),
            PAIRS,
            language="th",
        )

        self.assertEqual(values, {"amount_words": "หนึ่งร้อยบาทถ้วน"})
        self.assertEqual(doc.amount_words, "หนึ่งร้อยบาทถ้วน")
        thai_words.assert_called_once_with(100)

    def test_empty_source_clears_temporary_target(self):
        from print_designer.utils.number_to_words_fields import (
            apply_number_to_words_pairs,
        )

        doc = FakeDoc(amount=None, amount_words="old", currency="THB")

        values = apply_number_to_words_pairs(
            doc,
            FakeMeta(),
            PAIRS,
            language="th",
        )

        self.assertEqual(values, {"amount_words": ""})
        self.assertEqual(doc.amount_words, "")


if __name__ == "__main__":
    unittest.main()
