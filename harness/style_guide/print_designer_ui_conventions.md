# Print Designer UI Conventions

Coding standards for the Print Designer Vue app UI layer. These rules
are *prescriptive* — follow them when adding or changing UI components so
the editor stays visually consistent.

## 1. Adjacent button rows share a fixed width

**Rule**: When a row of buttons sits next to each other (toolbar, header,
action bar), they MUST all use the same width, picked from the longest
button's natural width. Don't let each button auto-size from its label.

**Why**: Visual alignment. A 100px "Export Jinja" next to a 70px "Import"
looks uneven; the eye reads them as separate groups even though they are
one toolbar.

**How**:

1. Measure the natural width of the longest label + `padding: 2px 8px`
   (e.g. devtools or `getBoundingClientRect()`).
2. Pick a clean number ≥ the longest natural width (e.g. round up to the
   nearest 10px).
3. Apply that width + `display: flex; align-items: center;
   justify-content: center;` to ALL buttons in the row via a single CSS
   group selector.

**Example** (`AppHeader.vue` — three buttons: `Export Jinja`, `Import`
dropdown, `Exit`):

```scss
.exit-btn,
.export-jinja-btn,
.import-template-btn {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    width: 100px;          /* standard width — match longest natural */
    justify-content: center;
}
```

**Where the pattern currently applies**:

- `print_designer/public/js/print_designer/components/layout/AppHeader.vue`
  — `Export Jinja` + `Import` dropdown + `Exit`

**When to apply**:

- A toolbar / header with 2+ adjacent buttons
- Modal footers with 2+ side-by-side buttons (e.g. Cancel + Confirm)
- A row of "Copy" / "Edit" / "Delete" actions in a card

**When NOT to apply**:

- A single isolated button (no group to align with)
- Buttons of clearly different roles separated by whitespace (e.g. a
  primary "Save" CTA next to a small "Cancel" link — different visual weight
  is intentional)

**When changing the standard width** (text added / removed from the
longest button):

1. Re-measure the longest natural width
2. Update the single shared `width: ...px` value in the group selector
3. Don't apply width individually per button

---

## 2. Theme-aware colors via Frappe CSS variables

**Rule**: Editor UI chrome (side panels, modals, dialogs, status
indicators) MUST use Frappe CSS variables (`var(--text-color)`,
`var(--text-muted)`, `var(--control-bg)`, `var(--bg-light-gray)`,
`var(--green-600)`, `var(--red-600)`, `var(--primary)`, etc.) instead of
hardcoded hex values, so the editor adapts to light and dark themes.

**Where the rule does NOT apply**:

- The page canvas itself (`.main-container`, `.resize-handle`) — the
  page is paper, always white
- Print-design defaults (`globalStyles.js`, `BaseBarcode.vue`,
  `defaultObjects.js`) — designer-chosen colors stored in the format

See `print_designer_harness/print_designer_dark_theme_improvements.md`
(when written) for the full scope.

---

## 3. Vue scoped styles: use `:deep()` for content inserted via `v-html`

**Rule**: When rendering HTML via `v-html` (e.g. Frappe's link formatter
output inside `BaseDynamicTextSpanTag.vue`), the inserted elements do
NOT receive the Vue `data-v-XXX` attribute. Any nested CSS selector in
the scoped `<style>` will be Vue-augmented with `data-v-XXX` on every
simple selector — which then FAILS to match the v-html content.

**Fix**: prefix nested selectors with `:deep()` so Vue skips the scope
attribute on the inner selector:

```scss
/* WRONG — compiles to .dynamic-span[data-v-X] a[data-v-X],
   which never matches the link inside v-html */
.dynamic-span a {
    color: var(--gray-900);
}

/* RIGHT — compiles to .dynamic-span[data-v-X] a,
   which matches the v-html-injected <a> */
.dynamic-span :deep(a) {
    color: var(--gray-900);
}
```

If you need a class on the v-html output, stamp it in the JS
post-processor (see `print_designer/public/js/print_designer/utils.js`
→ `getFormattedValue` for the `class="dynamic-span-link"` pattern).

---

## Adding a new convention

1. Add it to this file with a one-line rule + a "Why" + a "How" + an
   example
2. Reference the file in PR review checklists
3. If the convention produces reusable code (a class, a mixin), put the
   code in a shared file and reference it from here
