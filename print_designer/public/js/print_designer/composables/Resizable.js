import interact from "@interactjs/interact";
import "@interactjs/actions/resize";
import "@interactjs/auto-start";
import "@interactjs/modifiers";
import { useMainStore } from "../store/MainStore";
import { useElementStore } from "../store/ElementStore";
import {
  recursiveChildrens,
  checkUpdateElementOverlapping,
  getParentPage,
} from "../utils";

export function useResizable({
  element,
  resizeMoveListener,
  resizeStartListener,
  resizeStopListener,
  restrict = "parent",
}) {
  if (element && restrict) {
    if (
      interact.isSet(element.DOMRef) &&
      interact(element.DOMRef).resizable().enabled
    ) {
      return;
    }
    const MainStore = useMainStore();
    const ElementStore = useElementStore();
    const edges = {
      bottom: ".resize-bottom",
    };
    if (!element.relativeContainer) {
      edges.left = ".resize-left";
      edges.right = ".resize-right";
      edges.top = ".resize-top";
    }
    interact(element.DOMRef)
      .resizable({
        ignoreFrom: ".resizer",
        edges: edges,
        modifiers: [
          interact.modifiers.restrictEdges(),
          interact.modifiers.snapEdges({
            targets: MainStore.snapEdges,
          }),
        ],
        listeners: {
          move: resizeMoveListener,
        },
      })
      .on("resizestart", resizeStartListener)
      .on("resizeend", function (e) {
        resizeStopListener && resizeStopListener(e);
        if (element.DOMRef.className == "modal-dialog modal-sm") {
          return;
        }
        checkUpdateElementOverlapping(element);

        // Sync minRows for table elements after resize
        if (
          element.type === "table" &&
          element.columns &&
          element.columns.length > 0
        ) {
          const tableEl = element.DOMRef;
          if (!tableEl) return;

          // Measure the table's ACTUAL rendered height from the DOM
          // (getBoundingClientRect returns CSS pixels, same unit as canvas)
          const tableRect = tableEl.getBoundingClientRect();
          if (!tableRect || !tableRect.height) return;

          const totalRenderedHeight = tableRect.height;

          // Get header height (thead is always present when columns exist)
          const headerRow = tableEl.querySelector("thead tr");
          const headerHeightPx = headerRow
            ? headerRow.getBoundingClientRect().height || 0
            : 0;

          // Get a data row height if available; otherwise use the reserved-row
          const dataRow = tableEl.querySelector("tbody tr:not(.reserved-row)");
          const reservedRow = tableEl.querySelector("tbody tr.reserved-row");
          const sampleRow = dataRow || reservedRow;

          let rowHeightPx = 30; // fallback
          if (sampleRow) {
            rowHeightPx = sampleRow.getBoundingClientRect().height || 30;
          }

          // Content height = total rendered - header
          const contentHeightPx = totalRenderedHeight - headerHeightPx;
          if (contentHeightPx <= 0 || rowHeightPx <= 0) return;

          const calculatedMinRows = Math.max(
            0,
            Math.round(contentHeightPx / rowHeightPx),
          );

          // Only update if different from current value
          if (element.minRows !== calculatedMinRows) {
            element.minRows = calculatedMinRows;

            // Sync to form field
            if (MainStore.frappeControls["min_rows"]) {
              MainStore.frappeControls["min_rows"].set_value(calculatedMinRows);
            }
          }
        }

        if (element.parent == e.target.piniaElementRef.parent) return;
        if (
          !e.dropzone &&
          e.target.piniaElementRef.parent.type != "page" &&
          !MainStore.lastCloned
        ) {
          let splicedElement;
          let currentRect = e.target.getBoundingClientRect();
          let canvasRect = getParentPage(
            e.target.piniaElementRef.parent,
          ).DOMRef.getBoundingClientRect();
          let currentParent = e.target.piniaElementRef.parent;
          if (currentParent.type == "page") {
            splicedElement = currentParent.splice(
              e.target.piniaElementRef.index,
              1,
            )[0];
          } else {
            splicedElement = currentParent.childrens.splice(
              e.target.piniaElementRef.index,
              1,
            )[0];
          }
          splicedElement = { ...splicedElement };
          splicedElement.startX = currentRect.left - canvasRect.left;
          splicedElement.startY = currentRect.top - canvasRect.top;
          splicedElement.parent = ElementStore.Elements;
          recursiveChildrens({ element: splicedElement, isClone: false });
          ElementStore.Elements.push(splicedElement);
          let droppedElement = new Object();
          droppedElement[splicedElement.id] = splicedElement;
          MainStore.isDropped = droppedElement;
        }
      });
  }

  return;
}
