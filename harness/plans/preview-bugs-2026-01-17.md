# Print Designer Preview Bugs & Feature Requests - 2026-01-17

## Bug 1: Header/Content/Footer Not Respected in Preview

**URL**: <https://aws-solution.bunchee.online/desk/print/Sales%20Invoice/BL6907-00001>
**Status**: ✅ FIXED
**Root Cause**: The print_format.html was using old styles when `pdf_generator != "chrome"`, which didn't have proper header/footer positioning CSS
**Fix Applied**: Changed print_format.html to always use `render_styles()` for Print Designer formats, regardless of `pdf_generator` value

## Bug 2: Watermark "None" Shows Error Message

**Status**: ✅ FIXED
**Root Cause**: `Watermark Settings` is a single doctype (is_single: 1) but no record exists
**Fix Applied**:

- Added checks for both DocType existence AND single record existence in watermark.py
- Created Watermark Settings record (`WMRK-SETTINGS-00001`)
- Fixed condition `watermark_settings == "None"` to `watermark_settings != "None"` to prevent dynamic watermark when user selects "None"

## Bug 3: Language Defaulting to "en" Instead of Print Format Setting

**Status**: ✅ FIXED
**Fix**: Added `set_default_print_language()` calls in print.js on init and format change

## Feature 4: Watermark Custom Margins

**Status**: ✅ IMPLEMENTED
**Fields added to Print Settings**:

- `watermark_margin_top` (default: "10mm")
- `watermark_margin_bottom` (default: "10mm")
- `watermark_margin_left` (default: "10mm")
- `watermark_margin_right` (default: "10mm")
**Rendering updated in**: `signature_stamp.py`, `printview_watermark.py`

## Bug 5: Watermark Shows Even When "None" Selected

**Status**: ✅ FIXED
**Root Cause**: Code checked `watermark_settings == "None"` to look for document field watermark
**Fix**: Changed to `watermark_settings != "None"` so dynamic watermark only used when watermark mode is selected

## Bug 6: Watermark Margin Changes Not Applied

**Status**: ✅ FIXED
**Root Cause**: Missing single record existence check in `print_designer/public/js/print_designer/api/watermark.py`
**Fix**: Added `frappe.db.exists("Watermark Settings", None)` check before calling `frappe.get_single()`

## Completed

- [x] Grid/Rulers toggle button (toolbar + G shortcut)
- [x] Delete Table option (right-click context menu)
- [x] Auto-delete table when last column deleted
- [x] Empty table CSS warning (red dashed border)
- [x] Watermark "None" error - checks for single record existence
- [x] Language default from print format
- [x] Watermark custom margin fields (created in Print Settings)
- [x] Watermark shows even when "None" - fixed condition
- [x] Header/Content/Footer positioning bug (Bug 1) - always use new styles
- [x] Border toggle icons highlighting (Bug 8) - use var(--icon-stroke)
- [x] Save button RAM optimization - debounced thumbnail generation
- [x] Border style icons (Solid/Dotted/Dashed) - 3 new SVG icons added
- [x] Border style selector (solid/dotted/dashed) - new feature
- [x] Border Toggle Help Button - "?" icon in toolbar shows explanation of 5 border toggles (All/L/R/T/B)

## Bug 7: SVG Sprite Icons Loaded in Properties Panel (DOM Bloat)

**URL**: <https://aws-solution.bunchee.online/desk/print-designer/Invoice%20-%20AWS%20Solution>
**Status**: TODO
**Description**: The `<svg id="printIcons">` sprite (containing all icon symbols like `layerPanel`, `borderAll`, `borderLeftStyle`, etc.) is being loaded INSIDE the properties panel (`<div class="properties-container app-sections properties-panel">`). This causes:

- Unnecessary DOM bloat in properties panel
- Multiple SVG sprite instances if component is rendered multiple times
- Potential memory issues

**Root Cause**: SVG sprite with `display: none` is included in the properties panel component

**Evidence**:

```html
<div class="properties-container app-sections properties-panel">
  <svg id="printIcons" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="display: none;">
    <symbol id="layerPanel" ...>
    <symbol id="borderAll" ...>
    <!-- 50+ more symbols -->
  </svg>
</div>
```

**Solution Options**:

1. Move SVG sprite to a single parent component (App.vue) that loads once
2. Use external SVG sprite file loaded via `<use href="/assets/...#symbolId">`
3. Dynamically load icons only when needed

## Bug 8: Border Toggle Icons All Look Same (Dark Theme)

**URL**: <https://aws-solution.bunchee.online/desk/print-designer/Invoice%20-%20AWS%20Solution>
**Status**: ✅ FIXED
**Description**: Border toggle icons (`borderAll`, `borderLeftStyle`, `borderRightStyle`, `borderTopStyle`, `borderBottomStyle`) all look the same in Dark theme. User cannot distinguish which border is active.

**Root Cause**: Icons used hardcoded `fill: var(--gray-100)` and `fill: var(--gray-300)` which become similar shades in Dark theme, making active state invisible.

**Fix Applied**: Changed all border icon paths to use `fill: var(--icon-stroke)` which responds to the color prop from `IconsUse` component:

- Inactive: `color="var(--gray-600)"` → gray border
- Active: `color="var(--primary-color)"` → blue border

**Files Changed**: `print_designer/public/js/print_designer/icons/Icons.vue`

## Performance: Save Button RAM Optimization

**Status**: ✅ IMPLEMENTED
**Description**: Save button was consuming excessive RAM due to html2canvas thumbnail generation blocking the main thread.

**Changes Made**:

1. Added debouncing (`thumbnailDebounceMs: 5000`) to skip thumbnail if saved within 5 seconds
2. Added `isGeneratingThumbnail` flag to prevent concurrent thumbnail generation
3. Made thumbnail generation async (runs in background after save completes)
4. Added `thumbnailEnabled` toggle for faster saves when thumbnail isn't needed

**Files Changed**:

- `MainStore.js` - added state variables
- `ElementStore.js` - optimized saveElements with debouncing

## Feature: Border Style Selector (Solid/Dotted/Dashed)

**Status**: ✅ IMPLEMENTED
**Description**: Added visual toggle buttons to select border style (solid, dotted, dashed).

**New SVG Icons**:

- `borderStyleSolid` - solid line
- `borderStyleDotted` - dotted line (stroke-dasharray="1,4")
- `borderStyleDashed` - dashed line (stroke-dasharray="6,4")

**UI Location**: Border section in Properties Panel, between borderRadius and border position toggles.

**Behavior**:

- Click icon to set border style
- Active icon highlighted in blue (`var(--primary-color)`)
- Inactive icons shown in gray (`var(--gray-500)`)
- Supports Dark/Light theme via `var(--icon-stroke)`

**Files Changed**:

- `Icons.vue` - added borderStyleSolid, borderStyleDotted, borderStyleDashed symbols
- `PropertiesPanelState.js` - added borderStyleIcons function and field definition

## Remaining

- Test all fixes on remote site
