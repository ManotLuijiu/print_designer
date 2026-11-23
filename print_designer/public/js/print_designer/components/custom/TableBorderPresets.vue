<template>
	<div class="table-border-presets">
		<div class="preset-heading">
			<span>{{ __("Table grid") }}</span>
			<button v-if="table.borderPreset" class="preset-custom" type="button" @click="delete table.borderPreset">
				{{ __("Custom") }}
			</button>
		</div>
		<div class="preset-options" role="group" :aria-label="__('Table grid')">
			<button
				v-for="preset in presets"
				:key="preset.value"
				type="button"
				:aria-pressed="table.borderPreset === preset.value"
				:title="preset.description"
				@click="table.borderPreset = preset.value"
			>
				<span class="preset-icon" :data-pattern="preset.value" aria-hidden="true"></span>
				<span>{{ preset.label }}</span>
			</button>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { useMainStore } from "../../store/MainStore";

const MainStore = useMainStore();
const table = computed(() => MainStore.getCurrentElementsValues[0]);
const presets = [
	{ value: "no-grid", label: __("No Grid"), description: __("Hide all table borders") },
	{ value: "full-grid", label: __("Full Grid"), description: __("Show the outline, column dividers, and row separators") },
	{ value: "outline", label: __("Outline Only"), description: __("Show only the outside border") },
	{ value: "horizontal", label: __("Horizontal"), description: __("Show row separators and the top and bottom edges") },
];
</script>

<style scoped>
.table-border-presets {
	width: 100%;
}

.preset-heading {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 6px;
	font-size: 11px;
	font-weight: 600;
}

.preset-custom {
	padding: 0 2px;
	border: 0;
	background: none;
	color: var(--text-muted);
	font-size: inherit;
	text-decoration: underline;
}

.preset-options {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 5px;
}

.preset-options button {
	display: flex;
	align-items: center;
	gap: 6px;
	min-height: 34px;
	padding: 4px 6px;
	border: 1px solid var(--border-color);
	border-radius: 5px;
	background: var(--card-bg);
	color: var(--text-color);
	font-size: 11px;
	line-height: 1.2;
	text-align: start;
}

.preset-options button:hover {
	background: var(--subtle-fg);
}

.preset-options button[aria-pressed="true"] {
	border-color: var(--primary-color);
	background: var(--primary-color);
	color: white;
}

button:focus-visible {
	outline: 2px solid var(--primary-color);
	outline-offset: 2px;
}

.preset-icon {
	box-sizing: border-box;
	width: 16px;
	height: 13px;
	flex: none;
	border: 1px solid currentColor;
}

.preset-icon[data-pattern="no-grid"] {
	border-style: dotted;
	opacity: 0.55;
}

.preset-icon[data-pattern="full-grid"],
.preset-icon[data-pattern="horizontal"] {
	background: linear-gradient(currentColor, currentColor) center / 100% 1px no-repeat;
}

.preset-icon[data-pattern="full-grid"] {
	background:
		linear-gradient(currentColor, currentColor) center / 100% 1px no-repeat,
		linear-gradient(currentColor, currentColor) center / 1px 100% no-repeat;
}

.preset-icon[data-pattern="horizontal"] {
	border-inline: 0;
}
</style>
