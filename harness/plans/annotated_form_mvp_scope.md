# Annotated Form MVP Scope

## MVP goal

Prove that a user can take a source form image/PDF, annotate it hierarchically, and get a structured draft generated component-by-component.

The MVP should optimize for:

- low ambiguity
- predictable geometry
- manual reviewability
- compatibility with Print Designer concepts

## User story

A user opens a form image/PDF, marks `Header`, `Body`, and `Footer`, draws labeled child boxes inside them, and gets a generated draft where each component is recreated inside its exact region.

## MVP boundaries

### In scope

- load/open one source page image or PDF page preview
- define page size/orientation
- draw three mandatory parent regions:
  - Header
  - Body
  - Footer
- draw child boxes inside parents
- assign required label/type to each child box
- store both normalized and absolute coordinates
- crop each child region
- generate component output one box at a time
- assemble all generated components into one page draft
- allow review of each component result

### Out of scope for MVP

- full multi-page automation
- auto-detection of Header/Body/Footer
- unlabeled free-form import
- arbitrary HTML/CSS reverse parsing
- perfect font matching
- complete table intelligence
- advanced OCR correction workflows
- production-ready PDF export pipeline
- full approval/versioning system

## MVP workflow

## Step 1 — Open source document

Supported input:

- PNG/JPG
- one PDF page preview

User sees a single page canvas.

## Step 2 — Configure page

User sets or confirms:

- page size (A4 / custom)
- orientation
- source scaling

## Step 3 — Draw mandatory parent regions

User must create:

- Header
- Body
- Footer

Rule:

- child components cannot be created until all 3 parent regions exist

## Step 4 — Draw labeled child components

Inside a parent, user draws boxes and assigns labels.

Each component requires:

- parent reference
- label/type
- coordinates

## Step 5 — Generate one component at a time

System processes each component independently.

For MVP, generation can be sequential.

## Step 6 — Assemble draft

System places generated components back into page layout using stored geometry.

## Step 7 — Review

User reviews:

- each component preview
- placement
- obvious mismatches

## Step 8 — Save draft artifact

At minimum save:

- page metadata
- annotation hierarchy
- generated component payloads
- assembled draft model

## MVP supported component types

Recommended MVP labels:

- `text_block`
- `title`
- `logo_image`
- `image_block`
- `label_value_box`
- `rectangle_box`
- `signature_block`
- `notes_block`
- `totals_block`

## MVP unsupported or limited types

These should either be blocked or represented as placeholders:

- `items_table`
- `barcode`
- `qr_code`
- `dynamic_field_group`
- `multi_column_grid`
- `nested_container`
- `page_variant_header`
- `page_variant_footer`

## Recommended MVP outputs

### Primary output

- structured draft model aligned with Print Designer layout concepts

### Optional preview output

- simple HTML/CSS page preview

## Success criteria

The MVP is successful if a user can:

1. open a source page
2. define Header / Body / Footer
3. draw labeled child boxes
4. generate simple component drafts
5. see those drafts placed in the correct approximate positions
6. re-run only one bad component without rebuilding everything else

## UX principles for MVP

### 1. Force structure early

Do not allow a chaotic flat annotation mode first.

### 2. Require labels

A child box without a label is invalid.

### 3. Prefer explicit errors

If a component type is unsupported, show it clearly.

### 4. Keep generation local

The user should understand that one annotation = one generation task.

## Suggested MVP screens

### Screen A — Source page annotator

Capabilities:

- view page
- draw Header/Body/Footer
- draw child regions
- label regions

### Screen B — Component queue/review

Capabilities:

- list all components
- show status per component
- regenerate one component
- inspect crop and output side-by-side

### Screen C — Assembled draft preview

Capabilities:

- show full page result
- highlight source-to-output mapping
- let user jump back to one component

## MVP data model summary

### Page

- page size
- orientation
- source image/pdf metadata

### Parent region

- header/body/footer
- box coordinates

### Child region

- id
- label
- parent
- normalized box
- absolute box
- crop reference
- generation status

### Generated component

- source region id
- output fragment
- warnings
- confidence

## Recommended rollout order

### MVP-1

- page loading
- page config
- mandatory parent boxes

### MVP-2

- child box drawing
- label assignment
- coordinate persistence

### MVP-3

- crop extraction
- simple component generation

### MVP-4

- assembly preview
- re-run one component

## Risks inside MVP

- users may label components inconsistently
- tables will still be hard
- source scans may have skew/noise
- exact typography will still be imperfect
- some components may need human correction after generation

## Risk mitigation

- force label taxonomy from dropdown, not free text only
- keep unsupported types explicit
- preserve geometry as source of truth
- keep component generation isolated

## What MVP should deliberately not promise

- perfect full-form automation
- perfect PDF reproduction
- full table understanding
- instant conversion without annotation

## End state of MVP

At the end of MVP, the product should already demonstrate the key value:

**annotated hierarchical decomposition plus coordinate-aware component generation is practical and reduces confusion compared to whole-form generation.**
