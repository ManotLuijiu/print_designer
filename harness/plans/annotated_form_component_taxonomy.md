# Annotated Form Component Taxonomy

## Purpose

Define the label system for the annotated-form workflow.

This taxonomy exists because child components must be labeled at creation time. The label tells the system:

- what the region is
- which generator strategy to use
- whether the component is supported in MVP
- what validation rules apply

## Taxonomy design principles

### 1. Labels should describe function, not appearance only

Prefer:

- `company_header`
- `buyer_info`
- `signature_block`

Over vague labels like:

- `box1`
- `text2`
- `area_left`

### 2. Labels should be selected from controlled options

Use a predefined dropdown first.

Optional later:

- custom labels
- synonyms
- per-project extensions

### 3. Labels should map to generator strategies

Each label should imply:

- expected content type
- expected structure
- supported rendering path

## Taxonomy levels

## Level 0 — Root

- `page`

## Level 1 — Mandatory parent labels

These are required and always present:

- `header_parent`
- `body_parent`
- `footer_parent`

These are structural, not semantic business components.

## Level 2 — Child component labels

These are the user-assigned labels inside each parent.

## Header labels

### `logo_image`

Use when region contains:

- logo
- emblem
- brand mark

Typical output:

- image component

### `company_header`

Use when region contains:

- company name
- address
- phone
- tax id
- registration info

Typical output:

- grouped text block

### `document_title`

Use when region contains:

- form title
- large centered heading

Typical output:

- title text block

### `page_number`

Use when region contains:

- page x / y
- page reference text

Typical output:

- small text block

### `document_meta_box`

Use when region contains:

- document number
- date
- revision code
- top-right metadata panel

Typical output:

- label-value box

## Body labels

### `buyer_info`

Use when region contains:

- customer name
- customer address
- customer contact details

Typical output:

- label-value group or grouped text block

### `seller_info`

Use when region contains seller/vendor identity details distinct from company header.

### `invoice_info`

Use when region contains:

- invoice references
- linked document references
- billing data

Typical output:

- label-value box

### `order_reference_strip`

Use when region contains:

- one-row metadata strip
- order number / sales order / due date / salesperson

Typical output:

- boxed row / simplified table-like strip

### `items_table`

Use when region contains the main line-item table.

MVP status:

- generally unsupported or placeholder-only in first version

### `totals_block`

Use when region contains:

- subtotal
- discount
- tax
- grand total

Typical output:

- aligned numeric summary block

### `amount_in_words`

Use when region contains textual amount summary.

Typical output:

- single text block

### `notes_block`

Use when region contains remarks / notes / comments.

Typical output:

- text region

### `legal_text`

Use when region contains legal wording, conditions, disclaimer, or policy text.

Typical output:

- small multiline text block

### `image_block`

Use when the body contains a non-logo image region.

### `rectangle_box`

Use when a component is mostly a bordered block or container and needs to be preserved structurally.

### `label_value_box`

Use when a box contains labels on one side and values on the other side.

Useful for many Thai business forms.

## Footer labels

### `signature_block`

Use when region contains:

- signature line
- signer name
- date near signature
- approval label

Typical output:

- grouped signature component

### `approval_block`

Use when the footer block is explicitly an approval/authorization section.

### `footer_notes`

Use when footer contains extra notes, disclaimers, or short text.

## Cross-cutting generic labels

These can be used in any parent if needed.

### `text_block`

Fallback for simple text regions.

### `title`

Fallback for title-like text when `document_title` feels too specific.

### `static_image`

Fallback for image region.

### `unknown_component`

Use when user wants to annotate a region but does not yet know the best label.

Rule:

- should be allowed only temporarily
- should block final generation until relabeled

## MVP support classification

## Supported in MVP

- `logo_image`
- `company_header`
- `document_title`
- `page_number`
- `document_meta_box`
- `buyer_info`
- `invoice_info`
- `order_reference_strip` (limited/simple only)
- `totals_block`
- `amount_in_words`
- `notes_block`
- `legal_text`
- `signature_block`
- `rectangle_box`
- `label_value_box`
- `text_block`
- `image_block`

## Limited / placeholder in MVP

- `items_table`
- `approval_block`
- `seller_info`

## Unsupported in MVP

- `barcode`
- `qr_code`
- `dynamic_field_group`
- `nested_container`
- `multi_column_grid`

## Suggested label metadata model

```json
{
  "label": "buyer_info",
  "category": "body",
  "mvp_supported": true,
  "generator_strategy": "label_value_group",
  "expected_content": ["text", "multiline_text"],
  "notes": "Customer identity block"
}
```

## Generator strategy mapping

Example mapping:

- `logo_image` -> image strategy
- `company_header` -> grouped multiline text strategy
- `document_title` -> title text strategy
- `document_meta_box` -> boxed label-value strategy
- `buyer_info` -> grouped label-value strategy
- `totals_block` -> aligned totals strategy
- `signature_block` -> signature-line strategy
- `rectangle_box` -> container strategy
- `items_table` -> table strategy (placeholder early)

## Validation rules by label

Examples:

### `logo_image`

- should contain image-dominant region
- too much multiline text => warning

### `document_title`

- should be text-dominant
- usually short text

### `items_table`

- table lines detected expected
- if no row/column structure found => warning or blocker

### `signature_block`

- horizontal line or signer area likely expected
- may contain handwritten signature image

## Recommended label UX

### Label picker behavior

When user creates a child box:

1. choose parent first (already known from nesting)
2. choose label from dropdown filtered by parent
3. optional free-text notes
4. save component

### Parent-filtered dropdown

#### In Header

Suggested labels first:

- `logo_image`
- `company_header`
- `document_title`
- `page_number`
- `document_meta_box`

#### In Body

Suggested labels first:

- `buyer_info`
- `invoice_info`
- `order_reference_strip`
- `items_table`
- `totals_block`
- `amount_in_words`
- `notes_block`
- `rectangle_box`

#### In Footer

Suggested labels first:

- `signature_block`
- `approval_block`
- `footer_notes`
- `legal_text`

## Taxonomy evolution rule

New labels should be added only when:

- they represent a real repeated business pattern
- they need a distinct generator strategy
- existing labels are not enough

Avoid label explosion.

## Initial recommended canonical labels

If we want a compact first taxonomy, I recommend these as the starter set:

- `header_parent`
- `body_parent`
- `footer_parent`
- `logo_image`
- `company_header`
- `document_title`
- `page_number`
- `document_meta_box`
- `buyer_info`
- `invoice_info`
- `order_reference_strip`
- `items_table`
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

## Final recommendation

For MVP, keep the taxonomy structured but not huge.

The taxonomy should primarily help the system answer:

- what is this region?
- how should it be generated?
- is it supported right now?
