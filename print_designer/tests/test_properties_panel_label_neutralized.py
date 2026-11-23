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

import re
import unittest
from pathlib import Path

PROPERTIES_PANEL_STATE = (
    Path(__file__).parents[1] / "public/js/print_designer/PropertiesPanelState.js"
)


def _the_source_without_its_layout() -> str:
    """The source of the panel with every bit of whitespace taken out.

    The test reads the shape of the code, not the way it is laid out: a
    formatter is free to break a statement over several lines, or to space
    the brackets of an index differently, without changing what the code
    does.
    """
    source = PROPERTIES_PANEL_STATE.read_text()
    return re.sub(r"\s+", "", source)


class TestPropertiesPanelLabelNeutralized(unittest.TestCase):
    def test_does_not_overwrite_col_label_from_dynamic_content(self):
        source = _the_source_without_its_layout()

        self.assertNotIn(
            "col.dynamicContent[0].label",
            source,
            "PropertiesPanelState still contains `col.dynamicContent[0].label` — "
            "this is the overwrite path that wipes user-typed column headers "
            "(e.g. Thai 'ลำดับที่' → 'sequence') on every Table re-selection.",
        )

    def test_does_not_assign_col_label_to_fieldname_fallback(self):
        source = _the_source_without_its_layout()

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
        source = _the_source_without_its_layout()

        # Re-selecting a table should still bind dynamic content for each
        # existing column.
        self.assertIn("col.dynamicContent=[", source)
        self.assertIn(
            'dc.tableName=currentEL["table"].fieldname',
            source,
            "the dynamic content of a column is not bound to the selected "
            "table any more",
        )


if __name__ == "__main__":
    unittest.main()
