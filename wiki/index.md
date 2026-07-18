# Print Designer Wiki

## Architecture & Override Guides

### JavaScript Overrides

| Document | Description |
|---------|-------------|
| [Override JavaScript](override_javascript.md) | General guide for overriding Frappe JavaScript |
| [Print Format Language Override](print-format-language-override.md) | How we made print preview respect Print Format's default_print_language |
| [Print Designer Language Toggle](print-designer-language-toggle.md) | Planned: Add language toggle to Print Designer toolbar |

### Codebase Analysis

| Document | Description |
|---------|-------------|
| [Codebase Analysis](codebase-analysis.md) | Detailed analysis of print_designer codebase structure |
| [Border Styling Improvements](border-styling-improvements.md) | Enterprise border features implementation |

### API Documentation

| Document | Description |
|---------|-------------|
| [get_html_and_style.json](get_html_and_style.json) | API response for print preview |
| [get_print_settings_to_show.json](get_print_settings_to_show.json) | Print settings API |

---

## Quick Reference

### Override Print Page Language

```python
# hooks.py
page_js = {
    "print": [
        "public/js/print.js",  # Our override
    ],
}
```

### Find Elements by data-fieldname

```javascript
const print_format = $('input[data-fieldname="print_format"]').val();
const lang_input = $('input[data-fieldname="language"]');
```
