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

Intake is an optional supplier-document capture/verification workflow that
creates a draft Purchase Invoice; it must not submit it or independently post
VAT. The Sales Tax Invoice option is not supported by existing synchronization.
After PD-only/both-app migration, permissions, rollback/concurrency and real UI
tests pass, delete the old TBS Intake source and obsolete references/tests.
Keep live DocType/table/records, attachment File links and Purchase Invoices.
Prevent old TBS migrate/uninstall from reclaiming/removing PD-owned data. No
Intake workflow changes or financial/document writes were made by this handoff.

## Thailand Tax master plan and SI Services first chunks

See [master plan](wiki/thailand-tax-master-plan.md),
[SI-01 data contract](wiki/si-services-tax-data-contract-minimax.md),
[SI-02 service tracking](wiki/si-services-output-vat-undue-minimax.md), and
[SI-03 Preview reports](wiki/si-vat-preview-reports-minimax.md).

**User instruction: keep SI fields/layout as-is**, including values shown in
Details and Thai Tax Compliance. Reuse stored fields in background; do not move
or duplicate WHT/VAT/retention controls. The requested SI UI additions are only
Preview → VAT Due Report and VAT Undue Report below Accounting Ledger.

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
