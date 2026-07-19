# Print Designer Jinja Templates

## Overview

Print Designer uses Jinja templates to generate the HTML for print preview and PDF generation.

## Location

```
print_designer/print_designer/page/print_designer/jinja/
├── macros/
│   ├── spantag.html      # Dynamic text span generation
│   ├── styles.html       # Main CSS styles
│   └── styles_old.html   # Legacy styles
├── old_print_format.html # Legacy print format
└── ...
```

## Key Templates

### spantag.html

Generates the HTML for dynamic text fields.

**Line 44 - baseSpanTag wrapper:**

```jinja
<span
    class="{% if not field.is_static and field.is_labelled %}baseSpanTag{% endif %}"{% if not field.is_static and field.is_labelled %} style="display: flex; align-items: center"{% endif %}
>
```

**Structure:**

- `baseSpanTag` - wrapper when field has label
- `labelSpanTag` - the label text
- `valueSpanTag` - the field value
- `br` - line break if `field.nextLine`

### styles.html

CSS styles for print preview.

**Key classes:**

```css
.flexDynamicText .baseSpanTag { display: block; }
.flexDirectionColumn .baseSpanTag { display: block; }
```

## Common Fixes

### Center align label and value

**Problem:** Label and value not vertically centered.

**Solution:** Add inline style to `spantag.html` line 44:

```jinja
style="display: flex; align-items: center"
```

**Important:** Only add when `is_labelled` is true to avoid affecting empty spans.
