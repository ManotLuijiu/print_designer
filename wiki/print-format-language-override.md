# Print Format Language Override

## Problem

When viewing a Sales Invoice in Print Preview (`/desk/print/Sales Invoice/BL6907-00001`), the sidebar Language dropdown was showing English ("en") even when the Print Format had `default_print_language = "th"` (ไทย).

**Root Cause:** Frappe's `set_default_print_language()` used wrong priority:

```javascript
this.lang_code = this.frm.doc.language || print_format.default_print_language || frappe.boot.lang;
//                      ^^^^^^^^^^^^^^^^^^^ THIS won because it was first in the OR chain
```

The document's `language` field was "en", so it always took precedence over the Print Format's `default_print_language`.

---

## Solution: ERPNext-Style Override

### How Frappe Loads Print Page Scripts

```
1. Frappe defines PrintView class and page handler
2. Apps can add scripts via page_js hook
3. Scripts load AFTER Frappe's core code
```

### Key Concept: DON'T Override frappe.pages["print"]

The initial approach of overriding `frappe.pages["print"]` failed because:

- It runs BEFORE Frappe's core PrintView is fully initialized
- Frappe's core code then overwrites the override

### Correct Approach: ERPNext-Style

ERPNext's `public/js/print.js` shows the pattern:

```javascript
// 1. Call function immediately
handle_route_event();

function handle_route_event() {
  const route = frappe.get_route();
  
  // 2. Check if on correct page
  if (!doctype_list.includes(current_doctype)) return;
  
  // 3. Wait for page to load
  setTimeout(() => {
    // 4. Use jQuery to find existing elements
    const print_format = $('input[data-fieldname="print_format"]').val();
    // 5. Add functionality
  }, 500);
}
```

### hooks.py Configuration

```python
page_js = {
    "print": [
        "public/js/print.js",  # Our override
        "print_designer/js/print_designer/client_scripts/safe_pdf_client.js",
        "print_designer/js/print_designer/client_scripts/print.js",
    ],
}
```

**Path Note:** Use `public/js/print.js` (relative to app root), NOT `print_designer/public/js/print.js`.

---

## Implementation

### File: public/js/print.js

```javascript
/**
 * Print Designer - Print Page Language Override
 *
 * Safe client-only helper:
 * - wait for the print page inputs to exist
 * - ignore placeholder "Standard"
 * - fetch Print Format.default_print_language when a real format is selected
 * - apply it through the existing Language control
 */

const PDPrintLanguageState = {
  retries: 0,
  maxRetries: 20,
  applying: false,
  lastAppliedFormat: null,
};

apply_print_language();

$(document).on("change", 'input[data-fieldname="print_format"]', () => {
  queue_print_language_apply(150);
});

function apply_print_language() {
  const route = frappe.get_route();
  if (route[0] !== "print") return;
  queue_print_language_apply(500);
}

function queue_print_language_apply(delay = 0) {
  setTimeout(() => {
    apply_language_from_print_format();
  }, delay);
}

function apply_language_from_print_format() {
  const route = frappe.get_route();
  if (route[0] !== "print") return;

  const print_format = $('input[data-fieldname="print_format"]').val();
  const lang_input = $('input[data-fieldname="language"]');

  if (!lang_input.length || !print_format || print_format === "Standard") {
    if (PDPrintLanguageState.retries < PDPrintLanguageState.maxRetries) {
      PDPrintLanguageState.retries += 1;
      queue_print_language_apply(250);
    }
    return;
  }

  PDPrintLanguageState.retries = 0;

  if (PDPrintLanguageState.applying || PDPrintLanguageState.lastAppliedFormat === print_format) {
    return;
  }

  PDPrintLanguageState.applying = true;

  frappe.call({
    method: "frappe.client.get",
    args: {
      doctype: "Print Format",
      name: print_format,
    },
    callback: function (r) {
      PDPrintLanguageState.applying = false;

      if (r && r.message && r.message.default_print_language) {
        PDPrintLanguageState.lastAppliedFormat = print_format;
        set_language(r.message.default_print_language);
      }
    },
    error: function () {
      PDPrintLanguageState.applying = false;
    },
  });
}

function set_language(lang_code) {
  const lang_input = $('input[data-fieldname="language"]');
  const lang_display = $('.frappe-control[data-fieldname="language"] .control-value a');

  if (!lang_input.length || !lang_code) return;
  if (lang_input.val() === lang_code) return;

  lang_input.val(lang_code).trigger("change");

  if (lang_display.length) {
    lang_display.text(lang_code);
    lang_display.attr("href", "/desk/language/" + lang_code);
    lang_display.attr("data-name", lang_code);
    lang_display.attr("data-value", lang_code);
  }
}
```

---

## Language Priority Logic

**Original (Broken):**

1. Document's `language` field
2. Print Format's `default_print_language`
3. User's GUI language

**Fixed (Our Override):**

1. Print Format's `default_print_language` (highest priority)
2. User's selection

---

## Debugging Tips

1. **Add console.log at top** to verify script loads:

   ```javascript
   console.log("[PD PRINT] Script loaded!");
   ```

2. **Clear cache after changes**:

   ```bash
   bench --site yoursite clear-cache
   ```

3. **Restart may be needed** for hooks.py changes

4. **Check Network tab** to verify script is being requested

---

## Common Mistakes

- ❌ Trying to override `frappe.pages["print"]` - runs too early
- ❌ Wrong path in `page_js` - use `public/js/print.js`
- ❌ Not waiting for DOM elements - use `setTimeout`
- ❌ Modifying Frappe core files - use `page_js` override instead

---

## Related Files

### Modified Files

- `print_designer/hooks.py` - Added page_js entry
- `print_designer/public/js/print.js` - New override file
- `print_designer/print_designer/client_scripts/print.js` - Print Designer enhancements
- `print_designer/utils/safe_pdf_api.py` - Backend language handling
- `print_designer/overrides/printview_watermark.py` - Print preview override

### Reference Files

- Frappe core: `frappe-bench/apps/frappe/frappe/printing/page/print/print.js`
- ERPNext example: `frappe-bench/apps/erpnext/erpnext/public/js/print.js`

---

## Next Steps

Add Print Format Language toggle to Print Designer's toolbar (`/desk/print-designer/...`) so users can preview different languages while designing.

**See also:** [Override JavaScript](override_javascript.md)
