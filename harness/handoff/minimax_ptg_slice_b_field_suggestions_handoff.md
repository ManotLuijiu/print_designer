# PTG Slice B handoff: Smart field suggestions

## Context

Slice A (PTG-driven Import in print_designer) was completed earlier.
The next slice (per `harness/plans/minimax_ptg_annotated_form_to_print_designer_action_plan.md`)
is "Field-binding UI per child region".

Per the user's clarification:
> "for each sub-component (inside Parent Header/Body/Footer) not only label
> we need but we need user to specific related field (you fetch from doctype)"
> "after you got DocType from User you can realize that which fields are
> related to that block (component)"

The current state in PTG:

- `FieldPicker.vue` shows ALL fields from a DocType
- `field_metadata.py:get_doctype_fields()` returns everything
- The user picks manually — no smart suggestion

What Slice B needs:

- Add label-aware field suggestions
- Highlight "Suggested" fields at the top of FieldPicker
- Store the binding on the region (already works via `elementStore.updateElement(..., {binding, is_dynamic})`)
- Make field_bindings queryable from the print_designer import (already works via `generate_template` returning the html/css with bindings baked in)

## Status: SPEC ONLY (PTG workspace sandboxed)

This is a **handoff doc**, not an implementation. The PTG workspace is
sandboxed away from this session. Apply the spec to
`/home/frappe/frappe-bench/apps/print_template_generator/` directly.

---

## File 1 — `print_template_generator/api/field_metadata.py`

Add a new whitelisted function (next to the existing
`get_doctype_fields` / `get_child_table_fields`):

```python
# Heuristic mapping from region label to field-name keywords.
# Each label maps to a list of lowercase keywords that, if found in
# a DocType field's name OR label, make the field a "suggestion"
# for that region. Order matters (earlier = higher score).
LABEL_FIELD_KEYWORDS = {
    # Header
    "logo_image":           ["logo", "image", "brand", "emblem", "attach"],
    "company_header":       ["company", "address", "tax", "phone", "email",
                             "branch", "registration"],
    "document_title":       ["title", "subject", "name"],
    "page_number":          ["page", "topage", "paging"],
    "document_meta_box":    ["date", "doc_no", "doc_number", "ref", "code",
                             "revision"],
    # Body
    "buyer_info":           ["customer", "client", "buyer", "name", "address",
                             "contact", "phone", "email", "tax_id"],
    "seller_info":          ["vendor", "supplier", "seller", "payee"],
    "invoice_info":         ["invoice", "bill", "account", "due"],
    "order_reference_strip": ["po", "so", "order", "credit", "due_date"],
    "items_table":          [],  # handled by child-table branch below
    "totals_block":         ["total", "subtotal", "discount", "vat", "tax",
                             "amount", "sum", "grand", "net"],
    "amount_in_words":      ["words", "baht", "text", "amount_words",
                             "amount_in_words"],
    "notes_block":          ["notes", "remarks", "comment", "special"],
    "legal_text":           ["legal", "terms", "condition", "disclaimer",
                             "policy"],
    "image_block":          ["image", "attach", "photo", "signature"],
    "rectangle_box":        ["box", "code", "ref", "stamp", "seal"],
    "label_value_box":      ["label", "value", "key", "name", "amount"],
    "text_block":           ["name", "title", "description", "note", "remark"],
    # Footer
    "signature_block":      ["signature", "sign", "authorize", "approve",
                             "image", "attach"],
    "approval_block":      ["approval", "authorize", "sign_off", "verify"],
    "footer_notes":         ["footer", "note", "remark", "disclaimer"],
    "unknown_component":    [],
}


def _score_field(field, keywords):
    """Return a match score for a field against the label's keyword list.

    Higher score = better match. Returns 0 if no match.
    The first keyword in the list has the highest weight, since it's
    the most likely match for the label.
    """
    if not keywords:
        return 0
    name = (field.get("fieldname") or "").lower()
    label = (field.get("label") or "").lower()
    score = 0
    for idx, kw in enumerate(keywords):
        if kw in name or kw in label:
            # Earlier keywords = higher score. Base 100 minus position.
            score = max(score, 100 - idx * 10)
    return score


@frappe.whitelist(allow_guest=False)
def get_field_suggestions(doctype, region_label):
    """Return fields for a DocType, ranked by match strength for a region label.

    Returns:
        list of dicts: [{...field, "match_strength": "high"|"medium"|"low",
                         "score": int}, ...]
        Sorted by score descending. Image fields and child tables are
        included with their own categories.

    Use case: FieldPicker shows these as the "Suggested" section at the
    top so the user doesn't have to scroll through every field of the
    linked DocType.
    """
    if not doctype or not region_label:
        frappe.throw(_("doctype and region_label are required"))

    keywords = LABEL_FIELD_KEYWORDS.get(region_label, [])
    if not keywords:
        # No mapping for this label — return empty suggestions
        return []

    # Reuse the existing metadata fetcher (returns standard + bindable
    # fields + child tables)
    meta = get_doctype_fields(doctype)

    scored = []
    for field in meta.get("fields", []):
        score = _score_field(field, keywords)
        if score > 0:
            strength = "high" if score >= 80 else "medium" if score >= 50 else "low"
            scored.append({**field, "match_strength": strength, "score": score})

    for table in meta.get("child_tables", []):
        # A child table is a good fit for "items_table"-like labels
        if region_label in ("items_table", "order_reference_strip", "label_value_box"):
            scored.append({
                **table,
                "match_strength": "high",
                "score": 100,
            })

    # Sort by score desc, then by fieldname
    scored.sort(key=lambda f: (-f.get("score", 0), f.get("fieldname", "")))
    return scored
```

## File 2 — `print_template_generator/public/js/print_template_generator/store/FieldStore.js`

Add a new action to the store:

```js
// Add inside the `actions: {}` object:

async loadFieldSuggestions(doctype, regionLabel) {
    if (!doctype || !regionLabel) {
        this.suggestions = [];
        return [];
    }
    this.loadingSuggestions = true;
    try {
        const result = await frappe.call({
            method: "print_template_generator.print_template_generator.api.field_metadata.get_field_suggestions",
            args: { doctype, region_label: regionLabel },
        });
        this.suggestions = result.message || [];
        return this.suggestions;
    } catch (e) {
        console.error("PTG: Failed to load field suggestions", e);
        this.suggestions = [];
        return [];
    } finally {
        this.loadingSuggestions = false;
    }
},
```

And add to `state: () => ({...})`:

```js
suggestions: [],
loadingSuggestions: false,
```

## File 3 — `print_template_generator/public/js/print_template_generator/components/FieldPicker.vue`

Add a "Suggested" section at the top, fetched when a region label is
provided. New props + data + template changes:

```vue
<script setup>
import { ref, watch } from "vue";
import { useFieldStore } from "../store/FieldStore.js";

const props = defineProps({
    visible: { type: Boolean, default: false },
    doctype: { type: String, default: null },
    regionLabel: { type: String, default: null },  // NEW
});

const emit = defineEmits(["close", "select-field", "select-table", "select-child-field"]);

const fieldStore = useFieldStore();
const expandedTable = ref(null);
const childFields = ref([]);
const loadingChildren = ref(false);

// Existing: load all DocType fields on change
watch(
    () => props.doctype,
    (dt) => {
        if (dt) {
            fieldStore.loadDoctypeFields(dt);
        }
    },
    { immediate: true }
);

// NEW: load suggestions when region label changes
watch(
    () => props.regionLabel,
    (label) => {
        if (label && props.doctype) {
            fieldStore.loadFieldSuggestions(props.doctype, label);
        } else {
            fieldStore.suggestions = [];
        }
    },
    { immediate: true }
);

function onFieldClick(field) { emit("select-field", field); }
function onTableClick(table) { /* same as before */ }
async function loadChildFields(childDoctype) { /* same as before */ }
function onChildFieldClick(table, child) { /* same as before */ }
</script>
```

Update the template — add this section ABOVE the existing
"Document Fields" section, inside the `<div v-else>`:

```vue
<!-- Suggested (label-aware) -->
<div
    class="ptg-fields__section"
    v-if="fieldStore.suggestions && fieldStore.suggestions.length"
>
    <div class="ptg-fields__section-title">
        Suggested for "{{ regionLabel }}"
    </div>
    <div
        class="ptg-fields__item"
        v-for="field in fieldStore.suggestions"
        :key="'sug-' + field.fieldname"
        @click="onFieldClick(field)"
        :title="field.binding"
    >
        <span class="ptg-fields__label">{{ field.label }}</span>
        <span
            class="ptg-fields__match"
            :class="{
                'ptg-fields__match--high': field.match_strength === 'high',
                'ptg-fields__match--medium': field.match_strength === 'medium',
                'ptg-fields__match--low': field.match_strength === 'low',
            }"
        >
            {{ field.match_strength }}
        </span>
    </div>
</div>
```

Add to the scoped style:

```css
.ptg-fields__match {
    font-size: 9px;
    padding: 1px 4px;
    border-radius: 2px;
    margin-left: 6px;
    white-space: nowrap;
}
.ptg-fields__match--high   { background: var(--green-100, #d4edda); color: var(--green-800, #155724); }
.ptg-fields__match--medium { background: var(--yellow-100, #fff3cd); color: var(--yellow-800, #856404); }
.ptg-fields__match--low    { background: var(--gray-100, #f8f9fa); color: var(--gray-600, #6c757d); }
```

## File 4 — `print_template_generator/public/js/print_template_generator/App.vue`

Pass the selected element's label to FieldPicker when in bind mode.
Two changes:

1. Add a computed prop for the selected element's label:

```vue
<template>
    <FieldPicker
        v-if="mainStore.mode === 'bind'"
        :visible="mainStore.mode === 'bind'"
        :doctype="mainStore.targetDoctype"
        :region-label="selectedRegionLabel"
        @close="mainStore.mode = 'edit'"
        @select-field="onSelectField"
        @select-table="onSelectTable"
        @select-child-field="onSelectChildField"
    />
</template>
```

1. Add a computed in `<script setup>`:

```js
import { computed } from "vue";
// ...
const selectedRegionLabel = computed(() => {
    const el = elementStore.selectedElement;
    if (!el) return null;
    return el.label || el.type || null;
});
```

The element schema (from `ptg_template.py` JSON) should already have a
`label` field per region. If not, fall back to `el.type` (e.g. `text`).

## Acceptance criteria for Slice B

1. Opening a region in bind mode shows a "Suggested for {label}" section
   ABOVE the regular field list
2. Suggestions are sorted by `match_strength` (high → medium → low)
3. Clicking a suggestion binds it the same way clicking a regular field
   would (via `onSelectField` -> `elementStore.updateElement(..., {binding})`)
4. For label `items_table`, the child tables are returned as suggestions
   with strength "high"
5. For label `unknown_component` or labels not in the mapping, the
   suggestions array is empty (no error)
6. Existing flow (manually scrolling all fields) still works alongside
7. The print_designer "Import PTG" Slice A flow is unchanged —
   `get_field_suggestions` is read-only on the PTG side

## Test cases to add

```python
def test_get_field_suggestions_high_match():
    # Set up a DocType with fields "customer_name", "customer_address"
    # Call with region_label "buyer_info"
    # Assert: both fields returned with strength "high"

def test_get_field_suggestions_low_match():
    # Call with region_label "buyer_info" on DocType with "unrelated_field"
    # Assert: "unrelated_field" returned with strength "low" or empty

def test_get_field_suggestions_items_table():
    # DocType with child table "references"
    # Call with region_label "items_table"
    # Assert: child table returned as suggestion with strength "high"

def test_get_field_suggestions_unknown_label():
    # Call with region_label "unknown_label"
    # Assert: empty list, no error

def test_get_field_suggestions_no_doctype():
    # Call with empty doctype
    # Assert: throws validation error
```

## What this Slice does NOT do (deferred to Slice C+)

- Two-way sync "Push to PTG" from print_designer
- Field binding persistence to the PTG Template's `layout_json` (already
  there — FieldPicker calls `elementStore.updateElement` which writes the
  binding into the element's `binding` field, which is serialized to
  `layout_json` on save)
- Cross-checking field_bindings in print_designer before import
  (Slice A just dumps html+css from PTG, the bindings are baked into
  the Jinja expressions)
- Per-DocType custom label-to-field mapping UI (admin can override
  the heuristic mapping via PTG Settings if needed in a future slice)

## Notes for the implementer

- The heuristic label-to-field mapping (`LABEL_FIELD_KEYWORDS`) is a
  starting point. Real-world use will need adjustment. Add a
  "PTG Settings" field for custom overrides if/when needed.
- The match scoring is intentionally simple (substring match). For more
  sophisticated matching, swap in fuzzy matching or a learned model.
- The "Suggested" section is always above the "Document Fields" section
  so the most likely correct field is one click away.
- Suggestions are **not** auto-applied — the user still has to click to
  confirm. Auto-apply would be dangerous (wrong field = wrong output).
- `get_field_suggestions` is read-only. The print_designer import
  doesn't need any changes; PTG's `generate_template` already bakes
  the bound field paths into the output.
