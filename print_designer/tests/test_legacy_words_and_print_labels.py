"""Regression coverage for saved WHT bindings and already-Thai print labels."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from jinja2 import Environment, FileSystemLoader

from print_designer.utils.number_to_words_fields import (
    apply_number_to_words_pairs,
    get_primary_amount,
    validate_number_to_words_pairs,
)
from print_designer.utils.print_labels import translate_print_label


class Doc(SimpleNamespace):
    def get(self, key, default=None):
        return getattr(self, key, default)


class Meta:
    def __init__(self, fields):
        self.fields = fields

    def get_field(self, fieldname):
        fieldtype = self.fields.get(fieldname)
        return SimpleNamespace(fieldtype=fieldtype) if fieldtype else None


PAIR = {
    "source_field": "net_total_after_wht",
    "target_field": "net_total_after_wht_in_words",
}


def test_saved_wht_pair_uses_renamed_net_amount_and_exposes_legacy_binding():
    meta = Meta({
        "pd_custom_net_total_after_wht": "Currency",
        "pd_custom_net_total_after_wht_words": "Data",
        "grand_total": "Currency",
    })
    doc = Doc(pd_custom_net_total_after_wht=291000, grand_total=300000, currency="THB")
    result = apply_number_to_words_pairs(doc, meta, [PAIR], "th")
    expected = "สองแสนเก้าหมื่นหนึ่งพันบาทถ้วน"
    assert result["net_total_after_wht_in_words"] == expected
    assert result["pd_custom_net_total_after_wht_words"] == expected
    assert doc.get("net_total_after_wht_in_words") == expected
    assert get_primary_amount(doc, meta, [PAIR]) == 291000
    assert PAIR["source_field"] == "net_total_after_wht"  # saved design is unchanged


def test_existing_old_fields_are_not_replaced_by_new_fields():
    meta = Meta({
        "net_total_after_wht": "Currency",
        "net_total_after_wht_in_words": "Data",
        "pd_custom_net_total_after_wht": "Currency",
        "pd_custom_net_total_after_wht_words": "Data",
    })
    assert validate_number_to_words_pairs(meta, [PAIR]) == [PAIR]


def test_missing_or_incompatible_replacements_are_still_rejected():
    assert validate_number_to_words_pairs(Meta({}), [PAIR]) == []
    meta = Meta({
        "pd_custom_net_total_after_wht": "Data",
        "pd_custom_net_total_after_wht_words": "Currency",
    })
    assert validate_number_to_words_pairs(meta, [PAIR]) == []


@pytest.mark.parametrize("label", ["จำนวน", "วันที่ครบกำหนด", "ปริมาณ"])
def test_thai_output_does_not_translate_saved_thai_back_to_english(label):
    with patch("frappe._", return_value="English") as translate:
        assert translate_print_label(label, "th") == label
        translate.assert_not_called()


def test_english_source_headers_translate_through_the_same_helper():
    translations = {
        "Quantity": "ปริมาณ", "Due Date": "วันที่ครบกำหนด",
        "จำนวน": "Quantity", "วันที่ครบกำหนด": "Due Date",
    }
    macros = Path(__file__).parents[1] / "print_designer/page/print_designer/jinja/macros"
    env = Environment(loader=FileSystemLoader(macros))
    template = env.from_string(
        '{% from "table.html" import table with context %}{{ table(element, {}, "auto") }}'
    )
    with patch("frappe._", side_effect=lambda text, **kwargs: translations.get(text, text)):
        html = template.render(
            element={
                "heightType": "auto", "table": {"fieldname": "items"},
                "startX": 0, "startY": 0, "width": 600, "classes": [],
                "columns": [{"label": label} for label in
                            ("Quantity", "Due Date", "จำนวน", "วันที่ครบกำหนด")],
            },
            settings={}, doc={"items": []}, convert_css=lambda _: "",
            translate_table_column_label=lambda value: translate_print_label(value, "th"),
        )
    assert "Quantity" not in html
    assert "Due Date" not in html
    assert "ปริมาณ" in html
    assert "จำนวน" in html
    assert html.count("วันที่ครบกำหนด") == 2
