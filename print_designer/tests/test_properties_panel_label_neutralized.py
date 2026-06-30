"""Regression test: PropertiesPanelState must not silently overwrite a user's
column.label override when the Table field is re-selected.

The original "habit" code was:

    col.label =
        col.dynamicContent[0].label ||
        col.dynamicContent[0].fieldname;

…inside the `onChangeCallback` of the Table field. It pulled the label from
`frappe.get_user_settings(doctype, "GridView")[table.options]` and slammed it
onto every column on every table re-selection, wiping anything the user had
typed in the column header input (e.g. Thai "ลำดับที่" → "sequence").

The user now types the column header directly in the properties panel, so the
guard simply asserts that this overwrite no longer happens.
"""

import unittest
from pathlib import Path

PROPERTIES_PANEL_STATE = (
    Path(__file__).parents[1] / "public/js/print_designer/PropertiesPanelState.js"
)


class TestPropertiesPanelLabelNeutralized(unittest.TestCase):
    def test_does_not_overwrite_col_label_from_dynamic_content(self):
        source = PROPERTIES_PANEL_STATE.read_text()

        self.assertNotIn(
            "col.dynamicContent[0].label",
            source,
            "PropertiesPanelState still contains `col.dynamicContent[0].label` — "
            "this is the overwrite path that wipes user-typed column headers "
            "(e.g. Thai 'ลำดับที่' → 'sequence') on every Table re-selection.",
        )

    def test_does_not_assign_col_label_to_fieldname_fallback(self):
        source = PROPERTIES_PANEL_STATE.read_text()

        self.assertNotIn(
            "col.dynamicContent[0].fieldname",
            source,
            "PropertiesPanelState still falls back to `col.dynamicContent[0]"
            ".fieldname` for col.label — same overwrite path, just less visible.",
        )

    def test_dynamic_content_setup_is_still_intact(self):
        """The non-label parts of the table-reselect handler must remain so
        that re-selecting a table still wires up child DocFields correctly.
        """
        source = PROPERTIES_PANEL_STATE.read_text()

        # Re-selecting a table should still bind dynamic content for each
        # existing column.
        self.assertIn("col.dynamicContent = [", source)
        self.assertIn('dc.tableName = currentEL["table"].fieldname', source)


if __name__ == "__main__":
    unittest.main()
