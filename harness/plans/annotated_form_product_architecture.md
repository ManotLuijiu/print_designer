# Annotated Form Product Architecture

## Purpose

Design a new smart workflow for turning a source image/PDF form into structured layout output by using **manual spatial annotation** plus **component-by-component generation**.

This architecture is based on three confirmed decisions:

1. `Header`, `Body`, and `Footer` are mandatory top-level parent regions.
2. Every child component must have an explicit label/type.
3. Coordinates are stored in both normalized and absolute page units, with normalized coordinates as canonical.

## Product idea in one sentence

Treat a document page like a bounded map, let the user annotate hierarchical regions on that map, then generate and assemble the final form one component at a time.

## Core principles

### 1. Geometry-first, not CSS-first

The system should use spatial coordinates as the source of truth.

- user defines page size/orientation
- user annotates regions
- generator works inside locked boxes
- renderer converts coordinates into CSS / Print Designer units later

### 2. Hierarchy-first, not flat boxes

The page model should be explicitly hierarchical:

- Page
  - Header
  - Body
  - Footer
    - child components inside each parent

This matches Print Designer structure and reduces ambiguity.

### 3. Human-in-the-loop decomposition

The user provides the most important structural knowledge:

- where each region begins/ends
- what each component is
- what should be grouped together

The AI should not be responsible for discovering the whole form structure by itself.

## High-level system architecture

## A. Source document layer

Input types:

- PNG / JPG image
- PDF page(s)
- scanned paper form converted to image/PDF

Responsibilities:

- load source page
- determine page dimensions
- store page metadata
- optionally generate image preview for annotation

Primary output:

- page canvas
- page size metadata
- source page id

## B. Spatial annotation layer

This is the user-facing region annotation system.

### Top-level annotation

User must create exactly three parent regions first:

- Header
- Body
- Footer

These become the top-level layout containers.

### Child annotation

Inside each parent, user can draw child boxes.

Every child box must include:

- label/type
- coordinates
- optional notes
- optional ordering/index

Examples of labels:

- logo
- company_header
- title
- buyer_info
- invoice_info
- order_strip
- items_table
- totals_summary
- amount_in_words
- notes
- legal_footer
- signature_block

## C. Document region model

Each annotation becomes a structured region object.

### Page object

```json
{
  "page_id": "page-1",
  "page_size": {
    "width": 210,
    "height": 297,
    "unit": "mm",
    "orientation": "portrait"
  },
  "parents": ["header", "body", "footer"]
}
```

### Region object

```json
{
  "id": "region-001",
  "parent": "header",
  "label": "company_header",
  "source_box": {
    "x": 120,
    "y": 48,
    "width": 520,
    "height": 88,
    "unit": "px"
  },
  "normalized_box": {
    "x": 0.14,
    "y": 0.05,
    "width": 0.61,
    "height": 0.08
  },
  "notes": "Company name + address + tax id",
  "z_index": 1
}
```

## D. Coordinate system

The system should store **two forms of geometry**.

### 1. Canonical normalized coordinates

Relative to page width/height:

- `x_ratio`
- `y_ratio`
- `width_ratio`
- `height_ratio`

Why canonical:

- survives page resizing
- independent from source resolution
- portable across A4/Letter/custom sizes

### 2. Absolute source coordinates

Relative to the original page preview:

- `x`
- `y`
- `width`
- `height`
- `unit = px` or source page unit

Why store too:

- easier crop extraction
- easier visual debugging
- easier OCR / CV processing

### 3. Derived output coordinates

Used only at render/generation time:

- mm
- pt
- px
- Print Designer units

Conversion pattern:

- `output_x = normalized_x * target_page_width`
- `output_y = normalized_y * target_page_height`
- `output_w = normalized_w * target_page_width`
- `output_h = normalized_h * target_page_height`

## E. Component generation layer

The generator should work **one component at a time**.

Inputs per task:

- cropped image/PDF region
- region label
- region coordinates
- parent context (`header`, `body`, `footer`)
- page metadata
- optional user notes

Outputs per task:

- structured component definition
- styling hints
- confidence / warnings
- optional preview markup

Example output targets:

- Print Designer JSON fragment
- HTML/CSS fragment
- Jinja fragment

## F. Assembly layer

This layer recombines component outputs into a full document.

Responsibilities:

- preserve Header / Body / Footer hierarchy
- place components by normalized coordinates
- keep labels and metadata for later editing
- generate a full page artifact

Possible assembly outputs:

- Print Designer page/element tree
- HTML/CSS preview
- Jinja Print Format skeleton

## G. Review layer

The user must be able to review component outputs before finalization.

Recommended checks:

- geometry looks correct
- component label is correct
- generated content matches source crop
- unsupported components are clearly flagged

## H. Export / persistence layer

Store at least three artifacts:

1. source document metadata
2. annotation model
3. generated output model

This allows:

- re-running only one component
- correcting labels later
- switching output format without re-annotating

## Data flow

1. user loads image/PDF
2. system initializes page canvas
3. user marks `Header`, `Body`, `Footer`
4. user draws child boxes inside parents
5. user assigns component labels
6. system crops each component region
7. generator processes each region independently
8. assembly engine rebuilds full layout
9. user reviews and corrects
10. output is exported to target format

## Why this architecture is strong

- aligns with Print Designer hierarchy
- reduces AI ambiguity
- improves reproducibility
- isolates hard tasks into small tasks
- supports manual correction without redoing the whole page
- makes exact coordinate placement practical

## Target outputs this architecture can support later

- Print Designer JSON
- Jinja Print Format
- HTML/CSS bridge package
- PDF reconstruction preview
- annotation dataset for future model training

## Main architectural constraints

- top-level parents must be mandatory
- labels must be mandatory for child components
- no flat anonymous region set
- no geometry guessing as primary behavior
- unsupported complex components must be flagged, not silently converted

## Recommended first-generation output target

The most natural first target is:

- Print Designer-compatible structured layout fragments

Because the hierarchy and coordinate model already match that mental model well.
