# Minimax final checkpoint — 2026-06-29

## Current production state

- The blank Receipt canvas is fixed after explicitly pinning:
  - Vue `3.5.12`
  - Pinia `2.3.1`
- User confirmed the Receipt renders.
- Root cause evidence: inherited Pinia `2.1.7` did not notify Vue `3.5.12`
  component effects. After Pinia 2.3.1, console showed AppCanvas react from
  `storePages: 0` to `storePages: 1`, and AppPages rendered.
- Beta badge is removed.
- Header source is now centered with `left: 50%` and
  `transform: translateX(-50%)`.
- Temporary `[PrintDesigner:*]` console instrumentation is removed from source.

## Latest build

Build and cache clear completed successfully:

```text
print_designer.bundle.LONM7DFB.js
print_designer.bundle.5JPM3HQF.css
```

The target site cache was cleared by the combined build command. Browser
verification of this latest centered-header bundle has **not yet been run**.

## Immediate next action

Run `/tmp/diagnose_receipt.py` with the user-provided Administrator credential.
The temporary script now records `header_box`; verify:

- `dom_state.pages >= 1` before its forced-render probe
- `header_box.center == header_box.viewport` (within 1 pixel)
- served bundle is `print_designer.bundle.LONM7DFB.js`
- no `[PrintDesigner:*]` console messages
- no page errors or failed requests

The script performs an unsaved Add Page interaction. Do not click Save.

## Permanent tests

```bash
python3 -m unittest \
  print_designer.tests.test_frontend_dependencies \
  print_designer.tests.test_print_designer_header_source -v
```

All three current tests passed before the latest successful build:

- Vue/Pinia explicit compatible pins
- Beta badge absent
- header centered in viewport CSS

## Remaining warnings (non-blocking, separate work)

- `BaseDynamicTextSpanTag` receives undefined `index` in table preview rows.
- Vue hydration feature flag is not injected by the build.
- socket.io Unauthorized/fetch failure.
- Print Agent disabled by settings.
- unused image preload warnings.

Do not mix those warning cleanups into this verified dependency fix without
separate tests.

## Policy/documentation

`AGENTS.md` now records the Vue/Pinia compatibility policy and required
Playwright verification for future dependency changes.

## Important source integrity note

During cleanup, a broad temporary sed command removed three watchEffect openings
from AppCanvas. The build caught it, all three openings were restored, and the
subsequent build succeeded. Do not repeat that cleanup. Inspect `git diff` and
preserve the existing AppPreviewPdf, marquee, and navbar fixes.

