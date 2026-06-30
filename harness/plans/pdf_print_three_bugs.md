# PDF Print Three Bugs — Fix Plan (2026-06-30)

## User-Reported Bugs (URL: `https://aws-solution.bunchee.online/api/method/frappe.utils.print_format.download_pdf?doctype=Payment+Entry&name=ACC-PAY-2606-00001&format=Receipt&no_letterhead=1&_lang=en`)

| # | Bug | Status |
|---|---|---|
| 1 | Table has only 1 data row, no blank rows to fill content space | ✅ Fixed |
| 2 | `{{ pd_custom_net_total_after_wht_words }}` shows nothing | ✅ Fixed |
| 3 | URL `_lang=en` but Print Format `default_print_language=th` | ✅ Fixed |

Screenshot of broken state: `apps/print_designer/.claude/Capto_Capture 2569-06-30_11-14-38_AM.jpg`
Screenshot of fixed state: `apps/print_designer/.claude/pdf_print_after_all_3_fixes.png`

## Fix Details

### Bug 1 — Blank rows in table

**Files changed:**

- `print_designer/print_designer/page/print_designer/jinja/macros/table.html` — added `minRows` pad logic + `&nbsp;` for empty cells
- `print_designer/print_designer/page/print_designer/jinja/old_print_format.html` — same changes to inline `render_table` macro
- `print_designer/public/js/print_designer/PropertiesPanelState.js` — added "Min Rows" input next to "Rows"
- Print Format `Receipt` — set `minRows: 5` on both `print_designer_body` AND `print_designer_print_format` JSONs (must update BOTH; render uses `pd_format`)

**Lesson:** The Print Designer saves two parallel JSONs — `print_designer_body` (legacy) and `print_designer_print_format.body[*].childrens[*]` (current). The PDF render reads from `pd_format`, not `bodyElement`. Updating one without the other silently fails (the table has no `minRows` at render time).

### Bug 2 — Number-to-words computation

**File changed:** `print_designer/pdf.py::_handle_thai_amount_enhancement`

**Original bug:** function early-exited when doc had no `grand_total` attribute (Payment Entry uses `paid_amount`).

**Fix:**

1. Drop the `grand_total` requirement, gate only on `in_words` (which Payment Entry has).
2. Compute `primary_amount = grand_total or paid_amount or 0`.
3. For Thai language, set `doc.in_words = thai_money_in_words(primary_amount)`.
4. Also populate 4 `*_words` custom fields with `thai_amount_words`:
   - `pd_custom_net_total_after_wht_words`
   - `tbs_balance_payable_words`
   - `pd_custom_net_after_wht_retention_words`
   - `pd_custom_net_after_wht_retention_words_details`

Only fills fields whose value is currently None / empty so we don't clobber user-stored data.

### Bug 3 — Language priority

**File changed:** `print_designer/pdf.py::get_effective_language`

**Priority was:**

1. URL `_lang`
2. Print Format `default_print_language`
3. `frappe.local.lang`

**Now:**

1. Print Format `default_print_language`
2. URL `_lang`
3. `frappe.local.lang`

So the Print Format's explicit intent wins over the Desk's auto-injected `_lang=en` URL param.

## Deployment

- `bench restart` (user-approved) cleared gunicorn worker Python module caches
- `bench --site aws-solution.bunchee.online clear-cache` cleared site cache
- All 27+ tests still pass

## bd Tasks

- `print_designer-56s` ✅ Bug 1 closed
- `print_designer-34h` ✅ Bug 2 closed
- `print_designer-jzv` ✅ Bug 3 closed

## Open follow-up

- `print_designer-ime` (P3) — Audit why those custom fields are NULL in DB. May need a doc_event hook to populate them at save time, not just print time.
