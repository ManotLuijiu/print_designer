# PrintView Structure & Override Pattern

> How Print Designer overrides/extends Frappe's default `/printview` using custom Python controller and HTML template.

## Overview

Frappe's standard print view is served by `frappe.apps.print_designer.www.printview` (or via `frappe.printing.page.print_view.print_view`). Print Designer replaces this with its own implementation to inject:

- **Watermark** (positioned via CSS)
- **Page Number** (positioned via CSS)
- **Custom CSS bundles** (e.g., `watermark.bundle.scss`)
- **Thai font support** (Google Fonts + local fallbacks)

---

## PrintView HTML Structure

The generated HTML has a fixed 3-child structure under `#__print_designer`:

```
#__print_designer
├── div#header-html
│   └── div#header-render-container       ← position: relative, overflow: hidden
│       ├── <style>                       ← Injected CSS (watermark, fonts)
│       ├── div.pd-watermark              ← Watermark element
│       ├── div.pd-page-number            ← Page Number (when position = Top*)
│       ├── div.visible-pdf               ← Visible-only content
│       ├── div.hidden-pdf                ← PDF-only content (print view)
│       ├── div#firstPageHeader           ← Per-page header variants
│       ├── div#oddPageHeader
│       ├── div#evenPageHeader
│       └── div#lastPageHeader
│
├── div#body-content
│   └── ... (main document content)
│
└── div#footer-html  (class: hidden-pdf)
    └── div#footer-render-container      ← position: relative
        ├── div.pd-page-number            ← Page Number (when position = Bottom*)
        ├── div#firstPageFooter
        ├── div#oddPageFooter
        ├── div#evenPageFooter
        └── div#lastPageFooter
```

### Key Container Properties

| Container | Position | Overflow | Purpose |
|-----------|----------|----------|---------|
| `#header-render-container` | `relative` | `hidden` | Watermark / Page Number (Top*) |
| `#footer-render-container` | `relative` | `none` | Page Number (Bottom*) |

---

## Page Number Position Strategy

### Position → Container Mapping

The `page_number_position` setting determines where the page number element is placed:

| Position | Container | CSS Position |
|----------|-----------|--------------|
| **Top Right** | `#header-render-container` | `absolute; top: Xmm; right: Ymm` |
| **Top Left** | `#header-render-container` | `absolute; top: Xmm; left: Ymm` |
| **Top Center** | `#header-render-container` | `absolute; top: Xmm; left: 50%; transform: translateX(-50%)` |
| **Bottom Right** | `#footer-render-container` | `absolute; bottom: Xmm; right: Ymm` |
| **Bottom Left** | `#footer-render-container` | `absolute; bottom: Xmm; left: Ymm` |
| **Bottom Center** | `#footer-render-container` | `absolute; bottom: Xmm; left: 50%; transform: translateX(-50%)` |

### Key Principle

- **Top positions** → Place inside `#header-render-container` (uses `position: absolute`)
- **Bottom positions** → Place inside `#footer-render-container` (uses `position: absolute`)
- **NOT** `position: fixed` anymore — we use `position: absolute` within the relative container

### Why This Matters

1. **Watermark** is in header → Top positions align naturally
2. **Footer** is at page bottom → Bottom positions align naturally
3. Both containers have `position: relative` → child `position: absolute` anchors correctly

---

## Sidebar Settings Fields

These fields control page number appearance (from `/desk/print` sidebar):

```html
<div class="page-number-grid" style="...">
  <div class="page-number-display" data-fieldname="page_number_display">...</div>
  <div class="page-number-position" data-fieldname="page_number_position">
    <!-- Options: Top Right, Top Left, Top Center, Bottom Center, Bottom Right, Bottom Left -->
  </div>
  <div class="page-number-font-family" data-fieldname="page_number_font_family">...</div>
  <div class="page-number-font-size" data-fieldname="page_number_font_size">...</div>
  <div class="page-number-font-color" data-fieldname="page_number_font_color">...</div>
  <div class="page-number-border" data-fieldname="page_number_border">...</div>
  <div class="page-number-offset-grid" style="...">
    <!-- page_number_top, page_number_right, page_number_bottom, page_number_left -->
  </div>
</div>
```

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `page_number_display` | Select | Show | Toggle on/off |
| `page_number_position` | Select | Top Right | Placement location |
| `page_number_font_family` | Select | Sarabun | Font family |
| `page_number_font_size` | Int | 10 | Font size (pt) |
| `page_number_font_color` | Color | #000000 | Text color |
| `page_number_border` | Select | None | Border style |
| `page_number_top` | Int | 2 | Top offset (mm) |
| `page_number_right` | Int | 8 | Right offset (mm) |
| `page_number_bottom` | Int | 2 | Bottom offset (mm) |
| `page_number_left` | Int | 2 | Left offset (mm) |

### Position → Container Mapping (The Core Rule)

```
page_number_position  →  inject into
─────────────────────────────────────────
Top Right             →  #header-render-container
Top Left              →  #header-render-container
Top Center           →  #header-render-container
Bottom Right         →  #footer-render-container
Bottom Left          →  #footer-render-container
Bottom Center        →  #footer-render-container
```

The **current broken behavior**: `.pd-page-number` is placed as a sibling of `#header-html` (outside `#__print_designer`), using `position: fixed`. This does not work correctly for bottom positions.

The **correct behavior**: `.pd-page-number` is injected as a child of the matching container (`#header-render-container` or `#footer-render-container`), using `position: absolute`.

---

## Watermark CSS

```css
.pd-watermark {
    position: absolute;                    /* Anchored to #header-render-container */
    top: var(--watermark-top, 10mm);
    right: var(--watermark-right, 10mm);
    font-size: 24px;
    color: #999999;
    opacity: 0.6;
    font-family: Kanit, sans-serif;
    z-index: 1000;
    text-transform: uppercase;
    pointer-events: none;
    text-align: center;
}
```

---

## Page Number CSS

### Base Styles (for all positions)

```css
.pd-page-number {
    position: absolute;                    /* NOT fixed - anchored to container */
    z-index: 1001;
    font-family: var(--page-number-font, 'Sarabun', sans-serif);
    font-size: var(--page-number-size, 10pt);
    font-weight: 500;
    color: var(--page-number-color, #000000);
    background: rgba(255, 255, 255, 0.92);
    padding: 2px 8px;
    border-radius: 999px;
    border: var(--page-number-border, none);
    line-height: 1.3;
    pointer-events: none;
}
```

### Position-Specific Styles

```css
/* Top Right (default) */
.pd-page-number.top-right {
    top: var(--page-number-top, 2mm);
    right: var(--page-number-right, 8mm);
}

/* Top Left */
.pd-page-number.top-left {
    top: var(--page-number-top, 2mm);
    left: var(--page-number-left, 8mm);
}

/* Top Center */
.pd-page-number.top-center {
    top: var(--page-number-top, 2mm);
    left: 50%;
    transform: translateX(-50%);
}

/* Bottom Right */
.pd-page-number.bottom-right {
    bottom: var(--page-number-bottom, 2mm);
    right: var(--page-number-right, 8mm);
}

/* Bottom Left */
.pd-page-number.bottom-left {
    bottom: var(--page-number-bottom, 2mm);
    left: var(--page-number-left, 8mm);
}

/* Bottom Center */
.pd-page-number.bottom-center {
    bottom: var(--page-number-bottom, 2mm);
    left: 50%;
    transform: translateX(-50%);
}
```

---

## Override Pattern: printview.py

Print Designer provides its own `printview.py` controller at:

```
print_designer/www/printview.py
```

### How It Works

1. **Route Registration** (via `website_route_rules` in `hooks.py`):

   ```python
   website_route_rules = [
       {"from_route": "/printview", "to_route": "print_designer/www/printview"},
   ]
   ```

2. **get_context()** method:
   - Accepts query params: `doctype`, `name`, `format`, `no_letterhead`, `letterhead`, `settings`, `_lang`, `pdf_generator`
   - Fetches the doc and print format
   - Renders custom HTML template (not Frappe's default)
   - Passes `settings` JSON as context for watermark/page-number CSS injection

3. **Context Keys**:
   - `doc` — Document object
   - `print_format` — Print format name
   - `print_style` — CSS content for watermark, page-number
   - `page_number_html` — Page number element HTML (positioned correctly)
   - `lang` — Language code (`en`, `th`, etc.)
   - `pdf_generator` — `"chrome"` or `"weasyprint"`

---

## Template: printview.html

Located at `print_designer/www/printview.html`.

### Template Responsibilities

1. **Load CSS Bundles**:

   ```html
   <link rel="stylesheet" href="/assets/print_designer/css/print_designer.bundle.css">
   <link rel="stylesheet" href="/assets/print_designer/css/watermark.bundle.css">
   ```

2. **Inject Dynamic Print Style**:

   ```html
   <style>{{ print_style }}</style>
   ```

3. **Build HTML Structure**:

   ```html
   <div id="__print_designer">
       <div id="header-html">
           <div id="header-render-container">
               <!-- Watermark (always here) -->
               <div class="pd-watermark">{{ watermark_text or 'ORIGINAL' }}</div>
               
               <!-- Page Number (TOP positions only) -->
               {% if page_number_position.startswith('Top') %}
               {{ page_number_html }}
               {% endif %}
               
               <!-- Page-specific headers -->
               <div id="firstPageHeader">...</div>
               <div id="oddPageHeader">...</div>
               <div id="evenPageHeader">...</div>
               <div id="lastPageHeader">...</div>
           </div>
       </div>
       
       <div id="body-content">
           {{ body_html }}
       </div>
       
       <div id="footer-html" class="hidden-pdf">
           <div id="footer-render-container">
               <!-- Page Number (BOTTOM positions only) -->
               {% if page_number_position.startswith('Bottom') %}
               {{ page_number_html }}
               {% endif %}
               
               <!-- Page-specific footers -->
               <div id="firstPageFooter">...</div>
               <div id="oddPageFooter">...</div>
               <div id="evenPageFooter">...</div>
               <div id="lastPageFooter">...</div>
           </div>
       </div>
   </div>
   ```

---

## Server-Side Processing (printview.py)

### Settings JSON Schema

```json
{
    "watermark_top": 10,
    "watermark_right": 10,
    "page_number_display": "Show",
    "page_number_position": "Top Right",
    "page_number_font_family": "Sarabun",
    "page_number_font_size": 10,
    "page_number_font_color": "#000000",
    "page_number_border": "None",
    "page_number_top": 2,
    "page_number_right": 8,
    "page_number_bottom": 2,
    "page_number_left": 2
}
```

### Key Functions

```python
def generate_print_style(settings):
    """Generate CSS for watermark and page number from settings."""
    css_parts = []
    
    # Watermark CSS
    if settings.get("watermark_top") or settings.get("watermark_right"):
        top = settings.get("watermark_top", 0)
        right = settings.get("watermark_right", 0)
        css_parts.append(f"""
            .pd-watermark {{
                position: absolute;
                top: {top}mm;
                right: {right}mm;
            }}
        """)
    
    # Page Number CSS (base + position class)
    if settings.get("page_number_display") == "Show":
        position = settings.get("page_number_position", "Top Right")
        font_family = settings.get("page_number_font_family", "Sarabun")
        font_size = settings.get("page_number_font_size", 10)
        font_color = settings.get("page_number_font_color", "#000000")
        border = settings.get("page_number_border", "None")
        
        # Base styles
        border_css = get_border_css(border)
        css_parts.append(f"""
            .pd-page-number {{
                font-family: {font_family}, sans-serif;
                font-size: {font_size}pt;
                color: {font_color};
                {border_css}
            }}
        """)
        
        # Position class
        position_class = position.lower().replace(" ", "-")  # "Top Right" -> "top-right"
        css_parts.append(f"""
            .pd-page-number.{position_class} {{
                {get_position_css(position, settings)}
            }}
        """)
    
    return "\n".join(css_parts)


def get_position_css(position, settings):
    """Generate position-specific CSS based on position setting."""
    positions = {
        "Top Right": f"top: {settings.get('page_number_top', 2)}mm; right: {settings.get('page_number_right', 8)}mm;",
        "Top Left": f"top: {settings.get('page_number_top', 2)}mm; left: {settings.get('page_number_left', 8)}mm;",
        "Top Center": f"top: {settings.get('page_number_top', 2)}mm; left: 50%; transform: translateX(-50%);",
        "Bottom Right": f"bottom: {settings.get('page_number_bottom', 2)}mm; right: {settings.get('page_number_right', 8)}mm;",
        "Bottom Left": f"bottom: {settings.get('page_number_bottom', 2)}mm; left: {settings.get('page_number_left', 8)}mm;",
        "Bottom Center": f"bottom: {settings.get('page_number_bottom', 2)}mm; left: 50%; transform: translateX(-50%);",
    }
    return positions.get(position, positions["Top Right"])


def get_border_css(border_style):
    """Generate border CSS based on border style setting."""
    borders = {
        "None": "border: none;",
        "Solid": "border: 1px solid currentColor;",
        "Dashed": "border: 1px dashed currentColor;",
        "Dotted": "border: 1px dotted currentColor;",
    }
    return borders.get(border_style, borders["None"])


def generate_page_number_html(settings):
    """Generate page number element HTML with correct position class."""
    if settings.get("page_number_display") != "Show":
        return ""
    
    position = settings.get("page_number_position", "Top Right")
    position_class = position.lower().replace(" ", "-")
    
    return f'''
    <div class="pd-page-number {position_class}">
        Page <span class="page_info_page">1</span> / <span class="page_info_topage">1</span>
    </div>
    '''
```

---

## Extension Points

### 1. Per-Page Variations

The header/footer containers have variants for different pages:

| ID | Purpose |
|----|---------|
| `#firstPageHeader` | First page only |
| `#oddPageHeader` | Odd pages (1, 3, 5...) |
| `#evenPageHeader` | Even pages (2, 4, 6...) |
| `#lastPageHeader` | Last page only |

### 2. PDF Generator Selection

The `pdf_generator` parameter controls output:

- `chrome` → Use Chrome CDP (headless Chrome)
- `weasyprint` → Use WeasyPrint

---

## File Locations

| File | Purpose |
|------|---------|
| `print_designer/www/printview.py` | Python controller |
| `print_designer/www/printview.html` | Jinja template |
| `print_designer/public/css/watermark.bundle.scss` | Watermark styles |
| `print_designer/public/css/print_designer.bundle.scss` | Main print styles |
| `print_designer/public/css/signature_stamp.bundle.scss` | Signature/stamp styles |

---

## See Also

- [Frappe Print View Documentation](https://docs.frappe.io/docs/user/manual/en/setting-up-printing)
- [Print Designer Wiki](https://github.com/frappe/print_designer/wiki)
