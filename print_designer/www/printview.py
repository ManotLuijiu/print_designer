"""
Custom Print View for Print Designer
Replaces /printview to support watermark and page numbers for browser printing.

FIX: Now reuses shared logic from overrides/printview_watermark.py
instead of maintaining separate hardcoded fallbacks.

IMPORTANT: This file handles the WEBSITE print view (/printview URL).
The API endpoint frappe.www.printview.get_html_and_style is NOT overridden here.
It comes from the core Frappe file: frappe/frappe/www/printview.py
"""

import html as html_module
import re
from typing import Any

import frappe
from frappe.www.printview import get_context as core_get_context

# Import shared helpers from the newer override path
from print_designer.overrides.printview_watermark import (
    build_preview_copy_watermark_html,
    get_copy_watermark_text,
    get_page_number_border_css,
    get_page_number_position_css,
    get_watermark_position_css,
    log_to_print_designer,
    normalize_checkbox_value,
    normalize_copy_count,
    normalize_preview_color,
    normalize_watermark_font_size,
    normalize_watermark_measure,
    parse_watermark_settings_dict,
    resolve_basic_watermark_context,
)


def debug_get_html_and_style():
    """
    DEBUG: Check if this custom printview.py has get_html_and_style.
    It should NOT - the API endpoint comes from core Frappe.
    """
    print("[DEBUG PRINTVIEW] This is the CUSTOM printview.py (website print view)")
    print(
        "[DEBUG PRINTVIEW] The API endpoint frappe.www.printview.get_html_and_style comes from CORE frappe/frappe/www/printview.py"
    )
    print(
        "[DEBUG PRINTVIEW] This file only handles get_context for /printview URL (website sharing)"
    )


# Run debug on import
debug_get_html_and_style()

# Import shared helpers from the newer override path


def get_context(context: Any) -> dict:
    """
    Custom print view that wraps Frappe's core get_context()
    and adds watermark/page number support for Print Designer formats.
    """
    log_to_print_designer("[PRINTVIEW] Custom get_context called")

    # Call Frappe's core get_context
    print_context = core_get_context(context)

    # Get the body HTML
    body_html = print_context.get("body", "")
    if not body_html:
        return print_context

    # Get settings from form_dict
    settings = frappe.parse_json(frappe.form_dict.get("settings", "{}"))

    # Get print format to check if it's Print Designer
    print_format_name = frappe.form_dict.get("format")
    print_format_doc = None
    is_print_designer = False

    if print_format_name:
        try:
            print_format_doc = frappe.get_doc("Print Format", print_format_name)
            is_print_designer = (
                hasattr(print_format_doc, "print_designer")
                and print_format_doc.print_designer
                and hasattr(print_format_doc, "print_designer_body")
                and print_format_doc.print_designer_body
            )
        except Exception:
            pass

    # Only apply custom enhancements for Print Designer formats
    if is_print_designer:
        log_to_print_designer(f"[PRINTVIEW] Processing Print Designer format: {print_format_name}")

        # Inject watermark if configured (using shared logic)
        body_html = inject_watermark(body_html, settings, print_format_doc)

        # Inject page numbers if configured (using shared logic)
        body_html = inject_page_numbers(body_html, settings, print_format_doc)

        # Inject multi-copy if enabled
        body_html = inject_multi_copy(body_html, settings, print_format_doc)

        # Update context with modified body
        print_context["body"] = body_html

    return print_context


def inject_watermark(html_content: str, settings: dict, print_format_doc) -> str:
    """
    Inject watermark into HTML content using shared resolution logic.
    FIX: Now uses the same fallback chain as /desk/print/... path.
    """
    # Parse settings using shared helper
    parsed_settings = parse_watermark_settings_dict(settings)

    # Get doctype/name from settings for dynamic watermark
    context_doctype = parsed_settings.get("doctype")
    context_name = parsed_settings.get("name")

    # Use shared helper to resolve watermark context (same logic as /desk/print/...)
    base_context = resolve_basic_watermark_context(
        doctype=context_doctype,
        name=context_name,
        settings=settings,
        watermark_settings=parsed_settings.get("watermark_settings"),
    )

    watermark_mode = base_context["watermark_settings"]
    watermark_text = base_context["watermark_text"]

    # If no watermark configured, check print_designer_settings on print_format_doc
    if (not watermark_mode or watermark_mode == "None") and print_format_doc:
        pd_settings_str = print_format_doc.get("print_designer_settings", "{}")
        try:
            pd_settings = frappe.parse_json(pd_settings_str)
            if pd_settings and isinstance(pd_settings, dict):
                pd_watermark = pd_settings.get("watermark", {})
                if pd_watermark and isinstance(pd_watermark, dict):
                    pd_mode = pd_watermark.get("mode")
                    if pd_mode and pd_mode != "None":
                        watermark_mode = pd_mode
                        # Get per-format watermark text
                        if pd_mode == "Original on First Page":
                            watermark_text = frappe._("Original")
                        elif pd_mode == "Copy on All Pages":
                            watermark_text = frappe._("Copy")
                        elif pd_mode == "Original,Copy on Sequence":
                            watermark_text = frappe._("Original")
        except Exception:
            pass

    if not watermark_mode or watermark_mode == "None" or not watermark_text:
        return html_content

    # Get watermark parameters using shared normalization
    font_size = normalize_watermark_font_size(
        parsed_settings.get("watermark_font_size"), base_context.get("font_size", 24)
    )
    font_family = parsed_settings.get("watermark_font_family") or base_context.get(
        "font_family", "Kanit"
    )
    position = parsed_settings.get("watermark_position") or base_context.get(
        "position", "Top Right"
    )

    # Use shared normalization for margins
    margin_top = normalize_watermark_measure(
        parsed_settings.get("watermark_top"), base_context.get("margin_top", "0mm")
    )
    margin_right = normalize_watermark_measure(
        parsed_settings.get("watermark_right"), base_context.get("margin_right", "0mm")
    )
    margin_bottom = normalize_watermark_measure(
        parsed_settings.get("watermark_bottom"), base_context.get("margin_bottom", "0mm")
    )
    margin_left = normalize_watermark_measure(
        parsed_settings.get("watermark_left"), base_context.get("margin_left", "0mm")
    )

    # Get additional settings
    font_color = parsed_settings.get("watermark_font_color", "#999999")
    try:
        opacity = float(parsed_settings.get("watermark_opacity", 0.6))
    except (ValueError, TypeError):
        opacity = 0.6

    # Normalize color
    font_color = normalize_preview_color(font_color, "#999999")

    # Use shared position CSS generator
    position_config = {
        "position_top": parsed_settings.get("position_top"),
        "position_right": parsed_settings.get("position_right"),
        "position_bottom": parsed_settings.get("position_bottom"),
        "position_left": parsed_settings.get("position_left"),
    }
    position_css = get_watermark_position_css(
        position,
        position_config,
        margin_top=margin_top,
        margin_right=margin_right,
        margin_bottom=margin_bottom,
        margin_left=margin_left,
    )

    # Determine position type based on mode
    position_type = "absolute" if watermark_mode == "Original on First Page" else "fixed"

    log_to_print_designer(
        f"[PRINTVIEW] Building watermark: text={watermark_text}, mode={watermark_mode}, "
        f"position={position}, font_size={font_size}, position_type={position_type}"
    )

    # Build watermark HTML
    watermark_html = f"""
<style>
    @font-face {{
        font-family: 'Sarabun';
        src: url('/assets/print_designer/fonts/thai/Sarabun/Sarabun-Regular.ttf') format('truetype');
    }}
    .pd-watermark {{
        position: {position_type};
        {position_css}
        font-size: {font_size}px;
        color: {font_color};
        opacity: {opacity};
        font-weight: normal;
        font-family: {font_family}, sans-serif;
        z-index: 1000;
        text-transform: uppercase;
        pointer-events: none;
        text-align: center;
    }}
</style>
<div class="pd-watermark">{html_module.escape(str(watermark_text))}</div>
"""

    # Inject watermark into HTML
    # Always inject into header-html when it exists (position_type determines repeat, not injection point)
    log_to_print_designer(f"[PRINTVIEW] HTML first 500 chars: {html_content[:500]}")
    log_to_print_designer("[PRINTVIEW] Checking conditions:")
    log_to_print_designer(f"  - 'header-html' in content: {'header-html' in html_content}")
    log_to_print_designer(f"  - 'print-format' in content: {'print-format' in html_content}")
    log_to_print_designer(
        f"  - '__print_designer' in content: {'__print_designer' in html_content}"
    )
    log_to_print_designer(
        f"  - '__print-designer' in content: {'__print-designer' in html_content}"
    )

    # Inject watermark into header-render-container
    if 'id="header-render-container"' in html_content:
        # Use regex to find the opening div with header-render-container and inject watermark
        import re

        # Find the opening div tag and inject watermark + add position: relative style
        pattern = r'(<div[^>]*id="header-render-container"[^>]*>)'
        match = re.search(pattern, html_content)
        if match:
            opening_tag = match.group(1)
            # Add position: relative to existing style or create new style attribute
            if 'style="' in opening_tag:
                new_tag = opening_tag.replace('style="', 'style="position: relative; ')
            else:
                new_tag = opening_tag.replace(">", ' style="position: relative;">')
            new_tag_with_watermark = new_tag + watermark_html
            html_content = html_content.replace(opening_tag, new_tag_with_watermark, 1)
            log_to_print_designer("[PRINTVIEW] Injected into header-render-container")

            # DEBUG: Find watermark div and show its context
            wm_match = re.search(r'(<div class="pd-watermark">.{0,200})', html_content)
            if wm_match:
                log_to_print_designer(f"[DEBUG] Watermark context: {wm_match.group(1)}")
            # DEBUG: Show first 300 chars after injection
            header_pos = html_content.find('id="header-render-container"')
            if header_pos > 0:
                log_to_print_designer(
                    f"[DEBUG] Content after header-render-container: {html_content[header_pos : header_pos + 300]}"
                )
    elif '<div id="header-html">' in html_content:
        html_content = html_content.replace(
            '<div id="header-html">', f'<div id="header-html">{watermark_html}', 1
        )
        log_to_print_designer("[PRINTVIEW] Injected into header-html")
    elif '<div class="print-format">' in html_content:
        html_content = html_content.replace(
            '<div class="print-format">', f'{watermark_html}\n<div class="print-format">', 1
        )
        log_to_print_designer("[PRINTVIEW] Injected into print-format")
    elif '<div id="__print_designer">' in html_content:
        html_content = html_content.replace(
            '<div id="__print_designer">', f'{watermark_html}\n<div id="__print_designer">', 1
        )
        log_to_print_designer("[PRINTVIEW] Injected into __print_designer")
    elif '<div id="__print-designer">' in html_content:
        html_content = html_content.replace(
            '<div id="__print-designer">', f'{watermark_html}\n<div id="__print-designer">', 1
        )
        log_to_print_designer("[PRINTVIEW] Injected into __print-designer")
    else:
        html_content = watermark_html + html_content
        log_to_print_designer("[PRINTVIEW] No target found, prepended to content")

    return html_content


def inject_page_numbers(html_content: str, settings: dict, print_format_doc) -> str:
    """
    Inject page number elements into HTML content using shared resolution logic.

    Position mapping:
    - Top positions (Top Right, Top Left, Top Center) -> inject into #header-render-container
    - Bottom positions (Bottom Right, Bottom Left, Bottom Center) -> inject into #footer-render-container

    Uses position: absolute (not fixed) so it anchors to the relative container.
    """
    # Parse settings using shared helper
    parsed_settings = parse_watermark_settings_dict(settings)

    # Try to get print settings for fallback
    try:
        print_settings = frappe.get_single("Print Settings")
    except Exception:
        print_settings = {}

    # Get per-format page_number settings from print_designer_settings
    pd_page_number = {}
    if print_format_doc:
        pd_settings_str = print_format_doc.get("print_designer_settings", "{}")
        try:
            pd_settings = frappe.parse_json(pd_settings_str)
            if pd_settings and isinstance(pd_settings, dict):
                pd_page_number = pd_settings.get("page_number", {})
        except Exception:
            pass

    # Fallback chain: settings_dict > print_designer_settings > print_settings > defaults
    page_number_display = (
        parsed_settings.get("page_number_display")
        or (pd_page_number.get("display") if pd_page_number else None)
        or (getattr(print_settings, "page_number_display", None) if print_settings else None)
        or "Show"
    )

    if page_number_display != "Show":
        return html_content

    # Get page number parameters with proper fallback chain
    position = (
        parsed_settings.get("page_number_position")
        or (pd_page_number.get("position") if pd_page_number else None)
        or (getattr(print_settings, "page_number_position", None) if print_settings else None)
        or "Top Right"
    )
    font_family = (
        parsed_settings.get("page_number_font_family")
        or (pd_page_number.get("font_family") if pd_page_number else None)
        or (getattr(print_settings, "page_number_font_family", None) if print_settings else None)
        or "Sarabun"
    )
    font_size = (
        parsed_settings.get("page_number_font_size")
        or (pd_page_number.get("font_size") if pd_page_number else None)
        or (getattr(print_settings, "page_number_font_size", None) if print_settings else None)
        or 10
    )
    font_color = (
        parsed_settings.get("page_number_font_color")
        or (pd_page_number.get("font_color") if pd_page_number else None)
        or (getattr(print_settings, "page_number_font_color", None) if print_settings else None)
        or "#666666"
    )
    border_style = (
        parsed_settings.get("page_number_border")
        or (pd_page_number.get("border") if pd_page_number else None)
        or (getattr(print_settings, "page_number_border", None) if print_settings else None)
        or "Solid"
    )

    # Margin values
    margin_top = (
        parsed_settings.get("page_number_top")
        or (pd_page_number.get("top") if pd_page_number else None)
        or (getattr(print_settings, "page_number_top", None) if print_settings else None)
        or 2
    )
    margin_right = (
        parsed_settings.get("page_number_right")
        or (pd_page_number.get("right") if pd_page_number else None)
        or (getattr(print_settings, "page_number_right", None) if print_settings else None)
        or 2
    )
    margin_bottom = (
        parsed_settings.get("page_number_bottom")
        or (pd_page_number.get("bottom") if pd_page_number else None)
        or (getattr(print_settings, "page_number_bottom", None) if print_settings else None)
        or 2
    )
    margin_left = (
        parsed_settings.get("page_number_left")
        or (pd_page_number.get("left") if pd_page_number else None)
        or (getattr(print_settings, "page_number_left", None) if print_settings else None)
        or 2
    )

    # Normalize values
    try:
        font_size = int(font_size)
    except (ValueError, TypeError):
        font_size = 10

    try:
        margin_top = int(margin_top)
        margin_right = int(margin_right)
        margin_bottom = int(margin_bottom)
        margin_left = int(margin_left)
    except (ValueError, TypeError):
        margin_top = margin_right = margin_bottom = margin_left = 2

    font_color = normalize_preview_color(font_color, "#666666")

    log_to_print_designer(
        f"[PRINTVIEW] Building page number: position={position}, font_family={font_family}, "
        f"font_size={font_size}, color={font_color}, border={border_style}"
    )

    # Determine position class for CSS selector
    position_class = position.lower().replace(" ", "-")  # "Top Right" -> "top-right"

    # Determine which container to inject into based on position
    is_top_position = position.lower().startswith("top")

    log_to_print_designer(
        f"[PRINTVIEW] Page number: position={position}, is_top={is_top_position}, class={position_class}"
    )

    # Build page number HTML using shared helpers
    # IMPORTANT: Use position: absolute (not fixed) to anchor within relative container
    position_css = get_page_number_position_css(
        position,
        top=f"{margin_top}mm",
        right=f"{margin_right}mm",
        bottom=f"{margin_bottom}mm",
        left=f"{margin_left}mm",
    )
    border_css = get_page_number_border_css(border_style, font_color)

    page_number_html = f"""
<style>
    .pd-page-number {{
        position: absolute;
        {position_css}
        z-index: 1001;
        pointer-events: none;
        font-family: {font_family}, sans-serif;
        font-size: {font_size}pt;
        font-weight: 500;
        color: {font_color};
        background: rgba(255, 255, 255, 0.92);
        padding: 2px 8px;
        border-radius: 999px;
        {border_css}
        line-height: 1.3;
    }}
</style>
<div class="pd-page-number {position_class}">
    {frappe._("Page")} <span class="page_info_page">1</span> / <span class="page_info_topage">1</span>
</div>
"""

    # Inject page number based on position
    # Top positions -> header-render-container
    # Bottom positions -> footer-render-container
    if is_top_position:
        # Inject into header-render-container
        if 'id="header-render-container"' in html_content:
            pattern = r'(<div[^>]*id="header-render-container"[^>]*>)'
            match = re.search(pattern, html_content)
            if match:
                opening_tag = match.group(1)
                # Ensure container has position: relative
                if 'style="' in opening_tag:
                    if "position: relative" not in opening_tag:
                        new_tag = opening_tag.replace('style="', 'style="position: relative; ')
                    else:
                        new_tag = opening_tag
                else:
                    new_tag = opening_tag.replace(">", ' style="position: relative;">')
                html_content = html_content.replace(opening_tag, new_tag + page_number_html, 1)
                log_to_print_designer(
                    "[PRINTVIEW] Page number injected into header-render-container"
                )
        elif '<div id="header-html">' in html_content:
            html_content = html_content.replace(
                '<div id="header-html">',
                f'<div id="header-html"><div id="header-render-container" style="position: relative;">{page_number_html}',
                1,
            )
            log_to_print_designer(
                "[PRINTVIEW] Page number injected into header-html with new container"
            )
        elif '<div class="print-format">' in html_content:
            html_content = html_content.replace(
                '<div class="print-format">', page_number_html + '\n<div class="print-format">', 1
            )
            log_to_print_designer("[PRINTVIEW] Page number injected into print-format (fallback)")
        else:
            html_content += page_number_html
            log_to_print_designer("[PRINTVIEW] Page number appended (fallback)")
    else:
        # Inject into footer-render-container
        if 'id="footer-render-container"' in html_content:
            pattern = r'(<div[^>]*id="footer-render-container"[^>]*>)'
            match = re.search(pattern, html_content)
            if match:
                opening_tag = match.group(1)
                # Ensure container has position: relative
                if 'style="' in opening_tag:
                    if "position: relative" not in opening_tag:
                        new_tag = opening_tag.replace('style="', 'style="position: relative; ')
                    else:
                        new_tag = opening_tag
                else:
                    new_tag = opening_tag.replace(">", ' style="position: relative;">')
                html_content = html_content.replace(opening_tag, new_tag + page_number_html, 1)
                log_to_print_designer(
                    "[PRINTVIEW] Page number injected into footer-render-container"
                )
        elif '<div id="footer-html">' in html_content:
            # Find footer-html and add footer-render-container if needed
            footer_pattern = r'(<div[^>]*id="footer-html"[^>]*>)'
            footer_match = re.search(footer_pattern, html_content)
            if footer_match:
                footer_opening = footer_match.group(1)
                if 'id="footer-render-container"' not in html_content:
                    new_footer = (
                        footer_opening
                        + f'<div id="footer-render-container" style="position: relative;">{page_number_html}'
                    )
                    html_content = html_content.replace(footer_opening, new_footer, 1)
                    log_to_print_designer(
                        "[PRINTVIEW] Page number injected into footer-html with new container"
                    )
                else:
                    html_content = html_content.replace(
                        footer_opening, footer_opening + page_number_html, 1
                    )
                    log_to_print_designer("[PRINTVIEW] Page number injected into footer-html")
        elif '<div class="print-format">' in html_content:
            html_content = html_content.replace(
                '<div class="print-format">', page_number_html + '\n<div class="print-format">', 1
            )
            log_to_print_designer("[PRINTVIEW] Page number injected into print-format (fallback)")
        else:
            html_content += page_number_html
            log_to_print_designer("[PRINTVIEW] Page number appended (fallback)")

    return html_content


def inject_multi_copy(html_content: str, settings: dict, print_format_doc) -> str:
    """
    Inject multi-copy support into HTML content.

    When enable_multiple_copies is true and default_copy_count > 1,
    duplicates the HTML with per-copy watermarks.
    """
    # Parse settings using shared helper
    parsed_settings = parse_watermark_settings_dict(settings)

    # Try to get print settings for fallback
    try:
        print_settings = frappe.get_single("Print Settings")
    except Exception:
        print_settings = {}

    # Get copy settings with fallback chain
    copy_enabled = normalize_checkbox_value(
        parsed_settings.get("enable_multiple_copies"),
        normalize_checkbox_value(
            getattr(print_settings, "enable_multiple_copies", None) if print_settings else None,
            False,
        ),
    )
    copy_count = normalize_copy_count(
        parsed_settings.get("default_copy_count"),
        getattr(print_settings, "default_copy_count", 1) if print_settings else 1,
    )

    log_to_print_designer(
        f"[PRINTVIEW] Multi-copy check: enabled={copy_enabled}, count={copy_count}"
    )

    if not copy_enabled or copy_count <= 1:
        return html_content

    log_to_print_designer(f"[PRINTVIEW] Applying multi-copy: count={copy_count}")

    # Get watermark settings for per-copy watermarks
    watermark_mode = parsed_settings.get("watermark_settings") or "None"
    watermark_position = parsed_settings.get("watermark_position") or "Top Right"
    font_size = normalize_watermark_font_size(parsed_settings.get("watermark_font_size"), 24)
    font_family = parsed_settings.get("watermark_font_family") or "Kanit"
    watermark_color = normalize_preview_color(
        parsed_settings.get("watermark_font_color"), "#999999"
    )
    try:
        watermark_opacity = float(parsed_settings.get("watermark_opacity", 0.6))
    except (ValueError, TypeError):
        watermark_opacity = 0.6

    # Get margin values
    margin_top = normalize_watermark_measure(parsed_settings.get("watermark_top"), "0mm")
    margin_right = normalize_watermark_measure(parsed_settings.get("watermark_right"), "0mm")
    margin_bottom = normalize_watermark_measure(parsed_settings.get("watermark_bottom"), "0mm")
    margin_left = normalize_watermark_measure(parsed_settings.get("watermark_left"), "0mm")

    position_config = {
        "position_top": parsed_settings.get("position_top"),
        "position_right": parsed_settings.get("position_right"),
        "position_bottom": parsed_settings.get("position_bottom"),
        "position_left": parsed_settings.get("position_left"),
    }

    # Build separator style
    separator_style = """
<style>
    .pd-preview-copy-separator {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 30px;
        padding: 0 24px;
        background-color: #6c757d !important;
    }
    .pd-preview-copy-separator-label {
        display: flex;
        align-items: center;
        gap: 12px;
        width: min(960px, 100%);
        color: #fff;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .pd-preview-copy-separator-label::before,
    .pd-preview-copy-separator-label::after {
        content: "";
        flex: 1;
        border-top: 1px dashed #bdbdbd;
    }
    @media print {
        .pd-preview-copy-separator {
            display: none !important;
        }
    }
</style>
"""

    # Build copies with per-copy watermarks
    copies = []
    for idx in range(copy_count):
        copy_index = idx + 1
        watermark_text = get_copy_watermark_text(watermark_mode, copy_index)

        # Build per-copy watermark
        copy_watermark_html = ""
        if watermark_text:
            position_css = get_watermark_position_css(
                watermark_position,
                position_config,
                margin_top=margin_top,
                margin_right=margin_right,
                margin_bottom=margin_bottom,
                margin_left=margin_left,
            )
            copy_watermark_html = build_preview_copy_watermark_html(
                watermark_text,
                position_css,
                font_size,
                font_family,
                watermark_color,
                watermark_opacity,
            )

        # Build separator and page break for copies after first
        page_break = ""
        separator_html = ""
        if idx > 0:
            page_break = " page-break-before: always; break-before: page;"
            separator_html = f'<div class="pd-preview-copy-separator"><div class="pd-preview-copy-separator-label">{frappe._("Copy")} {copy_index}</div></div>'

        # Wrap copy with watermark
        copies.append(
            f'{separator_html}<div class="pd-preview-copy" data-copy-index="{copy_index}" style="position: relative;{page_break}">\n{copy_watermark_html}\n{html_content}\n</div>'
        )

    # Return multi-copy HTML
    return separator_style + "\n".join(copies)
