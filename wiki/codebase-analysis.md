# Print Designer Codebase Analysis

> Analysis Date: 2026-07-17

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Print Designer Architecture                 │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │ MainStore  │    │ElementStore │    │ GlobalStyles│    │
│  │  (Pinia)   │    │  (Pinia)    │    │  (Object)  │    │
│  └──────┬──────┘    └──────┬──────┘    └─────────────┘    │
│         │                    │                              │
│  ┌──────▼──────────────────────────────────────┐       │
│  │                  utils.js                       │       │
│  │  • setCurrentElement()                       │       │
│  │  • handleBorderIconClick()                  │       │
│  │  • getConditonalObject()                    │       │
│  │  • parseFloatAndUnit()                      │       │
│  └──────────────────────┬────────────────────────┘       │
│                         │                               │
│  ┌─────────────────────▼────────────────────────┐      │
│  │           PropertiesPanelState.js              │      │
│  │  • Dynamic property panel generation           │      │
│  │  • Border toggles (L/R/T/B)                 │      │
│  │  • Style mode controls                       │      │
│  └─────────────────────┬────────────────────────┘      │
│                        │                                │
│  ┌─────────────────────▼────────────────────────┐     │
│  │                Vue Components (29 files)         │     │
│  │  • BaseTable.vue - Table rendering             │     │
│  │  • BaseDynamicText.vue - Dynamic text         │     │
│  │  • AppCanvas.vue - Main canvas                │     │
│  │  • AppPropertiesPanel.vue - Properties       │     │
│  │  • AppToolbar.vue - Toolbar                  │     │
│  │  • AppLayer.vue - Layers panel               │     │
│  │  • ... (23 more)                           │     │
│  └──────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────┘
```

## Key Files & Responsibilities

### 1. State Management

| File | Lines | Purpose |
|------|-------|---------|
| `MainStore.js` | ~680 | Pinia store - selection, styles, page settings, global state |
| `ElementStore.js` | ~1800 | Pinia store - element CRUD operations |
| `globalStyles.js` | ~320 | Default styles for text, table, image, barcode |

### 2. Core Utilities (`utils.js`)

| Function | Purpose |
|----------|---------|
| `setCurrentElement()` | Add/remove elements from selection |
| `handleBorderIconClick()` | Toggle border styles |
| `getConditonalObject()` | Get style object based on mode |
| `parseFloatAndUnit()` | Parse CSS values with units |
| `childrensCleanUp()` | Clone elements with deep copy |

### 3. Composables (`composables/`)

| File | Purpose |
|------|---------|
| `Draw.js` | Drawing tools for creating elements |
| `Resizable.js` | Resize handles and logic |
| `Draggable.js` | Drag functionality |
| `DropZone.js` | Drop zone detection |
| `MarqueeSelectionTool.js` | Multi-select rectangle |
| `AttachKeyBindings.js` | Keyboard shortcuts |
| `ChangeValueUnit.js` | Unit conversion |

### 4. Properties Panel (`PropertiesPanelState.js`)

Dynamic property panel with:

- Text alignment controls
- Border toggles (L/R/T/B)
- Style mode selector (header/main/alt/label)
- Color picker
- Font controls
- Width/height inputs

## Current Style System

### Style Cascade

```
Style Priority (highest to lowest):
1. column.style (per-column overrides)
2. headerStyle / style / altStyle / labelStyle (element-level)
3. globalStyles[type][styleEditMode] (global defaults)
```

### Style Modes

| Mode | Property | Applies To |
|------|----------|----------|
| `header` | `headerStyle` | Table header cells |
| `main` | `style` | All rows |
| `alt` | `altStyle` | Alternate rows |
| `label` | `labelStyle` | Field labels |

## Component Structure

### Base Components

```
components/base/
├── BaseTable.vue         # Table with header/body, column selection
├── BaseTableTd.vue      # Table cell
├── BaseDynamicText.vue   # Dynamic text fields
├── BaseStaticText.vue    # Static text
├── BaseImage.vue         # Image element
├── BaseBarcode.vue       # Barcode
├── BaseRectangle.vue     # Rectangle/shape
├── BaseDynamicTextSpanTag.vue  # Span tag within dynamic text
└── BaseResizeHandles.vue # Resize handle decorations
```

### Layout Components

```
components/layout/
├── AppCanvas.vue         # Main editing canvas
├── AppPages.vue          # Page management
├── AppPropertiesPanel.vue # Right sidebar properties
├── AppPropertiesPanelSection.vue
├── AppToolbar.vue        # Top toolbar
├── AppLayer.vue         # Layers panel
├── AppHeader.vue         # Header
├── AppCodeEditor.vue     # Jinja code editor
├── AppDynamicPreviewModal.vue
├── AppDynamicTextModal.vue
├── AppBarcodeModal.vue
├── AppBarcodePreviewModal.vue
├── AppImageModal.vue
├── AppWidthHeightModal.vue
├── AppUserProvidedJinjaModal.vue
├── AppPreviewPdf.vue
├── AppModal.vue
├── LayersPanel.vue
└── AppTableContextMenu.vue
```

## Enterprise-Grade Improvements Analysis

### Priority 1: Border System (Current Focus)

| Issue | Current | Target |
|-------|---------|--------|
| L/R borders | Shared via `headerStyle` | Per-column via `columns[i].style` |
| Border width | Implicit | Explicit `borderLeftWidth` |
| Border color | Shared | Per-border color |

### Priority 2: Selection System

| Feature | Current | Enterprise |
|---------|---------|------------|
| Single select | ✅ | ✅ |
| Shift+click multi | ✅ | ✅ |
| Marquee select | ✅ | ✅ |
| Select row/column | ❌ | Add click header to select column |

### Priority 3: Layout System

Current: `position: absolute` only

```
Layout Types to Add:
• ABSOLUTE (current) - Precise positioning
• RELATIVE - Content flows naturally
• FLEX_ROW - Horizontal flow
• FLEX_COLUMN - Vertical flow
• GRID - Grid layout
```

### Priority 4: Copy/Paste

| Feature | Current | Enterprise |
|---------|---------|------------|
| Copy element | Basic | Format-aware copy |
| Paste element | Position offset | Smart positioning |
| Copy style only | ❌ | Style brush |
| Copy borders | ❌ | Per-border copy |

### Priority 5: Collaboration

| Feature | Current | Enterprise |
|---------|---------|------------|
| Undo/Redo | Basic | Multi-level |
| Version history | ❌ | Full history |
| Real-time collab | ❌ | Live cursors |

## Technical Debt

### 1. Code Duplication

- `PropertiesPanelState.js` - 1800+ lines, monolithic
- `BaseTable.vue` - 600+ lines
- Multiple similar patterns in `handleBorderIconClick`

### 2. Magic Strings

```javascript
// Current
const mapper = Object.freeze({
  main: "style",
  label: "labelStyle",
  header: "headerStyle",
  alt: "altStyle",
});

// Enterprise: TypeScript enums
enum StyleMode {
  MAIN = 'main',
  LABEL = 'label',
  HEADER = 'header',
  ALT = 'alt'
}
```

### 3. Global State Mutations

```javascript
// Current - direct mutation
MainStore.currentElements[element.id] = element;

// Enterprise - action
ElementStore.select(element)
```

### 4. Missing TypeScript

- No `.ts` files
- No interfaces for element types
- No compile-time safety

## Recommended Refactoring

### Phase 1: Type Safety

```typescript
// types/elements.ts
export interface TableElement extends BaseElement {
  type: 'table';
  columns: Column[];
  rows: Row[];
  styleEditMode: StyleMode;
  headerStyle: BorderStyle;
  style: BorderStyle;
  altStyle: BorderStyle;
  selectedColumn: Column | null;
}

export interface Column {
  id: string;
  label: string;
  style: ColumnStyle;
  dynamicContent: DynamicContent[];
  applyStyleToHeader: boolean;
}
```

### Phase 2: Extract Composable Functions

```typescript
// composables/useBorderStyling.ts
export const useBorderStyling = (element: TableElement) => {
  const toggleLeftBorder = () => { ... }
  const toggleRightBorder = () => { ... }
  const toggleTopBorder = () => { ... }
  const toggleBottomBorder = () => { ... }
  const isBorderActive = (side: BorderSide) => { ... }
  return { toggleLeftBorder, toggleRightBorder, toggleTopBorder, toggleBottomBorder, isBorderActive }
}
```

### Phase 3: Component Extraction

```
components/table/
├── Table.vue           # Main table wrapper
├── TableHeader.vue     # Header row
├── TableBody.vue       # Body rows
├── TableCell.vue       # Individual cell
├── TableContextMenu.vue
├── TableColumnEditor.vue
└── TableStylePanel.vue # Border controls
```

## Files to Modify for Border Fix

| File | Change |
|------|--------|
| `PropertiesPanelState.js` | Fix L/R targeting logic |
| `BaseTable.vue` | Verify CSS cascade |
| `utils.js` | Potentially add column-specific border functions |

## Next Steps

1. ✅ Fix R border targeting (in progress)
2. ⬜ Verify L/R work for all style modes
3. ⬜ Add border-width support
4. ⬜ Add border presets
5. ⬜ Visual border editor
