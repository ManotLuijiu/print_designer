# Minimax handoff: Receipt blank canvas

## Stop point

The dependency compatibility experiment is prepared but has **not been built or
browser-tested**. The exact next command is:

```bash
cd /home/frappe/frappe-bench
bench build --app print_designer
bench --site {site_name} clear-cache
```

Then run authenticated Playwright against:

`https://{site_name}/desk/print-designer/Receipt`

## Proven failure boundary

- Receipt data is valid and contains one page, header, footer, and elements.
- `ElementStore.Elements.length === 1` after loading.
- AppCanvas is mounted and sees the same store with one page.
- Normal DOM contains zero `.main-container` and `.margin-container` nodes.
- Adding a page changes store length to 2 but not the DOM.
- No AppPages component/VNode is created normally.
- Generated render code correctly uses
  `renderList($setup.ElementStore.Elements, ...)`.
- Store, state, and array all report reactive.
- Calling the AppCanvas component update manually immediately renders the full
  saved Receipt, proving data and AppPages are healthy.

Temporary console instrumentation confirms this sequence:

1. `[PrintDesigner:AppCanvas:pages] {storePages: 0}`
2. `[PrintDesigner:loadElements:start]`
3. `[PrintDesigner:loadElements:stored] {bodyPages: 1, storePages: 1}`
4. `[PrintDesigner:loadElements:complete] {storePages: 1}`
5. The AppCanvas watcher never runs again.

## Dependency hypothesis ready for verification

The previous generated bundle contained:

- Vue `3.5.12`
- inherited Pinia `2.1.7`

Official Pinia `2.3.1` declares Vue peer support `^2.7.0 || ^3.5.11`.

Local changes now explicitly pin:

- `vue: 3.5.12`
- `pinia: 2.3.1`

`yarn install --ignore-scripts` completed successfully and updated `yarn.lock`.
The permanent test passes:

```bash
python3 -m unittest print_designer.tests.test_frontend_dependencies -v
```

## Verification decision

After building the pinned dependencies:

- If the initial DOM has at least one page and Add Page updates the DOM, the
  dependency mismatch is confirmed. Remove all temporary `[PrintDesigner:*]`
  logs, rebuild, clear cache, and run the full verification checklist.
- If it remains blank, do not add `$forceUpdate` as the permanent fix. Verify the
  built bundle actually contains Pinia 2.3.1, then create a behavioral component
  test and continue tracing scheduler dependency links.

## Temporary instrumentation to remove after diagnosis

- `print_designer/public/js/print_designer/components/layout/AppCanvas.vue`
- `print_designer/public/js/print_designer/store/ElementStore.js`

## Current deployment

- Beta badge removal is deployed and visible.
- Current production bundle before the new dependency build:
  `print_designer.bundle.X3A2RXLC.js`
- It is instrumented and still blank without a manual forced render.
- Receipt database data has not been changed or saved.

## Preserve existing changes

Pre-existing fixes must remain:

- safe navbar selector/style restoration in `print_designer.bundle.js`
- AppPreviewPdf import in AppCanvas
- marquee lifecycle/null guards

Use `harness/checklists/receipt-production-verification.md` for final QA.

