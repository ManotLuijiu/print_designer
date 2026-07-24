<template>
	<div class="watermark-panel">
		<div class="panel-header">
			<strong>{{ __("Watermark Settings") }}</strong>
			<span class="close-btn" @click="MainStore.isWatermarkPanelEnabled = false">&times;</span>
		</div>
		
		<div class="panel-content">
			<!-- Watermark Mode -->
			<div class="form-group">
				<label>{{ __("Watermark Mode") }}</label>
				<select v-model="MainStore.watermark.mode">
					<option value="None">{{ __("None") }}</option>
					<option value="Original on First Page">{{ __("Original on First Page") }}</option>
					<option value="Copy on All Pages">{{ __("Copy on All Pages") }}</option>
					<option value="Original,Copy on Sequence">{{ __("Original,Copy on Sequence") }}</option>
				</select>
			</div>

			<!-- Custom Text -->
			<div class="form-group" v-if="MainStore.watermark.mode !== 'None'">
				<label>{{ __("Custom Text") }}</label>
				<input type="text" v-model="MainStore.watermark.custom_text" :placeholder="__('Optional: Custom watermark text')" />
			</div>

			<!-- Position -->
			<div class="form-group" v-if="MainStore.watermark.mode !== 'None'">
				<label>{{ __("Position") }}</label>
				<select v-model="MainStore.watermark.position">
					<option value="Top Left">{{ __("Top Left") }}</option>
					<option value="Top Right">{{ __("Top Right") }}</option>
					<option value="Center">{{ __("Center") }}</option>
					<option value="Bottom Left">{{ __("Bottom Left") }}</option>
					<option value="Bottom Right">{{ __("Bottom Right") }}</option>
				</select>
			</div>

			<!-- Margin -->
			<div class="form-group" v-if="MainStore.watermark.mode !== 'None'">
				<label>{{ __("Margin (mm)") }}</label>
				<div class="margin-inputs">
					<div class="margin-row">
						<div class="margin-field">
							<label>Top</label>
							<input type="number" v-model.number="MainStore.watermark.top" min="0" max="50" />
						</div>
						<div class="margin-field">
							<label>Bottom</label>
							<input type="number" v-model.number="MainStore.watermark.bottom" min="0" max="50" />
						</div>
					</div>
					<div class="margin-row">
						<div class="margin-field">
							<label>Left</label>
							<input type="number" v-model.number="MainStore.watermark.left" min="0" max="50" />
						</div>
						<div class="margin-field">
							<label>Right</label>
							<input type="number" v-model.number="MainStore.watermark.right" min="0" max="50" />
						</div>
					</div>
				</div>
			</div>

			<!-- Font Family -->
			<div class="form-group" v-if="MainStore.watermark.mode !== 'None'">
				<label>{{ __("Font") }}</label>
				<select v-model="MainStore.watermark.font_family">
					<option value="Sarabun">Sarabun</option>
					<option value="Kanit">Kanit</option>
					<option value="Prompt">Prompt</option>
					<option value="Noto Sans Thai">Noto Sans Thai</option>
				</select>
			</div>

			<!-- Font Size -->
			<div class="form-group" v-if="MainStore.watermark.mode !== 'None'">
				<label>{{ __("Font Size") }}: {{ MainStore.watermark.font_size }}px</label>
				<input type="range" v-model.number="MainStore.watermark.font_size" min="12" max="72" step="2" />
			</div>

			<!-- Font Color -->
			<div class="form-group" v-if="MainStore.watermark.mode !== 'None'">
				<label>{{ __("Color") }}</label>
				<input type="color" v-model="MainStore.watermark.font_color" />
			</div>

			<!-- Opacity -->
			<div class="form-group" v-if="MainStore.watermark.mode !== 'None'">
				<label>{{ __("Opacity") }}: {{ Math.round(MainStore.watermark.opacity * 100) }}%</label>
				<input type="range" v-model.number="MainStore.watermark.opacity" min="0.1" max="1" step="0.1" />
			</div>

			<!-- Save Button -->
			<div class="form-group" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border-color);">
				<button class="btn btn-primary" style="width: 100%;" @click="saveWatermarkSettings">
					{{ __("Save Watermark Settings") }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { useMainStore } from "../../store/MainStore";
import { useElementStore } from "../../store/ElementStore";

const MainStore = useMainStore();
const ElementStore = useElementStore();

const saveWatermarkSettings = async () => {
	try {
		await ElementStore.saveElements();
		frappe.show_alert({
			message: __("Watermark Settings Saved"),
			indicator: "green",
		}, 3);
	} catch (error) {
		console.error("[WatermarkPanel] Error saving watermark settings:", error);
		frappe.show_alert({
			message: __("Error saving watermark settings"),
			indicator: "red",
		}, 5);
	}
};
</script>

<style scoped>
.watermark-panel {
	position: absolute;
	left: 48px;
	top: 80px;
	background: var(--bg-color);
	border: 1px solid var(--border-color);
	border-radius: var(--border-radius-md);
	padding: 12px;
	width: 260px;
	z-index: 9999;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.panel-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 12px;
	padding-bottom: 8px;
	border-bottom: 1px solid var(--border-color);
}

.panel-header strong {
	color: var(--text-color);
	font-size: 13px;
}

.close-btn {
	cursor: pointer;
	font-size: 18px;
	color: var(--text-muted);
	line-height: 1;
}

.close-btn:hover {
	color: var(--text-color);
}

.panel-content {
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.form-group {
	display: flex;
	flex-direction: column;
	gap: 4px;
}

.form-group label {
	font-size: 11px;
	color: var(--text-muted);
	font-weight: 500;
}

.form-group select,
.form-group input[type="text"] {
	padding: 6px 8px;
	border: 1px solid var(--border-color);
	border-radius: var(--border-radius-sm);
	background: var(--bg-color);
	color: var(--text-color);
	font-size: 12px;
}

.form-group input[type="range"] {
	width: 100%;
}

.form-group input[type="color"] {
	width: 100%;
	height: 30px;
	border: 1px solid var(--border-color);
	border-radius: var(--border-radius-sm);
	cursor: pointer;
}

.margin-inputs {
	display: flex;
	flex-direction: column;
	gap: 6px;
}

.margin-row {
	display: flex;
	gap: 8px;
}

.margin-field {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 2px;
}

.margin-field label {
	font-size: 10px;
	color: var(--text-muted);
}

.margin-field input[type="number"] {
	width: 100%;
	padding: 4px 6px;
	border: 1px solid var(--border-color);
	border-radius: var(--border-radius-sm);
	background: var(--bg-color);
	color: var(--text-color);
	font-size: 12px;
}
</style>
