# Minimax action plan: Annotated Form MVP

## Purpose

This file is the implementation handoff for Minimax for the new annotated-form project.

Target outcome:

1. let a user open a source image/PDF page
2. force creation of three mandatory parent regions:
   - `Header`
   - `Body`
   - `Footer`
3. let the user draw labeled child regions inside those parents
4. store both normalized and absolute coordinates
5. process components one-by-one
6. assemble a structured page draft for review

## Source planning docs

Read these first:

- `harness/plans/annotated_form_product_architecture.md`
- `harness/plans/annotated_form_mvp_scope.md`
- `harness/plans/annotated_form_component_taxonomy.md`

## Confirmed design decisions

These are already decided and should not be revisited in MVP:

1. `Header`, `Body`, and `Footer` are mandatory top-level parents.
2. Every child component must have a label/type.
3. Coordinates must store both:
   - normalized ratios (canonical)
   - absolute page/source units
4. The system is geometry-first, not CSS-first.
5. This is a human-in-the-loop decomposition workflow, not blind whole-form conversion.

## Scope for Minimax now

Implement the **Annotated Form MVP** only.

### In scope now

- open one source page image or PDF preview
- page setup/config metadata
- parent region drawing for Header/Body/Footer
- child region drawing inside parents
- required label selection for child regions
- coordinate persistence
- crop extraction per child region
- per-component generation pipeline stub or simple generator
- assembled draft preview
- per-component review/regenerate flow if reasonably small

### Explicitly out of scope now

- full multi-page automation
- auto-detection of Header/Body/Footer
- arbitrary HTML/CSS import/export bridge
- full table intelligence
- barcode / QR support
- dynamic field inference
- perfect font matching
- complete production PDF pipeline
- unrestricted free-form labeling

## Product rules

### Hierarchy rule

The page model must be hierarchical, not flat:

- page
  - header_parent
  - body_parent
  - footer_parent
    - child components within each parent

Do not allow free child-region creation before all three parent regions exist.

### Label rule

Every child region must have a label.

Use controlled labels from the taxonomy, not arbitrary free text by default.

At minimum, support these labels in MVP:

- `logo_image`
- `company_header`
- `document_title`
- `page_number`
- `document_meta_box`
- `buyer_info`
- `invoice_info`
- `order_reference_strip`
- `totals_block`
- `amount_in_words`
- `notes_block`
- `legal_text`
- `signature_block`
- `rectangle_box`
- `label_value_box`
- `text_block`
- `image_block`
- `unknown_component`

### Coordinate rule

Store both:

- normalized coordinates — canonical
- absolute coordinates — source/debug/crop extraction

Recommended region shape:

```json
{
  "id": "region-001",
  "parent": "header_parent",
  "label": "company_header",
  "absolute_box": { "x": 120, "y": 48, "width": 520, "height": 88, "unit": "px" },
  "normalized_box": { "x": 0.14, "y": 0.05, "width": 0.61, "height": 0.08 }
}
```

## Recommended implementation slices

## Slice 1 - Source page + page model

### Goal

Create the base document/page model.

### Deliverables

- load a source image or PDF preview
- capture page size/orientation metadata
- initialize page root object
- create storage shape for parent/child regions

### Acceptance

- one page can be loaded and displayed
- page metadata exists
- empty annotation model can be saved/restored

## Slice 2 - Mandatory parent annotation

### Goal

Force the user to define `Header`, `Body`, `Footer` first.

### Deliverables

- drawing tool for rectangular parent regions
- validation that exactly these 3 exist
- prevent child annotations before parent completion

### Acceptance

- user can draw all 3 parents
- app blocks child creation until parents exist
- parent regions can be edited/resized

## Slice 3 - Child region annotation + taxonomy labels

### Goal

Allow user to create child components inside parents with required labels.

### Deliverables

- nested child box drawing
- label picker from taxonomy
- optional notes field
- parent-aware label suggestions

### Acceptance

- child region cannot be saved without label
- child region belongs to one parent
- label comes from controlled set

## Slice 4 - Coordinate persistence + crop extraction

### Goal

Make each component a precise spatial task.

### Deliverables

- store normalized + absolute coordinates
- crop region image for each child box
- save crop reference/path/identifier

### Acceptance

- every child region can generate a crop
- coordinates survive reload
- normalized coordinates can be converted back to page positions

## Slice 5 - Per-component generation pipeline

### Goal

Process one component at a time.

### MVP-supported component strategies

Support simple/safe types first:

- `text_block`
- `document_title`
- `logo_image`
- `image_block`
- `label_value_box`
- `rectangle_box`
- `signature_block`
- `notes_block`
- `totals_block`

### Deliverables

- component queue/list
- status per component
- simple generation output object per region
- warning/error state per component

### Acceptance

- each region can be processed independently
- failed region does not block all others
- user can re-run one region only

## Slice 6 - Assembly draft preview

### Goal

Recombine all generated pieces into a full page draft.

### Deliverables

- full-page assembled preview
- parent/child placement by geometry
- source-to-output mapping visibility

### Acceptance

- assembled preview respects Header/Body/Footer hierarchy
- components appear in correct approximate positions
- one region can be edited/regenerated without rebuilding everything manually

## Suggested files / modules Minimax should create

Exact repo paths can be adjusted after project structure review, but the MVP likely needs modules in these categories:

### Frontend / UI

- source page viewer / annotator
- parent region tool
- child region tool
- label picker dialog/panel
- component queue/review panel
- assembled preview panel

### Data / state

- page store/model
- annotation store/model
- component generation status store

### Backend / services if needed

- crop extraction helper
- persistence endpoint(s)
- optional generation task endpoint(s)

## Recommended data model

### Page

```json
{
  "id": "page-1",
  "size": { "width": 210, "height": 297, "unit": "mm" },
  "orientation": "portrait",
  "source": { "type": "image", "path": "..." }
}
```

### Parent region

```json
{
  "id": "parent-header",
  "label": "header_parent",
  "absolute_box": { "x": 0, "y": 0, "width": 800, "height": 180, "unit": "px" },
  "normalized_box": { "x": 0, "y": 0, "width": 1, "height": 0.16 }
}
```

### Child region

```json
{
  "id": "region-007",
  "parent": "parent-body",
  "label": "buyer_info",
  "notes": "customer address block",
  "absolute_box": { "x": 12, "y": 210, "width": 390, "height": 110, "unit": "px" },
  "normalized_box": { "x": 0.01, "y": 0.18, "width": 0.46, "height": 0.10 },
  "status": "pending"
}
```

## MVP support / non-support behavior

### Supported now

- simple text-like blocks
- images/logo
- rectangle-like containers
- signature blocks
- totals-like static summary block

### Placeholder or unsupported now

- `items_table`
- `barcode`
- `qr_code`
- `dynamic_field_group`
- `nested_container`
- `multi_column_grid`

If unsupported labels are selected, show explicit warning/blocker instead of guessing.

## Acceptance criteria

Annotated Form MVP is acceptable only if all are true:

1. user can load one source page
2. user must create Header / Body / Footer first
3. user can create child boxes only inside parents
4. each child box requires a label
5. coordinates are stored as both normalized and absolute
6. each child region can be cropped and processed independently
7. a draft assembled preview exists
8. one bad component can be retried without resetting the whole page
9. unsupported component types are clearly flagged

## Review checklist for me after Minimax finishes

I will review for:

1. strict Header/Body/Footer enforcement
2. label requirement on every child region
3. normalized coordinates as canonical
4. clean parent-child model
5. geometry-first implementation, not CSS-guess-first
6. component isolation / per-region retry
7. no accidental scope creep into full automation
8. unsupported component types handled explicitly

## Notes to Minimax

- Keep the MVP narrow and reviewable.
- Prefer strong annotation structure over clever automation.
- If ambiguous, require user labeling instead of guessing.
- Build for component-by-component execution, not whole-page magic.
- Do not run build/deploy commands automatically.
