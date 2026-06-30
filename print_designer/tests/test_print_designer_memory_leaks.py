"""Regression test for the RAM growth that the Print Designer suffered when
stores were pushed into on every load instead of replaced.

The original code:

  headers.forEach((header) => { this.Headers.push(header); });   # append
  footers.forEach((footer) => { this.Footers.push(footer); });   # append
  MainStore.metaFields.push({ ...obj });                          # append
  MainStore.dynamicData.push(...element.dynamicContent);         # append

...without a clearing step before the push, so each call to loadElements /
fetchMeta doubled or worse the in-memory design footprint. RAM grew
unboundedly until the host machine hit OOM.

This test asserts that every such accumulation is preceded by a clearing of
the destination array, and that the relevant store-state field declarations
exist so the pattern stays grep-able.
"""

import re
import unittest
from pathlib import Path

ELEMENT_STORE = Path(__file__).parents[1] / "public/js/print_designer/store/ElementStore.js"
FETCH_META_AND_DATA = (
    Path(__file__).parents[1] / "public/js/print_designer/store/fetchMetaAndData.js"
)


def _slice(source, start_marker, length=4000):
    idx = source.find(start_marker)
    if idx < 0:
        return ""
    return source[idx : idx + length]


class TestPrintDesignerMemoryLeaks(unittest.TestCase):
    # ---------- ElementStore.loadElements ----------

    def test_load_elements_clears_headers_before_push(self):
        source = ELEMENT_STORE.read_text()
        block = _slice(source, "async loadElements(printDesignName)")

        push_match = re.search(r"this\.Headers\.push\(", block)
        if push_match is None:
            self.fail("Headers.push not found in loadElements")

        clear_match = re.search(r"this\.Headers\.length\s*=\s*0", block)
        if clear_match is None:
            self.fail(
                "loadElements pushes into Headers without clearing first - "
                "every reload duplicates the header set in memory."
            )

        self.assertLess(
            clear_match.start(),
            push_match.start(),
            "Headers.length = 0 must come BEFORE Headers.push in loadElements.",
        )

    def test_load_elements_clears_footers_before_push(self):
        source = ELEMENT_STORE.read_text()
        block = _slice(source, "async loadElements(printDesignName)")

        push_match = re.search(r"this\.Footers\.push\(", block)
        if push_match is None:
            self.fail("Footers.push not found in loadElements")

        clear_match = re.search(r"this\.Footers\.length\s*=\s*0", block)
        if clear_match is None:
            self.fail(
                "loadElements pushes into Footers without clearing first - "
                "every reload duplicates the footer set in memory."
            )

        self.assertLess(
            clear_match.start(),
            push_match.start(),
            "Footers.length = 0 must come BEFORE Footers.push in loadElements.",
        )

    def test_load_elements_clears_dynamic_data(self):
        source = ELEMENT_STORE.read_text()
        block = _slice(source, "async loadElements(printDesignName)")

        # loadElements must explicitly reset MainStore.dynamicData before the
        # childrensLoad calls inside it (re)push dynamicContent entries.
        self.assertRegex(
            block,
            r"MainStore\.dynamicData\.length\s*=\s*0",
            "loadElements must reset MainStore.dynamicData before repopulating; "
            "otherwise dynamicContent gets duplicated on every reload.",
        )

    # ---------- fetchMetaAndData.fetchMeta ----------

    def test_fetch_meta_clears_metafields_before_push(self):
        source = FETCH_META_AND_DATA.read_text()
        block = _slice(source, "export const fetchMeta")

        push_match = re.search(r"MainStore\.metaFields\.push\(", block)
        if push_match is None:
            self.fail("metaFields.push not found in fetchMeta")

        clear_match = re.search(r"MainStore\.metaFields\.length\s*=\s*0", block)
        if clear_match is None:
            self.fail(
                "fetchMeta pushes into metaFields without clearing first - "
                "every visit duplicates the doctype meta in memory."
            )

        self.assertLess(
            clear_match.start(),
            push_match.start(),
            "metaFields.length = 0 must come BEFORE metaFields.push in fetchMeta.",
        )

    # ---------- defensive guards on the store declarations ----------

    def test_headers_and_footers_state_fields_exist(self):
        """Guard against someone renaming the state fields and accidentally
        hiding the leak again. The fix targets these exact names."""
        source = ELEMENT_STORE.read_text()

        self.assertRegex(source, r"\bHeaders\s*:\s*new\s+Array\s*\(")
        self.assertRegex(source, r"\bFooters\s*:\s*new\s+Array\s*\(")


if __name__ == "__main__":
    unittest.main()
