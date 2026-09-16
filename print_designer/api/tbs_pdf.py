# Copyright (c) 2024, MooCoding and Contributors
# License: GNU General Public License v3. See license.txt

"""
TBS PDF - Thai Business Suite Clean PDF Generation
================================================

Standalone PDF generation that uses ONLY the Print Format's HTML/CSS.
No Frappe Print View Styles, no .print-format-gutter, no conflicting CSS.

Architecture:
  1. Load Print Format HTML + CSS (only)
  2. Build standalone <!doctype html> with PrintFormatCSS in <style>
  3. Parse @page CSS for size/margins/orientation
  4. Generate PDF with Chromium using correct page dimensions
  5. Return inline (opens in Chrome viewer)
"""

import base64
import re

import frappe
from frappe.utils.data import escape_html
from frappe.www.printview import validate_print_permission
from werkzeug.wrappers import Response


@frappe.whitelist()
def download_tbs_pdf(
    doctype,
    name,
    print_format=None,
    no_letterhead=0,
    letterhead=None,
    language=None,
    settings=None,
    **kwargs,
):
    """
    Generate a clean PDF using ONLY the Print Format's HTML/CSS.

    Args:
        doctype: Document type (e.g., "Stock Entry")
        name: Document name (e.g., "MAT-STE-2026-00004")
        print_format: Print Format name (e.g., "DGS Stock Transfer - Form 4")
        no_letterhead: 0 = include letterhead, 1 = exclude
        letterhead: Letterhead name
        language: Language code (e.g., "th")
        settings: JSON string with additional settings (page_orientation, etc.)

    Returns:
        PDF binary with inline Content-Disposition
    """
    # Generate PDF using Chrome via frappe.get_print (respects pdf_generator)
    pdf_bytes = frappe.get_print(
        doctype=doctype,
        name=name,
        print_format=print_format,
        as_pdf=True,
        no_letterhead=no_letterhead,
        letterhead=letterhead,
        pdf_generator="chrome",
    )

    # Set response for inline display
    frappe.local.response.filename = f"{name.replace(' ', '-').replace('/', '-')}.pdf"
    frappe.local.response.filecontent = pdf_bytes
    frappe.local.response.type = "pdf"

    return pdf_bytes


@frappe.whitelist()
def pdf_comparison(
    doctype,
    name,
    print_format=None,
    no_letterhead=0,
    letterhead=None,
    language=None,
    settings=None,
    mode="tbs",
    **kwargs,
):
    """
    Return an HTML comparison page showing:
    1. Collapsible HTML source panel (the raw Print Format HTML + CSS)
    2. PDF preview panel (embedded PDF via data URI)

    This lets you see the real DOM + CSS AND the PDF rendering side-by-side.

    Args:
        mode: "tbs" = clean TBS approach (Print Format only)
              "frappe" = Frappe's standard approach (PrintView wrapper)
    """
    # Parse settings for forwarding to render pipeline
    parsed_settings = {}
    if settings:
        if isinstance(settings, str):
            try:
                parsed_settings = frappe.parse_json(settings) or {}
            except Exception:
                pass
        elif isinstance(settings, dict):
            parsed_settings = settings

    # Get HTML based on mode
    if mode == "tbs":
        # TBS approach: clean standalone HTML
        raw_html = get_standalone_print_html(
            doctype=doctype,
            name=name,
            print_format=print_format,
            no_letterhead=no_letterhead,
            letterhead=letterhead,
            language=language,
            settings=parsed_settings,
        )
        approach_label = "TBS PDF (Clean Standalone)"
    else:
        # Frappe approach: standard PrintView HTML with wrapper
        raw_html = get_frappe_print_html(
            doctype=doctype,
            name=name,
            print_format=print_format,
            no_letterhead=no_letterhead,
            letterhead=letterhead,
            language=language,
        )
        approach_label = "Frappe Standard PDF (With Wrapper)"

    # Extract body content from raw HTML for display
    body_match = re.search(r"<body[^>]*>(.*)</body>", raw_html, re.DOTALL)
    body_content = body_match.group(1).strip() if body_match else raw_html

    # Extract CSS from <style> tags
    style_match = re.search(r"<style[^>]*>(.*?)</style>", raw_html, re.DOTALL)
    css_content = style_match.group(1).strip() if style_match else ""

    # Generate PDF using Chrome via frappe.get_print (for faithful PDF preview)
    try:
        pdf_bytes = frappe.get_print(
            doctype=doctype,
            name=name,
            print_format=print_format,
            as_pdf=True,
            no_letterhead=no_letterhead,
            letterhead=letterhead,
            pdf_generator="chrome",
        )
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    except Exception as e:
        frappe.log_error(f"PDF comparison error: {e}")
        pdf_base64 = ""

    # Escape user-controlled values before interpolating into HTML
    doc_title = escape_html(f"{doctype} / {name}")
    pf_name = escape_html(print_format or "Standard")
    lang_attr = escape_html(language or "en")

    # Build comparison HTML page
    comparison_html = f"""<!DOCTYPE html>
<html lang="{lang_attr}">
<head>
    <meta charset="UTF-8">
    <title>PDF Comparison - {doc_title}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #1e1e2e;
            color: #cdd6f4;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        .header {{
            background: #181825;
            border-bottom: 1px solid #313244;
            padding: 12px 20px;
            display: flex;
            align-items: center;
            gap: 16px;
            flex-shrink: 0;
        }}
        .header h1 {{
            font-size: 16px;
            font-weight: 600;
            color: #cdd6f4;
        }}
        .badge {{
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }}
        .badge-tbs {{
            background: #1e3a5f;
            color: #89b4fa;
            border: 1px solid #89b4fa;
        }}
        .badge-frappe {{
            background: #3d2a4d;
            color: #cba6f7;
            border: 1px solid #cba6f7;
        }}
        .badge-pdf {{
            background: #1e3a2f;
            color: #a6e3a1;
            border: 1px solid #a6e3a1;
        }}
        .badge-html {{
            background: #3d2a1e;
            color: #fab387;
            border: 1px solid #fab387;
        }}
        .header-meta {{
            font-size: 12px;
            color: #6c7086;
        }}
        .panels {{
            display: flex;
            flex: 1;
            min-height: 0;
        }}
        .panel {{
            flex: 1;
            display: flex;
            flex-direction: column;
            min-width: 0;
            border-right: 1px solid #313244;
        }}
        .panel:last-child {{ border-right: none; }}
        .panel-header {{
            background: #181825;
            padding: 8px 16px;
            border-bottom: 1px solid #313244;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-shrink: 0;
        }}
        .panel-title {{
            font-size: 13px;
            font-weight: 600;
            color: #a6adc8;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .panel-body {{
            flex: 1;
            overflow: auto;
            min-height: 0;
        }}
        /* HTML source panel */
        .html-panel .panel-body {{
            padding: 0;
        }}
        .source-controls {{
            display: flex;
            gap: 8px;
            align-items: center;
        }}
        .tab-btn {{
            padding: 4px 12px;
            border: 1px solid #313244;
            background: transparent;
            color: #6c7086;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.15s;
        }}
        .tab-btn:hover {{ color: #cdd6f4; border-color: #45475a; }}
        .tab-btn.active {{
            background: #313244;
            color: #cdd6f4;
            border-color: #89b4fa;
        }}
        .source-content {{
            display: none;
            height: 100%;
        }}
        .source-content.active {{ display: block; }}
        pre {{
            margin: 0;
            padding: 16px;
            font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', monospace;
            font-size: 12px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-all;
            height: 100%;
            overflow: auto;
            color: #cdd6f4;
        }}
        pre .tag {{ color: #89b4fa; }}
        pre .attr {{ color: #f9e2af; }}
        pre .string {{ color: #a6e3a1; }}
        pre .comment {{ color: #6c7086; font-style: italic; }}
        pre .css-selector {{ color: #cba6f7; }}
        pre .css-property {{ color: #89b4fa; }}
        pre .css-value {{ color: #a6e3a1; }}
        /* PDF panel */
        .pdf-panel .panel-body {{
            background: #313244;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
            border-radius: 4px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.4);
        }}
        .no-pdf {{
            text-align: center;
            color: #6c7086;
            padding: 40px;
        }}
        /* Resize handle */
        .resize-handle {{
            width: 6px;
            background: #313244;
            cursor: col-resize;
            flex-shrink: 0;
            transition: background 0.15s;
        }}
        .resize-handle:hover {{ background: #45475a; }}
        /* Toolbar */
        .toolbar {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            gap: 8px;
            z-index: 100;
        }}
        .toolbar button {{
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s;
        }}
        .btn-print {{
            background: #89b4fa;
            color: #1e1e2e;
        }}
        .btn-print:hover {{ background: #b4befe; }}
        .btn-download {{
            background: #313244;
            color: #cdd6f4;
            border: 1px solid #45475a;
        }}
        .btn-download:hover {{ background: #45475a; }}
        @media print {{
            .header, .panel-header, .source-controls, .toolbar, .resize-handle {{ display: none !important; }}
            .panels {{ flex-direction: column; }}
            .panel {{ border-right: none; border-bottom: 1px solid #ccc; }}
            iframe {{ height: 100vh; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>PDF Comparison</h1>
        <span class="badge badge-{mode}">{approach_label}</span>
        <span class="badge badge-pdf">PDF</span>
        <span class="badge badge-html">HTML</span>
        <span class="header-meta">{pf_name} &bull; {doc_title}</span>
    </div>
    <div class="panels">
        <!-- Left: HTML Source -->
        <div class="panel html-panel">
            <div class="panel-header">
                <span class="panel-title">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
                    HTML Source &amp; CSS
                </span>
                <div class="source-controls">
                    <button class="tab-btn active" onclick="showTab('body')">Body</button>
                    <button class="tab-btn" onclick="showTab('css')">CSS</button>
                    <button class="tab-btn" onclick="showTab('all')">All</button>
                </div>
            </div>
            <div class="panel-body">
                <div id="tab-body" class="source-content active">
                    <pre>{highlight_html(body_content)}</pre>
                </div>
                <div id="tab-css" class="source-content">
                    <pre>{highlight_css(css_content)}</pre>
                </div>
                <div id="tab-all" class="source-content">
                    <pre>{highlight_html(raw_html)}</pre>
                </div>
            </div>
        </div>
        <div class="resize-handle"></div>
        <!-- Right: PDF Preview -->
        <div class="panel pdf-panel">
            <div class="panel-header">
                <span class="panel-title">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    PDF Preview
                </span>
            </div>
            <div class="panel-body">
                {
        f'<iframe src="data:application/pdf;base64,{pdf_base64}"></iframe>'
        if pdf_base64
        else '<div class="no-pdf"><p>PDF generation failed</p></div>'
    }
            </div>
        </div>
    </div>
    <div class="toolbar">
        <button class="btn-download" onclick="copyHTML()">Copy HTML</button>
        <button class="btn-print" onclick="window.print()">Print</button>
    </div>
    <script>
        function showTab(name) {{
            document.querySelectorAll('.source-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + name).classList.add('active');
            event.target.classList.add('active');
        }}
        function copyHTML() {{
            const html = atob("{pdf_base64}");
            navigator.clipboard.writeText(document.querySelector('.source-content.active pre').textContent).then(() => {{
                const btn = document.querySelector('.btn-download');
                btn.textContent = 'Copied!';
                setTimeout(() => btn.textContent = 'Copy HTML', 1500);
            }});
        }}
        // Resizable panels
        const panels = document.querySelector('.panels');
        const handle = document.querySelector('.resize-handle');
        let resizing = false;
        handle.addEventListener('mousedown', (e) => {{
            resizing = true;
            e.preventDefault();
        }});
        document.addEventListener('mousemove', (e) => {{
            if (!resizing) return;
            const pct = (e.clientX / window.innerWidth) * 100;
            document.querySelector('.html-panel').style.flex = `0 0 ${{pct}}%`;
            document.querySelector('.pdf-panel').style.flex = `0 0 ${{100 - pct}}%`;
        }});
        document.addEventListener('mouseup', () => {{ resizing = false; }});
    </script>
</body>
</html>"""

    # Return as a proper Flask Response so Frappe does NOT JSON-serialize the HTML
    response = Response(comparison_html, mimetype="text/html")
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response


@frappe.whitelist()
def tbs_html_preview(
    doctype,
    name,
    print_format=None,
    no_letterhead=0,
    letterhead=None,
    language=None,
    settings=None,
    **kwargs,
):
    """
    Return pure standalone HTML for style debugging.

    Uses ONLY the Print Format's HTML and CSS. No Frappe wrapper, no action-banner,
    no .print-format-gutter, no embedded PDF. Just the clean print body + CSS
    so you can inspect styles in DevTools.

    Returns text/html Response directly — NOT JSON.
    """
    print_format = print_format or kwargs.get("format")

    # Parse settings JSON if passed as string
    parsed_settings = {}
    if settings:
        if isinstance(settings, str):
            try:
                parsed_settings = frappe.parse_json(settings) or {}
            except Exception:
                pass
        elif isinstance(settings, dict):
            parsed_settings = settings

    # Build the clean standalone HTML
    standalone_html = get_standalone_print_html(
        doctype=doctype,
        name=name,
        print_format=print_format,
        no_letterhead=no_letterhead,
        letterhead=letterhead,
        language=language,
        settings=parsed_settings,
    )

    response = Response(standalone_html, mimetype="text/html")
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response


def get_standalone_print_html(
    doctype,
    name,
    print_format=None,
    no_letterhead=0,
    letterhead=None,
    language=None,
    settings=None,
):
    """
    Build standalone HTML using ONLY the Print Format's HTML and CSS.
    No Frappe Print View wrapper CSS, no .print-format-gutter, no action-banner.
    """
    # Load document and validate permission
    doc = frappe.get_doc(doctype, name)
    validate_print_permission(doc)

    # Load Print Format
    if not print_format:
        print_format = doc.meta.default_print_format or "Standard"

    pf = None
    if print_format and print_format != "Standard":
        try:
            pf = frappe.get_doc("Print Format", print_format)
        except Exception:
            pass

    no_letterhead = is_no_letterhead_enabled(no_letterhead)

    # Get letterhead
    letterhead_html = ""
    if not no_letterhead and letterhead:
        try:
            lh = frappe.get_doc("Letter Head", letterhead)
            if lh.content:
                letterhead_html = frappe.utils.jinja.render_template(
                    lh.content, {"doc": doc.as_dict()}
                )
        except Exception:
            pass

    # Get Print Format HTML through the proper render pipeline.
    # Both Print Designer and standard/Jinja formats are handled correctly
    # by get_standard_print_body, which calls get_html_and_style (triggering
    # the Print Designer override for Print Designer formats).
    # Forward settings so watermark/orientation from the sidebar are applied.
    print_body_html = get_standard_print_body(doc, pf, no_letterhead, letterhead, settings=settings)

    # Get Print Format CSS
    print_css = ""
    if pf and pf.css:
        print_css = pf.css

    # Build standalone HTML
    # Wrap body content with letterhead if present
    body_content = print_body_html
    if letterhead_html:
        body_content = f'<div class="letter-head">{letterhead_html}</div>\n{body_content}'

    # Extract page_orientation from settings (for PDF page sizing)
    page_orientation = "Portrait"
    if settings:
        page_orientation = settings.get("page_orientation", "Portrait")

    # Determine @page CSS from Print Format CSS
    page_css = build_page_css(print_css, page_orientation=page_orientation)

    # Build the complete standalone HTML
    # Note: we intentionally do NOT include:
    # - Frappe Print View Styles (standard.css)
    # - .print-format-gutter CSS
    # - .action-banner HTML
    # - Any framework CSS (Bootstrap, Desk, etc.)
    title = escape_html(doc.get_title() or name)
    lang_attr = escape_html(language or frappe.local.lang or "en")

    standalone_html = f"""<!DOCTYPE html>
<html lang="{lang_attr}" dir="ltr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
{page_css}
{print_css}
    </style>
</head>
<body>
{body_content}
</body>
</html>"""

    return standalone_html


def is_no_letterhead_enabled(value):
    """Normalize Frappe URL/form values for no_letterhead."""
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def get_standard_print_body(doc, print_format, no_letterhead, letterhead, settings=None):
    """
    Render standard/Jinja print format body HTML.

    Uses frappe.call() to avoid direct imports of frappe.www modules.
    Strips the Frappe print view wrapper (action-banner, print-format-gutter)
    to get ONLY the print format body content.
    """
    # Use frappe.call() to invoke the whitelisted get_html_and_style
    # This calls our override (printview_watermark) if available.
    # Forward settings so watermark/orientation from the sidebar are applied.
    try:
        result = frappe.call(
            "frappe.www.printview.get_html_and_style",
            doc=doc.doctype,
            name=doc.name,
            print_format=print_format.name if print_format else None,
            no_letterhead=is_no_letterhead_enabled(no_letterhead),
            letterhead=letterhead,
            settings=frappe.as_json(settings or {}),
        )
        if result and result.get("html"):
            body_html = extract_body_content(result["html"])
            # Strip the Frappe wrapper HTML:
            # Remove <div class="action-banner...>...</div>
            body_html = strip_frappe_wrapper(body_html)
            return body_html
    except Exception:
        pass
    return ""


def extract_body_content(html):
    """Return body inner HTML if a renderer returns a full document."""
    body_match = re.search(r"<body[^>]*>(.*?)</body>", html, flags=re.DOTALL | re.IGNORECASE)
    if body_match:
        return body_match.group(1).strip()

    html = re.sub(r"<!doctype[^>]*>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"<head[^>]*>.*?</head>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"</?html[^>]*>", "", html, flags=re.IGNORECASE)
    return html.strip()


def strip_frappe_wrapper(html):
    """
    Strip Frappe Print View wrapper elements from HTML.
    Removes: <div class="action-banner...>...</div>
    Removes: <div class="print-format-gutter">...
    Returns only the body content.
    """
    # Remove action-banner div
    html = re.sub(
        r'<div[^>]*class="[^"]*action-banner[^"]*"[^>]*>.*?</div>\s*',
        "",
        html,
        flags=re.DOTALL,
    )
    # Remove print-format-gutter wrapper div (the OUTER one, keeps inner content)
    # Match <div class="print-format-gutter"> but keep what's inside
    html = re.sub(
        r'<div[^>]*class="[^"]*print-format-gutter[^"]*"[^>]*>',
        "",
        html,
        count=1,
        flags=re.DOTALL,
    )
    return html


def build_page_css(print_css, page_orientation="Portrait"):
    """
    Extract @page CSS from Print Format CSS and build proper page rules.
    Falls back to A4 defaults based on orientation.
    """
    # Parse @page rule from Print Format CSS if present
    page_rule = extract_page_rule(print_css)

    if page_rule:
        # Use the @page rule from Print Format CSS
        return f"@page {{\n  {page_rule}\n}}"

    # No @page in CSS - build default based on orientation
    if page_orientation == "Landscape":
        return """@page {
  size: A4 landscape;
  margin: 0;
}"""
    else:
        return """@page {
  size: A4 portrait;
  margin: 0;
}"""


def extract_page_rule(css):
    """Extract @page rule from CSS string."""
    if not css:
        return None

    # Match @page { ... }
    match = re.search(r"@page\s*\{([^}]+)\}", css, re.DOTALL)
    if match:
        content = match.group(1)
        # Extract properties
        size_match = re.search(r"size\s*:\s*([^;]+);", content)
        margin_match = re.search(r"margin\s*:\s*([^;]+);", content)

        parts = []
        if size_match:
            parts.append(f"  size: {size_match.group(1).strip()};")
        if margin_match:
            parts.append(f"  margin: {margin_match.group(1).strip()};")

        return "\n".join(parts)

    return None


def get_frappe_print_html(
    doctype, name, print_format=None, no_letterhead=0, letterhead=None, language=None
):
    """
    Get HTML using Frappe's standard PrintView pipeline (with wrapper).
    This includes the .print-format-gutter, action-banner, and PrintView CSS.
    Used for the "frappe" mode in pdf_comparison.
    """
    doc = frappe.get_doc(doctype, name)
    validate_print_permission(doc)

    try:
        result = frappe.call(
            "frappe.www.printview.get_html_and_style",
            doc=doc.doctype,
            name=doc.name,
            print_format=print_format,
            no_letterhead=is_no_letterhead_enabled(no_letterhead),
            letterhead=letterhead,
        )
        if result and result.get("html"):
            return result["html"]
    except Exception:
        pass
    return "<body><p>Failed to load PrintView HTML</p></body>"


def highlight_html(html):
    """Basic HTML syntax highlighting for display."""
    if not html:
        return ""
    # Escape HTML entities first
    html_escaped = html.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Simple syntax highlighting
    result = []
    i = 0
    while i < len(html_escaped):
        if html_escaped[i : i + 4] == "&lt;":
            end = html_escaped.find("&gt;", i)
            if end == -1:
                result.append(html_escaped[i:])
                break
            tag = html_escaped[i : end + 4]
            highlighted = re.sub(
                r"(&lt;/?)([\w-]+)",
                r'<span class="tag">\1\2</span>',
                tag,
            )
            highlighted = re.sub(
                r"([\w-]+)(=)(&quot;[^&]*&quot;|\'[^\']*\')",
                r'<span class="attr">\1</span><span class="string">\2\3</span>',
                highlighted,
            )
            result.append(highlighted)
            i = end + 4
        else:
            result.append(html_escaped[i])
            i += 1
    return "".join(result)


def highlight_css(css):
    """Basic CSS syntax highlighting for display."""
    if not css:
        return ""
    css_escaped = (
        css.replace("&amp;", "&amp;amp;").replace("<", "&amp;lt;").replace(">", "&amp;gt;")
    )
    css_escaped = re.sub(
        r"([^{}+,>~:\s][^{}]*?)\s*\\{",
        r'<span class="css-selector">\1</span> {',
        css_escaped,
    )
    css_escaped = re.sub(
        r"([\w-]+)\s*:",
        r'<span class="css-property">\1</span>:',
        css_escaped,
    )
    css_escaped = re.sub(
        r":\s*([^;{}]+)",
        r': <span class="css-value">\1</span>',
        css_escaped,
    )
    return css_escaped
