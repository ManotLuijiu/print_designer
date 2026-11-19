/** Shared border rendering for Desk preview and standalone browser printview. */
function applyPDPreviewTableBorders(previewDocument) {
  if (!previewDocument) return;
  const cells = previewDocument.querySelectorAll(
    ["#tbs__print__page__preview #__print_designer", ".pd-browser-printview #__print_designer"]
      .flatMap((scope) => [
        `${scope} table.printTable > thead > tr > th[data-pd-preview-borders]`,
        `${scope} table.printTable > tbody > tr > td[data-pd-preview-borders]`,
      ]).join(","),
  );
  const intended = previewDocument.createElement("span").style;
  let paddingCells = 0;
  for (const cell of cells) {
    // Replace the legacy inline zero-width reset with the designer's borders.
    // Copy borders only: alignment, padding, sizing and fonts stay untouched.
    intended.cssText = cell.getAttribute("data-pd-preview-borders");
    for (const property of intended) {
      if (property === "border" || property.startsWith("border-")) {
        cell.style.setProperty(property, intended.getPropertyValue(property), "important");
      }
    }
    const row = cell.parentElement;
    if (row.dataset.pdRowKind === "padding") {
      paddingCells++;
      cell.style.setProperty("border-top-width", "0px", "important");
      cell.style.setProperty(
        "border-bottom-width", row.dataset.pdLastRow === "1" ? "1px" : "0px", "important",
      );
    }
  }
  console.log("[PD Preview Borders] Applied designer borders", {
    cells: cells.length, paddingCells,
  });
}

window.applyPDPreviewTableBorders = applyPDPreviewTableBorders;
