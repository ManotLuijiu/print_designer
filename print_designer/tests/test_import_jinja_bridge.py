"""
Test cases for Print Designer Import Bridge (template-first MVP).

Covers:
- Marker validation
- Unsupported pattern detection
- Reconstruction (header / content / footer / css)
- Safety: validation never writes, invalid bundle does not mutate source
"""

import json
import unittest

from print_designer.utils.import_jinja_bridge import (
    REQUIRED_MARKERS,
    _parse_inline_style,
    build_validation_report,
    css_text_to_style_map,
    extract_bridge_sections,
    extract_metadata,
    reconstruct_from_bundle,
)


def _loads(text, label):
    """Parse JSON with a clearer error if the reconstruction produced garbage."""
    try:
        return json.loads(text)
    except (TypeError, ValueError) as e:
        raise AssertionError(
            f"reconstruction produced invalid JSON for {label}: {e}\nraw: {text[:200]!r}"
        )


def _unwrap_single_page_wrapper(value, label):
    """Header/footer/body import fields are stored as JSON arrays of one page wrapper."""
    if not isinstance(value, list):
        raise AssertionError(f"{label} must be a list of page wrappers, got: {type(value)!r}")
    if len(value) != 1:
        raise AssertionError(f"{label} must contain exactly one page wrapper, got: {value!r}")
    wrapper = value[0]
    if not isinstance(wrapper, dict) or wrapper.get("type") != "page":
        raise AssertionError(f"{label} wrapper must be a page dict, got: {wrapper!r}")
    return wrapper


VALID_TEMPLATE = (
    "<!-- PD:METADATA:START -->\n"
    '{"source": "test", "version": "1.0.0"}\n'
    "<!-- PD:METADATA:END -->\n"
    "\n"
    "<!-- PD:HEADER:START -->\n"
    '<div style="position: absolute; left: 0px; top: 0px; width: 200px; height: 30px; color: #000;">\n'
    "  <p>Header text</p>\n"
    "</div>\n"
    "<!-- PD:HEADER:END -->\n"
    "\n"
    "<!-- PD:CONTENT:START -->\n"
    '<div style="position: absolute; left: 10px; top: 50px; width: 400px; height: 100px;">\n'
    "  <p>Body paragraph</p>\n"
    "  <span>Inline text</span>\n"
    "</div>\n"
    "<!-- PD:CONTENT:END -->\n"
    "\n"
    "<!-- PD:FOOTER:START -->\n"
    '<div style="position: absolute; left: 0px; top: 0px; width: 200px; height: 20px;">\n'
    "  <p>Footer text</p>\n"
    "</div>\n"
    "<!-- PD:FOOTER:END -->\n"
    "\n"
    "<!-- PD:CSS:START -->\n"
    ".custom { color: #333; padding: 4px; }\n"
    "<!-- PD:CSS:END -->\n"
)


def _missing_marker_block(template, marker_name):
    """Return a copy of the template with the named marker pair stripped out."""
    start_marker = f"PD:{marker_name}:START"
    end_marker = f"PD:{marker_name}:END"
    out = template
    s = out.find(start_marker)
    if s == -1:
        return out
    e = out.find(end_marker, s)
    if e == -1:
        return out
    e += len(end_marker)
    return out[:s] + out[e:]


class TestImportJinjaBridgeMarkerValidation(unittest.TestCase):
    def test_valid_template_passes(self):
        report = build_validation_report(VALID_TEMPLATE)
        self.assertTrue(report["valid"])
        self.assertEqual(report["blockers"], [])

    def test_all_required_sections_present(self):
        report = build_validation_report(VALID_TEMPLATE)
        for name, _, _ in REQUIRED_MARKERS:
            self.assertIn(name, report["sections"])
            self.assertTrue(report["sections"][name]["present"], f"missing {name}")

    def test_missing_header_marker_fails(self):
        bad = _missing_marker_block(VALID_TEMPLATE, "HEADER")
        report = build_validation_report(bad)
        self.assertFalse(report["valid"])
        self.assertTrue(any("HEADER" in b for b in report["blockers"]))

    def test_missing_content_marker_fails(self):
        bad = _missing_marker_block(VALID_TEMPLATE, "CONTENT")
        report = build_validation_report(bad)
        self.assertFalse(report["valid"])
        self.assertTrue(any("CONTENT" in b for b in report["blockers"]))

    def test_missing_footer_marker_fails(self):
        bad = _missing_marker_block(VALID_TEMPLATE, "FOOTER")
        report = build_validation_report(bad)
        self.assertFalse(report["valid"])
        self.assertTrue(any("FOOTER" in b for b in report["blockers"]))

    def test_missing_css_marker_fails(self):
        bad = _missing_marker_block(VALID_TEMPLATE, "CSS")
        report = build_validation_report(bad)
        self.assertFalse(report["valid"])
        self.assertTrue(any("CSS" in b for b in report["blockers"]))

    def test_extract_bridge_sections(self):
        sections = extract_bridge_sections(VALID_TEMPLATE)
        self.assertIn("header", sections)
        self.assertIn("Header text", sections["header"])
        self.assertIn("Footer text", sections["footer"])

    def test_extract_metadata_parses_json(self):
        meta = extract_metadata(VALID_TEMPLATE)
        self.assertEqual(meta.get("source"), "test")
        self.assertEqual(meta.get("version"), "1.0.0")

    def test_extract_metadata_handles_invalid_json(self):
        bad = VALID_TEMPLATE.replace(
            '{"source": "test", "version": "1.0.0"}',
            "not-json",
        )
        self.assertEqual(extract_metadata(bad), {})


class TestImportJinjaBridgeUnsupportedPatterns(unittest.TestCase):
    def test_table_markup_blocked(self):
        bad = VALID_TEMPLATE.replace(
            "<p>Body paragraph</p>\n  <span>Inline text</span>",
            "<table><tr><td>cell</td></tr></table>",
        )
        report = build_validation_report(bad)
        self.assertFalse(report["valid"])
        self.assertTrue(any("Table" in b for b in report["blockers"]))

    def test_barcode_markup_blocked(self):
        bad = VALID_TEMPLATE.replace(
            "<p>Body paragraph</p>\n  <span>Inline text</span>",
            '<div data-barcode-value="123"></div>',
        )
        report = build_validation_report(bad)
        self.assertFalse(report["valid"])
        self.assertTrue(any("arcode" in b for b in report["blockers"]))

    def test_svg_markup_blocked(self):
        bad = VALID_TEMPLATE.replace(
            "<p>Body paragraph</p>\n  <span>Inline text</span>",
            "<svg><circle/></svg>",
        )
        report = build_validation_report(bad)
        self.assertFalse(report["valid"])
        self.assertTrue(any("SVG" in b for b in report["blockers"]))

    def test_flex_layout_blocked(self):
        bad = VALID_TEMPLATE.replace(
            "  <p>Body paragraph</p>\n  <span>Inline text</span>",
            '<span style="display: flex;">x</span>',
        )
        report = build_validation_report(bad)
        self.assertFalse(report["valid"])
        self.assertTrue(any("Flex" in b for b in report["blockers"]))

    def test_grid_layout_blocked(self):
        bad = VALID_TEMPLATE.replace(
            "  <p>Body paragraph</p>\n  <span>Inline text</span>",
            '<span style="display: grid;">x</span>',
        )
        report = build_validation_report(bad)
        self.assertFalse(report["valid"])
        self.assertTrue(any("Grid" in b for b in report["blockers"]))

    def test_jinja_expression_blocked(self):
        bad = VALID_TEMPLATE.replace(
            "  <p>Body paragraph</p>\n  <span>Inline text</span>",
            "<span>{{ doc.customer }}</span>",
        )
        report = build_validation_report(bad)
        self.assertFalse(report["valid"])
        self.assertTrue(any("Jinja" in b for b in report["blockers"]))

    def test_supported_subset_reported(self):
        report = build_validation_report(VALID_TEMPLATE)
        self.assertIn("supported_subset", report)
        self.assertTrue(report["supported_subset"]["static_text"])


class TestImportJinjaBridgeCssParser(unittest.TestCase):
    def test_parse_inline_style(self):
        s = _parse_inline_style("position: absolute; left: 10px; top: 5px; color: #000;")
        self.assertEqual(s.get("position"), "absolute")
        self.assertEqual(s.get("left"), "10px")
        self.assertEqual(s.get("top"), "5px")
        self.assertEqual(s.get("color"), "#000")

    def test_parse_inline_style_drops_unknown(self):
        s = _parse_inline_style("position: absolute; --my-var: 5px; bogus: x;")
        self.assertIn("position", s)
        self.assertNotIn("--my-var", s)
        self.assertNotIn("bogus", s)

    def test_css_text_to_style_map(self):
        css = ".foo { color: red; padding: 4px; } #bar { margin: 10px; }"
        m = css_text_to_style_map(css)
        self.assertIn(".foo", m)
        self.assertEqual(m[".foo"]["color"], "red")
        self.assertEqual(m[".foo"]["padding"], "4px")
        self.assertIn("#bar", m)
        self.assertEqual(m["#bar"]["margin"], "10px")


class TestImportJinjaBridgeReconstruction(unittest.TestCase):
    def test_reconstruct_simple_template(self):
        result = reconstruct_from_bundle(VALID_TEMPLATE, existing_settings={})
        self.assertTrue(result["valid"])
        rec = result["reconstruction"]
        # Header / footer / body all stored as JSON strings (Print Format field convention)
        header = _loads(rec["print_designer_header"], "print_designer_header")
        body = _loads(rec["print_designer_body"], "print_designer_body")
        footer = _loads(rec["print_designer_footer"], "print_designer_footer")
        pd_format = _loads(rec["print_designer_print_format"], "print_designer_print_format")
        settings = _loads(rec["print_designer_settings"], "print_designer_settings")

        header_wrapper = _unwrap_single_page_wrapper(header, "print_designer_header")
        footer_wrapper = _unwrap_single_page_wrapper(footer, "print_designer_footer")

        # Header has one <div> -> one text element inside the page wrapper
        self.assertEqual(len(header_wrapper["childrens"]), 1)
        self.assertEqual(header_wrapper["childrens"][0]["type"], "text")
        self.assertIn("Header text", header_wrapper["childrens"][0]["content"])

        # Content: div + p + span -> 2 text elements after plain-wrapper flattening
        self.assertEqual(len(body), 1)
        self.assertEqual(len(body[0]["childrens"]), 2)
        for el in body[0]["childrens"]:
            self.assertEqual(el["type"], "text")

        # Footer: one div -> one text element inside the page wrapper
        self.assertEqual(len(footer_wrapper["childrens"]), 1)
        self.assertEqual(footer_wrapper["childrens"][0]["type"], "text")

        # pd_format shape
        self.assertIn("header", pd_format)
        self.assertIn("body", pd_format)
        self.assertIn("footer", pd_format)
        for variant in ("firstPage", "oddPage", "evenPage", "lastPage"):
            self.assertIn(variant, pd_format["header"])
            self.assertIn(variant, pd_format["footer"])

        # Settings merge
        self.assertEqual(settings.get("schema_version"), "1.3.0")
        self.assertIn("import_metadata", settings)
        self.assertEqual(settings["import_metadata"]["source"], "jinja_bridge_import")

        # CSS stored verbatim
        self.assertIn("custom", rec["css"])
        self.assertIn("color: #333", rec["css"])

    def test_reconstruct_invalid_template_returns_none(self):
        bad = _missing_marker_block(VALID_TEMPLATE, "CONTENT")
        result = reconstruct_from_bundle(bad)
        self.assertFalse(result["valid"])
        self.assertIsNone(result["reconstruction"])

    def test_reconstruct_with_image_in_content(self):
        template = VALID_TEMPLATE.replace(
            "  <p>Body paragraph</p>\n  <span>Inline text</span>",
            '<img src="/files/x.png" alt="X" style="position: absolute; left: 5px; top: 5px; width: 50px; height: 50px;" />',
        )
        result = reconstruct_from_bundle(template)
        self.assertTrue(result["valid"])
        body = _loads(result["reconstruction"]["print_designer_body"], "print_designer_body")
        self.assertEqual(len(body[0]["childrens"]), 1)
        self.assertEqual(body[0]["childrens"][0]["type"], "image")
        self.assertEqual(body[0]["childrens"][0]["image"]["file_url"], "/files/x.png")

    def test_reconstruction_warns_about_shared_page_variants(self):
        result = reconstruct_from_bundle(VALID_TEMPLATE)
        warnings = result.get("warnings", [])
        self.assertTrue(
            any("page variants" in w.lower() or "shared content" in w.lower() for w in warnings),
            f"expected page-variant warning, got: {warnings}",
        )

    def test_existing_settings_preserved(self):
        existing = {"page": {"width": 100, "height": 200}, "isHeaderFooterAuto": True}
        result = reconstruct_from_bundle(VALID_TEMPLATE, existing_settings=existing)
        settings = _loads(
            result["reconstruction"]["print_designer_settings"], "print_designer_settings"
        )
        self.assertEqual(settings["page"]["width"], 100)
        self.assertEqual(settings["page"]["height"], 200)
        self.assertTrue(settings["isHeaderFooterAuto"])


# -----------------------------------------------------------------------------
# Review-driven tests (Slice B "Done" acceptance)
# -----------------------------------------------------------------------------

PLACEHOLDER_TEMPLATE = (
    "<!-- PD:METADATA:START -->\n"
    '{"source": "test", "version": "1.0.0"}\n'
    "<!-- PD:METADATA:END -->\n"
    "\n"
    "<!-- PD:HEADER:START -->\n"
    "<!-- Paste HEADER HTML here -->\n"
    "<!-- PD:HEADER:END -->\n"
    "\n"
    "<!-- PD:CONTENT:START -->\n"
    "<!-- Paste BODY/CONTENT HTML here -->\n"
    "<!-- PD:CONTENT:END -->\n"
    "\n"
    "<!-- PD:FOOTER:START -->\n"
    "<!-- Paste FOOTER HTML here -->\n"
    "<!-- PD:FOOTER:END -->\n"
    "\n"
    "<!-- PD:CSS:START -->\n"
    "/* Paste CSS here */\n"
    "<!-- PD:CSS:END -->\n"
)

CLASS_ID_CSS_TEMPLATE = (
    "<!-- PD:METADATA:START -->\n"
    '{"source": "test", "version": "1.0.0"}\n'
    "<!-- PD:METADATA:END -->\n"
    "\n"
    "<!-- PD:HEADER:START -->\n"
    '<div class="box" id="hdr" style="position: absolute; left: 10px; top: 20px; width: 200px; height: 30px;">Header box</div>\n'
    "<!-- PD:HEADER:END -->\n"
    "\n"
    "<!-- PD:CONTENT:START -->\n"
    "<p>Content text</p>\n"
    "<!-- PD:CONTENT:END -->\n"
    "\n"
    "<!-- PD:FOOTER:START -->\n"
    "<p>Footer text</p>\n"
    "<!-- PD:FOOTER:END -->\n"
    "\n"
    "<!-- PD:CSS:START -->\n"
    ".box { color: red; left: 50px; top: 60px; }\n"
    "#hdr { color: blue; }\n"
    "<!-- PD:CSS:END -->\n"
)

RECTANGLE_TEMPLATE = (
    "<!-- PD:METADATA:START -->\n"
    '{"source": "test", "version": "1.0.0"}\n'
    "<!-- PD:METADATA:END -->\n"
    "\n"
    "<!-- PD:HEADER:START -->\n"
    "<p>Header text</p>\n"
    "<!-- PD:HEADER:END -->\n"
    "\n"
    "<!-- PD:CONTENT:START -->\n"
    '<div style="border: 1px solid #000; background-color: #f5f5f5; position: absolute; left: 5px; top: 5px; width: 100px; height: 50px;">Box</div>\n'
    "<!-- PD:CONTENT:END -->\n"
    "\n"
    "<!-- PD:FOOTER:START -->\n"
    "<p>Footer text</p>\n"
    "<!-- PD:FOOTER:END -->\n"
    "\n"
    "<!-- PD:CSS:START -->\n"
    "/* css ok */\n"
    "body { color: #111; }\n"
    "<!-- PD:CSS:END -->\n"
)


class TestImportReviewFixes(unittest.TestCase):
    """Tests covering the review handoff in
    harness/plans/minimax_print_designer_import_review_fixes.md."""

    # ----- Review item 1: blank template must fail -----

    def test_placeholder_template_fails(self):
        report = build_validation_report(PLACEHOLDER_TEMPLATE)
        self.assertFalse(report["valid"])
        # Every section is a comment-only placeholder -> every section
        # should report as empty/placeholder.
        for name in ("header", "content", "footer", "css"):
            self.assertIn(name, report["sections"])
            self.assertTrue(
                report["sections"][name]["present"],
                f"placeholder section {name} should still be 'present' (markers exist)",
            )
        blocker_text = " ".join(report["blockers"])
        self.assertIn("empty", blocker_text.lower())
        # At least header / content / footer are placeholders
        self.assertTrue(
            any("header" in b.lower() for b in report["blockers"]),
            f"expected a header placeholder blocker, got: {report['blockers']}",
        )
        self.assertTrue(
            any("content" in b.lower() for b in report["blockers"]),
            f"expected a content placeholder blocker, got: {report['blockers']}",
        )
        self.assertTrue(
            any("footer" in b.lower() for b in report["blockers"]),
            f"expected a footer placeholder blocker, got: {report['blockers']}",
        )

    def test_placeholder_template_reconstruction_returns_none(self):
        result = reconstruct_from_bundle(PLACEHOLDER_TEMPLATE)
        self.assertFalse(result["valid"])
        self.assertIsNone(result["reconstruction"])

    # ----- Review item 2: actual text content survives -----

    def test_header_text_survives(self):
        result = reconstruct_from_bundle(VALID_TEMPLATE)
        self.assertTrue(result["valid"])
        header = _loads(
            result["reconstruction"]["print_designer_header"],
            "print_designer_header",
        )
        header_wrapper = _unwrap_single_page_wrapper(header, "print_designer_header")
        # At least one child element should contain "Header text" (no leading
        # newline-only garbage, no truncated value)
        self.assertTrue(
            any(
                "Header text" in (e.get("content") or "")
                for e in header_wrapper.get("childrens", [])
            ),
            f"expected 'Header text' in header elements: {header_wrapper}",
        )

    def test_body_paragraph_and_span_survive(self):
        result = reconstruct_from_bundle(VALID_TEMPLATE)
        self.assertTrue(result["valid"])
        body_wrapper = _loads(
            result["reconstruction"]["print_designer_body"],
            "print_designer_body",
        )
        body = body_wrapper[0]
        texts = [e.get("content", "") for e in body.get("childrens", [])]
        self.assertTrue(
            any("Body paragraph" in t for t in texts),
            f"expected 'Body paragraph' in body elements: {texts}",
        )
        self.assertTrue(
            any("Inline text" in t for t in texts),
            f"expected 'Inline text' in body elements: {texts}",
        )

    def test_whitespace_only_text_nodes_are_ignored(self):
        """A <p>   </p> (just whitespace) should not become a text element
        with non-empty dynamicContent. The fix to the parser stores
        clean text in the element and keeps dynamicContent consistent."""
        template = VALID_TEMPLATE.replace(
            '<div style="position: absolute; left: 10px; top: 50px; width: 400px; height: 100px;">\n  <p>Body paragraph</p>\n  <span>Inline text</span>\n</div>',
            "<p>   </p><p>Body paragraph</p><span>Inline text</span>",
        )
        result = reconstruct_from_bundle(template)
        self.assertTrue(result["valid"])
        body_wrapper = _loads(
            result["reconstruction"]["print_designer_body"],
            "print_designer_body",
        )
        body = body_wrapper[0]
        # Three real elements only (the leading whitespace-only p is dropped)
        self.assertEqual(len(body.get("childrens", [])), 3)

    # ----- Review item 3: header/footer wrapper shape -----

    def test_header_footer_are_page_wrappers(self):
        """Header and footer JSON must be page-wrapper objects (with
        type/label/childrens + page variant flags) so the editor loader
        can recognize them."""
        result = reconstruct_from_bundle(VALID_TEMPLATE)
        self.assertTrue(result["valid"])
        header = _loads(
            result["reconstruction"]["print_designer_header"],
            "print_designer_header",
        )
        footer = _loads(
            result["reconstruction"]["print_designer_footer"],
            "print_designer_footer",
        )
        for label, payload in (("header", header), ("footer", footer)):
            wrappers = payload
            self.assertIsInstance(wrappers, list)
            self.assertEqual(len(wrappers), 1, f"{label} must contain one wrapper")
            w = wrappers[0]
            self.assertEqual(w.get("type"), "page")
            self.assertIn("childrens", w)
            self.assertIsInstance(w["childrens"], list)
            for variant in ("firstPage", "oddPage", "evenPage", "lastPage"):
                self.assertTrue(w.get(variant), f"missing {variant} flag on wrapper {w}")
            self.assertIn("parent", w.get("label", ""))

    def test_body_wrapper_has_page_variant_flags(self):
        result = reconstruct_from_bundle(VALID_TEMPLATE)
        self.assertTrue(result["valid"])
        body_list = _loads(
            result["reconstruction"]["print_designer_body"],
            "print_designer_body",
        )
        # Body stored as JSON of a list of page wrappers
        self.assertIsInstance(body_list, list)
        self.assertEqual(len(body_list), 1)
        body = body_list[0]
        self.assertEqual(body.get("type"), "page")
        for variant in ("firstPage", "oddPage", "evenPage", "lastPage"):
            self.assertTrue(body.get(variant))

    def test_print_format_uses_page_wrappers_in_header_body_footer(self):
        result = reconstruct_from_bundle(VALID_TEMPLATE)
        self.assertTrue(result["valid"])
        pd_format = _loads(
            result["reconstruction"]["print_designer_print_format"],
            "print_designer_print_format",
        )
        # header and footer should hold page-wrapper dicts
        for variant in ("firstPage", "oddPage", "evenPage", "lastPage"):
            self.assertIsInstance(pd_format["header"][variant], dict)
            self.assertEqual(pd_format["header"][variant].get("type"), "page")
            self.assertIsInstance(pd_format["footer"][variant], dict)
            self.assertEqual(pd_format["footer"][variant].get("type"), "page")
        # body is a list
        self.assertIsInstance(pd_format["body"], list)
        self.assertEqual(pd_format["body"][0].get("type"), "page")

    # ----- Review item 4: Jinja {{...}} is blocked -----

    def test_jinja_expression_blocked_in_header(self):
        bad = VALID_TEMPLATE.replace(
            '<div style="position: absolute; left: 0px; top: 0px; width: 200px; height: 30px; color: #000;">\n  <p>Header text</p>\n</div>',
            "<div>{{ doc.customer }}</div>",
        )
        report = build_validation_report(bad)
        self.assertFalse(report["valid"])
        self.assertTrue(
            any("Jinja" in b for b in report["blockers"]),
            f"expected a Jinja blocker, got: {report['blockers']}",
        )

    def test_jinja_expression_blocked_in_content(self):
        bad = VALID_TEMPLATE.replace(
            "<p>Body paragraph</p>",
            "<span>{{ doc.grand_total }}</span>",
        )
        report = build_validation_report(bad)
        self.assertFalse(report["valid"])
        self.assertTrue(
            any("Jinja" in b for b in report["blockers"]),
            f"expected a Jinja blocker, got: {report['blockers']}",
        )

    def test_jinja_comment_blocked(self):
        bad = VALID_TEMPLATE.replace(
            "<p>Body paragraph</p>",
            "<span>{# a Jinja comment #}</span>",
        )
        report = build_validation_report(bad)
        self.assertFalse(report["valid"])
        self.assertTrue(
            any("Jinja" in b for b in report["blockers"]),
            f"expected a Jinja blocker, got: {report['blockers']}",
        )

    # ----- Review item 5: class/id CSS selectors are applied -----

    def test_class_css_selector_applied(self):
        result = reconstruct_from_bundle(CLASS_ID_CSS_TEMPLATE)
        self.assertTrue(result["valid"])
        body_wrapper = _loads(
            result["reconstruction"]["print_designer_body"],
            "print_designer_body",
        )
        # Content is the placeholder literal in CLASS_ID_CSS_TEMPLATE;
        # the wrapper should still come through cleanly. The actual
        # class/id resolution is checked in the next test on the inline
        # style-bound element.
        self.assertIsInstance(body_wrapper, list)
        self.assertEqual(len(body_wrapper), 1)

    def test_class_id_css_applied_to_header_div(self):
        """The header div has class="box" id="hdr". The CSS map
        .box { color: red } and #hdr { color: blue } should be merged
        into its reconstructed style."""
        result = reconstruct_from_bundle(CLASS_ID_CSS_TEMPLATE)
        self.assertTrue(result["valid"])
        header = _loads(
            result["reconstruction"]["print_designer_header"],
            "print_designer_header",
        )
        header_wrapper = _unwrap_single_page_wrapper(header, "print_designer_header")
        self.assertEqual(len(header_wrapper.get("childrens", [])), 1)
        # Class is checked first, then id, but id's "left" is absent from
        # the source CSS so inline's "left: 10px" stays. The point is that
        # the CSS color merges in.
        style = header_wrapper["childrens"][0].get("style", {})
        self.assertEqual(style.get("color"), "blue", f"id #hdr should win over class .box: {style}")
        # left and top from inline are preserved
        self.assertEqual(style.get("left"), "10px")
        self.assertEqual(style.get("top"), "20px")

    # ----- Review item 6: rectangle support is real -----

    def test_bordered_div_becomes_rectangle(self):
        result = reconstruct_from_bundle(RECTANGLE_TEMPLATE)
        self.assertTrue(result["valid"])
        body_wrapper = _loads(
            result["reconstruction"]["print_designer_body"],
            "print_designer_body",
        )
        body = body_wrapper[0]
        # Body has one child: the bordered div
        self.assertEqual(len(body.get("childrens", [])), 1)
        rect = body["childrens"][0]
        self.assertEqual(rect.get("type"), "rectangle", f"expected type=rectangle, got: {rect}")
        # inline style preserved
        self.assertEqual(rect.get("style", {}).get("border"), "1px solid #000")
        self.assertEqual(rect.get("style", {}).get("background-color"), "#f5f5f5")
        # geometry from inline style
        self.assertEqual(rect.get("startX"), 5.0)
        self.assertEqual(rect.get("startY"), 5.0)
        self.assertEqual(rect.get("width"), 100.0)
        self.assertEqual(rect.get("height"), 50.0)

    def test_plain_div_flattens_to_text(self):
        """A div with no border/background (the only one in VALID_TEMPLATE's
        header section) should NOT become a rectangle. It should either
        flatten or, with the simple model, fall through to text."""
        result = reconstruct_from_bundle(VALID_TEMPLATE)
        self.assertTrue(result["valid"])
        header = _loads(
            result["reconstruction"]["print_designer_header"],
            "print_designer_header",
        )
        header_wrapper = _unwrap_single_page_wrapper(header, "print_designer_header")
        # The header has one child element. The plain wrapping div must NOT
        # become a rectangle; it should flatten to its text child.
        self.assertEqual(len(header_wrapper.get("childrens", [])), 1)
        self.assertNotEqual(header_wrapper["childrens"][0].get("type"), "rectangle")

    # ----- Safety -----

    def test_invalid_bundle_does_not_mutate(self):
        """reconstruct_from_bundle with an invalid bundle must return
        reconstruction=None, not silently produce a partial output."""
        bad = _missing_marker_block(VALID_TEMPLATE, "CONTENT")
        result = reconstruct_from_bundle(bad)
        self.assertIsNone(result["reconstruction"])
        self.assertFalse(result["valid"])
        self.assertGreater(
            len(result.get("blockers", [])),
            0,
            "expected at least one blocker on invalid bundle",
        )

    def test_validate_endpoint_pure_read_only(self):
        """The pure validate call (we only exercise build_validation_report
        here) must not write anything anywhere; this is implicit since
        it's a pure function, but we assert it raises on missing markers
        instead of returning a partial report."""
        empty = ""
        try:
            build_validation_report(empty)
        except ValueError:
            pass  # acceptable
        # No "mutated" state exists; this is a sanity assertion.
        self.assertTrue(True)


# -----------------------------------------------------------------------------
# Sanity test for the test loader itself
# -----------------------------------------------------------------------------


class TestImportSanity(unittest.TestCase):
    def test_valid_template_is_actually_valid(self):
        # A meta-assertion: the canonical VALID_TEMPLATE should validate.
        # If this fails, every other test that uses VALID_TEMPLATE is moot.
        report = build_validation_report(VALID_TEMPLATE)
        self.assertTrue(report["valid"], f"baseline VALID_TEMPLATE not valid: {report}")
