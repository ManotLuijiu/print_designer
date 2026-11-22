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

## Browser printview copy watermark ownership

For `/printview` multi-copy output (`print_designer-awi`, 2026-11-20),
`www/printview.py:get_context` must not inject a general watermark into the base
HTML before `inject_multi_copy` duplicates it. Only the copy renderer adds each
copy's watermark. Otherwise "Original on First Page" produces two originals on
the first copy and another on the second. Single-copy output retains its general
watermark. Copy-option checks and watermark-mode fallback resolution are shared
between the rendering branches. Regression: `test_printview_watermark_copies.py`.
Verify actual Chrome PDF page text as well as DOM counts; the AWS quotation must
have Original counts `[1, 0]` across its two pages.

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

## Desk and browser printview table borders and blank padding

User-approved behavior (2026-11-20, `print_designer-e5r`): all Print Designer
Desk print previews show designer-configured vertical borders and separators
under actual data rows. Blank padding rows have no interior horizontal lines;
the outside bottom boundary remains. Do not center-align `td` vertically.

The current and legacy table templates expose intended border CSS in
`data-pd-preview-borders` and mark data/padding rows. `applyPDPreviewTableBorders`
in `public/js/print_table_borders.js` is shared by Desk preview and standalone
browser `/printview` (`print_designer-y4x`). Desk loads it before `print.js` via
`page_js`; `www/printview.html` loads it and applies it after adding the
`pd-browser-printview` marker. It changes only border properties inside
`#__print_designer table.printTable` under those two preview markers, preserving
saved colors/styles/hidden edges. It processes every copy in screen and print
media. Standard Frappe tables and unmarked renderers remain unaffected.
Do not replace it with an unscoped CSS rule or underline every padding row.
Regression tests: `print_designer/tests/test_desk_preview_table_borders.py`.
Retain the `[PD Preview Borders]` diagnostic logs until the user requests removal.

## Custom default template installer

See [Minimax handoff](wiki/custom-default-templates-installer-minimax.md) and
[implementation notes](wiki/default-templates-installer-implementation.md) for
recursive missing-only installation. The exported
`default_templates/asean_business_suite/services_quotation.json` is a copy of
the approved quotation with dynamic `Company.company_logo` images and no
source-site logo assets or sample document selection. It is not site neutral:
the header and the footer still carry the source company's static text (name,
tax id, contact, bank details), so a site that installs it has to replace that
text before it prints. The category name is not an installed-app dependency.
The importer is implemented
(`print_designer/default_templates_installer.py`) and runs from `after_install`;
it only fills in formats that are missing and never overwrites an existing
one. The dry run and the backfill of the sites that already run the app go
through the admin API
(`print_designer/api/default_templates_api.py::run_default_template_installation`),
which is a separate step that needs its own authorization - see the tracked
issue. Regression tests:
`print_designer/tests/test_default_templates_installer.py`.

## Sales Order milestone actions

See [Generate Invoice / copy feedback handoff](wiki/sales-order-generate-invoice-button-minimax.md)
and [implementation notes](wiki/sales-order-generate-invoice-button-implementation.md).
The workflow is implemented: a saved draft SO → Generate Invoice creates one
draft Sales Invoice per milestone → the SO can be submitted while the links
survive → the invoices are submitted afterwards. The draft mapping uses a
request scoped, internal only exception; the normal ERPNext checks stay in
place. Add row and the copy feedback stay available, the legacy
`pd_custom_add_invoice_schedule_row` field is now the Generate Invoice button
and the separate Add Milestone toolbar button is gone. Keep this feature in
Print Designer.

A milestone bills a part of the contract, it does not deliver a part of the
service. The invoice line therefore keeps the contract quantity and scales the
rate by the portion (`rate = so_item.rate * invoice_portion / 100`), because
ERPNext works the line amount out as `qty * rate` and the status updater bills
the line amount against the order. The portion is stored in
`pd_custom_invoice_portion`, the `%` column of the Sales Invoice Item right
after the Amount column, installed by
`print_designer/commands/install_milestone_invoice_item_fields.py`. The
submission guard compares quantity, portion and amount, never the rate.

The generated milestone line clears `margin_type`, `margin_rate_or_amount` and
`pricing_rules`: the milestone rate is derived from the contract, so ERPNext
must not price it a second time (`Sales Invoice` has no `ignore_pricing_rule`
field). The generation takes a row lock on the Sales Order and re-reads the
milestone rows under that lock, so two requests at the same time cannot both
invoice the same milestone. A Sales Order line without a quantity is left out
of the invoice. The three endpoints that change a Sales Order
(`seed_invoice_schedule`, `add_invoice_schedule_row`,
`generate_milestone_invoices`) are POST only.

A milestone invoice carries only its part of the contract: the fixed
`discount_amount` of the header and the tax rows with the amount `Actual` are
split over the milestone portions (`_allocate_fixed_amounts`), the last
milestone gets the rounding remainder so the parts add up to the amount of the
order, and a discount or a charge in percent is left to ERPNext. The invoice
is dated at the date of the milestone: ERPNext v16 works the posting date out
again on every save, so the generated invoice sets `set_posting_time` and the
dates of the payment schedule move with it. After the Sales Order is
submitted its milestones are frozen and the billing date of the draft invoice
is the user's own business: the posting date can still be changed in the
form and the change survives the submit of the invoice. The submission guard compares the
item, the unit of measure, the conversion factor, the project and the date
beside the quantity, the portion and the amount, and a draft that no longer
matches is refused with a message that says what has changed. The link
between a milestone and its invoice belongs to the server: every save of the
Sales Order reconciles the stored links (`reconcile_milestone_links`) and the
timestamp of the order moves with every change of a milestone, so a form that
was opened before the generation cannot erase the links.

Regression tests: `print_designer/tests/test_invoice_schedule.py`,
`print_designer/tests/test_invoice_schedule_flow.py`,
`print_designer/tests/test_invoice_schedule_generation.py`,
`print_designer/tests/test_invoice_schedule_buttons.py` and
`print_designer/tests/test_milestone_invoice_item_field.py`. The browser
verification of the buttons is in the
[milestone UI notes](wiki/sales-order-milestone-ui-e2e-minimax.md).

## Milestone invoice payment schedule date types

Investigated on 2026-11-21 with `SO-69-08-00001` (issue `print_designer-01f`).
Generating the milestone invoices failed inside ERPNext:

```text
File ".../erpnext/controllers/accounts_controller.py", line 2715, in set_due_date
    self.due_date = max(due_dates)
TypeError: '>' not supported between instances of 'datetime.date' and 'str'
```

The payment schedule of a milestone invoice mixes date types. The child table
of the order and of the invoice is the same `Payment Schedule`, but the field
of the order carries `no_copy = 1`, so the mapper leaves the invoice without a
schedule and ERPNext builds it in `make_sales_invoice` with
`doclist.set_payment_schedule()`. That function takes the posting date of the
new invoice, which is the default `Today` and therefore a **string**
(`frappe.utils.nowdate()` returns a string). A date that ERPNext works out
from that posting date stays a string, while a date that is taken over from
the order is a `datetime.date`.

`frappe.utils.add_to_date` keeps the type of its input: it sets
`as_string = True` for a string and returns `date.strftime(DATE_FORMAT)`.
`add_days` delegates to it, so `_shift_payment_schedule` used to keep the
mixed types - and it skipped the whole schedule when the offset was zero.

`_shift_payment_schedule` now normalizes every populated due date and discount
date with `getdate` before it moves them, and the early return for a zero
offset is gone. The calendar days do not change, only the type. Do not catch
and ignore the TypeError, replace the core `set_due_date`, remove the invoice
Payment Schedule or turn every date into text to make the comparison work.

The collection-date policy of the schedule is a separate question and is not
part of this repair: the first row of the schedule is anchored to the day the
invoice is generated, not to the date of the order.

Regression tests: `print_designer/tests/test_invoice_schedule_mixed_dates.py`.
The detail is in the
[mixed-date notes](wiki/milestone-invoice-mixed-dates-minimax.md).

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

### The app's own test runner

`bench run-tests` preloads the test records of **every installed app** before
it runs the first test (`frappe/testing/environment.py` ->
`_create_global_test_record_dependencies`). On a site whose other apps carry
incomplete fixture data that preload dies before any Print Designer test
runs. On `demo.bunchee.online` HRMS is installed without its payroll module,
so the Leave Type records that HRMS generates link to the Earning Component,
a DocType that is not installed there, and the preload fails with
`LinkValidationError`.

The app therefore has its own runner, which runs the same test modules with
the same environment setup and without the global preload:

```bash
bench --site <site> execute print_designer.commands.run_tests.main

# A single module
bench --site <site> execute print_designer.commands.run_tests.main \
  --kwargs '{"modules": ["print_designer.tests.test_invoice_schedule_flow"]}'
```

It prints a summary (`tests`, `failures`, `errors`, `skipped`) and raises
when a test fails, so the exit code stays meaningful.

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

## Invoice Schedule milestone dropdown and legacy handler collision

See [Minimax handoff](wiki/invoice-schedule-payment-term-dropdown-minimax.md).
The free-text Invoice Schedule `payment_term` field collides with the legacy
ERPNext `frm.cscript.payment_term` handler, which assumes a Payment Schedule
row and loads a Payment Term master. Skip that legacy handler only for Invoice
Schedule; preserve its behavior elsewhere. Use native Autocomplete with
`ignore_validation: 1` to suggest existing terms while retaining manual names.
Use the Print Designer permission-checked lookup; this site's TBS override of
Desk search has an incompatible signature. Do not edit core or TBS for this fix.

Verified in a real browser on `aws-solution.bunchee.online`
(Sales Order `SO-69-08-00001`, never saved): the milestone cell lists
`ส่งงานช่วง UAT (60%)` for the text `ส่งงาน`, a mouse click puts the exact name
in the row, a manual name survives the blur without the "Payment Term not
found" dialog, and the expanded row editor behaves the same. The scoped
wrapper is installed once per form and the original ERPNext handler still
runs for the real Payment Schedule rows. A user without Payment Term read
gets a permission error and no suggestions.

Two traps when repeating the check: the Payment Schedule grid also has a
`payment_term` column, so a page-level selector can hit the wrong grid - scope
it to `frm.fields_dict.pd_custom_invoice_schedule.grid.wrapper`. And clear the
input before typing, otherwise the search runs on the old value plus the new
text and finds nothing. The Payment Schedule dropdown itself stays broken by
the TBS search override; that is pre-existing and out of scope.

## Python indentation convention is per file

Every changed Python file keeps the indentation style it already had. The
repository mixes tabs and spaces, and the style is a property of the file, not
of the project: `print_designer/custom/invoice_schedule.py`,
`print_designer/tests/test_invoice_schedule.py` and `print_designer/uninstall.py`
use tabs, most of `print_designer/tests/` uses spaces, and the isort settings
in `pyproject.toml` ask for `indent = "\t"`.

A new file follows the convention of the files next to it, not the isort
setting and not the Ruff default.

**Do not use a Ruff-formatted diff as the churn measure.** Comparing HEAD
against the Ruff-formatted current file hides an indentation change: Ruff
normalises to spaces, so a tab file that was converted to spaces still matches
its own formatted output and the measured churn is 0. Measure the indentation
style of the current file against the indentation style of HEAD instead, and
use `git diff --cached -w` to see how much of the diff is whitespace only.

**Restoring the layout is a three way merge, not a formatter run.** Normalise
both sides with Ruff using the indentation style of the file, merge the
semantic change onto the HEAD layout, and verify the result compiles and has
the same syntax tree as the current version. Do not run `ruff format` across
the repository to tidy the diff: it rewrites the untouched code of every file
it touches.

## Sales Invoice milestone percentage grid order

User requirement (2026-11-21): Items grid must show `Item, Quantity, Rate, %, Amount`
with the existing row number first. `pd_custom_invoice_portion` is a read-only
Percent field anchored after `rate`, width `columns: 1`; it is not a discount.
The app's field installer owns this metadata for install/migrate. Existing
saved GridView layouts can omit the field regardless of `in_list_view: 1`.
`public/js/invoice_schedule/sales_invoice_milestone_grid.js` wraps only the
current Sales Invoice Items grid's column setup to insert it after Rate while
retaining other saved columns. It does not clear or persist over user settings,
change core prototypes, or save invoices. Adjust widths only as needed to fit.
Regression: `node print_designer/tests/test_sales_invoice_milestone_grid.cjs`.

The Sales Invoice WHT script must load only through `doctype_js`, alongside
`thailand_wht_vat_helper.js`. Do not also import it from `public/js/app.js`:
that duplicate global copy cannot access `pd_apply_item_wht_config`, throws
on refresh and prevents later form handlers (including the grid) from running.

## VAT DocType ownership relocation and Sales VAT lifecycle

User-approved relocation verified on AWS on 2026-11-21: **VAT Offset Entry,
Thai Sales VAT, VAT Type, Thai VAT Recognition and Thai VAT Recognition Item**
now belong to module `Print Designer`, app `print_designer`. Print Designer is
independent of TBS; essential VAT behavior must work without TBS installed.
New controllers belong under `print_designer.print_designer.doctype.<slug>`.
Keep DocType names, database tables, IDs, links and historical data unchanged.

See [VAT relocation and Sales VAT action plan for Minimax](wiki/vat-relocation-and-sales-vat-plan-minimax.md).
The user split this work into two jobs: finish controller/import/RPC/hook/test
migration after the completed module relocation, then repair VAT recognition
and reporting. **The new controllers were generated `pass` stubs at inspection;
substantial VAT Offset Entry and Thai VAT Recognition logic remains in old TBS
files. Do not treat relocated metadata as proof that behavior was migrated.**
User requirement: once the Print Designer implementations are stable and pass
migration/authorization/accounting/UI E2E tests, **delete the old TBS source
folders for these same five DocTypes**, plus obsolete hooks/imports/RPC references
and duplicated tests/assets. Do not delete the old behavior before it is ported.
This is source/package cleanup only: never delete the live DocTypes, tables,
records or links now owned by Print Designer. Port meaningful tests before
retiring copies, and verify TBS migrate/uninstall cannot remove the new owner's
data. Any temporary old-path RPC shim needs a documented retirement condition.

Port authorization checks too, replacing mandatory TBS helper dependencies with
independent Print Designer/Frappe equivalents. Update old dotted paths in callers;
optional TBS compatibility shims may delegate to PD, never the reverse. Prevent
old TBS JSON/uninstall routines from reclaiming/removing the new ownership.

The intended ordinary flow is deferred services SI → Output VAT Undue → receipt
allocation/qualifying tax event → recognition → Thai Sales VAT; already-due VAT
routes directly into reportable records. Use VAT treatment/tax-point events,
not stock flags alone. Support partial receipts, mixed items, reversals and
report periods. Ensure exactly one GL reclassification per event; existing PE
regional GL and old recognition JE paths must not both post it. Avoid commits
inside hooks, duplicate whole-invoice reporting and unreviewed live backfills.
Thai VAT Recognition currently has `is_submittable=0` despite old submit/cancel
logic; resolve that mismatch explicitly in the migration tests. No VAT workflow
implementation or live tax-data changes were made by this documentation task.

## WHT and PND ownership in independent Print Designer

User decision and AWS ownership verification (2026-11-21): **Thai WHT Rate
Setting** now belongs to module/app Print Designer. Its controller is
`print_designer.print_designer.doctype.thai_wht_rate_setting.thai_wht_rate_setting`.
It remains a child table. PND1/PND3/PND53/PND54 Form and their corresponding Items
DocTypes already belong to PD; do not recreate them or move them back to TBS.
Essential VAT/WHT/PND behavior must work without TBS installed.

See [WHT/PND relocation supplement for Minimax](wiki/wht-pnd-ownership-relocation-minimax.md)
and the [VAT migration plan](wiki/vat-relocation-and-sales-vat-plan-minimax.md).
Both old/new WHT rate child controllers are `pass`; existing lookup/calculation
logic lives in TBS `thai_tax/utils/tax_calculator.py`, requirement checks in
`validators.py`, and child validation in Thai Tax Settings JS. Port/reconcile
that behavior and its tests; do not assume module relocation moved it.

**Parent relocation now explicitly approved and verified:** Thai Tax Settings
also belongs to PD at `print_designer.print_designer.doctype.thai_tax_settings.thai_tax_settings`.
It remains a Single DocType whose `default_wht_rates` hosts Thai WHT Rate Setting.
Preserve settings values in `tabSingles` and child links/IDs/rates; do not create
a different parent or reset existing configuration. The new parent controller is
a `pass` stub, while the old TBS controller contains validation, account creation,
cache handling and RPCs. Port/review that logic, permissions and settings JS,
replace required TBS helper/installer imports with PD-owned equivalents, and
resolve old child `.rate` references against the actual rate-field schema.
Review existing PD WHT categories/income types/certificates for one authoritative
rate-selection policy, preserving zero rates, effective dates and company scope.

After PD functionality is stable and its migration/permission/calculation/UI/PND
tests pass, delete the old TBS `thai_tax/doctype/thai_wht_rate_setting/` and
`thai_tax/doctype/thai_tax_settings/` source folders and obsolete duplicate
references/handlers, as with the five VAT relocations. This extends the named
VAT/WHT/settings portion of the retirement scope to seven DocTypes; the
Intake relocation below brings the overall scope to **eight DocTypes**. Preserve
live DocTypes/tables/rows/rates, parent links and PND filings; protect ownership
against old TBS migrate/uninstall. No rate changes or filing actions are part
of this documentation task.

## Thai Tax Invoice Intake relocation to Print Designer

User-confirmed and AWS-verified on 2026-11-21: **Thai Tax Invoice Intake** now
belongs to Print Designer at
`print_designer.print_designer.doctype.thai_tax_invoice_intake.thai_tax_invoice_intake`.
It is the eighth named tax relocation (five VAT DocTypes, WHT rate child,
Thai Tax Settings, then Intake). See [Minimax Intake handoff](wiki/tax-invoice-intake-relocation-minimax.md).

The new controller/JS were generated stubs at inspection; old TBS source still
contains verification/rejection, attachment access, draft PI synchronization,
status/failure handling, privileged sweep RPC and extensive authorization tests.
Port behavior, UI, permissions, callers and tests before declaring migration
stable. Replace mandatory TBS helper imports with PD-owned/Frappe equivalents.
Preserve POST-only mutations and caller-authorized Intake/File/PI access.

**The port is done (2026-11-22).** The controller of Print Designer owns the
whole workflow and imports no Thai Business Suite module:

- `print_designer/print_designer/doctype/thai_tax_invoice_intake/thai_tax_invoice_intake.py`
  implements `set_verification_status`, `sync_to_purchase_invoice`,
  `validate_for_sync`, `validate_the_amounts_of_the_invoice`,
  `validate_the_booking_of_the_invoice`, `read_attachment`,
  `create_purchase_invoice`, `record_failure` and `sweep_pending_intakes`.
  Every state change answers only to a POST, the purchase invoice is created
  with the rights of the caller, the attachment is bound to the intake and its
  File record is checked for the right to read, and a failed run rolls back to
  a savepoint and records the failure on the intake.
- The authorization helpers are Print Designer owned:
  `print_designer/custom/document_permission.py` (a missing document and a
  forbidden document are refused the same way) and
  `print_designer/custom/maintenance_access.py` (the role of the maintenance).
- The client workflow lives in
  `print_designer/print_designer/doctype/thai_tax_invoice_intake/thai_tax_invoice_intake.js`.
  The three buttons are POSTs on the document, the form is frozen during the
  call and reloaded afterwards, and the visibility follows the state.
- The Thai Business Suite controller is a behaviour free shim that re-exports
  the exact class of Print Designer.
- `print_designer/patches/relocate_thai_tax_doctypes.py` reasserts the
  ownership of `Thai Tax Settings`, `Thai WHT Rate Setting` and
  `Thai Tax Invoice Intake` without creating a row.
- The tests are `print_designer/tests/test_thai_tax_invoice_intake.py` (26),
  `print_designer/tests/test_thai_tax_invoice_intake.cjs`,
  `print_designer/tests/test_thai_tax_settings_client.cjs` and the retained
  `thai_business_suite/tests/test_tax_invoice_intake_authorization.py` (23).

Intake is an optional supplier-document capture/verification workflow that
creates a draft Purchase Invoice; it must not submit it or independently post
VAT. The Sales Tax Invoice option is not supported by existing synchronization.
After PD-only/both-app migration, permissions, rollback/concurrency and real UI
tests pass, delete the old TBS Intake source and obsolete references/tests.
Keep live DocType/table/records, attachment File links and Purchase Invoices.
Prevent old TBS migrate/uninstall from reclaiming/removing PD-owned data. The
old TBS Intake source is still present; its deletion is a separate cleanup.

## Document naming series overrides stay in Thai Business Suite

User decision, 2026-11-22: **Print Designer does not add its own
`naming_series_variables` hook.** The document naming series overrides stay
in Thai Business Suite, where they already live
(`thai_business_suite/overrides/naming.py`, registered in
`thai_business_suite/hooks.py`): `DBEYY`, `DMM`, `BEYY`, `DYY`, `DYYYY`,
`DDD`, `DWW`, `DFY`, `DOT`, `SLASH`, `ABBR`, `ACAT`, `ASUB`.

Rules that follow from that decision:

- Do not register a `naming_series_variables` mapping in
  `print_designer/hooks.py`. Frappe resolves a custom parser with the first
  hook entry (`frappe.model.naming.has_custom_parser` uses `method[0]`), and
  ERPNext already registers `ABBR`. A second registration of the same key
  would make the winner depend on the order of the installed apps.
- Do not copy the whole TBS naming override into Print Designer. Only the
  variables a relocated DocType needs would be candidates, and today no
  Print Designer DocType needs one.
- A relocated DocType keeps its naming series string as it is. The Thai Tax
  Invoice Intake keeps `TTI-.DBEYY.DMM.-`; on a site where Thai Business
  Suite is installed the Thai variables resolve exactly as before, because
  the hook is global and not bound to the owner of the DocType.
- On a site without Thai Business Suite (for example
  `digisoft-erp.bunchee.online`, which installs `digisoft_erp` as the peer of
  TBS on purpose), a naming part that no app provides is not resolved by
  Frappe and stays literal in the name. Frappe's own naming logic stays the
  fallback of the site. This is a known later item, tracked separately: when
  that site is debugged, evaluate an option that lets the user choose
  Frappe's default document naming series there.
- The dependency direction stays one way: TBS may depend on Print Designer,
  never the other way round. A naming override in TBS never becomes a
  requirement of the core Print Designer implementation.

## Thailand Tax master plan and SI Services first chunks

See [master plan](wiki/thailand-tax-master-plan.md),
[SI-01 data contract](wiki/si-services-tax-data-contract-minimax.md),
[SI-02 service tracking](wiki/si-services-output-vat-undue-minimax.md), and
[SI-03 Preview reports](wiki/si-vat-preview-reports-minimax.md).

**User instruction: keep SI fields/layout as-is**, including values shown in
Details and Thai Tax Compliance. Reuse stored fields in background; do not move
or duplicate WHT/VAT/retention controls. Latest requested menu behavior:
**Draft SI:** Preview → Output VAT Report and Output VAT Undue Report below
Accounting Ledger. **Submitted SI:** move existing Output VAT Report from Tools
to View, preserving its Thai Output VAT Report route/filters; keep Analyze in
Grist in Tools. Do not add a Submitted Undue action unless separately requested.
Learn the existing injection from TBS public/js/sales_invoice_grist.js. Draft
previews are explicit read-only projections labeled Not Posted, not tax records;
normal monthly posted reports must continue excluding drafts. No automatic save
of dirty/new drafts. Follow the revised SI-03 wiki for separate Task A/B tests.

All scoped submitted service SIs should have Output VAT Undue tracking, including
exempt/non-registered sales, but zero-tax tracking must have explicit reason and
no undue balance. Record presence is not VAT liability. Genuine deferred VAT,
already-due VAT, exempt supply, non-registration and zero-rated treatment remain
distinct. Do not manufacture VAT from a default rate or all taxes/charges.
Draft SIs do not post tracking; reports are read-only and do not backfill.

Implement/document each small chunk separately after its prerequisites. Current
company registration is read from TBS-owned Thai Company Settings: resolve an
independent per-company source; the relocated Single Thai Tax Settings is not
that DocType. No additional relocation or new visible SI fields are implicitly
authorized by this plan. Preserve eight-relocation ownership/data protections.

## Tax relocation includes all relevant functions

Explicit user requirement: all behavior relevant to the eight relocated tax
DocTypes must move from TBS into independent Print Designer—not only their
JSON/controllers. See [master plan: complete behavior ownership](wiki/thailand-tax-master-plan.md#complete-behavior-ownership--explicit-user-requirement).
Include tax-specific helpers/calculators/validators, permission checks, RPCs,
document/regional hooks, JS actions, report queries, settings cache/setup logic,
install/migrate/uninstall paths, fixtures and meaningful tests. Inventory old/new
function paths and all callers beyond the DocType folders. Port independent
PD/Frappe permission helpers; do not retain required TBS imports or duplicate
posting engines. Keep unrelated TBS functionality intact when extracting shared
utilities. Optional TBS consumers/wrappers may delegate to PD only, with explicit
retirement conditions; app installation order is not the ownership mechanism.

After PD-only/both-app install, migration, authorization, accounting and UI tests
prove stability, retire old TBS implementations and obsolete registrations,
callers and duplicated tests/assets. Preserve live schema/data/Single values,
child rows, attachments and links. No actual function migration or old-source
deletion was performed by this documentation update.

## SI-02 Output VAT Undue ledger: identity, race and migration

The ledger of the undue output VAT is the `Output VAT Undue` document. One
orchestration path writes it:
`print_designer/custom/output_vat_undue_tracking.py`. The controller
`print_designer/print_designer/doctype/output_vat_undue/output_vat_undue.py` is
the compatibility surface of that path and holds no logic of its own.

The identity of a row is the invoice it belongs to:

- the document names itself after the field `sales_invoice`
  (`autoname: field:sales_invoice`), and the insert of the tracking sets the
  name of the row to the name of the invoice, so the primary key of the table
  is the uniqueness of the ledger,
- there is **no** unique index on the column `sales_invoice`, on purpose. The
  rows of the old implementation carry a name of their own and a site can hold
  more than one row for an invoice, because the old implementation wrote a row
  per submit without a uniqueness of its own. Such a table cannot take that
  index without a rewrite of the history of the ledger,
- the `exists()` check stays, but only as an optimisation. The race of two
  transactions is settled by the insert: the insert runs inside a transaction
  local savepoint, a collision of the primary key is recognised through the
  adapter of the site (`is_primary_key_violation`, `is_unique_key_violation`),
  and the loser of the race carries on with the row of the winner. A
  permission, a link, a validation or another database error still surfaces.
  The original database error sits in `exc.args[2]` of both
  `frappe.DuplicateEntryError` and `frappe.UniqueValidationError`,
- the work stays inside the transaction of the invoice. There is no commit in
  the hook, the ledger creates no GL entry, and the cancellation keeps the row
  as the history of the sale.

The schema of the ledger is applied by the model synchronisation of Frappe. The
reviewed migration `print_designer.patches.migrate_output_vat_undue_ledger`
runs after it and verifies the columns, the naming and the primary key, reports
the invoices that carry more than one row of the old implementation, and takes
the unique flag of the field back when those rows would make the unique index
impossible. It creates nothing: no row, no GL entry, no backfill.

The tests are `print_designer/tests/test_output_vat_undue_tracking.py`. The
tests of the site skip themselves while the ledger of the site is not migrated.

The ledger was migrated and verified on `demo.bunchee.online`: `autoname` is
`field:sales_invoice`, `allow_rename` is 0, the metadata carries 39 DocFields,
the table carries 41 physical columns, the only physical indexes are
`PRIMARY (name)` and `creation`, there is no separate unique index on
`sales_invoice`, and the table holds no row - the migration creates no
historical tracking and no GL entry. The patch reports nothing on a second
run. The site level tests of the ledger run on that site now (34 tests, 0
failures).

The treatment of a Sales Invoice is resolved by the site itself: the Thai
Business Suite `apply_vat_treatment()` writes it while the invoice is saved
and overwrites a manual `VAT Undue` with the treatment that the tax template
of the company leads to. The ledger reads the persisted treatment, so the row
of the demo site carries `VAT Due` and the status `Already Due`. A site level
test has to expect the decision of the invoice and not a reason of its own.

`aws-solution.bunchee.online` still carries the legacy schema, the legacy
metadata and no row; its migration needs a separate authorization. Detail in
[SI-02 notes](wiki/si-services-output-vat-undue-minimax.md).

## SI-03 Task A: the draft VAT previews of a Sales Invoice

Implemented on 2026-11-21 in Print Designer. Task B (the move of the
submitted Output VAT Report action from Tools to View) is not started; it
belongs to the client script of Thai Business Suite.

A saved draft of a Sales Invoice gets two buttons in the `Preview` group of
the form, below the `Accounting Ledger` button of ERPNext: `Output VAT
Report` and `Output VAT Undue Report`. A new invoice gets no button (it has
no stored values) and a submitted invoice gets no button (it has its own
report). The endpoint `print_designer.api.sales_invoice_vat_preview.get_draft_vat_preview`
reads the SI-01 contract of one draft and returns a projection; it writes
nothing: no row of the Output VAT Undue ledger, no GL entry, no change of
the invoice. The permission is checked on the server, the client filter is
not an authorization.

`Output VAT Report` mirrors the row of the existing query report `Thai
Output VAT Report` (Tax Invoice No., Tax Invoice Date, Customer Name, Customer
Tax ID, Base Amount, VAT Amount) and adds the decision of the invoice. That
report reads submitted invoices only (`si.docstatus = 1`), so it cannot show
a draft and the preview is a projection instead; no second report was created
only to match a button label. `Output VAT Undue Report` projects the ledger
side (status, reason, eligible service base, prospective undue VAT, VAT
already due); its identity is the Print Designer ledger `Output VAT Undue`,
whose row name is the Sales Invoice name. A collision check over all apps
found no report or doctype called `Output VAT Undue Report`.

Tests: `print_designer/tests/test_sales_invoice_vat_preview.py` (19 tests, 0
failures, 0 errors, 0 skipped on `demo.bunchee.online`) and
`print_designer/tests/test_sales_invoice_vat_preview.cjs` (run with `node`).
The full app on that site: 540 tests, 0 failures, 0 errors, 4 skipped. The
browser proof of the buttons needs a build of the app and a cleared cache of
the site. Detail in [SI-03 notes](wiki/si-vat-preview-reports-minimax.md).

## SI-03 Task B: the submitted Output VAT Report action

Implemented on 2026-11-22 in Print Designer. The action of a submitted Sales
Invoice sits in the `View` group of the form; it used to sit in the `Tools`
group, where the client script of Thai Business Suite registered it.

- `print_designer/public/js/sales_invoice/output_vat_report.js` registers the
  action in the `View` group of a submitted invoice and removes the old
  registration of the `Tools` group. A draft and a cancelled invoice get no
  action: a draft owns the previews of Task A, a cancelled invoice owns
  neither.
- `print_designer/boot.py` publishes `print_designer_output_vat_report`: the
  name of the report and the flag `available`. The flag is true when the
  report exists on the site and the user holds the report permission on the
  Sales Invoice - the same permission the query report asks for. A site
  without the report gets no button, so the action never opens a report that
  cannot run.
- `thai_business_suite/public/js/sales_invoice_grist.js` retires its own
  registration of the action, so the action is never shown twice.
  `Analyze in Grist` stays in the `Tools` group, unchanged.
- The report identity and the filters are unchanged: the query report `Thai
  Output VAT Report` with `company` of the invoice, `from_date` and
  `to_date` of the posting date and `invoice_name` of the invoice. The
  report itself is still owned by Thai Business Suite; its data source and
  its accounting are a separate job. This change is navigation only: no
  field, no layout and no accounting of the Sales Invoice changed.

Tests: `print_designer/tests/test_output_vat_report_action.py` (7 tests, 0
failures, 0 errors) and
`print_designer/tests/test_output_vat_report_action.cjs` (run with `node`).
The full app on that site: 571 tests, 0 failures, 0 errors, 4 skipped. With
the old registration of Thai Business Suite and without the hook entry of the
new script, 3 of the 7 backend tests fail. The browser proof waits for a
build of the app and a cleared cache of the site, like the proof of Task A.

## Audit of the Thai VAT and WHT calculation modules

Done on 2026-11-22. The oracle of the derived amounts is the canonical
backfill of Thai Business Suite
(`thai_business_suite/commands/backfill_canonical_wht_fields.py`): the base of
a Sales Invoice is `total` (without VAT), the base of a Sales Order and of a
Quotation is `grand_total`, the net after the retention is only derived with
an active retention, and only the payment amount is clamped to zero. The three
calculation modules of Print Designer follow that oracle exactly - the
derivation was not changed.

- The wording of the calculated amounts named the default currency of the
  site instead of the currency of the document (Frappe's `money_in_words`
  falls back to the currency of the site). The wording of the three modules
  now lives in one place, `print_designer/custom/thai_calculation_words.py`,
  and it names the currency of the document. The language of the wording is
  unchanged; the print format still decides the language of the printed
  document through the number to words pairs.
- A VAT row of a document in another currency kept an empty base amount, so
  the contract reported a VAT of zero in the currency of the company and the
  Output VAT Undue ledger stored that zero. The base amount is now the tax
  amount converted with the rate of the document, the way ERPNext computes it,
  and a row that keeps its empty base amount is reported as a warning.
- The constraint validation of the three modules is never called, the base of
  the validation differs from the base of the derivation and
  `sales_invoice_comprehensive_wht_handler` is dead code. These three
  findings are documented in `wiki/si-vat-wht-calculation-audit-minimax.md`
  and are deliberately not changed: registering the validation would start to
  block documents that are saved today, and the payment amount clamp is the
  active guard.
- The files that only carried the mechanical cleanup of an earlier phase
  (`sales_invoice_calculations.py`, `sales_order_calculations.py`,
  `quotation_calculations.py` and both copies of
  `regional/purchase_invoice_tax_override.py`) were restored to the state of
  the last commit before the audit, so that the diff shows only the work that
  changes something. The two copies of the purchase invoice override are
  identical again.

Tests: `print_designer/tests/test_si_vat_wht_calculation_audit.py` (17 tests,
0 failures, 0 errors). Without the two fixes the module reports 3 failures.
The related suites (contract, ledger, preview, resolver): 138 tests, 0
failures, 0 errors. The full app: 588 tests, 0 failures, 0 errors, 4 skipped.

## The Thai Tax Settings controller is ported to Print Designer

Done on 2026-11-22, the first of the relocated tax controllers that is a
singleton of the site. The settings carry the state of the Thai tax: the
withholding tax, the VAT rate, the branch code, the numbering of the
certificates and the reports of the forms 1, 3 and 53.

- `print_designer/print_designer/doctype/thai_tax_settings/thai_tax_settings.py`
  is the live controller with the endpoints. The old controller of Thai
  Business Suite could not work against the metadata of the doctype: the
  doctype carries neither the four accounts of the tax nor a field named
  `rate` in the row of a rate. The port reads the accounts only when the
  doctype carries them, reads the rates from the fields that the row really
  has (`tax_rate`, `individual_rate`, `company_rate`, `government_rate`),
  reads the values with `get` and refuses the creation of the accounts when
  the account that was created could not be remembered.
- The authorization is the one of Print Designer:
  `print_designer/custom/maintenance_access.py` (the role of System Manager)
  and `print_designer/custom/document_permission.py` (the right of the
  doctype). Print Designer does not import Thai Business Suite.
- `print_designer/patches/relocate_thai_tax_doctypes.py` puts the ownership
  back after the model synchronisation. The patch carries the `Thai Tax
  Settings` and the `Thai WHT Rate Setting`, and it touches the metadata
  only. The ownership was applied to `demo.bunchee.online` and the settings
  of that site were not touched.
- The old path of Thai Business Suite is a behaviour-free shim that
  re-exports the controller and the endpoints from Print Designer.

Tests: `print_designer/tests/test_thai_tax_settings.py` (12 tests, 0 failures,
0 errors). The negative proof: with the reading of the rates as it was in
Thai Business Suite, 2 of the 10 tests fail; with the reading of the
accounts as attributes, 1 of the 10 tests errors with the `AttributeError` of
the old code. The tests of Thai Business Suite that use the old path: 49
tests, 0 failures, 0 errors. The whole app: 598 tests, 0 failures, 0 errors,
4 skipped.

## The tax calculator of Thailand is ported to Print Designer

Done on 2026-11-22. The calculator of the withholding tax of Thai Business
Suite (`thai_business_suite/thai_tax/utils/tax_calculator.py`) lives in
Print Designer now, so the tax of Thailand works on a site where Thai
Business Suite is not installed.

- `print_designer/custom/thai_tax_calculator.py` holds the behaviour: the
  rate of an income type (the `Thai WHT Rate Setting` first, the rates of
  the law of Thailand as the fallback), the amount of the withholding tax,
  the form of the withholding tax (PND1, PND3, PND53), the rate of a row
  for the kind of the party, the settings of a party, the check digit of
  the tax identification number of Thailand, the check of the tax of a
  document, the certificate of the withholding tax of a payment entry and
  the address of a party.
- The certificate keeps the shape of Thai Business Suite (`Withholding Tax
  Cert`, one income item per row of the withholding tax). The certificate of
  Print Designer (`Withholding Tax Certificate`) is a different document
  with a different shape and is not used by this path.
- The old path of Thai Business Suite is a behaviour-free shim. Its three
  callers (the two overrides of the payment entry and the validator of the
  income type) keep working through the shim.

Tests: `print_designer/tests/test_thai_tax_calculator.py` (19 tests, 0
failures, 0 errors). The negative proof: with the kind of the party always
a company and the effective dates of the rate ignored, 2 of the 19 tests
fail. The tests of Thai Business Suite that use the old path: 104 tests, 0
failures, 0 errors. The whole app: 619 tests, 0 failures, 0 errors, 4
skipped.

## Type debt cleanup of the Thai WHT and retention modules

Done on 2026-11-21 for `print_designer/regional/purchase_order_wht_override.py`,
`print_designer/regional/purchase_invoice_wht_override.py` and
`print_designer/custom/payment_entry_retention.py`. All three are now clean
(basedpyright 0 errors, ruff passes, `py_compile` ok) and the full app on
`demo.bunchee.online` still runs 540 tests with 0 failures and 0 errors.

Only behaviour-identical transformations are allowed in this area:

- A scalar field is written with `doc.set("field", value)` and read with
  `doc.get("field")`. `BaseDocument.set` ends in `self.__dict__[key] = value`
  for a field that is not a table, and `BaseDocument` does not override
  `__setattr__` (`frappe/model/base_document.py:348`). A **table** field is not
  equivalent: `set()` would initialise or extend the child list.
- `typing.cast` is the tool for the optional dates and for the union of
  `frappe.db.get_value`: it is a runtime no-op, so `flt(cast(float, value))`
  and `cast(date, getdate(value))` keep the old behaviour exactly.
- `frappe.defaults.get_defaults()` and `frappe.utils.nowdate()` are imported
  directly; `frappe.get_defaults` does not exist.
- A multi line right hand side is bound to a local variable first, so the
  expression and its operator precedence stay unchanged.

Do not run `ruff format` over the repository for this and do not script the
rewrite: an earlier scripted attempt mangled seven files and had to be restored
from HEAD. The rest of the repository debt stays in `print_designer-4hc`; the
repository wide error count of basedpyright is now 2978, down from 3413.
Detail in [the cleanup notes](wiki/type-debt-cleanup-wht-retention-minimax.md).

## The VAT Offset Entry controller is ported to Print Designer

Done on 2026-11-21, the first of the relocated VAT controllers with its
behaviour in Print Designer. The order of the work is the Sales Invoice side
first: the Sales Invoice netting and the recognition of the Sales Invoice flow
come before the Purchase Invoice side, which is not urgent now.

- `print_designer/print_designer/doctype/vat_offset_entry/vat_offset_entry.py`
  is the live controller. The metadata was already owned by Print Designer
  (`module: "Print Designer"`, submittable, 31 fields), so the file carries
  the behaviour of the netting: both invoices submitted, the same party and
  the same company, an outstanding amount on both, a difference account for a
  partial offset, a tolerance of 0.50 THB for a full offset, a cash account
  always, and a Journal Entry that always balances.
- `print_designer/custom/document_permission.py` holds the permission helper
  the controller needs. It is the Thai Business Suite helper ported with the
  same semantics and without importing Thai Business Suite: the check of the
  right is muted, so the answer of the request does not tell a document that
  is not on the site from a document that the caller may not read.
- `print_designer/tests/test_vat_offset_entry.py` holds the eight ported
  tests. They create real invoices, a real offset entry and a real submitted
  Journal Entry.
- The old path of Thai Business Suite is a shim that re-exports the
  controller and the lookup from Print Designer. The dependency runs from Thai
  Business Suite to Print Designer, never the other way round. The shim is
  removed together with the old Thai Business Suite source folder, when the
  remaining callers use the Print Designer path.

On `demo.bunchee.online`: 8 tests of the ported controller, 3 tests of the
Thai Business Suite module that imports the old path, and the whole app with
548 tests, 0 failures, 0 errors, 4 skipped. Detail in
[the relocation plan](wiki/vat-relocation-and-sales-vat-plan-minimax.md).

The controllers that still carry no behaviour in Print Designer: Thai Sales
VAT, VAT Type, Thai VAT Recognition Item and Thai WHT Rate Setting. They are
plain `Document` subclasses, and the compatibility shims of Thai Business Suite
re-export the exact classes of Print Designer. They are tracked in
`print_designer-114`.

`Thai Tax Settings`, the tax calculator and `Thai Tax Invoice Intake` carry
their behaviour in Print Designer since 2026-11-22; see
[the settings](wiki/thai-tax-settings-port-minimax.md),
[the calculator](wiki/thai-tax-calculator-port-minimax.md) and
[the intake](wiki/tax-invoice-intake-relocation-minimax.md).


## The Thai VAT Recognition controller is ported to Print Designer

Done on 2026-11-22, the second of the relocated VAT controllers with its
behaviour in Print Designer. The recognition recognizes the output VAT of a
sale on the day the tax becomes due under the Thai law: on the delivery for
the goods, on the payment for the services.

- `print_designer/print_designer/doctype/thai_vat_recognition/thai_vat_recognition.py`
  is the live controller. The metadata was reconciled with the behaviour:
  the document is submittable (`is_submittable: 1`), because the recognition
  of the payment posts a journal entry and the cancellation of the
  recognition reverses it.
- `print_designer/tests/test_thai_vat_recognition.py` holds the sixteen tests
  of the controller. They create a real invoice, a real payment entry, a
  real delivery note and a real submitted journal entry.
- `print_designer/patches/relocate_thai_vat_doctypes.py` reasserts the
  ownership of the five Thai VAT DocTypes on the sites that carried them.
- The old path of Thai Business Suite is a behaviour-free shim that
  re-exports the controller and the endpoints from Print Designer.

**The party of the VAT rows is the inherited defect of Thai Business Suite**

The old controller put `party_type: "Customer"` and `party: self.customer` on
both rows of the journal entry of the recognition. ERPNext accepts a party
only on a receivable, a payable or an equity account
(`erpnext/accounts/party.py`), so the journal entry could not be written at
all, and a party on a VAT account would open an outstanding amount for the
customer. The port keeps the rows free of a party and waives the
requirement of ERPNext (`party_not_required`) only when a site models a VAT
account as a receivable or as a payable. Tracked as `print_designer-dbb`.

**Rules of the controller**

- The accounts stay configuration driven. The controller reads the accounts
  of the company from the fields of Print Designer, then from the fields of
  Thai Business Suite on the sites that carry them, and falls back to the
  name of the account. A field that the site does not carry is never
  queried. The controller never creates an account and never rewrites the
  accounting configuration of a company.
- The dates of the recognition are dates and not the text of a date
  (`normalize_dates()`), so that the recognition and the invoice carry the
  same date in the same shape.
- The link to the journal entry and the status are written with `db_set()`,
  not with an assignment in `on_submit`: the document has already been
  written when the post save methods run, and a recognition that is read
  again has to find the entry that it reverses.
- The cancellation of the recognition cancels the journal entry, and the
  journal entry writes the reversal of its own rows in the ledger.

On `demo.bunchee.online`: 16 tests of the ported controller and the whole app
with 564 tests, 0 failures, 0 errors, 4 skipped. The disposable VAT accounts
of the tests live inside a savepoint, so the site keeps no account, no entry
of the ledger and no trace of the tests. Detail in
[the relocation plan](wiki/vat-relocation-and-sales-vat-plan-minimax.md).


## E-Signatures / SignuDoc handoff

See [repository analysis](wiki/signudoc-repository-analysis.md) and
[Minimax implementation plan](wiki/e-signatures-signudoc-minimax.md). The user
created five blank DocTypes in Print Designer on 2026-11-22: E Signature
Profile, Request and Event are normal DocTypes; E Signature Recipient and
Field are child tables. None is Single or Submittable. Extend the existing
generated files; signing integration is still planned, not implemented.

Prefer an optional server-side SignuDoc service adapter, subject to a Thai PDF
and service capability spike. Keep this independent of TBS and preserve existing
image signature/stamp printing. An image is not recipient consent or PDF
cryptographic verification. Freeze the actual PDF before field placement, use
verified durable webhooks plus reconciliation, and retain exact completed PDF
bytes: rerendering, watermarking or merging after sealing can invalidate it.
Do not send production invitations or submit accounting documents for this work.


### ASEAN e-signature rollout

Print Designer targets all 11 ASEAN countries. User-specified country phases:
1. Thailand and Laos; 2. Vietnam and Myanmar; 3. Brunei, Cambodia, Indonesia,
Malaysia, Philippines, Singapore and Timor-Leste. These are country rollout
phases, separate from engineering chunks ES-01–ES-05 in the
[Minimax plan](wiki/e-signatures-signudoc-minimax.md#asean-product-scope-and-country-rollout).
Build one country-configurable engine during Phase 1. Separate country/jurisdiction,
recipient locale, timezone and currency; snapshot consent/policy versions. Verify
provider UI/email/certificate localization and actual Thai/Lao/Myanmar/Khmer
shaping and Vietnamese diacritics. Enable each country only after its own staging
tests and current country-policy review; successful English signing or Thai
configuration does not establish regional legal or language support. No additional
blank DocTypes are required for this planning addition.


## Sales Invoice — Thai withholding versus ERPNext tax collection

For the Thai customer-withholding workflow, use Print Designer's **Thai Tax
Compliance → Subject to Withholding Tax** (`pd_custom_subject_to_wht`). When
Thai WHT applies, the customer deducts it from the cash payment. The invoice
receivable is settled through the bank receipt plus withholding tax receivable
in **Payment Entry → Receive**. The WHT amount depends on the applicable income
type and rate. The ฿300 below is an example at 3%.

| Amount | Print Designer Thai WHT | ERPNext `apply_tds` on Sales Invoice |
| --- | ---: | ---: |
| Base amount | ฿10,000 | ฿10,000 |
| VAT amount | +฿700 | +฿700 |
| Tax at source | −฿300 withheld from cash | +฿300 collected from the customer |
| Invoice total / receivable | ฿10,700 | ฿11,000 |
| Net cash paid by the customer | ฿10,400 | ฿11,000 |

On a Sales Invoice, ERPNext's standard `apply_tds` runs the customer-side tax
collection (TCS) engine. When its category and thresholds produce an amount,
ERPNext adds that amount to the invoice. Leave `apply_tds` unchecked for the
Thai customer-withholding workflow unless a separate standard collection rule
is intentionally required. Keep VAT Due / VAT Undue under **VAT Treatment**.

The SI field **Net Total After WHT** shows the amount before VAT less WHT
(฿9,700 in the example). Use the Payment Entry to verify the actual bank
receipt (฿10,400). The Thai calculator is owned by Print Designer.
