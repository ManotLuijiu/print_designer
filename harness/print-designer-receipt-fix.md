# Print Designer Receipt editor: runtime failure handoff

## Problem

Opening `/desk/print-designer/Receipt` mounts part of the Vue application, but initialization then fails and leaves the editor in a partially initialized state.

Primary console error:

```text
TypeError: Cannot read properties of null (reading 'style')
    at new PrintDesigner (print_designer.bundle.js)
```

Other reproducible errors/warnings:

```text
[Vue warn]: Failed to resolve component: AppPreviewPdf
TypeError: Cannot read properties of undefined (reading 'getBoundingClientRect')
    at MarqueeSelectionTool.js:107
```

The Vue hydration feature-flag warning, unused preload warnings, disabled Print Agent message, and socket.io authorization error are not the cause of the editor initialization failure.

## Root cause 1: unsafe navbar selector

File:

`print_designer/public/js/print_designer/print_designer.bundle.js`

The constructor mounts Vue and then assumes this selector always exists:

```js
let headerContainer = document.querySelector("header .container");
headerContainer.style.width = "100%";
```

On the current TBS/Frappe Desk layout, `header .container` can be absent. Accessing `headerContainer.style` throws after the Vue app has mounted. This explains why some controls or the canvas may appear while the editor remains broken.

### Required change

- Do not make successful editor initialization depend on navbar markup.
- Resolve the current navbar element with a narrow selector, preferably `.navbar .container` with `header .container` only as a compatibility fallback.
- Guard all style reads/writes when no matching element exists.
- Restore only the original inline style values on route change. Do not reset properties to arbitrary values such as `null` or `auto`, because that can overwrite styles owned by another application extension.
- Always unmount the Vue app on route change even when no navbar element was found.

Suggested structure:

```js
const headerContainer =
	document.querySelector(".navbar .container") ||
	document.querySelector("header .container");

const originalHeaderStyles = headerContainer
	? {
		width: headerContainer.style.width,
		minWidth: headerContainer.style.minWidth,
		userSelect: headerContainer.style.userSelect,
	  }
	: null;

if (headerContainer) {
	headerContainer.style.width = "100%";
	headerContainer.style.minWidth = "100%";
	headerContainer.style.userSelect = "none";
}

frappe.router.once("change", () => {
	if (headerContainer && originalHeaderStyles) {
		Object.assign(headerContainer.style, originalHeaderStyles);
	}
	app.unmount();
});
```

Do not solve this by adding a fake `.container` element to the page.

## Root cause 2: missing component import

File:

`print_designer/public/js/print_designer/components/layout/AppCanvas.vue`

The template renders:

```vue
<AppPreviewPdf v-if="MainStore.mode == 'preview'" />
```

The component exists at:

`print_designer/public/js/print_designer/components/layout/AppPreviewPdf.vue`

but it is not imported by the `<script setup>` block.

### Required change

Add:

```js
import AppPreviewPdf from "./AppPreviewPdf.vue";
```

No manual component registration is needed with Vue `<script setup>`.

## Root cause 3: marquee handler assumes every page is mounted

File:

`print_designer/public/js/print_designer/composables/MarqueeSelectionTool.js`

The mouse-up handler calls:

```js
const pageRect = page.DOMRef.getBoundingClientRect();
```

`DOMRef` is intentionally initialized as `null`, and a page may be unmounted or not yet mounted during initialization, mode changes, or route teardown. The handler must tolerate that lifecycle state.

The same block assigns to undeclared variable `a`:

```js
a = { ...canvas };
```

This is a second latent exception in ES-module strict mode.

### Required change

- Return safely if the directive canvas is unavailable during teardown.
- Skip any page whose `DOMRef` is missing or does not expose `getBoundingClientRect`.
- Declare the page-relative selection bounds locally with `const`.
- Ensure marquee cleanup still occurs when no eligible pages exist.
- In the directive `unmounted` hook, guard `canvas` before removing listeners and reset local state.

Core loop should follow this shape:

```js
for (const page of ElementStore.Elements) {
	if (!page?.DOMRef?.getBoundingClientRect) continue;

	const pageRect = page.DOMRef.getBoundingClientRect();
	const relativeBounds = { ...selectionBounds };
	relativeBounds.x -= pageRect.x;
	relativeBounds.y -= pageRect.y;

	// Existing child hit-testing, using relativeBounds.
}
```

Avoid reusing the name `canvas` for both the directive DOM node and the selection-bounds object. Rename the bounds object to `selectionBounds` to prevent shadowing and teardown mistakes.

## Recommended implementation scope

Only these source files should need changes:

1. `print_designer/public/js/print_designer/print_designer.bundle.js`
2. `print_designer/public/js/print_designer/components/layout/AppCanvas.vue`
3. `print_designer/public/js/print_designer/composables/MarqueeSelectionTool.js`

Do not modify Frappe core or Thai Business Suite navbar code to accommodate this app.

## Validation

### Static checks

- Confirm `AppCanvas.vue` imports `AppPreviewPdf`.
- Confirm there is no unconditional `.style` access on a `querySelector` result.
- Confirm there is no assignment to undeclared `a` in `MarqueeSelectionTool.js`.
- Confirm all `page.DOMRef.getBoundingClientRect()` calls in the marquee handler are lifecycle-safe.

### Browser checks

1. Open `/desk/print-designer/Receipt` from a fresh Desk session.
2. Confirm there is no `PrintDesigner` constructor rejection.
3. Confirm there is no `Failed to resolve component: AppPreviewPdf` warning.
4. Drag-select across empty canvas space and across existing elements.
5. Click without dragging several times; no marquee exception should occur.
6. Add a page and repeat selection before and after the new page renders.
7. Enter PDF preview mode and confirm the preview component renders.
8. Exit the editor and confirm navbar width and text selection return to their exact prior inline values.
9. Re-enter the same editor without a full page refresh to detect leaked listeners or stale Vue mounts.

### Build/deployment checks

After source changes, rebuild the app assets using the bench command appropriate for this installation, then clear Frappe caches and force-refresh the browser. Verify that the served `print_designer.bundle.js` contains the null guard; otherwise an old hashed/cached asset can make a correct source change appear ineffective.

## Acceptance criteria

- Receipt editor loads without an unhandled promise rejection.
- Canvas and property controls remain functional after initialization.
- PDF preview resolves and renders.
- Marquee selection never calls `getBoundingClientRect` on a missing page reference.
- Repeated route entry/exit does not leak event listeners or leave navbar styles changed.
- No Frappe core changes are required.
