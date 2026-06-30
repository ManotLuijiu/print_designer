"""Regression tests for the Print-Preview-side footer anchor.

These guard ``print_designer/pdf.py::_anchor_footer_to_bottom`` and its
call site in ``_prepare_print_designer_context`` so the Jinja-template
print preview (which bypasses Pinia and reads saved ``startY`` values
directly) places the footer cluster at the bottom of the page —
matching the editor's behaviour added by ``alignFooterToBottom`` in
``ElementStore.js``.
"""

import ast
import re
import unittest
from pathlib import Path

PDF_PY = Path(__file__).parents[1] / "pdf.py"


def _load_source():
    return PDF_PY.read_text()


def _sim_anchor(footer, page_height, footer_height):
    """In-process mirror of the algorithm under test.

    Lives here so we can exercise edge cases (empty footer, malformed
    children, near-zero deltas, regression against the buggy
    page-bottom formula) without importing pdf.py — that module pulls
    in Frappe and isn't importable in a bare ``python -m unittest``.
    """
    if not footer or len(footer) == 0:
        return
    wrapper = footer[0]
    children = wrapper.get("childrens") if isinstance(wrapper, dict) else None
    if not children:
        return
    wrapper_start_y = wrapper.get("startY")
    wrapper_height = wrapper.get("height") or 0
    if wrapper_start_y is None or wrapper_height <= 0:
        return
    max_child_bottom = max((c.get("startY") or 0) + (c.get("height") or 0) for c in children)
    delta = wrapper_height - max_child_bottom
    if abs(delta) < 0.5:
        return
    for child in children:
        child["startY"] = (child.get("startY") or 0) + delta
        if isinstance(child.get("pageY"), (int, float)):
            child["pageY"] = child["pageY"] + delta


class TestFooterAnchorInPdfPy(unittest.TestCase):
    def test_anchor_helper_defined(self):
        source = _load_source()
        self.assertIn(
            "def _anchor_footer_to_bottom(",
            source,
            "pdf.py must define `_anchor_footer_to_bottom` so the Jinja "
            "print preview places the footer at the bottom of the page.",
        )

    def test_anchor_helper_signature(self):
        source = _load_source()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_anchor_footer_to_bottom":
                args = [a.arg for a in node.args.args]
                self.assertEqual(
                    args,
                    ["footer", "page_height", "footer_height"],
                    f"_anchor_footer_to_bottom signature is {args}; "
                    "expected ('footer', 'page_height', 'footer_height').",
                )
                return
        self.fail("_anchor_footer_to_bottom not found after parsing pdf.py")

    def test_anchor_uses_wrapper_height_not_page_bottom(self):
        """Guard against the bug that pushed children off the page.

        The buggy version computed ``delta = wrapper_start_y + wrapper_height -
        max_child_bottom``, which doubles the page height into the translation
        when children's ``startY`` is already wrapper-relative. The fix must
        compute ``delta = wrapper_height - max_child_bottom``.
        """

        source = _load_source()
        match = re.search(
            r"def _anchor_footer_to_bottom\([^)]*\):\s*(?P<body>.*?)(?:\n\ndef |\Z)",
            source,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(match, "could not isolate the body of _anchor_footer_to_bottom")
        body = match.group("body")
        self.assertNotIn(
            "wrapper_bottom",
            body,
            "_anchor_footer_to_bottom must NOT compute wrapper_bottom = "
            "wrapper_start_y + wrapper_height; children's startY is "
            "wrapper-relative so the target is wrapper_height alone.",
        )
        self.assertIn(
            "wrapper_height -",
            body,
            "_anchor_footer_to_bottom must use `wrapper_height - "
            "max_child_bottom` to anchor the cluster inside the wrapper.",
        )

    def test_anchor_called_in_print_designer_context(self):
        source = _load_source()
        idx = source.index("def _prepare_print_designer_context")
        slice = source[idx:]
        end_marker = "\n\ndef "
        body_end = slice.find(end_marker, slice.index("(") + 1)
        body = slice[: body_end if body_end > 0 else len(slice)]
        self.assertIn(
            "_anchor_footer_to_bottom(",
            body,
            "_prepare_print_designer_context must call _anchor_footer_to_bottom "
            "before passing footerElement to the Jinja template.",
        )

    def test_anchor_helper_handles_empty_and_malformed_inputs(self):
        # Case 1: empty footer → no-op, must not throw.
        _sim_anchor([], 1122.52, 188.97)
        _sim_anchor(None, 1122.52, 188.97)

        # Case 2: wrapper height 0 → no-op, must not throw.
        _sim_anchor(
            [
                {
                    "startY": 933.55,
                    "height": 0,
                    "childrens": [
                        {"startY": 30, "height": 28, "pageY": 130},
                    ],
                }
            ],
            1122.52,
            188.97,
        )

        # Case 3: typical case — children at top of wrapper, anchor to
        # bottom. Children's startY are wrapper-relative; delta should
        # be wrapper_height - max_child_bottom (NOT page_bottom - max).
        footer = [
            {
                "startY": 933.55,
                "height": 188.97,
                "childrens": [
                    {"startY": 30.14, "height": 28.5, "pageY": 130},
                    {"startY": 47.22, "height": 92, "pageY": 147},
                    {"startY": 147.03, "height": 29.89, "pageY": 260},
                ],
            }
        ]
        _sim_anchor(footer, 1122.52, 188.97)
        # bottoms: 58.64, 139.22, 176.92 → max 176.92
        # delta = 188.97 - 176.92 = 12.05
        self.assertAlmostEqual(footer[0]["childrens"][0]["startY"], 42.19, places=2)
        self.assertAlmostEqual(footer[0]["childrens"][1]["startY"], 59.27, places=2)
        self.assertAlmostEqual(footer[0]["childrens"][2]["startY"], 159.08, places=2)
        self.assertAlmostEqual(footer[0]["childrens"][0]["pageY"], 142.05, places=2)

        # Case 4: children already aligned → delta near 0, no change.
        aligned = [
            {
                "startY": 933.55,
                "height": 188.97,
                "childrens": [
                    {"startY": 159.0, "height": 30},
                    {"startY": 159.0, "height": 30},
                ],
            }
        ]
        _sim_anchor(aligned, 1122.52, 188.97)
        self.assertAlmostEqual(aligned[0]["childrens"][0]["startY"], 159.0, places=4)

        # Case 5: regression — the buggy formula would translate
        # children past the page edge. With the fixed formula every
        # child must land inside the wrapper (startY < wrapper_height).
        footer2 = [
            {
                "startY": 933.55,
                "height": 188.97,
                "childrens": [
                    {"startY": 30, "height": 28},
                    {"startY": 50, "height": 80},
                    {"startY": 120, "height": 30},
                ],
            }
        ]
        _sim_anchor(footer2, 1122.52, 188.97)
        for child in footer2[0]["childrens"]:
            self.assertLess(
                child["startY"],
                188.97,
                f"child startY={child['startY']} must stay inside the wrapper (height=188.97)",
            )
            self.assertGreaterEqual(child["startY"], 0)


if __name__ == "__main__":
    unittest.main()
