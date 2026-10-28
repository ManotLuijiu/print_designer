"""Regression tests for the Print Designer preview page layout.

The screen preview renders the designer page as a fixed sheet:

* the header is absolutely positioned at the top of the page,
* the footer is absolutely positioned at the bottom of the page,
* the body occupies the band between them.

The body band must clip its content. With ``overflow: visible`` a body that is
taller than the band (a Sales Invoice with many rows, for example) spilled out
of the band and was painted underneath the absolutely positioned footer, so the
footer overlapped the content (reported as "footer overlaps content" in the
preview).

The print media rules must keep the header and the footer static: the Chrome
pipeline renders the header and the footer as separate pages and relies on the
static flow to measure their height, and the body page has to be able to flow
over several pages.
"""

import unittest

import frappe

STYLES_TEMPLATE = "print_designer/page/print_designer/jinja/macros/styles.html"


def render_styles():
    settings = {
        "page": {
            "width": 210,
            "height": 297,
            "marginTop": 0,
            "marginBottom": 0,
            "marginLeft": 0,
            "marginRight": 0,
            "headerHeightWithMargin": 80,
            "footerHeightWithMargin": 45,
        },
        "PDFPrintDPI": 96,
    }
    env = frappe.get_jenv()
    template = env.from_string(
        "{% from '" + STYLES_TEMPLATE + "' import render_styles with context %}"
        "{{ render_styles(settings) }}"
    )
    return template.render(settings=settings)


class TestPreviewLayoutCss(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = render_styles()
        screen, _, print_media = cls.css.partition("@media print")
        cls.screen = screen
        cls.print_media = print_media

    def test_styles_are_rendered(self):
        self.assertIn("#__print_designer", self.css)
        self.assertIn("@media screen", self.css)
        self.assertIn("@media print", self.css)

    def test_body_band_clips_its_content_in_screen_media(self):
        """The body band must not let the content spill under the footer."""
        self.assertIn("overflow: auto !important", self.screen)
        self.assertNotIn("overflow: visible !important", self.screen)

    def test_body_band_is_positioned_between_header_and_footer(self):
        self.assertIn(
            "height: calc(100% - var(--header-height) - var(--footer-height))", self.screen
        )
        self.assertIn("top: var(--header-height)", self.screen)

    def test_header_and_footer_stay_at_the_page_edges_in_screen_media(self):
        self.assertIn("#header-html", self.screen)
        self.assertIn("#footer-html", self.screen)
        self.assertIn("position: absolute !important", self.screen)
        self.assertIn("bottom: 0 !important", self.screen)

    def test_print_media_keeps_header_and_footer_static(self):
        """The Chrome pipeline renders header/footer as separate pages and
        measures their height from the static flow."""
        self.assertIn("#header-html, #footer-html", self.print_media)
        self.assertIn("position: static !important", self.print_media)

    def test_page_box_uses_the_designer_page_size(self):
        self.assertIn("--page-width:", self.screen)
        self.assertIn("--page-height:", self.screen)


if __name__ == "__main__":
    unittest.main()
