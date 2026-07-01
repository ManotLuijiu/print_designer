# Print Designer Import MVP — file-by-file implementation plan

## Goal

Implement a **safe Import MVP** for Print Designer using a **template-first bridge workflow**.

The MVP must:

1. accept only a bridge template with explicit markers
2. validate `Header`, `Content`, `Footer`, and `CSS` sections before save
3. support only a limited reconstruction subset first
4. write back to Print Designer fields only after explicit confirmation
5. reject arbitrary unmarked HTML/CSS input

## Non-goals for MVP

Do **not** implement these in MVP:

- arbitrary HTML parser
- best-effort section guessing
- reverse-engineering full layout from any pasted HTML
- tables
- barcode
- dynamic fields
- page-variant logic (`firstPage`, `oddPage`, `evenPage`, `lastPage`)
- nested flow containers

## Bridge contract

Required markers:

```html
<!-- PD:METADATA:START -->
...
<!-- PD:METADATA:END -->

<!-- PD:HEADER:START -->
...
<!-- PD:HEADER:END -->

<!-- PD:CONTENT:START -->
...
<!-- PD:CONTENT:END -->

<!-- PD:FOOTER:START -->
...
<!-- PD:FOOTER:END -->

<!-- PD:CSS:START -->
...
<!-- PD:CSS:END -->
```

Importer must reject files missing any required marker pair.

## File-by-file plan

## 1) `print_designer/api/print_format_export_import.py`

### Add new whitelisted APIs

Recommended new endpoints:

- `download_print_designer_import_template(print_format_name=None)`
- `validate_print_designer_import_bundle(bundle_text, print_format_name=None)`
- `import_print_designer_from_jinja_bundle(print_format_name, bundle_text, overwrite=False)`

### Responsibilities

#### `download_print_designer_import_template(...)`

- return a text template string
- include required markers
- optionally include metadata:
  - bridge contract version
  - source format name
  - schema version
  - import mode = `template-first`
- this endpoint is read-only

#### `validate_print_designer_import_bundle(...)`

- parse sections from the uploaded template
- return structured validation response only
- do not save anything
- call helper functions from a utility module
- report:
  - markers present/missing
  - extracted section lengths
  - unsupported HTML patterns found
  - whether import is allowed
  - warnings vs blockers

Suggested response shape:

```json
{
  "valid": true,
  "blockers": [],
  "warnings": [],
  "sections": {
    "header": {"present": true, "length": 1200},
    "content": {"present": true, "length": 4800},
    "footer": {"present": true, "length": 300},
    "css": {"present": true, "length": 1500}
  },
  "supported_subset": {
    "static_text": true,
    "images": true,
    "rectangles": true,
    "absolute_positioning": true
  },
  "unsupported_detected": ["table", "barcode"]
}
```

#### `import_print_designer_from_jinja_bundle(...)`

- require `print_format_name`
- require write permission on `Print Format`
- validate first
- refuse import if blockers exist
- build reconstructed Print Designer JSON
- write only after successful reconstruction
- write these fields:
  - `print_designer_header`
  - `print_designer_body`
  - `print_designer_footer`
  - `print_designer_print_format`
  - `print_designer_settings`
  - `css`
- keep `print_designer = 1`
- do not touch unrelated fields

### Important API rule

Validation and import must stay separate.

- `validate_*` = preview only
- `import_*` = write only after passing validation

---

## 2) New helper module

### `print_designer/utils/import_jinja_bridge.py`

Create a dedicated helper module so parsing and reconstruction logic stays out of the API file.

### Suggested helpers

#### Marker parsing

- `extract_bridge_sections(bundle_text)`
- `extract_metadata(bundle_text)`
- `require_marker_pair(name, start_marker, end_marker)`

#### Validation

- `validate_bridge_sections(sections)`
- `detect_unsupported_patterns(html, css)`
- `build_validation_report(...)`

#### Reconstruction

- `html_section_to_pd_elements(section_html, section_name, css_context)`
- `css_text_to_style_map(css_text)`
- `build_pd_page(children, section_name)`
- `build_pd_format_layout(header, body, footer)`
- `build_import_settings(existing_settings, css_text, metadata)`

### MVP-supported node mapping

Map only these HTML patterns first:

#### Static text

From:

- `<div>text</div>`
- `<p>text</p>`
- `<span>text</span>`

To:

- Print Designer `text` element
- `isDynamic = false`

#### Rectangle-like containers

From:

- absolutely positioned `<div>` with border/background/size

To:

- Print Designer `rectangle`

#### Images

From:

- `<img ...>`
- background-image is optional later, not MVP-first

To:

- Print Designer `image`

#### Positioning

Read only a minimal CSS subset first:

- `position: absolute`
- `left`
- `top`
- `width`
- `height`
- `font-size`
- `font-weight`
- `text-align`
- `color`
- `background-color`
- `border`
- `padding` (optional)

### Explicit blockers in MVP

Return blockers if found:

- `<table`
- barcode-like markup
- nested complex layout wrappers
- flex/grid layouts that cannot be mapped safely
- Jinja expressions in imported HTML beyond permitted static placeholders

---

## 3) `print_designer/public/js/print_designer/components/layout/AppHeader.vue`

### Add new actions

Add two UI actions:

- `Download Import Template`
- `Import HTML + CSS`

Keep existing export button.

### Responsibilities

- open template download flow
- open import dialog
- pass current `print_format_name`

### UX rule

Import buttons should clearly state:

- template-first workflow only
- arbitrary HTML is unsupported

Example labels:

- `Download Import Template`
- `Import Template`

---

## 4) New frontend dialog

### `print_designer/public/js/print_designer/components/dialogs/ImportJinjaBridgeDialog.js`

Create a dedicated dialog parallel to `ExportJinjaDialog.js`.

### Responsibilities

#### Step A — input

Allow one of these:

- upload template file
- paste full template text into editor

Prefer supporting both, but textarea paste is enough for MVP.

#### Step B — validate

Dialog calls:

- `validate_print_designer_import_bundle`

Show:

- section presence
- length summary
- blockers
- warnings
- unsupported items

#### Step C — import confirm

If validation passes:

- enable `Import` button
- call `import_print_designer_from_jinja_bundle`

#### Step D — success

On success:

- notify user
- optionally reload current format in Print Designer route

### Recommended dialog sections

- help text at top
- large textarea or file upload field
- validation results panel
- import button disabled until valid

---

## 5) Optional editor reuse

### `print_designer/public/js/print_designer/components/layout/AppCodeEditor.vue`

If convenient, reuse this component for the pasted template text area.

Use only if it reduces complexity. If not, a regular textarea in the dialog is acceptable for MVP.

---

## 6) Tests

### Python tests

Create a new test file, e.g.:

- `print_designer/tests/test_import_jinja_bridge.py`

### Test cases

#### Marker validation

- valid template passes
- missing header marker fails
- missing content marker fails
- missing footer marker fails
- missing css marker fails

#### Unsupported pattern detection

- table markup returns blocker
- barcode markup returns blocker
- simple text/image/rectangle markup passes with warnings at most

#### Reconstruction

- simple header block becomes `print_designer_header`
- simple content block becomes `print_designer_body`
- simple footer block becomes `print_designer_footer`
- import writes JSON strings to correct fields

#### Safety

- invalid template does not mutate format
- validation endpoint does not write anything

---

## 7) Harness / docs updates

### Update planning docs only after implementation stabilizes

Potential docs to update later:

- `harness/plans/print_designer_html_css_bridge.plan.md`
- `harness/plans/print_designer_import_bridge_template.example.html`

Do not change product scope silently; keep MVP constraints explicit.

## Import algorithm (MVP)

## Step 1 — parse template

- locate all marker pairs
- extract raw strings for metadata/header/content/footer/css
- fail fast if any required section missing

## Step 2 — validate subset

- scan header/content/footer HTML for unsupported patterns
- scan CSS for unsupported constructs if needed
- produce blockers/warnings

## Step 3 — convert CSS

- build a minimal style map keyed by selector/class/id when possible
- for MVP, inline style parsing may be enough
- class selector support can be partial

## Step 4 — reconstruct PD elements

For each supported node:

- compute element type
- assign id
- set geometry from style
- set style object
- attach children if rectangle wrapper

## Step 5 — build page containers

- header => one page wrapper with `childrens`
- content => one page wrapper with `index: 0`
- footer => one page wrapper with `childrens`

## Step 6 — build `print_designer_print_format`

For MVP use simplest shape:

- `header.firstPage`
- `header.oddPage`
- `header.evenPage`
- `header.lastPage`
- `body[0]`
- same footer variants copied from single footer section if needed

Safe simplification:

- use same imported header/footer for all page variants in MVP

## Step 7 — merge settings

- preserve existing `print_designer_settings` where possible
- update `schema_version`
- store import metadata
- keep page defaults if not explicitly imported

## Step 8 — write fields

Only after successful full reconstruction:

- save header/body/footer/format/settings/css

## Suggested implementation order

1. `import_jinja_bridge.py` marker extraction
2. `validate_*` backend API
3. frontend import dialog with validation only
4. helper reconstruction for supported subset
5. `import_*` backend save API
6. success reload flow
7. tests

## Acceptance criteria

Import MVP is acceptable only if all are true:

1. user can download/use a template with required markers
2. invalid template is rejected before save
3. valid simple template imports successfully
4. header/content/footer are restored separately
5. CSS is stored separately
6. unsupported constructs are blocked with clear messages
7. no arbitrary HTML auto-guessing is attempted

## Suggested messages

### Blocker examples

- `Missing PD:CONTENT markers`
- `Table markup is not supported in Import MVP`
- `Barcode markup is not supported in Import MVP`
- `Only template-first bridge files are supported`

### Warning examples

- `Some unsupported inline styles were ignored`
- `Header/footer imported as shared content for all page variants`

## Final recommendation

The safest MVP is:

- **template download**
- **validate first**
- **simple subset import only**
- **explicit user confirmation before write**

Anything broader should wait until the bridge metadata story is stronger.
