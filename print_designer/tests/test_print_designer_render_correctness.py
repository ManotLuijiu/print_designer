"""Regression tests for two bugs observed on the Receipt design:

1. Custom fields whose values are null/empty on the live document were
   rendered as literal `{{ fieldname }}` Jinja templates instead of empty.

2. The footer wrapper correctly anchored at the bottom of the page after
   the user changed Page Settings > Footer Height, but the footer CHILDREN
   kept their old drag positions — so the printed page showed an empty
   wrapper at the bottom and the actual footer items floating in the
   upper-middle area.
"""

import unittest
from pathlib import Path

UTILS_JS = Path(__file__).parents[1] / "public/js/print_designer/utils.js"
ELEMENT_STORE = Path(__file__).parents[1] / "public/js/print_designer/store/ElementStore.js"


class TestPrintDesignerEmptyFieldsKeepJinjaPlaceholder(unittest.TestCase):
    """Empty doc fields must keep the ``{{ fieldname }}`` Jinja placeholder so:

    - the editor's Custom Data preview shows the wired-up field reference
      (instead of an empty area), and
    - the Jinja print pipeline can substitute the actual value at print
      time when the doc is loaded.
    """

    def test_dynamic_text_fallback_uses_jinja_placeholder(self):
        source = UTILS_JS.read_text()
        block = source[
            source.index("export const getFormattedValue") : source.index(
                "export const updateDynamicData"
            )
        ]
        self.assertIn(
            "`{{ ${field.fieldname} }}`",
            block,
            "getFormattedValue lost the dynamic-text `{{ fieldname }}` "
            "Jinja placeholder fallback — empty doc fields will no longer "
            "show the wired-up field reference in the editor preview or "
            "the print output.",
        )

    def test_default_case_in_switch_uses_jinja_placeholder(self):
        source = UTILS_JS.read_text()
        idx = source.index("switch (field.fieldname)")
        block = source[idx : idx + 1000]
        self.assertIn(
            "`{{ ${field.fieldname} }}`",
            block,
            "The fall-through `default` case in the value-unavailable "
            "switch should fall back to a `{{ fieldname }}` Jinja "
            "placeholder, not an empty string.",
        )

    def test_image_attach_types_return_null_not_placeholder(self):
        """Image / Attach Image fields must remain `null` so the editor
        doesn't render a literal `{{ fieldname }}` where an image should
        go."""
        source = UTILS_JS.read_text()
        block = source[
            source.index("export const getFormattedValue") : source.index(
                "export const updateDynamicData"
            )
        ]
        self.assertRegex(
            block,
            r'\["Image, Attach Image"\]\.indexOf\(field\.fieldtype\)\s*!=\s*-1\s*\?\s*null\s*:\s*`\{\{ \$\{field\.fieldname\} \}\}`',
            "Image / Attach Image fields must keep the `null` branch of "
            "the ternary so the editor doesn't try to render a placeholder "
            "where an image belongs.",
        )


class TestPrintDesignerFooterAnchorsToBottom(unittest.TestCase):
    """Bug 2: footer wrapper was anchored correctly, but its children were
    not — so the printed footer items appeared mid-page instead of at the
    bottom. ``alignFooterToBottom`` is the new helper that snaps them.
    """

    def test_align_footer_to_bottom_action_exists(self):
        source = ELEMENT_STORE.read_text()
        self.assertIn(
            "alignFooterToBottom",
            source,
            "ElementStore needs an alignFooterToBottom action that "
            "translates wrapper children to the wrapper's bottom edge.",
        )

    def test_align_helper_iterates_wrapper_children(self):
        source = ELEMENT_STORE.read_text()
        helper_idx = source.index("alignFooterToBottom(wrapper)")
        block = source[helper_idx : helper_idx + 2000]
        self.assertIn(
            "wrapper.childrens",
            block,
            "alignFooterToBottom must operate on wrapper.childrens.",
        )
        self.assertIn(
            ".startY =",
            block,
            "alignFooterToBottom must adjust each child's startY.",
        )

    def test_load_elements_calls_align_for_footer(self):
        """``loadElements`` must re-snap the footer cluster when a design is
        loaded, so a stale saved design is normalised to its Page Settings
        rather than its last drag.
        """
        source = ELEMENT_STORE.read_text()
        load_idx = source.index("async loadElements(printDesignName)")
        block = source[load_idx : load_idx + 5000]
        self.assertIn(
            "this.alignFooterToBottom",
            block,
            "loadElements must invoke alignFooterToBottom on the footer wrapper.",
        )

    def test_align_helper_skips_when_wrapper_or_children_missing(self):
        source = ELEMENT_STORE.read_text()
        helper_idx = source.index("alignFooterToBottom(wrapper)")
        block = source[helper_idx : helper_idx + 1500]
        self.assertIn("!wrapper", block)
        self.assertIn("!wrapper.childrens", block)
        self.assertIn("wrapperHeight <= 0", block)

    def test_align_helper_uses_wrapper_height_not_page_bottom(self):
        """Guard against the bug that translated children past the page edge.

        Children's ``startY`` is wrapper-relative (the wrapper rectangle is
        the only positioned ancestor). Anchoring them to the page bottom
        (i.e. ``wrapper.startY + wrapperHeight``) would push the cluster off
        the page entirely. The fix must translate by
        ``wrapperHeight - max_child_bottom`` so the cluster's bottom lands on
        the wrapper's bottom inside the wrapper's own coordinate system.
        """
        source = ELEMENT_STORE.read_text()
        helper_idx = source.index("alignFooterToBottom(wrapper)")
        block = source[helper_idx : helper_idx + 1500]
        self.assertNotIn(
            "wrapperBottom",
            block,
            "alignFooterToBottom must not compute a page-bottom target; "
            "children's startY is wrapper-relative.",
        )
        self.assertIn(
            "wrapperHeight -",
            block,
            "alignFooterToBottom must compute delta as `wrapperHeight - "
            "maxChildBottom` to anchor inside the wrapper.",
        )


if __name__ == "__main__":
    unittest.main()
