<template>
  <div class="drag-paint-controls" v-if="element">
    <div class="paint-modes">
      <button
        class="btn btn-xs"
        :class="{ 'btn-success': paintMode === 'on', 'btn-default': paintMode !== 'on' }"
        @click="startPaint('on')"
        :disabled="isPainting"
      >
        {{ __("Paint On") }}
      </button>
      <button
        class="btn btn-xs"
        :class="{ 'btn-danger': paintMode === 'off', 'btn-default': paintMode !== 'off' }"
        @click="startPaint('off')"
        :disabled="isPainting"
      >
        {{ __("Paint Off") }}
      </button>
      <button
        class="btn btn-xs"
        :class="{ 'btn-warning': paintMode === 'toggle', 'btn-default': paintMode !== 'toggle' }"
        @click="startPaint('toggle')"
        :disabled="isPainting"
      >
        {{ __("Toggle") }}
      </button>
    </div>
    <div v-if="isPainting" class="painting-status">
      <span class="badge badge-info">{{ __("Drag to paint") }}</span>
      <button class="btn btn-xs btn-secondary" @click="stopPaint">
        {{ __("Done") }}
      </button>
    </div>
    <div class="help-text">
      {{ __("Click and drag on cells to apply border changes") }}
    </div>
  </div>
</template>

<script setup>
import { computed, onUnmounted } from "vue";
import { useMainStore } from "../../store/MainStore";
import { getConditonalObject } from "../../utils";

const MainStore = useMainStore();

const element = computed(() => MainStore.getCurrentElementsValues[0]);

const paintMode = computed(() => MainStore.borderPaintMode || "toggle");
const isPainting = computed(() => MainStore.isBorderPainting || false);

const startPaint = (mode) => {
  MainStore.isBorderPainting = true;
  MainStore.borderPaintMode = mode;
  MainStore.borderPaintTarget = null;

  // Add document-level listeners
  document.addEventListener("mouseup", stopPaint);
  document.addEventListener("mouseover", handlePaint);

  frappe.show_alert({
    message: __("Border paint mode:") + " " + __(mode),
    indicator: "info",
  });
};

const stopPaint = () => {
  MainStore.isBorderPainting = false;
  MainStore.borderPaintMode = "toggle";
  MainStore.borderPaintTarget = null;

  document.removeEventListener("mouseup", stopPaint);
  document.removeEventListener("mouseover", handlePaint);
};

const handlePaint = (e) => {
  if (!MainStore.isBorderPainting) return;

  // Find the cell element
  const cell = e.target.closest("th, td");
  if (!cell) return;

  // Prevent processing same cell multiple times in one drag
  if (MainStore.borderPaintTarget === cell) return;
  MainStore.borderPaintTarget = cell;

  // Get cell index to determine which border to paint
  const row = cell.parentElement;
  const cells = Array.from(row.children);
  const cellIndex = cells.indexOf(cell);
  const isFirstCell = cellIndex === 0;
  const isLastCell = cellIndex === cells.length - 1;
  const isHeaderRow = row.parentElement.tagName === "THEAD";

  // Get style object
  const el = element.value;
  if (!el) return;

  let style;
  if (isHeaderRow) {
    style = el.columns?.[cellIndex]?.style || el.headerStyle;
  } else {
    style = el.columns?.[cellIndex]?.style || el.style;
  }

  if (!style) return;

  // Determine which border to paint based on position
  let borderProp;
  if (isFirstCell) borderProp = "borderLeftStyle";
  else if (isLastCell) borderProp = "borderRightStyle";

  if (!borderProp) return;

  // Apply based on paint mode
  switch (MainStore.borderPaintMode) {
    case "on":
      delete style[borderProp];
      style[borderProp] = "solid";
      break;
    case "off":
      style[borderProp] = "hidden";
      break;
    case "toggle":
      if (style[borderProp] === "hidden") {
        delete style[borderProp];
        style[borderProp] = "solid";
      } else {
        style[borderProp] = "hidden";
      }
      break;
  }
};

onUnmounted(() => {
  // Cleanup on component unmount
  document.removeEventListener("mouseup", stopPaint);
  document.removeEventListener("mouseover", handlePaint);
});
</script>

<style scoped>
.drag-paint-controls {
  padding: 8px;
}

.paint-modes {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
}

.paint-modes .btn {
  flex: 1;
  font-size: 11px;
  padding: 4px 6px;
}

.painting-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  padding: 4px 8px;
  background: var(--yellow-100);
  border-radius: 4px;
}

.help-text {
  font-size: 10px;
  color: var(--text-muted);
  text-align: center;
}
</style>
