import unittest
from pathlib import Path

APP_HEADER = Path(__file__).parents[1] / "public/js/print_designer/components/layout/AppHeader.vue"
APP_CANVAS = Path(__file__).parents[1] / "public/js/print_designer/components/layout/AppCanvas.vue"


class TestPrintDesignerHeaderSource(unittest.TestCase):
    def test_header_does_not_show_beta_badge(self):
        source = APP_HEADER.read_text()

        self.assertNotIn(">Beta</span>", source)

    def test_header_has_horizontal_padding(self):
        source = APP_HEADER.read_text()

        self.assertIn("padding: 0 16px;", source)

    def test_header_spans_full_parent_width_with_left_right_offsets(self):
        source = APP_HEADER.read_text()

        self.assertIn("position: absolute;", source)
        self.assertIn("top: 0;", source)
        self.assertIn("left: 0;", source)
        self.assertIn("right: 0;", source)

    def test_header_does_not_use_js_positioning(self):
        source = APP_HEADER.read_text()

        self.assertNotIn("getElementById", source)
        self.assertNotIn("getBoundingClientRect", source)
        self.assertNotIn("ResizeObserver", source)
        self.assertNotIn(':style="headerStyle"', source)

    def test_header_no_longer_includes_logo_image(self):
        source = APP_HEADER.read_text()

        self.assertNotIn("print-designer-logo.svg", source)
        self.assertNotIn("app-icon", source)

    def test_header_no_longer_renders_logout_icon(self):
        source = APP_HEADER.read_text()

        self.assertNotIn("es-line-log-out", source)

    def test_header_does_not_set_background_color(self):
        source = APP_HEADER.read_text()

        self.assertNotIn("background-color", source)
        self.assertNotIn("--navbar-bg", source)

    def test_canvas_renders_header_inside_print_format_container(self):
        source = APP_CANVAS.read_text()

        self.assertIn('import AppHeader from "./AppHeader.vue"', source)
        self.assertIn('<AppHeader :print_format_name="print_format_name"', source)


if __name__ == "__main__":
    unittest.main()
