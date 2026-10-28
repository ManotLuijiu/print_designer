"""Regression tests for the Chrome header/footer page script.

Frappe's Chrome generator replicates the header/footer once per body page by
calling ``clone_and_update`` inside the header/footer page.  That function is
defined in ``update_page_no.js``.

Before the fix the script was only injected by the Print Designer PDF
generator, so with the Frappe generator the call silently failed: the
header/footer PDF stayed a single page and merging it with a multi page body
(e.g. a document printed in two copies) failed with::

    IndexError: Sequence index out of range

The script is now injected into the header/footer page for every generator and
it must be safe to load more than once, because the Print Designer generator
injects it into the page head as well.
"""

import unittest
from pathlib import Path

from bs4 import BeautifulSoup

UPDATE_PAGE_NO_JS = (
    Path(__file__).parents[1] / "print_designer/page/print_designer/update_page_no.js"
)


class TestUpdatePageNoScript(unittest.TestCase):
    def test_script_is_loaded_once_even_if_injected_twice(self):
        source = UPDATE_PAGE_NO_JS.read_text()

        self.assertIn("window.clone_and_update", source)
        self.assertIn("window.update_page_no", source)
        self.assertIn("if (window.clone_and_update && window.update_page_no)", source)

    def test_script_does_not_use_top_level_const_declarations(self):
        """Top level `const` would raise on a second load of the script."""
        source = UPDATE_PAGE_NO_JS.read_text()

        self.assertNotIn("\nconst ", source)

    def test_script_exposes_the_functions_frappe_calls(self):
        source = UPDATE_PAGE_NO_JS.read_text()

        self.assertIn("const clone_and_update", source)
        self.assertIn("const update_page_no", source)


class TestHeaderFooterScriptInjection(unittest.TestCase):
    def test_script_is_added_to_the_head_of_the_header_footer_page(self):
        from print_designer.pdf import add_update_page_no_script

        soup = BeautifulSoup("<html><head></head><body></body></html>", "html.parser")

        head = add_update_page_no_script(soup, [])

        self.assertEqual(len(head), 1)
        script = head[0]
        self.assertEqual(script.name, "script")
        rendered = str(script)
        self.assertIn("clone_and_update", rendered)
        # the javascript must not be escaped, otherwise the page script breaks
        self.assertIn("=>", rendered)
        self.assertIn("&&", rendered)

    def test_existing_head_content_is_kept(self):
        from print_designer.pdf import add_update_page_no_script

        soup = BeautifulSoup("<html><head></head><body></body></html>", "html.parser")
        style = soup.new_tag("style")
        style.string = "body { margin: 0; }"

        head = add_update_page_no_script(soup, [style])

        self.assertEqual(len(head), 2)
        self.assertEqual(head[0].name, "style")
        self.assertEqual(head[1].name, "script")

    def test_header_footer_hook_injects_the_script(self):
        from print_designer import pdf

        source = Path(pdf.__file__).read_text()

        self.assertIn("head = add_update_page_no_script(soup, head)", source)


if __name__ == "__main__":
    unittest.main()
