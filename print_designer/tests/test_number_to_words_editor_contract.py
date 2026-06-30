import unittest
from pathlib import Path


APP = Path(__file__).parents[1]
MAIN_STORE = APP / "public/js/print_designer/store/MainStore.js"
ELEMENT_STORE = APP / "public/js/print_designer/store/ElementStore.js"
FETCH_META = APP / "public/js/print_designer/store/fetchMetaAndData.js"
PROPERTIES_PANEL = APP / "public/js/print_designer/PropertiesPanelState.js"


class TestNumberToWordsEditorContract(unittest.TestCase):
    def test_settings_persist_number_to_words_pairs(self):
        self.assertIn(
            "numberToWordsFieldPairs: MainStore.numberToWordsFieldPairs",
            ELEMENT_STORE.read_text(),
        )

    def test_loaded_settings_restore_pairs(self):
        self.assertIn("settings.numberToWordsFieldPairs || []", ELEMENT_STORE.read_text())

    def test_fetch_doc_overlays_preview_values(self):
        source = FETCH_META.read_text()
        self.assertIn("get_number_to_words_preview", source)
        self.assertIn("Object.assign(doc, previewValues)", source)

    def test_page_settings_exposes_pair_dialog(self):
        source = PROPERTIES_PANEL.read_text()
        self.assertIn('fieldname: "source_field"', source)
        self.assertIn('fieldname: "target_field"', source)
        self.assertIn('fieldname: "currency_field"', source)

    def test_main_store_declares_pair_state(self):
        self.assertIn("numberToWordsFieldPairs: []", MAIN_STORE.read_text())


if __name__ == "__main__":
    unittest.main()
