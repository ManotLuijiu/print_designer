# Print Designer - Border Styling Improvements

> Analysis Date: 2026-07-17

## Current Architecture

### Key Files

- `PropertiesPanelState.js` - Border toggle logic
- `BaseTable.vue` - CSS cascade for header styles  
- `utils.js` - Border handling utilities

### CSS Cascade Issue (Root Cause)

```vue
<!-- BaseTable.vue line 57 -->
:style="[
  headerStyle,                           // Applied first (all cells share)
  column.applyStyleToHeader && column.style,  // Applied second (can override)
]"
```

**Problem**: `headerStyle` is shared by ALL header cells. Setting borders here affects every cell.

## Current Status

| Border | Status | Notes |
|--------|--------|-------|
| L | ✅ Fixed | Targets `columns[0].style` |
| R | ✅ Fixed | Targets `columns[n-1].style` |
| T | ✅ Working | Correct behavior |
| B | ✅ Working | Correct behavior |

## Implementation Details

### PropertiesPanelState.js Changes

```javascript
// For L/R in header mode (no column selected), target specific column's style
if (styleEditMode === "header" && !hasSelectedColumn && selectedElement?.columns?.length) {
  let targetColumnStyle;

  if (name === "borderLeftStyle") {
    // L: target first column's style
    targetColumnStyle = selectedElement.columns[0].style;
  } else if (name === "borderRightStyle") {
    // R: target last column's style
    targetColumnStyle = selectedElement.columns[selectedElement.columns.length - 1].style;
  }

  if (targetColumnStyle) {
    if (targetColumnStyle[name] === "hidden") {
      targetColumnStyle[name] = "solid";
    } else {
      targetColumnStyle[name] = "hidden";
    }
  }
  return;
}
```

### BaseTable.vue Changes

- Removed `!important` from `border-left-style` and `border-right-style` (lines 525-532)
- This allows `column.style` to properly override `headerStyle`

## Fix for R Border (P0)

### Root Cause

R toggle targets `headerStyle` (shared) instead of `columns[n-1].style` (last column only).

### Fix Steps

1. Add debug logging to confirm R targets `columns[n-1].style`
2. Ensure R sets `columns[columns.length - 1].style.borderRightStyle`
3. Remove `headerStyle.borderRightStyle` when setting column-specific

## Enterprise Improvements

### P1: Separate border-width from style

**Current**: `borderLeftStyle: "solid"` (implicit width)
**Enterprise**: Separate properties per border side

```javascript
column.style = {
  borderLeftWidth: "1px",
  borderLeftColor: "#000", 
  borderLeftStyle: "solid",
  borderRightWidth: "2px",
  borderRightColor: "#333",
  borderRightStyle: "solid",
}
```

### P2: Border Presets

| Preset | L | R | T | B | Inner V | Inner H |
|--------|---|---|---|---|---|----------|----------|
| No Grid | off | off | off | off | off | off |
| Full Grid | on | on | on | on | on | on |
| Outline Only | on | on | on | on | off | off |
| Horizontal Only | off | off | on | on | off | on |

### P3: Visual Border Editor

```
┌──────────────────────────────────────────────┐
│  ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ │
│  └──┘ └──┘ └──┘ └──┘ └──┘ └──┘ └──┘ └──┘ │
│  ┌──┐        Selected Cell         ┌──┐ │
│  │▓▓│                              │▓▓│ │
│  └──┘                              └──┘ │
│  ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ │
│  └──┘ └──┘ └──┘ └──┘ └──┘ └──┘ └──┘ └──┘ │
└──────────────────────────────────────────────┘
```

### P4: Drag-to-Paint Borders

```javascript
isDragPainting = ref(false)
paintMode = ref('toggle') // 'toggle' | 'on' | 'off'

onMouseDown(e) {
  if (e.altKey) isDragPainting.value = true
}
onMouseMove(e) {
  if (isDragPainting.value) {
    getCellAtPosition(e).applyBorder(borderSide, paintMode)
  }
}
```

## Priority Matrix

| Priority | Improvement | Status | Effort | Impact |
|----------|-------------|--------|--------|--------|
| ✅ P0 | Fix R border targeting | **DONE** | 1 day | Critical |
| ✅ P1 | Separate border-width | **DONE** | 2 days | High |
| ✅ P2 | Border presets | **DONE** | 2 days | High |
| ✅ P3 | Visual border editor | **DONE** | 3 days | Medium |
| ✅ P4 | Drag-to-paint | **DONE** | 3 days | Medium |
| ✅ P5 | Copy/paste borders | **DONE** | 2 days | Low |
| ✅ P6 | Per-border color | **DONE** | 2 days | Low |
| ✅ P7 | Selection border uses primary color | **DONE** | - | - |

## Selection Border Styling

Table column selection now uses primary color (#7b4b57 burgundy) instead of default border color.

### File: BaseTable.vue

**Line 63** - Class applied to selected column header:

```vue
:class="(menu?.index == index || column == selectedColumn) && 'current-column'"
```

**Lines 519-521** - CSS for selection border:

```css
.current-column {
  outline: 1.5px solid var(--primary-color);
  outline-offset: -1.5px;
}
```

### CSS Variable

`--primary-color` is defined as `#7b4b57` (burgundy) in App.vue `.main-layout`.

## Implementation Details (P1-P6)

### P2: Border Presets

```javascript
const borderPresets = [
  { name: "No Grid", borders: { L: false, R: false, T: false, B: false } },
  { name: "Full Grid", borders: { L: true, R: true, T: true, B: true } },
  { name: "Outline Only", borders: { L: true, R: true, T: true, B: true, innerV: false, innerH: false } },
  { name: "Horizontal", borders: { L: false, R: false, T: true, B: true, innerH: true } },
];
```

### P5: Copy/Paste Borders

```javascript
let copiedBorderStyle = null;
const copyBorderStyle = () => { /* copies all border properties */ };
const pasteBorderStyle = () => { /* pastes border properties */ };
```

### P6: Per-Border Colors

```javascript
const perBorderColor = (side, label) => {
  // Returns color input for L/R/T/B borders
};
```

### BaseTable.vue Per-Border Color Support

Column styles now support:

- `borderLeftColor`
- `borderRightColor`
- `borderTopColor`
- `borderBottomColor`

### P3: Visual Border Editor

3x3 grid Vue component for clicking individual border sides (TL, T, TR, L, C, R, BL, B, BR).
Uses `markRaw()` to avoid Vue reactivity warnings.

### P4: Drag-to-Paint Borders

Controls: Paint On, Paint Off, Paint Toggle, Stop.

**Key Fixes:**

- In Vue context, `ref` is DOM element, use `ref?.appendChild()` directly
- Use `markRaw()` on imported Vue components to avoid reactivity warnings
- Added null guards to `ChangeValueUnit.js` for undefined inputs

## References

- `PropertiesPanelState.js` - Border toggle functions
- `BaseTable.vue` - Table rendering and style cascade
- `utils.js` - Style manipulation utilities

## UI Design Notes

### Primary Color

Print Designer uses **burgundy (#7b4b57)** as primary color, NOT the default Frappe blue (#2490ef).

```css
/* In App.vue .main-layout */
--primary: #7b4b57;
--primary-color: #7b4b57;
```

When adding UI buttons/controls, use:

- Active state: `btn-primary` (burgundy background)
- Inactive state: `btn-default` (gray)

### Table Selection Border Color

**File:** `BaseTable.vue`

**Class applied to selected column header (line 63):**
```vue
:class="(menu?.index == index || column == selectedColumn) && 'current-column'"
```

**CSS (lines 519-521):**
```css
.current-column {
    outline: 1.5px solid var(--primary-color);
    outline-offset: -1.5px;
}
```

**Resizer hover states (lines 541, 555):**
```css
.resizer:hover,
.resizer-active,
.resizing {
    border-right: 2px solid var(--primary-color);
}
```

---

# Bug: Print Format Language Auto-Select

> Bug Date: 2026-07-17
> URLs: `{print_url}`
> Print Format: `{print_format_name}` (set to default_print_language = "ไทย")

## Issue

Language selector keeps auto-selecting "en" even when:

1. Print Format `{print_format_name}` has `default_print_language` set to "ไทย"
2. Default Print Language in system is set to "ไทย"

## Root Cause

In `print.js` `set_default_print_language()`:

- The function was checking document language (`this.frm.doc.language`) BEFORE print format's `default_print_language`
- The `get_print_format()` function may not return custom fields like `default_print_language`
- User's GUI language (`frappe.boot.lang`) was overriding Print Format preference

## Fix Applied

1. **Always reload Print Format** via `frappe.client.get` to get `default_print_language`
2. **New priority order**:
   - Print Format's `default_print_language` (highest)
   - User's localStorage preference (preserve user choice)
   - Document's language
   - User's GUI language
   - Thai fallback

3. **Added `update_language_selectors()`** to sync all language selector UIs

## Files Changed

| File | Change |
|------|--------|
| `client_scripts/print.js` | Fixed `set_default_print_language()` priority |

## Debug Logging Added

```javascript
console.log('[Language Debug] Print format:', print_format_name);
console.log('[Language Debug] Print format default_print_language:', print_format?.default_print_language);
console.log('[Language Debug] Document language:', this.frm?.doc?.language);
```

## Verification Steps

1. Go to Print Format list: `/desk/print-format/{print_format_name}`
2. Confirm `default_print_language` is set to "ไทย"
3. Open document: `/desk/print/{doctype}/{docname}`
4. Check language selector shows "ไทย" (not "en")
5. Check console for debug logs showing `[Language Debug] Using print format language: ไทย`
