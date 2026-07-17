<template>
	<Icons />
	<div class="sidebar">
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
		</div>
		<LayersPanel v-if="MainStore.isLayerPanelEnabled" />
	</div>
</template>

<script setup>
import Icons from "../../icons/Icons.vue";
import IconsUse from "../../icons/IconsUse.vue";
import { useMainStore } from "../../store/MainStore";
import LayersPanel from "./LayersPanel.vue";
import { ref } from "vue";
const MainStore = useMainStore();
const showBorderHelp = ref(false);

const iconClasses = (id, icon) => {
	const isActive = MainStore.activeControl == id;
	console.log('[Toolbar] iconClasses:', { id, icon, activeControl: MainStore.activeControl, isActive });
	return [
		icon,
		"tool-icons",
		{ "active-tool-icon": isActive },
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

/* Toggle icons (layer, grid, help) - IconsUse component */
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
