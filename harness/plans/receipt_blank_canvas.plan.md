# Receipt blank canvas repair plan

## Objective

Restore `/desk/print-designer/Receipt` without modifying or recreating the saved
Receipt design, remove the obsolete **Beta** badge, and verify the deployed result
with Playwright.

## Verified production state (2026-06-29)

- Site: `https://{site_name}/desk/print-designer/Receipt`
- Site is hosted by this bench: `sites/{site_name}`.
- Authentication works with the user-provided Administrator account. Do not store
  the password in this repository or harness.
- The served Print Format is intact:
  - `doc_type`: `Payment Entry`
  - `print_designer_body`: valid JSON containing one page and multiple elements
  - one header and one footer are present
  - `print_designer_after_table` is `null` and is not the cause
- Live Pinia state after load:
  - `MainStore.doctype = "Payment Entry"`
  - `MainStore.metaFields.length = 172`
  - `ElementStore.Elements.length = 1`
  - `ElementStore.Headers.length = 1`
  - `ElementStore.Footers.length = 1`
- Rendered DOM after load:
  - `.main-container`: 0
  - `.margin-container`: 0
  - `#canvas`: present, with only the page-button wrapper
- Clicking **Add New Page** without saving changes store length from 1 to 2, but
  rendered page count remains 0.
- AppCanvas sees the same store instance and sees one element in setup state.
- No page exception, failed request, HTTP >= 400 response, or framework overlay.

## Disproven hypotheses

1. Corrupt/missing Receipt data — false; the payload is valid and loaded.
2. Malformed `print_designer_after_table` — false; it is `null`.
3. Pinia subscription fixed by `storeToRefs` — false. A build using explicit
   `storeToRefs(ElementStore)` still rendered zero pages. The experiment was
   reverted from source and its temporary test removed.

## Remaining tasks

1. Capture the Vue component tree after load and determine whether any
   `AppPages` component instance is created.
2. Inspect the compiled AppCanvas render function in the generated bundle and
   compare it with the Vue source. Confirm whether the `v-for` is compiled and
   whether a stale/cached SFC artifact is being used.
3. Compare current Frappe Vue/compiler/Pinia versions with the last known working
   asset build or deployment. The sudden regression is consistent with a build
   or compiler boundary change, but this is not yet proven.
4. Add a behavioral regression test that mounts AppCanvas with an ElementStore
   containing one page and asserts one AppPages root is rendered. Avoid another
   source-text-only test for the blank canvas.
5. Implement only the root-cause fix, rebuild, clear the target site cache, and
   verify initial page count is at least 1 before any interaction.
6. Verify page content, drag selection, PDF preview, exit/re-entry, navbar style
   restoration, and absence of relevant console errors.
7. Verify the **Beta** badge is absent after the final rebuild.

## Commands

```bash
python3 -m unittest print_designer.tests.test_print_designer_header_source -v
bench build --app print_designer
bench --site {site_name} clear-cache
```

Use `/tmp/diagnose_receipt.py` only if it still exists. It is temporary and must
not be committed. It writes `/tmp/receipt-diagnostic.json` and
`/tmp/receipt-blank.png`.

## Safety constraints

- Do not click **Save** while the canvas is blank; this could overwrite the valid
  persisted design with an empty client state.
- Do not migrate, modify the Receipt database row, or recreate the Print Format.
- Preserve all pre-existing uncommitted changes.
- Do not push, commit, or deploy outside this bench without explicit approval.

