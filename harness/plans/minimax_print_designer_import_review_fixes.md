# Minimax fix list: Print Designer Import review findings

## Purpose

This file is the follow-up review handoff for the current Import MVP implementation.

The architecture is good, but the current implementation is **not ready to merge**. The issues below are ordered by priority and include concrete patch guidance.

## Merge status

Current status: **do not merge yet**.

## Blocking issues

## 1) Placeholder template validates as valid

### Problem

The downloaded/default template currently passes validation even when the user has not filled any section content.

This is dangerous because importing a blank template can overwrite an existing Print Designer format with near-empty content.

### Root cause

Validation treats placeholder comments like these as real content:

```html
<!-- Paste HEADER HTML here -->
```

The current section check only looks at `section.strip()`, so comment-only sections are treated as non-empty.

### Files

- `print_designer/utils/import_jinja_bridge.py`
- `print_designer/api/print_format_export_import.py`
- `print_designer/tests/test_import_jinja_bridge.py`

### Fix guidance

#### In `import_jinja_bridge.py`

Add a helper that removes placeholder comments / empty comments before checking whether a section is meaningfully filled.

Suggested helper shape:

- `_strip_html_comments(text)`
- `_meaningful_section_text(text)`

Behavior:

- remove HTML comments
- trim whitespace
- use the cleaned result for emptiness validation

Then update `validate_bridge_sections()` so that:

- marker-only placeholder content becomes a **blocker**
- genuinely short but non-empty content can still be a warning if desired

#### In tests

Add a test that feeds the default template / placeholder-only template and asserts:

- `valid == False`
- blockers mention empty sections

---

## 2) Text reconstruction loses actual text content

### Problem

Reconstructed text elements currently contain newline content or empty content instead of the actual visible text.

This is a hard blocker because imported content becomes unusable.

### Root cause

`_PDNodeBuilder` stack handling is wrong. The current parser creates text elements for `div`, `p`, and `span`, but `handle_data()` writes to the wrong level and nested text is not attached to the intended node.

### Files

- `print_designer/utils/import_jinja_bridge.py`
- `print_designer/tests/test_import_jinja_bridge.py`

### Fix guidance

#### In `import_jinja_bridge.py`

Refactor `_PDNodeBuilder` so that text-bearing nodes are tracked explicitly.

Recommended simpler model:

- keep a stack of active element nodes, not just child lists
- when a supported text-like tag starts, push that element as the current target
- `handle_data()` appends text to the current text element
- on end tag, pop correctly

Alternative acceptable MVP simplification:

- flatten supported nodes instead of trying to preserve nesting
- but actual visible text must still be captured correctly

#### Important rule

Do not store just `"\n"` or whitespace-only text as meaningful text content.

#### In tests

Add/repair tests that assert:

- header text contains `Header text`
- body contains `Body paragraph`
- span content survives reconstruction
- whitespace-only text nodes are ignored

---

## 3) Header/footer are written in the wrong shape for Print Designer loader

### Problem

The importer currently saves `print_designer_header` and `print_designer_footer` as raw element arrays.

But `ElementStore.loadElements()` expects header/footer page-wrapper objects with fields like:

- `childrens`
- `firstPage`
- `oddPage`
- `evenPage`
- `lastPage`

So imported formats may save but then fail or behave incorrectly when reopened in Print Designer.

### Files

- `print_designer/utils/import_jinja_bridge.py`
- `print_designer/public/js/print_designer/store/ElementStore.js`
- `print_designer/tests/test_import_jinja_bridge.py`

### Fix guidance

#### In `import_jinja_bridge.py`

Change reconstruction so that:

- `print_designer_header` is a JSON string of page-wrapper objects, not raw children
- `print_designer_footer` is also a JSON string of page-wrapper objects
- `print_designer_body` continues matching the page-wrapper convention already used by the editor

Recommended MVP approach:

- create one wrapper for header with:
  - `type: "page"`
  - `childrens: [...]`
  - `firstPage: true`
  - `oddPage: true`
  - `evenPage: true`
  - `lastPage: true`
- do the same for footer

Then build `print_designer_print_format` consistently from the wrapper children.

#### In tests

Add assertions that parsed header/footer JSON each contain wrapper objects with:

- `childrens`
- page variant flags

---

## 4) Jinja `{{ ... }}` expressions are not blocked

### Problem

Validation blocks `{% for %}`, `{% if %}`, and `{% set %}`, but it currently allows direct Jinja expressions like:

```html
{{ doc.customer }}
```

That contradicts the intended Import MVP safety model.

### Files

- `print_designer/utils/import_jinja_bridge.py`
- `print_designer/tests/test_import_jinja_bridge.py`

### Fix guidance

#### In `import_jinja_bridge.py`

Extend blocker patterns to catch at least:

- `{{ ... }}`
- optionally `{# ... #}` comments too if you want the import surface stricter

Suggested blocker message:

- `Jinja expressions in imported HTML are not supported in Import MVP`

#### In tests

Add a direct test for:

```html
<span>{{ doc.customer }}</span>
```

Expected result:

- `valid == False`
- blockers mention Jinja expressions

---

## 5) Class/id CSS selector resolution is broken

### Problem

The CSS parser stores selectors with their prefixes:

- `.foo`
- `#bar`

But `_resolve_style()` looks them up using unprefixed values:

- `foo`
- `bar`

As a result, class/id styles are never applied.

### Files

- `print_designer/utils/import_jinja_bridge.py`
- `print_designer/tests/test_import_jinja_bridge.py`

### Fix guidance

#### In `import_jinja_bridge.py`

Fix `_resolve_style()` so it uses the correct selector keys:

- lookup class selectors using `f".{class_name}"`
- lookup ids using `f"#{id_value}"`

Also keep inline style precedence higher than class/id style.

#### In tests

Add a test like:

- HTML: `<div class="box">Hello</div>`
- CSS: `.box { color:red; left:10px; top:20px; }`

Expected:

- reconstructed style contains `color: red`
- coordinates reflect `left/top`

---

## 6) Rectangle support is claimed but not actually implemented

### Problem

Docs and validation say MVP supports rectangles/simple containers, but the current parser turns every `div`, `p`, and `span` into `type: "text"`.

So rectangle/container support is currently over-claimed.

### Files

- `print_designer/utils/import_jinja_bridge.py`
- `print_designer/tests/test_import_jinja_bridge.py`
- dialog/help text if needed

### Fix guidance

Choose one of these and keep the implementation honest:

### Option A — Implement rectangle MVP support

Convert a `div` into `rectangle` when it clearly behaves like a container, for example when style includes one or more of:

- border / border-width / border-style / border-color
- background-color
- explicit width + height

Possible MVP rule:

- bordered/background `div` => `rectangle`
- plain text-only `p` / `span` => `text`

### Option B — Narrow the documented support

If rectangle reconstruction is too much right now:

- remove rectangle from the supported subset/help text
- classify those cases as unsupported or fallback text-only with warning

Recommendation: **Option A** if small enough.

---

## Medium issues

## 7) Import button should be disabled until valid

### Problem

The dialog currently allows clicking Import at any time, then shows an error if invalid.

This works, but it does not match the planned UX.

### Files

- `print_designer/public/js/print_designer/components/dialogs/ImportJinjaBridgeDialog.js`

### Fix guidance

After each validation result:

- disable primary action when invalid
- enable only when `report.valid === true`

This makes the flow clearer and reduces user confusion.

---

## 8) Download fallback is weak

### Problem

On download error, the dialog retries the same API call and then tries clipboard fallback.

If the server/network call failed the first time, the second call likely fails too.

### Files

- `print_designer/public/js/print_designer/components/dialogs/ImportJinjaBridgeDialog.js`
- possibly `print_designer/public/js/print_designer/components/layout/AppHeader.vue`

### Fix guidance

Simplest fix:

- remove the second server call fallback
- if download API fails, show a message instead of pretending clipboard fallback is reliable

Better fix:

- reuse an already-fetched template string for clipboard fallback if available

---

## 9) `overwrite` argument is misleading

### Problem

`import_print_designer_from_jinja_bundle(..., overwrite=False)` accepts `overwrite`, but it does not meaningfully affect behavior.

### Files

- `print_designer/api/print_format_export_import.py`
- `print_designer/public/js/print_designer/components/dialogs/ImportJinjaBridgeDialog.js`

### Fix guidance

Pick one:

- remove `overwrite` from API + frontend now
- or implement real overwrite semantics if that is needed later

Recommendation: **remove it for MVP**.

---

## Test gaps to close

## Required new tests

### Validation

- placeholder/default template must fail
- `{{ ... }}` Jinja expression must fail
- empty section after comment stripping must fail

### Reconstruction

- actual text content survives
- header/footer saved in wrapper shape compatible with editor loader
- class/id CSS selectors affect reconstructed style
- rectangle case either reconstructs properly or is explicitly unsupported

### Safety

- invalid bundle never mutates a Print Format
- validation endpoint remains pure preview

---

## Suggested implementation order for Minimax

1. fix placeholder validation
2. fix Jinja expression blocker
3. fix text reconstruction
4. fix header/footer wrapper shape
5. fix class/id CSS selector resolution
6. either implement rectangle support or narrow support claims
7. tighten UI: disable Import until valid
8. clean up `overwrite`
9. expand tests

## Review target after fixes

When resubmitting, the updated implementation should satisfy all of these:

- blank template cannot be imported
- actual text content is preserved
- imported format reloads in Print Designer without header/footer shape issues
- Jinja expressions are blocked
- class/id CSS selectors work for the supported subset
- supported/unsupported claims match actual behavior
