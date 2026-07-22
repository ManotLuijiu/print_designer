<template>
	<Icons />
	<div class="sidebar" v-bind="attrs">
		<div class="toolbar-section mt-3">
			<div>
				<template
					v-for="({ id, aria_label, icon, isDisabled }, key) in MainStore.controls"
					:key="id"
				>
					<span
						v-if="!isDisabled"
						:key="id"
						:title="aria_label"
						:class="iconClasses(id, icon)"
						@click="MainStore.setActiveControl(key)"
					>
						<svg :viewBox="`0 0 24 24`" width="16" height="16">
							<use
								:href="`#${icon}`"
								:style="[
									MainStore.activeControl == id
											? `--icon-stroke: white; fill: white`
												: `--icon-stroke: var(--text-muted)`,
										]"
									/>
							</svg>
						</span>
					</template>
			</div>
			<div class="toolbar-divider"></div>
			<IconsUse
				name="layerPanel"
				key="layerPanel"
				:size="32"
				:padding="8"
				:color="MainStore.isLayerPanelEnabled ? 'white' : 'var(--text-muted)'"
				:class="['tool-icons', { 'active-toggle-icon': MainStore.isLayerPanelEnabled }]"
				:title="__('Layers Panel')"
				@click="console.log('[Toolbar] Layer clicked, isLayerPanelEnabled:', MainStore.isLayerPanelEnabled, 'toggle classes:', MainStore.isLayerPanelEnabled ? 'tool-icons active-toggle-icon' : 'tool-icons'), MainStore.isLayerPanelEnabled = !MainStore.isLayerPanelEnabled"
			/>
<IconsUse
					name="gridTool"
					:size="32"
					:padding="8"
					:color="MainStore.isGridVisible ? 'white' : 'var(--text-muted)'"
					:class="['tool-icons', { 'active-toggle-icon': MainStore.isGridVisible }]"
					:title="__('Grid View (G)')"
					@click="console.log('[Toolbar] Grid clicked, isGridVisible:', MainStore.isGridVisible, 'toggle classes:', MainStore.isGridVisible ? 'tool-icons active-toggle-icon' : 'tool-icons'), MainStore.isGridVisible = !MainStore.isGridVisible"
				/>
			<IconsUse
					name="watermarkTool"
					:size="32"
					:padding="8"
					:color="MainStore.isWatermarkPanelEnabled ? 'white' : 'var(--text-muted)'"
					:class="['tool-icons', { 'active-toggle-icon': MainStore.isWatermarkPanelEnabled }]"
					:title="__('Watermark Settings')"
					@click="MainStore.isWatermarkPanelEnabled = !MainStore.isWatermarkPanelEnabled"
				/>
			<div class="toolbar-divider"></div>
			<!-- Language Toggle -->
			<div class="language-toggle-container">
				<IconsUse
					name="languageIcon"
					:size="32"
					:padding="8"
					:color="MainStore.previewLanguage ? 'white' : 'var(--text-muted)'"
					:class="['tool-icons', { 'active-toggle-icon': MainStore.previewLanguage }]"
					:title="__('Preview Language')"
					@click="showLanguageMenu = !showLanguageMenu"
				/>
				<div v-if="showLanguageMenu" class="language-menu">
					<div class="language-menu-header">
						<strong>{{ __('Preview Language') }}</strong>
						<span class="close-btn" @click="showLanguageMenu = false">&times;</span>
					</div>
					<div class="language-options">
						<label
							v-for="lang in availableLanguages"
							:key="lang.code"
							:class="['language-option', { active: MainStore.previewLanguage === lang.code }]"
						>
							<input
								type="radio"
								:name="'previewLanguage'"
								:value="lang.code"
								v-model="MainStore.previewLanguage"
								@change="onLanguageChange"
							/>
							{{ lang.label }}
						</label>
					</div>
				</div>
			</div>
			<div class="toolbar-divider"></div>
			<!-- Help Button for Border Toggle Explanation -->
			<div class="help-popover-container">
				<IconsUse
					name="helpIcon"
					:size="32"
					:padding="8"
					:color="showBorderHelp ? 'white' : 'var(--text-muted)'"
					:class="['tool-icons', { 'active-toggle-icon': showBorderHelp }]"
					:title="__('Border Help')"
					@click="showBorderHelp = !showBorderHelp"
				/>
				<div v-if="showBorderHelp" class="help-popover">
					<div class="help-popover-header">
						<strong>{{ __("Border Toggles Help") }}</strong>
						<span class="close-btn" @click="showBorderHelp = false">&times;</span>
					</div>
					<div class="help-content">
						<div class="help-row">
							<span class="help-icon all"><strong>All</strong></span>
							<span>{{ __("Show/Hide all borders at once") }}</span>
						</div>
						<div class="help-row">
							<span class="help-icon left"><strong>L</strong></span>
							<span>{{ __("Toggle LEFT border of all cells") }}</span>
						</div>
						<div class="help-row">
							<span class="help-icon right"><strong>R</strong></span>
							<span>{{ __("Toggle RIGHT border of all cells") }}</span>
						</div>
						<div class="help-row">
							<span class="help-icon top"><strong>T</strong></span>
							<span>{{ __("Toggle TOP border of all cells") }}</span>
						</div>
						<div class="help-row">
							<span class="help-icon bottom"><strong>B</strong></span>
							<span>{{ __("Toggle BOTTOM border of all cells") }}</span>
						</div>
						<hr class="help-divider" />
						<div class="help-note">
							<em>{{ __("Note: In table mode, borders between cells may appear hidden when adjacent cells also hide the same border.") }}</em>
						</div>
					</div>
				</div>
			</div>
			<WatermarkPanel v-if="MainStore.isWatermarkPanelEnabled" />
		</div>
		<LayersPanel v-if="MainStore.isLayerPanelEnabled" />
</div>
</template>

<script setup>
import Icons from "../../icons/Icons.vue";
import IconsUse from "../../icons/IconsUse.vue";
import { useMainStore } from "../../store/MainStore";
import LayersPanel from "./LayersPanel.vue";
import WatermarkPanel from "./WatermarkPanel.vue";
import { ref, useAttrs, watch } from "vue";

defineOptions({ inheritAttrs: false });
const attrs = useAttrs();

const MainStore = useMainStore();
const showBorderHelp = ref(false);
const showLanguageMenu = ref(false);

// Available languages for preview
const availableLanguages = [
	{ code: null, label: __('System Default') },
	{ code: 'th', label: 'ไทย' },
	{ code: 'en', label: 'English' },
];

// Initialize from Print Format's default_print_language
const initLanguage = () => {
	const printFormatName = MainStore.printDesignName;
	if (printFormatName) {
		frappe.call({
			method: 'frappe.client.get',
			args: {
				doctype: 'Print Format',
				name: printFormatName,
			},
			callback: function(r) {
				if (r && r.message && r.message.default_print_language) {
					MainStore.previewLanguage = r.message.default_print_language;
				}
			},
		});
	}
};

// Watch for print format changes
watch(() => MainStore.printDesignName, (newVal) => {
	if (newVal) {
		initLanguage();
	}
});

// Called when user changes language
const onLanguageChange = () => {
	showLanguageMenu.value = false;
	// Language is already set via v-model="MainStore.previewLanguage"
	console.log('[PD] Language changed to:', MainStore.previewLanguage);
};

// Initialize on mount
if (MainStore.printDesignName) {
	initLanguage();
}

const iconClasses = (id, icon) => {
	const isActive = MainStore.activeControl == id;
	return [
		icon,
		'tool-icons',
		{ 'active-tool-icon': isActive },
	];
};
</script>

<style scoped>
.sidebar {
	display: flex;
	padding: 0 6px;
}
.toolbar-section {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 0;
	position: relative;
}
.tool-icons {
	display: flex;
	align-items: center;
	justify-content: center;
	user-select: none;
	cursor: pointer;
	width: 32px;
	height: 32px;
	--icon-stroke: var(--text-color);
}
.tool-icons:hover:not(.active-tool-icon) {
	background-color: var(--primary);
	border-radius: var(--border-radius-sm);
}
.tool-icons:hover:not(.active-tool-icon) use {
	fill: white;
	--icon-stroke: white;
}
.active-layer-icon {
	cursor: pointer;
	--icon-stroke: #f9f3e6;
	border-radius: var(--border-radius-sm);
	background-color: var(--primary);
	margin: 6px;
}
.active-tool-icon {
	background-color: var(--primary);
	--icon-stroke: white;
	border-radius: var(--border-radius-sm);
}
.active-tool-icon,
.active-tool-icon use {
	fill: white !important;
	stroke: white !important;
	--icon-stroke: white !important;
}

/* Toggle icons (layer, grid, help, language) - IconsUse component */
.active-toggle-icon {
	background-color: var(--primary) !important;
	border-radius: var(--border-radius-sm) !important;
}
.active-toggle-icon,
.active-toggle-icon use {
	fill: white !important;
	stroke: white !important;
	--icon-stroke: white !important;
}

/* Left toolbar tools (mouseTool, textTool, etc.) - inline SVG */
.toolbar-section > div:first-child .active-tool-icon {
	background-color: var(--primary) !important;
	border-radius: var(--border-radius-sm) !important;
}
.toolbar-section > div:first-child .active-tool-icon svg use {
	fill: white !important;
	stroke: white !important;
	--icon-stroke: white !important;
}


.toolbar-divider {
	width: 32px;
	height: 1px;
	background-color: var(--border-color);
	margin: 4px auto;
}

/* Language Toggle Menu */
.language-toggle-container {
	position: relative;
}
.language-menu {
	position: absolute;
	left: 48px;
	top: 0;
	background: var(--bg-color);
	border: 1px solid var(--border-color);
	border-radius: var(--border-radius-md);
	padding: 12px;
	width: 180px;
	z-index: 1000;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
.language-menu-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 10px;
	padding-bottom: 8px;
	border-bottom: 1px solid var(--border-color);
}
.language-menu-header strong {
	color: var(--text-color);
	font-size: 12px;
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
.language-options {
	display: flex;
	flex-direction: column;
	gap: 4px;
}
.language-option {
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 6px 8px;
	border-radius: var(--border-radius-sm);
	cursor: pointer;
	font-size: 12px;
	color: var(--text-color);
}
.language-option:hover {
	background: var(--control-bg);
}
.language-option.active {
	background: var(--primary);
	color: white;
}
.language-option input[type="radio"] {
	margin: 0;
}

/* Help Popover Styles */
.help-popover-container {
	position: relative;
}
.help-popover {
	position: absolute;
	left: 48px;
	top: 0;
	background: var(--bg-color);
	border: 1px solid var(--border-color);
	border-radius: var(--border-radius-md);
	padding: 12px;
	width: 260px;
	z-index: 1000;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
.help-popover-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 10px;
	padding-bottom: 8px;
	border-bottom: 1px solid var(--border-color);
}
.help-popover-header strong {
	color: var(--text-color);
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
.help-content {
	font-size: 12px;
}
.help-row {
	display: flex;
	align-items: center;
	margin-bottom: 6px;
	gap: 8px;
}
.help-icon {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	width: 24px;
	height: 20px;
	border: 1px solid var(--border-color);
	border-radius: 3px;
	font-size: 10px;
	font-weight: bold;
	background: var(--control-bg);
}
.help-icon.all {
	background: var(--primary);
	color: white;
	border-color: var(--primary);
}
.help-icon.left {
	border-left: 3px solid var(--text-color);
}
.help-icon.right {
	border-right: 3px solid var(--text-color);
}
.help-icon.top {
	border-top: 3px solid var(--text-color);
}
.help-icon.bottom {
	border-bottom: 3px solid var(--text-color);
}
.help-divider {
	border: none;
	border-top: 1px solid var(--border-color);
	margin: 10px 0;
}
.help-note {
	font-size: 11px;
	color: var(--text-muted);
	line-height: 1.4;
}
</style>
