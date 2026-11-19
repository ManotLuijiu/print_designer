Before writing code, first explore the project structure,
then invoke the nextjs-doc skill for documentation.

## Print Designer Theme

**CSS Variables (defined in `App.vue` `.main-layout`):**

```css
--primary: #7b4b57;      /* Burgundy/wine color - NOT blue! */
--primary-color: #7b4b57;
```

**IMPORTANT:** Do NOT assume `--primary` is blue (#2490ef) like Frappe default. Print Designer overrides it to burgundy (#7b4b57).

**Toolbar icon colors:**

- Use `white` for active icons (white on burgundy background = visible)
- Use `var(--text-muted)` for inactive icons
- When passing `color` prop to `IconsUse`, use `'white'` when active, `'var(--text-muted)'` otherwise

**CSS files location:** `print_designer/public/css/*.scss`

- `print_designer.bundle.scss` - main wrapper styles
- `global_typography_override.bundle.scss` - Thai font overrides
- `signature_stamp.bundle.scss` - signature/stamp styles
- `watermark.bundle.scss` - watermark settings styles

## Frontend dependency policy

- Treat Vue and Pinia versions as a compatibility pair. Do not upgrade either independently or rely on undeclared versions inherited from Frappe.
- Keep supported versions explicitly pinned in this app package.json. Current verified pair: Vue `3.5.12` and Pinia `2.3.1`.
- Do not perform blanket dependency upgrades. Upgrade one related dependency group at a time and review peer requirements first.
- Any Vue, Pinia, build-tool, or lockfile change must include an updated `yarn.lock`, the frontend dependency regression test, `bench build --app print_designer`, target-site cache clearing, and authenticated Playwright verification of `/desk/print-designer/Receipt`.
- A successful build alone is insufficient. Vue `3.5.12` with inherited Pinia `2.1.7` loaded saved data into Pinia but did not trigger Vue component rerenders, leaving the canvas blank without a runtime exception.

## Table editing: collapse, selection, and column width fixes

Regression investigated on 2026-11-19 in `Quotation - AWS Solution` on
`aws-solution.bunchee.online` (tracking issue: `print_designer-wsg`).
Symptoms: clicking a table collapsed it to one line, cleared the selected
column, and prevented normal width editing. Removing the console exception
alone did not fix the interaction.

### Causes and fixes

- **Undefined callback argument** — In
  `print_designer/public/js/print_designer/PropertiesPanelState.js`, the
  `tableStyleEditMode` callback accepted `_value` but read `value`. Keep the
  parameter and references consistent. Selecting `main` must retain the column;
  other style modes clear it.
- **Min Rows initialization overwrote saved height** — In
  `print_designer/public/js/print_designer/frappeControl.js`, an immediate
  watcher recalculated height when the properties panel opened. An unset
  `minRows` became `0`; measurements from a detached table produced a zero
  header height, changing the saved height from about 221 pixels to 0.
  Normalize the displayed default with `object?.minRows ?? 0` without writing
  it back on selection. Watch table identity and row count together, and
  recalculate height only when the count changes on the same table. Require
  mounted, measurable rows and include visible data rows in the minimum height.
- **Stale DOM reference after refresh** — In
  `print_designer/public/js/print_designer/composables/Element.js`, do not skip
  binding merely because `element.DOMRef` exists. If Vue replaces the node
  during a table refresh, remove the old Interact.js binding and bind the new
  node. An obsolete, detached reference makes `onClickOutside` treat header
  clicks as outside clicks and gives incorrect layout measurements.
- **Column resizing triggered header reordering** — In
  `print_designer/public/js/print_designer/components/base/BaseTable.vue`, use
  `@mousedown.left.stop.prevent` on the column resizer, select its table and
  column explicitly, and route mouseup through the existing cleanup handler.
  A resize gesture must change width without starting native header dragging.

### Diagnostics and verification

- **Keep console logs until the user explicitly asks to remove them.** This is
  an explicit user instruction. Retain the `[TableSizing]` logs for DOM
  rebinding, Min Rows synchronization, height recalculation, and column resize
  start/finish. Existing selection logs are also useful for this investigation.
- For Vue fixes, use the installed `vue-best-practices`, `vue-debug-guides`, and
  `vue-testing-best-practices` skills as applicable.
- Verify with real Playwright mouse clicks and dragging. Directly dispatching
  header events or inspecting Pinia state alone missed this regression.
- Assert that selection and reselection preserve table height, the column stays
  selected, dragging changes its visible width, header order stays unchanged,
  and no page errors occur. Do not save test edits to the production format.
- Regression test: `print_designer/tests/test_table_column_editing.py`.
  Credentials come from the app `.env`; never put them in tests or logs.

```bash
PRINT_DESIGNER_E2E=1 \
PRINT_DESIGNER_E2E_SITE_URL=https://aws-solution.bunchee.online \
python -m pytest print_designer/tests/test_table_column_editing.py \
  print_designer/tests/test_properties_panel_label_neutralized.py -q
bench build --app print_designer
bench --site aws-solution.bunchee.online clear-cache
```

Build and clear the target-site cache before running browser verification
against changed frontend assets. The regression test changes only the browser's
unsaved design state.

## Desk preview watermark and page number routing

Investigated on 2026-11-20 with `Quotation - AWS Solution` (issue
`print_designer-5du`). PDF Forms is installed after Print Designer on the AWS
site and overrides `frappe.www.printview.get_html_and_style`; its fallback calls
core directly, bypassing Print Designer overlays. Desk previews now use
`print_designer.api.desk_preview.get_html_and_style`, which preserves PDF Forms
template previews and otherwise calls Print Designer's permission-checked renderer.
Keep this explicit routing; changing app order is not a reliable repair.

Frappe's `set_input(default)` does not populate `additional_settings` for unchanged
Select/Check controls. Initialize missing setting keys from sidebar defaults,
preserving explicit `None`, `Hide`, zero and unchecked values. An explicit basic
sidebar watermark mode must also take precedence over global Watermark Settings
mode `None`; explicitly selected templates retain their own mode/custom text.
Regression tests: `test_desk_preview_dispatch.py`,
`test_desk_preview_watermark_mode.py`, and `test_desk_preview_request.cjs`.
Keep preview diagnostic console logs until the user explicitly requests removal.

## Saved WHT words bindings and Thai print labels

Quotation regression investigated on 2026-11-20 (`print_designer-lcy`): saved
formats can still bind `net_total_after_wht` / `net_total_after_wht_in_words`
after those fields were renamed to `pd_custom_net_total_after_wht` /
`pd_custom_net_total_after_wht_words`. The number-to-words utility resolves these
known aliases only when the old metadata field is absent and the typed replacement
exists. It publishes request-only values under both target names so saved layouts
and design previews work without changing the schema, saved format or transaction.
Use the configured net-after-WHT source; do not substitute grand total for it.

The AWS site's Thai translation dictionary has reverse entries such as
`จำนวน → Quantity` and `วันที่ครบกำหนด → Due Date`. Print labels already saved in
Thai must not be translated a second time for Thai output. Use the shared Jinja
`translate_print_label` method in current/legacy table, span and static-text
templates; English source labels still use the selected language's dictionary.
Regression coverage: `test_legacy_words_and_print_labels.py` plus the existing
number-to-words and print-layout tests.

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files
- **NEVER auto-commit or auto-push code** — always present changes and ask for approval before committing or pushing

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:

   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```

5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**

- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
- **NEVER auto-commit or auto-push without presenting changes first** — always ask for approval before committing and before pushing
<!-- END BEADS INTEGRATION -->

## Test Credentials

**Location:** `apps/print_designer/.env`

Contains:

- `SITE_USERNAME`
- `SITE_PASSWORD`

**Note:** Actual credentials are stored in this file - do NOT commit to git or share.

---

## WHT DocType Naming (Tier 2)

### Tier 2.1: Tax Withholding Category — IMPLEMENTED

- **Doc name (ID)** = `category_name_en` — already has full English format (e.g. `Transport 1% (PND3)`)
- **`title_field`** = `category_name` — Thai display (e.g. `ค่าขนส่ง 1% (ภงด.3)`)
- **No uniqueness issues** — 34 records, all `category_name_en` values are unique
- **PND54** — uses `Oversea` as recipient_type in doc name (already in `category_name_en`)
- **Migration** — rename via DB UPDATE, update all cross-links (TWI.tax_withholding_category, TWC.pd_custom_thai_wht_income_type) in same transaction

### Tier 2.2: Thai WHT Income Type — IMPLEMENTING

**Schema changes:**

- Keep `conditions` + `conditions_th` as-is (nuanced details beyond recipient_type)
- Add `recipient_type_th` (Select) — Thai options matching `recipient_type`:
  - `Individual` → `บุคคลธรรมดา`, `Corporation` → `นิติบุคคล`, `Foundation/Association` → `มูลนิธิ/สมาคม`, `Oversea` → `ต่างประเทศ`, `Government` → `รัฐบาล`
- Add `doc_title_th` (Data) — compound Thai display: `{income_category_th} {recipient_type_th} {tax_rate} {form_type_th}`

**Doc name format:** `{income_category} {recipient_type} {tax_rate} {form_type}`

- Example: `Advertising Income Corporation 2 PND53`

**`title_field`** = `doc_title_th` — compound Thai display

e.g. `ค่าโฆษณา นิติบุคคล 2 ภงด.53`

## E2E Testing

### Credentials

Credentials for testing are stored in `print_designer/.env`:

```bash
SITE_URL="https://digisoft-erp.bunchee.online"
SITE_USERNAME="Administrator"
SITE_PASSWORD="manlucha"
```

Load credentials in Python tests:

```python
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="/home/frappe/frappe-bench/apps/print_designer/.env")

site_url = os.getenv("SITE_URL")
username = os.getenv("SITE_USERNAME")
password = os.getenv("SITE_PASSWORD")
```

### Test Location

All E2E tests are in `print_designer/print_designer/tests/`:

```
print_designer/print_designer/tests/
├── test_page_orientation.py       # Page orientation feature tests
├── test_watermark_system.py       # Watermark functionality tests
├── test_company_preview.py        # Company logo/branding tests
└── ...
```

### Running Tests

```bash
# Run specific test
cd /home/frappe/frappe-bench/apps/print_designer
python -m pytest print_designer/tests/test_page_orientation.py -v

# Run all tests
bench run-tests --app print_designer
```

### Test Pattern (Python Playwright)

```python
from playwright.sync_api import sync_playwright
import os
import time
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv(dotenv_path="/home/frappe/frappe-bench/apps/print_designer/.env")
site_url = os.getenv("SITE_URL")
username = os.getenv("SITE_USERNAME")
password = os.getenv("SITE_PASSWORD")

def test_page_orientation_api_fetch():
    """Test that page_orientation is auto-populated from Print Format."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path="/home/frappe/frappe-bench/chromium/chrome-linux/headless_shell"
        )
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        
        # Login
        page.goto(f"{site_url}/desk/login")
        page.fill("#login_email", username)
        page.fill("#login_password", password)
        page.click(".btn-login")
        page.wait_for_url(f"{site_url}/desk/**", timeout=30000)
        time.sleep(5)
        
        # Navigate to print preview
        page.goto(f"{site_url}/desk/print/Stock%20Entry/MAT-STE-2026-00004")
        page.wait_for_load_state("networkidle")
        time.sleep(5)
        
        # Check page_orientation dropdown value
        result = page.evaluate('''() => {
            const field = document.querySelector('[data-fieldname="page_orientation"]');
            if (!field) return { found: false };
            const select = field.querySelector('select');
            return { found: true, value: select ? select.value : null };
        }''')
        
        print(f"page_orientation value: {result}")
        
        # Verify it matches Print Format value (Landscape)
        assert result['found'], "page_orientation field not found"
        assert result['value'] == 'Landscape', f"Expected Landscape, got {result['value']}"
        
        browser.close()
```

### Key Test Scenarios

1. **API Fetch**: Verify `page_orientation` is auto-populated from Print Format doctype
2. **Manual Override**: User can change orientation, preview updates with `.landscape` class
3. **CSS Injection**: Landscape CSS is injected with `!important` to override defaults
4. **Print Format Change**: When print format changes, orientation resets to new format's value

## PI Customs Entries / Import Clearance Item Table

**The child table for customs/VAT entries in Purchase Invoices is `tabImport Clearance Item`** — NOT a separate `tbs_customs_entries` table. It stores per-row VAT data with `parenttype='Purchase Invoice'`.

Key columns:
- `parent` = PI name
- `parenttype` = 'Purchase Invoice' (distinguishes from Import Clearance ICI rows)
- `vendor_name` = Supplier code (join to `tabSupplier.name`)
- `vendor_display_name` = Display name (often empty — use JOIN to `tabSupplier.supplier_name`)
- `vat_type` = Customs VAT / Inclusive VAT / Exclusive VAT / No VAT
- `base_amount` = Base amount in THB
- `vat_amount` = VAT amount
- `description` = Expense description

**Important**: The Doctype for this child table is `Import Clearance Item`, and the actual DB table is `tabImport Clearance Item`.

**Query pattern** (always JOIN to `tabSupplier` for vendor names):
```sql
SELECT ici.*, COALESCE(s.supplier_name, ici.vendor_name) AS vendor_display_name
FROM `tabImport Clearance Item` ici
INNER JOIN `tabPurchase Invoice` pi ON pi.name = ici.parent
LEFT JOIN `tabSupplier` s ON s.name = ici.vendor_name
WHERE ici.parenttype = 'Purchase Invoice' AND ici.vat_amount > 0
```
