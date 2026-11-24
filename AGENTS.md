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

Regression investigated on 2026-11-19 in a saved quotation on
`[site]` (tracking issue: `print_designer-wsg`).
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
PRINT_DESIGNER_E2E_SITE_URL=https://[site] \
python -m pytest print_designer/tests/test_table_column_editing.py \
  print_designer/tests/test_properties_panel_label_neutralized.py -q
bench build --app print_designer
bench --site [site] clear-cache
```

Build and clear the target-site cache before running browser verification
against changed frontend assets. The regression test changes only the browser's
unsaved design state.

## Whole-table border edits and Table grid presets

Investigated on the AWS Receipt designer (issue `print_designer-ejr`).
Selecting the table set Style Mode to **All Rows**, but the previous color
picker and Solid/Dotted/Dashed buttons edited only the table defaults.
`BaseTableTd.vue` renders column styles last. Receipt had table color
`#4F9DD9` and five columns overriding it with `#B4CD29`. Changing the line
pattern used the same write scope. The old Solid indicator also assumed
`solid` whenever the selected object omitted its own line pattern.
The designer's outer-cell CSS forced solid edges with `!important`, so those
edges could disagree with the active pattern or preset. Keep the solid edges
as a CSS fallback that yields to inline table styling.

- Use `tableBorders.js` for whole-table color and line-pattern edits. All Rows
  updates the body defaults and matching alternate-row, column, and edge
  overrides. Table Header updates the header independently. Keep legacy
  Apply Style to Header behavior for explicit column edits and preserve the
  prior linked header values during a bulk body edit using
  `column.linkedHeaderBorderStyle`. Apply that snapshot only while the link is
  enabled, and clear it on an explicit Yes/No change. Explicit header edits in
  `column.headerBorderStyle` apply independently. Preserve widths, alignment,
  and hidden edges.
- An empty column `backgroundColor` inherits the table header fill when
  Apply Style to Header is enabled. Receipt had a saved fill of `#cdcbf2`
  and empty column colors. Vue dropped the empty inline value and fell back
  to white. Jinja converted the empty value to transparent. Skip the empty
  column background for linked header styles in both renderers so they use
  the same fill. A non-empty column color still overrides the header fill
  when linked. To edit the shared fill, select the whole table and use
  **Style Mode → Table Header**, then **Font Settings → Background**.
- Treat selected columns and dynamic text as editor state. Clear these on
  load and in the serialized layout, and let a click on an empty body cell
  return to the whole table. Receipt previously reopened with an old column
  selection from its saved JSON. Initialize the canvas marquee on canvas
  mousedown. An eager marquee element caused the first table mouseup to clear
  the selection even though the table had handled mousedown.
- The combined Border Color control shows the effective shared value for the
  current scope, or an empty value for mixed colors. This lets users reapply a
  table default that already exists in storage. The Solid/Dotted/Dashed
  indicator reflects a common visible pattern.
- The old preset buttons ignored the inner-border flags, so Outline Only
  could leave a grid. The table-only **Table grid** buttons store
  `borderPreset` on the table. **No Grid** hides all edges. **Full Grid**
  shows the outline, column dividers and populated-row separators.
  **Outline Only** shows the outside perimeter. **Horizontal** shows the
  top and bottom edges and populated-row separators. Padding skips interior
  horizontal separators and keeps the final edge when the preset calls for it.
  **Custom** restores the manual edge layout without altering color or pattern.
- Keep the Vue geometry in `tableBorders.js` and the print geometry in
  `jinja/macros/table_border_presets.html` in sync. Both print schema versions
  include the same preset mask. The shared Desk/browser border script replays
  those borders and leaves a preset table's padding edges under its control.
  Tables without a saved preset use their manual edges.
- Receipt's Horizontal header regression (`print_designer-4vq`) came from
  Vue keeping saved side-style keys ahead of a later `borderStyle`
  shorthand when merging style objects. For named presets, merge the saved
  styles first and append the four preset edge styles at the end. Verify
  both sides of each header cell in the browser with the shorthand saved
  after the side keys.

Use `print_designer/tests/test_receipt_border_presets.py` to verify real
designer actions without saving edits. `test_desk_preview_table_borders.py`
covers the current and legacy print renderers, with and without presets.

## Receipt designer save, footer, and preview language regression

Verified on the receipt designer of a live site (issue `print_designer-x1g`).
The layout save, the thumbnail capture, and the language refresh each had a
separate role in the reported behavior.

- **Slow Save.** After the layout save response, `ElementStore.generatePreview()`
  used html2canvas to clone the full Desk DOM. Scope the clone to the first
  print page, its ancestors, and styles. Keep automatic thumbnail work in the
  background and hold its in-progress flag through capture, upload, and
  linking. In the authenticated browser comparison, capture dropped from about
  7.8 seconds to 0.3 seconds. The test intercepted network writes, so these are
  browser capture timings.
- **Save Footer crash.** The thumbnail uploader assigned `null` to the
  undeclared `MainStore.print_designer_preview_img` property. When Page Settings
  remounted, Pinia's `storeToRefs(MainStore)` scanned that value and threw
  `Cannot read properties of null (reading 'effect')`. The uploader now returns
  the file URL without assigning temporary state to the store. In
  `PropertiesPanelState.js`, use `toRef(MainStore, fieldName)` for the individual
  reactive inputs these controls need. Save Footer persists the restored
  layout, and Close returns to the canvas without saving.
- **Language toggle discarded unsaved edits.** The toggle previously reran
  `fetchMeta()`, which loaded the saved layout again and registered another
  preview-document watcher. `App.vue` now uses
  `fetchMeta({ loadLayout: false })` to refresh translated metadata and preview
  values in the open design. Load the layout on initial open and register the
  preview-document watcher once.

Keep the `[Print Designer Save]` timings for layout preparation, the save
request, thumbnail capture, and upload/linking until the user explicitly asks
to remove them. Use
`print_designer/tests/test_receipt_designer_save.py` for authenticated
Playwright verification after building the app and clearing the target site
cache. The test intercepts layout and thumbnail writes, checks Save Footer for
Vue errors, and verifies that unsaved width and height edits survive switching
among Thai, English, and System Default.

## Saved table column headings and language preview

Receipt's Payment References dialog can rename the Allocated Amount column
from `จัดสรร` to `รับชำระ` (issue `print_designer-rba`). The previous
metadata refresh replaced every linked column's saved `label` with the
translated field label. Keep that refresh read-only for saved captions.
Display translated metadata for default headings. A typed heading receives
`labelIsCustom` on Confirm and prints literally in both template versions.
The main Save action persists the caption and flag. The Receipt designer
browser test covers the dialog, language changes, Save payload, and reload.

The shared default table-column captions are `Order` / `ลำดับที่`, `Receive` / `รับชำระ`,
`Document Type` / `ประเภทเอกสาร`, and
`Document Number` / `เลขที่เอกสาร` (issue `print_designer-xrj`).
`utils/print_labels.py` maps exact old captions for the designer and both
print templates. This affects default headings across Print Designer tables.
Keep custom headings literal and preserve the underlying DocType field names.

## Footer text and signature line alignment

On Receipt (issue `print_designer-3r1`), a generated footer flex row held
the receipt label and a signature rectangle as direct siblings. Both X
coordinates were saved relative to the same row. The renderer added the
label's rendered width to the rectangle's left margin, moving the line
63 px right and shrinking it. In `relative_containers.html`, give direct
items in these footer rows a shared horizontal origin while preserving
their height in the row. Keep generated columns in their normal flow.
The shared footer renderer preserves the saved offsets without editing
the Print Format. Regression coverage is in
`print_designer/tests/test_printview_footer_and_table_height.py`.

## Desk preview watermark and page number routing

Investigated on 2026-11-20 with a saved quotation (issue
`print_designer-5du`). PDF Forms is installed after Print Designer on a live
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
source-site logo assets or sample document selection. It is site neutral: the
identity of the page is resolved at print time. The company name, the address,
the tax id, the phone number and the e-mail address come from the Company of
the printed Quotation. The address comes from the printed Quotation itself
(`doc.get("company_address_display")`) and is shown as text. The bank details
come from the Bank Account that carries the Account that the Company selects
as its default bank account. The contact is shown with its full name. A site
that installs the package therefore prints the identity of its own data and
has no text to replace. The category name is not an installed-app dependency.
The importer is implemented
(`print_designer/default_templates_installer.py`) and runs from `after_install`;
it only fills in formats that are missing and never overwrites an existing
one. The dry run and the backfill of the sites that already run the app go
through the admin API
(`print_designer/api/default_templates_api.py::run_default_template_installation`),
which is a separate step that needs its own authorization - see the tracked
issue. Regression tests:
`print_designer/tests/test_default_templates_installer.py` and
`print_designer/tests/test_services_quotation_template.py`.

## Phase 2: export as default template, transaction profiles

See [Phase 2 notes](wiki/default-template-export-phase-2-minimax.md). The
Desk action **Export as Default Template** (alongside, not replacing,
**Export Format**) exports a saved Print Designer format as an
installer-ready JSON file. It is download only: it never writes into the app
folder and never writes into a site, because a site that may write into an
app folder turns a content decision into a remote code path.

- Export: `print_designer/api/default_template_export.py`
  (`build_template_document`, `get_categories`, `export_as_default_template`).
  Both endpoints of the client are `@frappe.whitelist()`: an endpoint that
  is not whitelisted is refused by the request handler before the function
  starts, so the call of the Desk never reaches the code. A test checks
  that they stay whitelisted.
- Profile: `print_designer/custom/print_format_profile.py` with the Print
  Format fields `pd_custom_transaction_direction` (`Pay`, `Receive`) and
  `pd_custom_transaction_type` (`Services`, `Goods`). A Sales Invoice has no
  direction; a Payment Entry has an optional direction and type; every other
  doctype has no profile. The profile is advisory: it never changes a posting
  or a tax.
- Suggestions: `print_designer/api/print_format_suggestion.py` and the
  advisory preselection in `print_designer/public/js/print.js`. A format
  without a profile stays general purpose and is never suggested; the
  selection of the user is never overwritten. The client tracks the choice
  of the user (`PDProfileSuggestionState`), refuses to overwrite a choice
  that was made while the request was in flight, and bounds its retries
  with `patchMaxRetries`.
  The behaviour of the client is covered by
  `print_designer/tests/test_print_view_profile_suggestion.cjs`, which
  runs the real client script in a sandbox and runs with the suite
  through `print_designer/tests/test_print_view_profile_suggestion.py`.
- The profile fields are installed **before** the savepoint of the import
  loop: a schema change commits the transaction of MySQL implicitly and
  destroys the savepoint of the installer.
- The profile is **validated against the doctype of the format** in
  `build_template_document()`, the single point where a profile enters a
  template: a Sales Invoice format has no direction, and a format of any
  other doctype has no profile. The Desk hides the fields of the
  unsupported doctypes, but the hidden field is only a convenience, the
  server refuses the value. `validate_profile()` carries the rules.
- Both profile fields carry a **blank first option** (`"\nPay\nReceive"`,
  `"\nServices\nGoods"`). Frappe fills the value of a new `Select` with
  its **first option** (`frappe/model/create_new.py`), so a field that
  started with `Pay` would silently give **every** new format a profile,
  and a general purpose template would be suggested as if it were
  transaction specific. Never remove the blank option.

Two column rules decide what a template may hold, and both are enforced by
the installer:

- Every design field of the `Print Format` doctype is a JSON custom field
  whose column carries `CHECK (json_valid(...))`. An empty string is not
  valid JSON, so the export writes `null` and never `""` for an absent
  design. A template that carries `""` fails the insert with
  `OperationalError: (4025, 'CONSTRAINT tabPrint Format.<field> failed')`.
- A field that is not a child table holds a scalar or a string. The
  installer normalises a list or an object into its JSON string, the way
  Frappe stores `format_data` of the print format builder. This is the
  safety net for the templates of **other** sources: a template that an
  older version of the app exported, or a template of another app.
- The packages of this app carry the shape that Frappe stores themselves.
  The shipped `payment_entry_thai_tax_invoice.json` used to carry its
  `format_data` as a JSON list, so the file could not be inserted at all
  and only survived because the installer rewrote the value first. It
  carries the JSON string now. Regression test:
  `print_designer/tests/test_thai_tax_invoice_template.py`.

The first package of Phase 2 is the `ASEAN Receipt`
(`default_templates/asean_business_suite/receipt.json` with its
`.assets.yaml`): a Payment Entry layout with the labels of ERPNext, the
dynamic `Company.company_logo` branding, the profile `Receive` / `Services`
and the amount in words of a receipt (`received_amount` in the currency of
the account that receives the money). It was built with the export pipeline,
so it has the shape that the export produces. The payload of the package is
the **designer blobs of the package itself**: row containers with their
geometry, the page variants, the text leaves and the image binding. A
package that carries only the `header`, `body` and `footer` blobs renders
an **empty page**, because the renderer needs the container envelope.
Regression tests:
`print_designer/tests/test_asean_receipt_template.py` and the round trip in
`print_designer/tests/test_default_template_export.py`.

The plan asks for a **review before an export is accepted for a release**:
the remaining static text, the Jinja, the assets, the DocType fields and
the renderer dependencies. The outcome is recorded in the companion
manifest of the package, in its `review_before_release` section, so the
review is auditable. For the `ASEAN Receipt` the package ships no static
asset (its only image is the dynamic company logo), so no privacy
preserving asset creation or rollback is needed, and the design carries
no Jinja at all: every value is a field binding of the designer.

A transaction is classified through the **real path of the workflow**: a
Sales Invoice through its own item rows, a receipt (`Receive`) through the
Sales Invoices of its `references`, a supplier payment (`Pay`) through the
Purchase Invoices of its `references`. The type is only suggested when the
linked invoices agree, so a receipt that pays a service invoice and a
goods invoice at once stays unclassified and the manual selection stays
available. **A Payment Entry has no `items` table**, so a receipt is never
classified from its own rows. A linked invoice is only read when the user
may read it (`frappe.has_permission(doctype, "read", invoice)`), so a
restricted invoice is never classified through a side channel.

The Desk actions of a saved Print Designer format are the three actions of
the menu of the form: the backup **Export Format**, the existing
**Import Format** and the new **Export as Default Template**. Each of them
is registered exactly once, and a format that is not a Print Designer
format carries none of them. The export asks for the public format name,
the filename and the destination category, and the default filename is a
slug of the name of the format. Executable proof:
`print_designer/tests/test_print_format_default_template_action.cjs` (run
with `node`). It runs with the suite as well, so a client script that the
browser refuses does not stay unnoticed. The check that also runs with the
suite reads the registered client code: `print_designer/tests/test_print_format_default_template_action.py`.

The installer is hardened against a hostile template file, because a
template is data that a site downloads:

- The walk that collects the referenced fields is bounded by
  `MAX_DESIGN_DEPTH`, so a deeply nested payload cannot exhaust the stack
  of the installer.
- A template whose analysis throws is reported under `failed` and skipped.
  One malformed template never aborts the whole installation.

The dialog of the export uses the real Frappe API
(`dialog.disable_primary_action()`, `dialog.enable_primary_action()`).
A failed export leaves the dialog open and restores the primary action, so
the user can try again.

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
SITE_URL="https://[site]"
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
runs. On `[site]` HRMS is installed without its payroll module,
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

Verified in a real browser on `[site]`
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
- The two client scripts belong to the suite of the app and not only to a
  proof that has to be repeated by hand:
  `print_designer/tests/test_thai_tax_client_workflows.py` runs them with
  `node` and fails when one of them fails.

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
  `[site]`, which installs `your_app` as the peer of
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

The ledger was migrated and verified on `[site]`: `autoname` is
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

`[site]` still carries the legacy schema, the legacy
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
failures, 0 errors, 0 skipped on `[site]`) and
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

## The VAT of a Payment Entry and the mandatory tax invoice fields

Fixed on 2026-11-24 (tracked as `print_designer-622`). The taxes of a
Payment Entry are the rows of **Advance Taxes and Charges**, and that
doctype carries the amount of the tax in `tax_amount`. It has **no**
`amount` field.

Two functions read the amount of a tax row, and both read `amount`, so both
always read zero:

- `_validate_mandatory_tax_invoice_fields()` in
  `print_designer/custom/payment_entry_server_events.py`: `has_vat` stayed
  `False`, so the function returned before it checked anything. The
  mandatory Thai tax invoice number (`pd_custom_tax_invoice_number`) and
  the mandatory Thai tax invoice date (`pd_custom_tax_invoice_date`) were
  never enforced on a payment that carries a VAT.
- `_auto_fill_tax_base_amount()` of the same module: the fallback that
  derives the tax base from the allocated amount of the payment never ran.

Both read `tax_amount` now. The receipt of a customer is **not** refused:
`validate()` returns for a `payment_type` of `Receive` before it reaches
the check, and the mandatory fields are the fields of the tax invoice of a
**purchase**.

Never read `amount` on a tax row of a Payment Entry. Read `tax_amount`.
The details are in
`wiki/payment-entry-vat-tax-invoice-validation-minimax.md`.
Tests: `print_designer/tests/test_payment_entry_tax_invoice_validation.py`
(9 tests). Without the fix the suite reports 1 failure and 1 error.

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
  only. The ownership was applied to `[site]` and the settings
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
`[site]` still runs 540 tests with 0 failures and 0 errors.

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

## Type safety of the canonical WHT controllers

Done on 2026-11-23 for the three canonical WHT files: the certificate
controller, the receive register controller and the retirement patch of the
legacy link. The 121 BasedPyRight diagnostics of those files are zero, the
full app on `[site]` still runs 717 tests with 0 failures and 0
errors.

The shared helper is `print_designer/custom/document_fields.py`:

- `field_value(doc, fieldname)` returns the raw value of a dynamic field.
- `field_text(doc, fieldname)` returns a string, an empty string for `None`.

Use them instead of repeating `cast("Any", doc.get(fieldname))` at every call
site. The rules for this area:

- A dynamic field of a document is read with `doc.get("field")` and written
  with `doc.set("field", value)`. Frappe does not declare the fields of a
  DocType on the class, `Document` has no `__getattr__`, and the type checker
  therefore rejects the attribute access even though the value exists at
  runtime.
- `Meta.get_field(fieldname)` returns `None` for an unknown field. Narrow the
  result before `field.fieldtype`, `field.fieldname` or `field.options`.
- `frappe.db.get_value(..., as_dict=True)` and `frappe.get_all()` are
  dynamically typed. Cast or check the result before a dynamic key is read.
- `frappe.msgprint` accepts `blue`, `green`, `orange`, `red` and `yellow`.
  The client maps `orange` and `yellow` to the warning alert, so there is no
  `warning` indicator.
- Do not add a whole file BasedPyRight suppression for these files.
- Format only the files that were edited. The repository mixes tabs and spaces
  per file.

The PND item path of the certificate controller is not wired to a hook, so it
was proven with an A/B probe against HEAD instead of an assumption: the
`PND53Form.before_save()` rebuilds `items` from the submitted and issued
certificates of the period, so a manually inserted item is replaced by the
form on save. That is pre-existing behaviour. Detail in
[the cleanup notes](wiki/type-debt-cleanup-wht-retention-minimax.md).

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

On `[site]`: 8 tests of the ported controller, 3 tests of the
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

On `[site]`: 16 tests of the ported controller and the whole app
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


## Issued and received 50 Tawi certificate ownership

The agreed issued WHT record is Print Designer's **Withholding Tax
Certificate**. Use it for 50 Tawi the company issues on supplier payments.
**Receive WHT Register** is the separate Print Designer DocType for
certificates received from customers. An Issued WHT Register report should
read the issued certificate records. The existing **WHT Certificate Register**
report queries legacy Payment Entry columns absent on AWS and needs updating
before it can serve as that register.

- Both certificate parents currently have an `income_items` table using
  **Withholding Tax Item**. Keep the existing child DocType and table name.
  The user moved its live AWS module to **Print Designer**. Verification
  confirmed the ownership change, zero rows on AWS, and an effective
  `income_type` field that is still a mandatory **Select**.
- The canonical Print Designer child definition uses a mandatory **Link**
  to **Thai WHT Income Type**. Switch the live field to that contract and
  map legacy Select values to valid master record IDs wherever data exists.
  Check each site's rows and callers. Both apps still ship a definition
  for this child, so coordinate source retirement to prevent future app
  syncs from restoring the old module or Select schema.
- The current TBS Payment Entry submit hook can still create **Withholding
  Tax Cert**. The legacy calculator writes Select-style labels into
  `income_items.income_type`. The Print Designer generator currently fills
  header amounts. Update the Pay issuance and cancellation flow to use the
  Print Designer certificate and populate one child row per WHT line with
  a valid income type ID. Verify one certificate per qualifying payment,
  multiple income rows, totals, cancellation, print output and PND
  reporting. Retire the old **Withholding Tax Cert** and TBS's duplicate
  child definition only after checking historical records and repointing
  callers. Preserve any existing certificate numbers and source links.
- **Thai Withholding Tax Detail** is a legacy Form 50 Tawi child intended
  for details stored directly on Payment Entry. It is separate from
  **Withholding Tax Item**. AWS has zero rows and no Payment Entry field
  referencing it. A self-reference remains in its definition. Audit other
  sites and the legacy Form 50 Tawi installer before retiring it.

The Payment Entry field installer review found 21 active preview field
definitions in `install_payment_entry_fields.py` and 26 active compliance
definitions in `install_payment_entry_thai_fields.py`, with no overlapping
fieldnames. `install_payment_entry_thai_wht_fields.py` is a draft stub.
If consolidating the installers, preserve active fieldnames and stored values
until consumers of similar fields have been reviewed.

## Canonical withholding tax certificate mapping

`print_designer/custom/wht_canonical_mapping.py` decides the line of the
certificate, the line of a row, the form of the tax and the classification.
`print_designer/custom/wht_certificate_creator.py` creates the certificate
from that decision. Both are Print Designer owned.

- The catalogue of **Thai WHT Income Type** is the source of truth. A
  transaction reaches it through
  `Tax Withholding Category.pd_custom_thai_wht_income_type`.
- **The classification names the form of the tax.** `Individual - Staff
  (PND.1)`, `Individual - Non-staff (PND.3)` and `Company/Juristic Person
  (PND.53)` always agree with `PND1 Form`, `PND3 Form` and `PND53 Form`. A
  certificate whose classification and form disagree lands in the wrong PND
  return.
- The kind of the payee decides the form of the legacy fallback: a juristic
  person is reported on PND53, an individual on PND1 or PND3. A service paid to
  a juristic person uses the line of a service of a company
  (`5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service`), the same service paid to
  an individual uses the line of an individual.
- The line of the certificate and the line of a row are strict `Select` values
  of the canonical DocType. The strings must match the runtime options
  exactly, including the Thai spelling.
  `print_designer/tests/test_wht_canonical_mapping.py` asserts every mapped
  line against the metadata of the certificate.
- `print_designer/tests/test_wht_certificate_creator.py` asserts the creation
  itself: one submitted certificate per payment entry, the reuse of that
  certificate by a second call, the amounts of the certificate and of its
  rows, the agreement of the classification and the form of the tax, the
  validity of every line, and the refusal of a payment entry that is not an
  outgoing payment to a supplier.
- **One mapping decides the certificate.** `wht_certificate_generator.py`
  reads the same mapping as the creator: its fallback carries only the
  description of the items of the purchase invoice and the rate of the
  payment entry, never the line of the certificate, the line of its rows,
  the form of the tax or the classification. A fallback fills the gaps of
  the canonical mapping and never replaces a value of that mapping with
  nothing. The preview of the generator shows the values that the creation
  makes.
  `print_designer/tests/test_wht_certificate_generator.py` asserts this.
- **The certificate names the payment that pays it.** `payment_entry` is a
  mandatory field of the `Withholding Tax Certificate`, so a cash purchase,
  which carries no payment entry, cannot have a certificate. The path that
  created a certificate from the purchase invoice could therefore never
  insert one and made the submit of the purchase invoice fail with
  `Failed to create WHT Certificate`. That path is retired; a cash purchase
  that is paid through a payment entry receives its certificate from that
  payment entry.
  `print_designer/tests/test_cash_purchase_wht_certificate_path.py` guards
  this: the retired path is not registered, and a cash purchase of a service
  with the tax of Thailand submits and creates no certificate.
- **The endpoints of the certificate ask for the right.** The creation of a
  certificate from a payment entry and the manual creation are a POST, and
  the caller must be allowed to read the payment entry and to create the
  certificate. The preview asks for the right to read the payment entry,
  because it shows the data of the payment entry and of its purchase
  invoice. The refusal is made before the payment entry is loaded, so that
  a caller without the right learns nothing about the document, and it is
  raised out of the endpoint instead of being reported as a failure of the
  work. `print_designer/tests/test_wht_certificate_endpoints.py` guards
  this.
- **The payment entry names its certificate.** The creator of the
  certificate keeps the link of the payment entry and its certificate, so
  that every path of the creation leaves the payment entry linked: the path
  of the calculator and the path of the payment entry of a purchase invoice
  alike. The link is kept again when the certificate exists already. A site
  without the field of the link has no link to keep, and the certificate is
  then the only record of the withholding.
  `print_designer/tests/test_wht_certificate_creator.py` guards this.
- **The cancellation of the certificate clears the links and leaves the
  status.** The controller removes the item of the form of the tax, clears
  the link of the payment entry in both directions and leaves the status of
  the certificate as it was written at its creation. The status drifts: the
  field carries `Draft`, `Issued`, `Submitted to Revenue Dept` and
  `Cancelled`, and the controller moves it neither on a submit nor on a
  cancel. Which of them the field shall carry is a decision of the product
  and is tracked on its own.
  `print_designer/tests/test_wht_certificate_cancellation.py` holds the
  behaviour of today.
  The cancellation of the certificate takes part in the transaction of the
  caller and commits nothing of its own. A commit inside `on_cancel()` ended
  the transaction of the caller: it persisted the half finished work of the
  caller and it destroyed the savepoints of the caller. Frappe owns the
  transaction boundary of the request, of the background job and of the
  command line, so the controller of a document must not commit. The removal
  of that commit is tracked in Beads (`print_designer-64n`), where it is closed.
  A test of the cancellation leans on a savepoint therefore: the savepoint of
  the test is rolled back at the end, and the test keeps the removal of the
  rows one by one as a fallback for the case where the savepoint is gone.

## The canonical reader of the report data of the withholding tax

`print_designer/custom/wht_report_data.py` owns the reading of the canonical
documents of the withholding tax of Thailand. The reports and the tasks of
the Thai Business Suite read the data of the withholding tax through it, so
the knowledge of the schema lives in one place and no report of the suite
names a table or a column of the certificate any more.

- `get_certificates(...)` reads the **Withholding Tax Certificate** with the
  filters of the company, of the date of the certificate, of the date of the
  payment, of the form of the tax, of the state, of the supplier and of the
  tax identification number.
- `get_income_items(...)` reads the **Withholding Tax Item**, the incomes of
  the certificates.
- `get_certificate_lines(...)` returns **one row for every income** of every
  certificate. A certificate without an income is still reported: the row
  carries the totals of the certificate and the income type of the
  certificate itself.
- `get_receive_registers(...)` reads the **Receive WHT Register**, the
  counterpart of the certificate for the withholding tax that is received.
  The withholding tax that is paid and the withholding tax that is received
  stay apart.
- `get_invalid_certificates()` returns the submitted certificates whose tax
  is not the tax of their base amount at their own rate.
- `get_pnd_form_type_names(...)` and `get_pnd_type_of_form(...)` map the form
  of the withholding tax between the name of the report (`PND53`) and the name
  of the certificate (`PND53 Form`).
- `get_income_code(...)` reads the code of the income of Thailand at the
  beginning of the type of an income, `find_income_code(...)` finds it
  anywhere in the description of the income of a certificate, e.g.
  `1. เงินเดือน ค่าจ้าง ฯลฯ 40(1) - Salary` carries `40(1)`.
- The reader asks for the right to read the certificate and of the register
  before it reads them.

`print_designer/tests/test_wht_report_data.py` guards the reader.

### The suite reads the canonical documents

The reports, the tasks and the validators of the Thai Business Suite name no
table of the certificate that was deleted:

- `thai_tax/report/company_tax_report/company_tax_report.py` reports one row
  for every income of the certificate.
- `thai_tax/report/tax_withholding_summary/tax_withholding_summary.py`
  reports the outgoing certificates and the incoming registers.
- `thai_tax/report/thai_wht_attachment/thai_wht_attachment.py` reports the
  certificates with their attachments. The four names that face the
  attachment belong together and name the canonical certificate: the link of
  the column of the report, the `ref_doctype` of the report, the
  `attached_to_doctype` of the file that the client uploads and the route of
  the link of the client. A name that stays on the deleted certificate
  silently breaks the upload, because the file hangs on a document that does
  not exist, and the route breaks the link the same way. The client builds
  the route out of the name of the certificate and never out of a written
  slug.
  `thai_business_suite/tests/test_wht_reports_canonical.py` holds the four
  names together.
- `thai_tax/report/pnd_reports/pnd_reports.py`, `thai_tax/tasks.py`,
  `thai_tax/utils/base_report.py` and `thai_tax/utils/validators.py` read the
  canonical columns.
- The print format `New WHT Cert` prints the canonical certificate; it reads
  the address of the supplier from the link `supplier` and from the field
  `supplier_address` of the certificate.
- The client of the payment entry, the page of the accounting of the suite
  and the link of the workspace name the canonical certificate.

The one place that still names the deleted certificate is the manager of the
workspace of a client site: the shortcut belongs to the workspace of `your_app`,
whose records of the withholding tax are not moved.

## The ownership of the DocTypes of the tax is put back safely

Several DocTypes of the tax of Thailand live in more than one app: the
canonical DocTypes of Print Designer, the copies of the Thai Business Suite
and the copies of a fork of a client. The model synchronisation imports the
metadata of every app, and the owner of a DocType is the app whose metadata
was imported last.

`print_designer/custom/doctype_ownership.py` owns the rule:

- a DocType of the modules of the Thai Business Suite (`Thai Tax`,
  `Thai Business Suite`) is taken back to Print Designer,
- a DocType of a fork of a client is **never** taken. The
  fork carries the records of the withholding tax of that client, and a
  DocType that is taken from such an owner changes the metadata of those
  records with it,
- a DocType of an unknown owner is kept, with a message in the log of the
  migration.

`print_designer/patches/relocate_thai_tax_doctypes.py` follows that rule and
covers the canonical `Withholding Tax Certificate` and `Withholding Tax
Item` next to the three DocTypes of the tax. The patch
`print_designer/patches/guard_thai_tax_doctype_ownership.py` applies the same
rule to every DocType of the tax, of the VAT and of the withholding tax, so
that the sites that already ran the first patches are guarded as well.

`print_designer/tests/test_tax_doctype_ownership_guard.py` guards the rule.
On the demo site the guard is a no-op: every DocType is already owned by
Print Designer and no metadata is imported. On
`[site]` the `Withholding Tax Item` is owned by
the fork of a client and is kept; its schema is the same as the canonical one, so
the certificate of Print Designer reads its incomes unchanged.

## The rules of the income type of the certificate

The certificate of the withholding tax carries one income type of its own and
one income type for every row of its incomes. The rules that decide them
live in `print_designer/custom/wht_certificate_creator.py` and are held by
`print_designer/tests/test_wht_certificate_income_type_rules.py`.

- **The income type of the certificate is the income type of the transaction.**
  It is read from the field `pd_custom_wht_income_type` (or
  `pd_custom_wht_income_type_details`) of the payment entry. The value is
  either the name of a `Thai WHT Income Type` or the name of a
  `Tax Withholding Category` of ERPNext, which is resolved through the link
  `pd_custom_thai_wht_income_type` of that category.
- **A transaction without a type falls back to the type of the kind of the
  payee.** A company falls back to the service, an individual to the service
  of an individual.
- **A row of the incomes keeps its own type when it carries one.** The field
  `tbs_income_type` of the row of the withholding tax wins; a row without one
  takes the type of the transaction.
- **The rate of the certificate is the rate of its first row.** A transaction
  that mixes two rates therefore shows the rate of its first row next to the
  income type of the transaction. This is the current behavior; it is
  recorded as an open question in Beads and is not changed silently.
- **A party that is not a supplier has no tax id and no address.** The tax id
  is read from the `Supplier` and the address only from a supplier, so a
  payment to another kind of party leaves both fields empty.
- **Every record of the catalogue of the site has a line.** The map of
  `CERTIFICATE_INCOME_TYPES` in `print_designer/custom/wht_canonical_mapping.py`
  covers every record of `Thai WHT Income Type` of the site; the test proves
  it for the records that are installed.

The certificate is created only for a payment entry that pays a supplier. A
payment that receives money belongs to the `Receive WHT Register`, not to the
certificate.

## The retirement of the legacy certificate of the withholding tax

The legacy `Withholding Tax Cert` is gone as a doctype. The mapping of every
one of its fields onto the canonical documents, the decision about the records
of the client, and the plan of the retirement are written down in
[the retirement plan](wiki/wht-legacy-retirement-and-field-mapping-minimax.md).

The short version: the client site carries 13 legacy rows. Eight of them are
mirrored in the canonical `Withholding Tax Certificate` and five in the
canonical `Receive WHT Register`, so nothing is lost when the legacy table
goes. Two gaps have to be closed first: the postal address of the payee is
not carried over into `supplier_address`, and the link `income_type` of the
five incoming rows is empty. The child table `Withholding Tax Item` is
shared, so the child rows of the legacy certificates have to be deleted with
their parents.

Nothing on a live site of a client is written without the word of the client.

## Thai Withholding Tax Certificate Form 50 Tawi

- The reusable form 50 ทวิ view model lives in Print Designer:
  `print_designer/custom/form_50_tawi.py`. It maps a **Withholding Tax
  Certificate** onto the statutory rows 1 to 6 (row 4 split into 4a and 4b),
  the totals, the Thai amount in words, the PND and withholding method
  checkboxes, the party identity, the tax ID boxes, the branch text and the
  signature date. A certificate without `income_items` falls back to the
  parent fields. Amounts are read from the certificate, never recalculated
  from a rate.
- It is registered as a Jinja method in `hooks.py`
  (`get_form_50_tawi_data`, `get_form_50_tawi_wrapper_class`), so a client
  print format only binds presentation values and never repeats tax mapping.
- **The two parties of the form:** the reference form 50 ทวิ asks the
  **withholder of the tax** (the payer, the company that pays) in its first
  section and the **party that is withheld from** (the supplier of the
  certificate) in its second one. The view model gives `company_tax_id`
  (from the linked Company), `company` and `company_address` for the first,
  and `supplier_tax_id`, `supplier_name` and `supplier_address` (from the
  certificate) for the second. A print format keeps the two apart; the format
  of the client site is guarded by
  `test_the_section_of_the_withholder_carries_the_company` and
  `test_the_section_of_the_withheld_carries_the_supplier` in the test of that
  client site.
- Only the print format named exactly **Form 50 Tawi** is a Form 50 format.
  Every other print format follows the Print Designer path.
- **Per format wrapper marker:** a form or report may put its own unique
  marker (class or id) on the first `<div>` of its wrapper. Format local CSS
  may then be scoped to that marker. A correction that must not reach other
  formats, the browser print output or the PDF output belongs in a screen
  only media rule inside the format's own stylesheet. Never neutralize the
  shared `.print-format` rules of Frappe core or of Print Designer.
- The scoped Desk preview rule of the Form 50 format is
  `.print-format.print-format-preview:not(.landscape):has(.dgs-form-50-tawi)`
  and it stays inside the Form 50 format CSS.
- **Page orientation of the certificate formats:** `page_orientation` is a
  Print Designer custom field on Print Format and the Desk preview takes the
  orientation of the selected format through
  `print_designer/public/js/print.js`
  (`apply_page_orientation_from_print_format()`). A certificate format
  created before that field existed carries no orientation and falls back to
  the global Print Settings, which can start the preview in Landscape. The
  patch `print_designer/patches/set_certificate_print_format_orientation.py`
  fills the empty value of every **Withholding Tax Certificate** print format
  with `Portrait`. Only empty values are filled, so an orientation chosen
  explicitly is never changed and a sidebar selection still wins.

## The assets of the templates of this app

- A template of this app is printed on a site that may not install another
  app. A font that is loaded from the assets of another app is therefore
  missing on such a site, and the Thai text falls back to a font that has no
  Thai glyphs. **Every font of this app is loaded from
  `/assets/print_designer/fonts/...`**, the path of this app.
- The font files are shipped by this app under
  `print_designer/public/fonts/thai/`. The path of the framework
  (`/assets/frappe/...`) is also fine, because Frappe is installed on every
  site.
- The guard is `print_designer/tests/test_template_asset_ownership.py`:
  - `test_the_app_loads_a_font` proves that the guard sees the fonts of the
    app, so it cannot pass without proving anything.
  - `test_no_font_of_the_app_comes_from_another_app` proves that every font
    of every source of the app is loaded from `/assets/print_designer/`.
  - `test_every_font_of_the_app_is_shipped_by_the_app` proves that every such
    font file exists in `print_designer/public/`.
  - `test_no_asset_of_the_app_comes_from_another_app` proves that every asset
    of every source of the app, the fonts and the images, is loaded from
    `/assets/print_designer/` or from `/assets/frappe/`.
  - `test_every_asset_of_the_app_is_shipped_by_the_app` proves that every such
    asset file exists in `print_designer/public/`. The bundle of a source is
    skipped, because the build writes it under a hashed name.
- The PND templates `PND/PND3/pnd3.html` and `PND/PND53/pnd53.html` used to
  load the Thai font from the assets of another app.
  They now load it from the path of this app.
- The print format of the Form 50 that this app ships loaded the Thai font
  from the assets of another app. It now loads it from the path of this app.
- **The digit boxes of the PND forms** render the character at an index with
  `x[i:i+1]` and not with `x[i] if i < x|length else ''`. A comparison
  operator in the text of an HTML template is flagged by the linter, and the
  escaped form (`&lt;`) breaks the template with a `TemplateSyntaxError`.
  Slicing never raises and returns an empty string out of range, so the two
  forms are equivalent for a string, a list and an empty input.
