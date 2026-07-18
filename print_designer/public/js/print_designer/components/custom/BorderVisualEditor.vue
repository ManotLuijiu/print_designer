<template>
  <div class="border-visual-editor" v-if="element">
    <div class="border-grid">
      <div class="grid-cell top-left" @click="toggle('TL')">
        <span :class="{ 'border-active': isActive('TL') }">TL</span>
      </div>
      <div class="grid-cell top" @click="toggle('T')">
        <span :class="{ 'border-active': isActive('T') }">T</span>
      </div>
      <div class="grid-cell top-right" @click="toggle('TR')">
        <span :class="{ 'border-active': isActive('TR') }">TR</span>
      </div>
      <div class="grid-cell left" @click="toggle('L')">
        <span :class="{ 'border-active': isActive('L') }">L</span>
      </div>
      <div class="grid-cell center">
        <span class="cell-icon">⊞</span>
      </div>
      <div class="grid-cell right" @click="toggle('R')">
        <span :class="{ 'border-active': isActive('R') }">R</span>
      </div>
      <div class="grid-cell bottom-left" @click="toggle('BL')">
        <span :class="{ 'border-active': isActive('BL') }">BL</span>
      </div>
      <div class="grid-cell bottom" @click="toggle('B')">
        <span :class="{ 'border-active': isActive('B') }">B</span>
      </div>
      <div class="grid-cell bottom-right" @click="toggle('BR')">
        <span :class="{ 'border-active': isActive('BR') }">BR</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useMainStore } from "../../store/MainStore";
import { getConditonalObject } from "../../utils";

const MainStore = useMainStore();

// Map side to property name
const propMap = {
  TL: "borderTopLeftStyle",
  T: "borderTopStyle",
  TR: "borderTopRightStyle",
  L: "borderLeftStyle",
  R: "borderRightStyle",
  B: "borderBottomStyle",
  BL: "borderBottomLeftStyle",
  BR: "borderBottomRightStyle",
};

const element = computed(() => MainStore.getCurrentElementsValues[0]);

const getStyle = () => {
  if (!element.value) return {};
  return getConditonalObject({
    reactiveObject: () => element.value,
    isStyle: true,
  }) || {};
};

const isActive = (side) => {
  const style = getStyle();
  const prop = propMap[side];
  if (!style || !prop) return false;
  // Active if: has border style AND NOT hidden
  const value = style[prop];
  return value && value !== "hidden";
};

const toggle = (side) => {
  const style = getStyle();
  const prop = propMap[side];
  if (!style || !prop) return;

  const isHidden = style[prop] === "hidden";
  if (isHidden) {
    // Remove hidden or set to solid
    delete style[prop];
    style[prop] = "solid";
  } else {
    style[prop] = "hidden";
  }
};
</script>

<style scoped>
.border-visual-editor {
  padding: 8px;
}

.border-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(3, 1fr);
  gap: 2px;
  width: 80px;
  height: 80px;
  margin: 0 auto;
  background: var(--gray-100);
  border: 1px solid var(--border-color);
  border-radius: 4px;
}

.grid-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 10px;
  font-weight: 600;
  color: var(--text-muted);
  background: var(--bg-color);
  transition: all 0.15s ease;
  user-select: none;
}

.grid-cell:hover {
  background: var(--gray-200);
}

.grid-cell span {
  padding: 2px 4px;
  border-radius: 2px;
}

.grid-cell span.border-active {
  background: var(--primary-color);
  color: white;
}

.cell-icon {
  color: var(--gray-400);
  font-size: 14px;
}
</style>
