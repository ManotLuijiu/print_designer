"""
Print Designer Import Bridge - helper module.

Template-first Import MVP. Validates and reconstructs a small safe subset
of HTML/CSS into Print Designer JSON. Keeps marker parsing, validation,
and reconstruction out of the API file.

Markers required in the import template:
    <!-- PD:METADATA:START --> ... <!-- PD:METADATA:END -->
    <!-- PD:HEADER:START -->   ... <!-- PD:HEADER:END -->
    <!-- PD:CONTENT:START -->  ... <!-- PD:CONTENT:END -->
    <!-- PD:FOOTER:START -->   ... <!-- PD:FOOTER:END -->
    <!-- PD:CSS:START -->      ... <!-- PD:CSS:END -->

MVP supported subset:
    - static text (div, p, span -> text element)
    - bordered/background div -> rectangle element
    - absolutely positioned div with border/background/size
    - img -> image
    - simple inline style parsing for position/size/font/color/background

Explicit blockers:
    - <table
    - <svg
    - barcode-like markup
    - flex/grid layouts that cannot be mapped safely
    - any Jinja syntax in imported HTML ({{...}}, {%...%}, {#...#})
"""

import json
import re
from html.parser import HTMLParser

# Marker pair definitions
REQUIRED_MARKERS = (
    ("metadata", "PD:METADATA:START", "PD:METADATA:END"),
    ("header", "PD:HEADER:START", "PD:HEADER:END"),
    ("content", "PD:CONTENT:START", "PD:CONTENT:END"),
    ("footer", "PD:FOOTER:START", "PD:FOOTER:END"),
    ("css", "PD:CSS:START", "PD:CSS:END"),
)

# MVP-supported subset
SUPPORTED_SUBSET = {
    "static_text": True,
    "images": True,
    "rectangles": True,
    "absolute_positioning": True,
}

# CSS properties whose presence on a div makes it a rectangle (not text)
RECTANGLE_CSS_HINTS = {
    "border",
    "border-width",
    "border-color",
    "border-style",
    "background",
    "background-color",
    "background-image",
}

# Unsupported HTML patterns -> blocker
# Note: covers both block tags (table, svg), layout features (flex/grid),
# barcode-like content, AND any Jinja syntax (expressions, statements, comments).
BLOCKER_PATTERNS = (
    (r"<table\b", "Table markup is not supported in Import MVP"),
    (r"<svg\b", "SVG markup is not supported in Import MVP"),
    (r"data-barcode", "Barcode markup is not supported in Import MVP"),
    (r"jbarcode|jsbarcode", "Barcode library markup is not supported in Import MVP"),
    (r"display\s*:\s*flex", "Flex layouts are not supported in Import MVP"),
    (r"display\s*:\s*grid", "Grid layouts are not supported in Import MVP"),
    (r"\{\{\s*[^{}]+\s*\}\}", "Jinja expressions in imported HTML are not supported in Import MVP"),
    (r"\{\%\s*for\b", "Jinja for-loops in imported HTML are not supported in Import MVP"),
    (r"\{\%\s*if\b", "Jinja conditionals in imported HTML are not supported in Import MVP"),
    (r"\{\%\s*set\b", "Jinja set statements in imported HTML are not supported in Import MVP"),
    (r"\{\#", "Jinja comments in imported HTML are not supported in Import MVP"),
)

# CSS properties we read for reconstruction (MVP subset)
READ_CSS_PROPERTIES = {
    "position",
    "left",
    "top",
    "right",
    "bottom",
    "width",
    "height",
    "font-size",
    "font-weight",
    "font-family",
    "font-style",
    "text-align",
    "color",
    "background-color",
    "background-image",
    "border",
    "border-width",
    "border-color",
    "border-style",
    "border-radius",
    "padding",
    "padding-top",
    "padding-right",
    "padding-bottom",
    "padding-left",
    "margin",
    "margin-top",
    "margin-right",
    "margin-bottom",
    "margin-left",
    "line-height",
    "letter-spacing",
    "opacity",
}


# -----------------------------------------------------------------------------
# Marker parsing
# -----------------------------------------------------------------------------


def _marker_token(text, marker):
    """Resolve a marker to the exact token stored in the bundle.

    Preferred shape is an HTML comment marker like:
        <!-- PD:HEADER:START -->
    but we also tolerate raw marker strings for defensive compatibility.
    """
    comment_token = f"<!-- {marker} -->"
    if comment_token in text:
        return comment_token
    return marker


def _extract_between(text, start_marker, end_marker):
    """Return the text between the first occurrence of start_marker and end_marker.

    Raises ValueError if either marker is missing.
    """
    start_token = _marker_token(text, start_marker)
    end_token = _marker_token(text, end_marker)
    start = text.find(start_token)
    if start == -1:
        raise ValueError(f"Missing start marker: {start_marker}")
    start += len(start_token)
    end = text.find(end_token, start)
    if end == -1:
        raise ValueError(f"Missing end marker: {end_marker}")
    return text[start:end]


def require_marker_pair(name, start_marker, end_marker, text):
    """Return (raw_section_text, length) for the named section.

    Raises ValueError with a user-friendly message if a marker is missing.
    """
    try:
        section = _extract_between(text, start_marker, end_marker)
        return section, len(section)
    except ValueError as e:
        raise ValueError(f"Missing {name} markers: {e}")


def extract_bridge_sections(bundle_text):
    """Return dict of section name -> section text. All sections are required."""
    sections = {}
    for name, start_marker, end_marker in REQUIRED_MARKERS:
        section, _ = require_marker_pair(name, start_marker, end_marker, bundle_text)
        sections[name] = section
    return sections


def extract_metadata(bundle_text):
    """Return parsed metadata dict from the METADATA section, or {} on parse error."""
    try:
        section, _ = require_marker_pair(
            "metadata",
            "PD:METADATA:START",
            "PD:METADATA:END",
            bundle_text,
        )
        meta = json.loads(section.strip())
        if not isinstance(meta, dict):
            return {}
        return meta
    except (ValueError, json.JSONDecodeError):
        return {}


# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------

_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def _strip_html_comments(text):
    """Remove HTML comments from a text fragment."""
    if not text:
        return ""
    return _HTML_COMMENT_RE.sub("", text)


def _strip_css_comments(text):
    """Remove CSS comments from a text fragment."""
    if not text:
        return ""
    return _CSS_COMMENT_RE.sub("", text)


def _meaningful_section_text(text):
    """Return text with comment placeholders stripped and whitespace trimmed.

    Used to decide whether a section's content is "meaningful" for
    validation. A section that only contains HTML comments, CSS comments,
    or whitespace is treated as empty / placeholder.
    """
    if not text:
        return ""
    cleaned = _strip_html_comments(text)
    cleaned = _strip_css_comments(cleaned)
    return cleaned.strip()


def detect_unsupported_patterns(html, css=""):
    """Return list of (pattern_label, matched_text) for every blocker found."""
    hits = []
    for pattern, label in BLOCKER_PATTERNS:
        for m in re.finditer(pattern, html, re.IGNORECASE):
            hits.append((label, m.group(0)))
    if css:
        for pattern, label in BLOCKER_PATTERNS:
            for m in re.finditer(pattern, css, re.IGNORECASE):
                hits.append((label, m.group(0)))
    return hits


def validate_bridge_sections(sections):
    """Validate meaningful content of all required sections.

    Returns list of (severity, message) tuples. severity is 'blocker' or 'warning'.

    Sections that only contain HTML comments / whitespace are treated
    as placeholders (blocker). Genuinely short but non-empty content
    is a warning.
    """
    findings = []
    for name, _, _ in REQUIRED_MARKERS:
        section = sections.get(name, "")
        meaningful = _meaningful_section_text(section)
        if not meaningful:
            findings.append(
                (
                    "blocker",
                    f"Section {name} is empty (only comments or whitespace — fill in the template before importing)",
                )
            )
            continue
        if name != "metadata" and len(meaningful) < 4:
            findings.append(("warning", f"Section {name} is very short"))
    return findings


def build_validation_report(bundle_text):
    """Run all validation checks and return a structured report dict.

    Returns:
        {
            "valid": bool,
            "blockers": [...],
            "warnings": [...],
            "sections": {name: {"present": bool, "length": int}},
            "supported_subset": {...},
            "unsupported_detected": [...],
        }
    """
    # 1) Sections
    raw_sections = {}  # name -> raw text (for downstream checks)
    sections = {}  # name -> {present, length} (for the report)
    section_findings = []
    for name, start_marker, end_marker in REQUIRED_MARKERS:
        try:
            text, length = require_marker_pair(name, start_marker, end_marker, bundle_text)
            raw_sections[name] = text
            sections[name] = {"present": True, "length": length}
        except ValueError as e:
            sections[name] = {"present": False, "length": 0}
            section_findings.append(("blocker", str(e)))

    if section_findings:
        # Cannot continue without all required sections
        return {
            "valid": False,
            "blockers": [m for sev, m in section_findings if sev == "blocker"],
            "warnings": [m for sev, m in section_findings if sev == "warning"],
            "sections": sections,
            "supported_subset": dict(SUPPORTED_SUBSET),
            "unsupported_detected": [],
        }

    # 2) Section-level findings (use raw text, not the report dict)
    body_findings = validate_bridge_sections(raw_sections)
    # 3) Pattern blockers
    unsupported = []
    for label, _ in detect_unsupported_patterns(
        raw_sections["header"] + raw_sections["content"] + raw_sections["footer"],
        raw_sections["css"],
    ):
        unsupported.append(label)
    pattern_findings = [("blocker", label) for label in set(unsupported)]

    all_findings = body_findings + pattern_findings
    blockers = [m for sev, m in all_findings if sev == "blocker"]
    warnings = [m for sev, m in all_findings if sev == "warning"]

    return {
        "valid": len(blockers) == 0,
        "blockers": blockers,
        "warnings": warnings,
        "sections": sections,
        "supported_subset": dict(SUPPORTED_SUBSET),
        "unsupported_detected": sorted(set(unsupported)),
    }


# -----------------------------------------------------------------------------
# CSS parsing (MVP subset)
# -----------------------------------------------------------------------------


def _parse_inline_style(style_text):
    """Parse a CSS inline-style string into a dict of property -> raw value.

    Only READ_CSS_PROPERTIES are kept; everything else is dropped silently.
    """
    out = {}
    if not style_text:
        return out
    for decl in style_text.split(";"):
        if ":" not in decl:
            continue
        prop, _, value = decl.partition(":")
        prop = prop.strip().lower()
        value = value.strip()
        if prop in READ_CSS_PROPERTIES and value:
            out[prop] = value
    return out


def _split_selectors(selector_text):
    """Split a selector list (e.g. '.a, #b, div') into individual selectors.

    Returns list of normalized selector strings.
    """
    return [s.strip() for s in selector_text.split(",") if s.strip()]


def css_text_to_style_map(css_text):
    """Parse a CSS string into {selector: {property: value}}.

    MVP: very simple — strips comments, splits on `}` and parses the
    body. Supports comma-separated selector lists (each becomes its own
    key in the returned dict). Doesn't resolve cascades or pseudo-classes.

    Selectors are kept as-is so that .class and #id lookups work.
    """
    out = {}
    if not css_text:
        return out
    cleaned = re.sub(r"/\*.*?\*/", "", css_text, flags=re.DOTALL)
    for rule in cleaned.split("}"):
        if "{" not in rule:
            continue
        selector, _, body = rule.partition("{")
        selector = selector.strip()
        if not selector or not body.strip():
            continue
        parsed = _parse_inline_style(body)
        if not parsed:
            continue
        for sel in _split_selectors(selector):
            out[sel] = dict(parsed)  # copy so each selector has its own dict
    return out


# -----------------------------------------------------------------------------
# HTML reconstruction (MVP subset)
# -----------------------------------------------------------------------------


def _is_rectangle_style(style):
    """True if the inline style indicates a bordered/background container.

    Used to decide whether a `div` becomes a rectangle element vs. is
    flattened into its parent. The MVP rule: any of border/border-* or
    background/background-color or background-image makes it a rectangle.
    """
    if not style:
        return False
    return any(key in style for key in RECTANGLE_CSS_HINTS)


def _flatten_text(s):
    """Collapse whitespace inside a text node.

    Replace runs of whitespace with a single space and strip the ends.
    Returns "" if the result is empty.
    """
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()


class _PDNodeBuilder(HTMLParser):
    """Builds Print Designer element dicts from a tiny HTML subset.

    Uses a proper node stack (parent element on top) so that text data
    is captured on the right element. Supported tags:

        - img          -> image element
        - p, span      -> text element (real visible text)
        - div          -> rectangle (if has border/background) OR
                          its children are flattened into the parent
                          (if no rectangle-like styling, no div wrapper
                          is emitted)

    Attributes read: style (inline CSS), src (image), width/height
    (numeric px for size; other units left as-is).
    """

    def __init__(self, css_map=None):
        super().__init__(convert_charrefs=True)
        self.css_map = css_map or {}
        self.next_id = 1
        # Stack of active nodes. Each node: {"tag", "attrs", "style",
        # "text_buffer", "children", "element"} where element is the
        # PD element dict being built (or None for placeholder nodes
        # whose children get flattened into the parent).
        self.stack = []
        # Root-level emitted elements (the final result)
        self.root = []

    def _alloc_id(self):
        cid = f"imp{self.next_id}"
        self.next_id += 1
        return cid

    @staticmethod
    def _px(value, default=0.0):
        if not value:
            return default
        m = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*(px)?\s*$", str(value))
        if m:
            try:
                return float(m.group(1))
            except (TypeError, ValueError):
                return default
        return default

    def _resolve_style(self, attrs):
        """Resolve CSS precedence for the MVP subset.

        Order:
            class styles < id styles < inline styles
        """
        resolved = {}
        cls = attrs.get("class")
        if cls and self.css_map:
            for c in cls.split():
                key = f".{c}"
                if key in self.css_map:
                    resolved.update(self.css_map[key])
        eid = attrs.get("id")
        if eid and self.css_map:
            key = f"#{eid}"
            if key in self.css_map:
                resolved.update(self.css_map[key])
        inline_style = _parse_inline_style(attrs.get("style", ""))
        resolved.update(inline_style)
        return resolved

    def _make_text_element(self, text, style):
        """Create a text element with the given accumulated text + style."""
        clean = _flatten_text(text)
        el = {
            "id": self._alloc_id(),
            "type": "text",
            "content": clean,
            "contenteditable": False,
            "isDynamic": False,
            "dynamicContent": [],
            "isFixedSize": False,
            "style": style,
        }
        if clean:
            el["dynamicContent"] = [
                {
                    "doctype": "",
                    "parentField": "",
                    "fieldname": "content",
                    "value": clean,
                    "fieldtype": "StaticText",
                    "is_static": True,
                    "is_labelled": False,
                    "nextLine": False,
                    "parseJinja": False,
                    "style": {},
                    "labelStyleEditing": False,
                }
            ]
        el["startX"] = self._px(style.get("left", "0"))
        el["startY"] = self._px(style.get("top", "0"))
        el["pageX"] = el["startX"]
        el["pageY"] = el["startY"]
        el["width"] = self._px(style.get("width", "0"))
        el["height"] = self._px(style.get("height", "0"))
        return el

    def _make_rectangle_element(self, style):
        """Create a rectangle element from a styled container."""
        el = {
            "id": self._alloc_id(),
            "type": "rectangle",
            "isDraggable": False,
            "isResizable": False,
            "isDropZone": False,
            "style": style,
        }
        el["startX"] = self._px(style.get("left", "0"))
        el["startY"] = self._px(style.get("top", "0"))
        el["pageX"] = el["startX"]
        el["pageY"] = el["startY"]
        el["width"] = self._px(style.get("width", "0"))
        el["height"] = self._px(style.get("height", "0"))
        return el

    def _make_image_element(self, attrs, style):
        a = dict(attrs)
        src = a.get("src") or ""
        name = a.get("alt") or (src.rsplit("/", 1)[-1] if src else "") or ""
        return {
            "id": self._alloc_id(),
            "type": "image",
            "isDraggable": False,
            "isResizable": False,
            "isDropZone": False,
            "isDynamic": False,
            "image": {
                "name": name,
                "file_name": name,
                "file_url": src,
            },
            "startX": self._px(style.get("left", "0")),
            "startY": self._px(style.get("top", "0")),
            "pageX": self._px(style.get("left", "0")),
            "pageY": self._px(style.get("top", "0")),
            "width": self._px(a.get("width", style.get("width", "0"))),
            "height": self._px(a.get("height", style.get("height", "0"))),
            "style": style,
        }

    def _emit(self, element):
        """Attach an element to the nearest real ancestor (or root if none)."""
        for parent in reversed(self.stack):
            if parent.get("element") is not None:
                parent["element"].setdefault("childrens", []).append(element)
                return
        self.root.append(element)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        style = self._resolve_style(a)

        if tag == "img":
            # Leaf element: emit directly
            self._emit(self._make_image_element(a, style))
            # Push a no-op scope so text after img is ignored (no parent)
            self.stack.append(
                {
                    "tag": tag,
                    "attrs": a,
                    "style": style,
                    "text_buffer": "",
                    "children": [],
                    "element": None,
                }
            )
            return

        if tag in ("p", "span"):
            # Text-bearing node: push a node with element
            el = self._make_text_element("", style)
            self._emit(el)
            self.stack.append(
                {
                    "tag": tag,
                    "attrs": a,
                    "style": style,
                    "text_buffer": "",
                    "children": [],
                    "element": el,
                }
            )
            return

        if tag == "div":
            if _is_rectangle_style(style):
                # Rectangle: push as element
                el = self._make_rectangle_element(style)
                self._emit(el)
                self.stack.append(
                    {
                        "tag": tag,
                        "attrs": a,
                        "style": style,
                        "text_buffer": "",
                        "children": [],
                        "element": el,
                    }
                )
            else:
                # Plain wrapper div: flatten its children into the parent
                self.stack.append(
                    {
                        "tag": tag,
                        "attrs": a,
                        "style": style,
                        "text_buffer": "",
                        "children": [],
                        "element": None,
                    }
                )
            return

        # Unknown tag — treat as flattening wrapper (children pass through)
        self.stack.append(
            {
                "tag": tag,
                "attrs": a,
                "style": style,
                "text_buffer": "",
                "children": [],
                "element": None,
            }
        )

    def handle_data(self, data):
        if not self.stack:
            return
        self.stack[-1]["text_buffer"] += data

    def handle_endtag(self, tag):
        if not self.stack:
            return
        node = self.stack.pop()
        # Flush any text from the closing node
        if node.get("element") and node["element"].get("type") == "text":
            # Replace the text element's content with the full accumulated text
            accumulated = (node["element"].get("content", "") or "") + node["text_buffer"]
            clean = _flatten_text(accumulated)
            node["element"]["content"] = clean
            if clean:
                node["element"]["dynamicContent"] = [
                    {
                        "doctype": "",
                        "parentField": "",
                        "fieldname": "content",
                        "value": clean,
                        "fieldtype": "StaticText",
                        "is_static": True,
                        "is_labelled": False,
                        "nextLine": False,
                        "parseJinja": False,
                        "style": {},
                        "labelStyleEditing": False,
                    }
                ]
            else:
                # Empty text after comments/whitespace strip — drop the
                # dynamicContent and the element itself if it has no other value
                node["element"]["dynamicContent"] = []
        elif node.get("element") is None:
            # Flattening wrapper: if it carried direct visible text, emit that
            # as a text element using the wrapper's own resolved style. If the
            # text is only whitespace, it disappears naturally.
            extra = node.get("text_buffer", "")
            clean = _flatten_text(extra)
            if clean:
                self._emit(self._make_text_element(clean, node.get("style", {})))
            elif self.stack and extra:
                self.stack[-1]["text_buffer"] += extra

    def result(self):
        return self.root


def html_section_to_pd_elements(section_html, section_name="header", css_map=None):
    """Parse a small subset of HTML and return a list of PD element dicts.

    Suitable for header/content/footer sections. css_map is the optional
    output of css_text_to_style_map() for resolving class/id-based styles.
    """
    if not section_html or not section_html.strip():
        return []
    parser = _PDNodeBuilder(css_map=css_map)
    try:
        parser.feed(section_html)
        parser.close()
    except Exception:
        # On parse error, return whatever we have so far rather than failing
        # the whole import — validation is the strict path; reconstruction is best-effort.
        pass
    return parser.result()


# -----------------------------------------------------------------------------
# Page / format / settings builders
# -----------------------------------------------------------------------------


def build_pd_page(children, section_name="body", page_index=0):
    """Build a Print Designer 'page' wrapper around element children.

    Returns a dict compatible with ElementStore.loadElements() expectations:
    top-level page wrapper with type/index/childrens plus page variant
    flags (firstPage/oddPage/evenPage/lastPage) so the editor and Print
    Format loader can recognize it.
    """
    return {
        "type": "page",
        "index": page_index,
        "isDropZone": False,
        "childrens": children,
        "isDraggable": False,
        "isResizable": False,
        "snapPoints": [None, None],
        "snapEdges": [None, None, None, None],
        "firstPage": True,
        "oddPage": True,
        "evenPage": True,
        "lastPage": True,
    }


def _build_page_wrapper(children, section_name="section"):
    """Build a page wrapper suitable for header/footer/body children.

    MVP: same children reused across page variants (per Slice A plan).
    """
    return {
        "type": "page",
        "label": f"{section_name}_parent",
        "index": 0,
        "isDropZone": False,
        "childrens": children,
        "isDraggable": False,
        "isResizable": False,
        "snapPoints": [None, None],
        "snapEdges": [None, None, None, None],
        "firstPage": True,
        "oddPage": True,
        "evenPage": True,
        "lastPage": True,
    }


def build_pd_format_layout(header_wrapper, body_wrapper, footer_wrapper):
    """Build a `print_designer_print_format` dict from the three page wrappers.

    MVP: same imported header/footer reused across page variants.
    """
    return {
        "header": {
            "firstPage": header_wrapper,
            "oddPage": header_wrapper,
            "evenPage": header_wrapper,
            "lastPage": header_wrapper,
        },
        "body": [body_wrapper],
        "footer": {
            "firstPage": footer_wrapper,
            "oddPage": footer_wrapper,
            "evenPage": footer_wrapper,
            "lastPage": footer_wrapper,
        },
    }


def build_import_settings(existing_settings, css_text, metadata):
    """Merge existing Print Designer settings with import metadata + CSS.

    Preserves existing settings keys where possible, then overlays
    schema_version, currentFonts defaults, and any metadata keys.
    """
    base = dict(existing_settings or {})
    base["schema_version"] = base.get("schema_version") or "1.3.0"
    base["import_metadata"] = dict(metadata or {})
    base["import_metadata"]["source"] = "jinja_bridge_import"
    if not base.get("currentFonts"):
        base["currentFonts"] = ["Sarabun"]
    if not base.get("currentPageSize"):
        base["currentPageSize"] = "A4"
    if not base.get("textControlType"):
        base["textControlType"] = "dynamic"
    # CSS is stored separately on Print Format, not in settings.
    return base


# -----------------------------------------------------------------------------
# Top-level reconstruction entry point
# -----------------------------------------------------------------------------


def reconstruct_from_bundle(bundle_text, existing_settings=None):
    """Validate + reconstruct from a bundle text.

    Returns:
        {
            "valid": bool,
            "blockers": [...],
            "warnings": [...],
            "reconstruction": {
                "print_designer_header":  "...",   # JSON string of [page wrapper]
                "print_designer_body":     "...",   # JSON string of [page wrapper]
                "print_designer_footer":   "...",   # JSON string of [page wrapper]
                "print_designer_print_format": "...", # JSON string with header/body/footer keys
                "print_designer_settings":  "...",
                "css":                      "...",
            } or None if invalid,
        }
    """
    report = build_validation_report(bundle_text)
    if not report["valid"]:
        return {
            "valid": False,
            "blockers": report["blockers"],
            "warnings": report["warnings"],
            "reconstruction": None,
        }

    sections = {
        k: _strip_for_section(bundle_text, k) for k in ("header", "content", "footer", "css")
    }
    metadata = extract_metadata(bundle_text)
    css_map = css_text_to_style_map(sections["css"])

    header_children = html_section_to_pd_elements(sections["header"], "header", css_map)
    content_children = html_section_to_pd_elements(sections["content"], "content", css_map)
    footer_children = html_section_to_pd_elements(sections["footer"], "footer", css_map)

    header_wrapper = _build_page_wrapper(header_children, "header")
    body_wrapper = build_pd_page(content_children, "body", 0)
    footer_wrapper = _build_page_wrapper(footer_children, "footer")

    settings = build_import_settings(existing_settings, sections["css"], metadata)
    pd_format = build_pd_format_layout(header_wrapper, body_wrapper, footer_wrapper)

    warnings = list(report["warnings"])
    # MVP simplification warning: header/footer applied to all page variants
    warnings.append("Header/footer imported as shared content for all page variants")

    return {
        "valid": True,
        "blockers": [],
        "warnings": warnings,
        "reconstruction": {
            "print_designer_header": json.dumps([header_wrapper]),
            "print_designer_body": json.dumps([body_wrapper]),
            "print_designer_footer": json.dumps([footer_wrapper]),
            "print_designer_print_format": json.dumps(pd_format),
            "print_designer_settings": json.dumps(settings),
            "css": sections["css"],
        },
    }


def _strip_for_section(bundle_text, name):
    """Pull raw text between the markers for a named section."""
    start = f"PD:{name.upper()}:START"
    end = f"PD:{name.upper()}:END"
    try:
        return _extract_between(bundle_text, start, end)
    except ValueError:
        return ""
