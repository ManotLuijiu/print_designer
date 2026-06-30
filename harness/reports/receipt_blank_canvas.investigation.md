# Receipt blank canvas investigation report

## Result so far

The blank canvas is not caused by deleted or corrupt Receipt data. The server
returns the complete design and `ElementStore` contains it, but Vue creates no
page DOM nodes. The failure boundary is between AppCanvas render evaluation and
AppPages component creation.

## Production evidence

| Check | Result |
|---|---|
| Page identity | PASS — Receipt / TBS |
| Editor shell | PASS |
| Receipt API payload | PASS — one saved page |
| ElementStore load | PASS — one page, header, footer |
| Canvas page DOM | FAIL — zero pages |
| Add-page store mutation | PASS — length becomes two |
| Add-page DOM mutation | FAIL — remains zero |
| Page errors | PASS — none |
| Failed requests | PASS — none |
| HTTP errors | PASS — none |

## Build/deployment state

- A diagnostic build produced
  `print_designer.bundle.YO7Q7UL5.js` and was served by production.
- That build included a `storeToRefs` experiment; production still rendered zero
  pages, disproving that hypothesis.
- Source was subsequently reverted, but a final rebuild after the revert has not
  yet been run.
- `AppHeader.vue` now removes the Beta badge in source.
- The Beta badge regression test passes, but that change also awaits the final
  rebuild.

## Existing user changes

Before this session, the worktree already contained changes in:

- `components/layout/AppCanvas.vue`: import `AppPreviewPdf`
- `composables/MarqueeSelectionTool.js`: lifecycle/null guards
- `print_designer.bundle.js`: safe navbar selector/style restoration

These address older reproducible errors and must be preserved.

## Next investigation checkpoint

Inspect the live Vue vnode/component tree and generated render function. If
AppPages VNodes do not exist despite `setupState.ElementStore.Elements.length ===
1`, the generated render function or SFC build/cache is the primary suspect. If
VNodes exist but are unmounted, trace the component scheduler and AppPages root.

