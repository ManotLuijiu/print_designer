<template>
	<div 
		v-if="showWatermark"
		class="watermark-overlay"
		:style="watermarkStyle"
	>
		<div class="watermark-text" :style="textStyle">
			{{ watermarkText }}
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { useMainStore } from "../../store/MainStore";

const MainStore = useMainStore();

console.log('[WatermarkOverlay] MainStore.mode:', MainStore.mode);
console.log('[WatermarkOverlay] MainStore.watermark:', MainStore.watermark);

const showWatermark = computed(() => {
	const wm = MainStore.watermark;
	const wmMode = wm?.mode || 'None';
	const isEnabled = wm && wmMode !== 'None';
	const show = MainStore.mode === 'header' || MainStore.mode === 'footer' || isEnabled;
	console.log('[WatermarkOverlay] showWatermark computed:', show);
	console.log('[WatermarkOverlay] MainStore.mode:', MainStore.mode);
	console.log('[WatermarkOverlay] watermark.mode:', wmMode);
	console.log('[WatermarkOverlay] isEnabled:', isEnabled);
	return show;
});

const watermarkText = computed(() => {
	const wm = MainStore.watermark;
	if (!wm || wm.mode === 'None') return '';
	
	// Use language toggle to determine text
	const isThai = MainStore.previewLanguage === 'th';
	
	// If custom text is set, use it
	if (wm.custom_text) return wm.custom_text;
	
	switch (wm.mode) {
		case 'Original on First Page':
			return isThai ? 'ต้นฉบับ' : 'Original';
		case 'Copy on All Pages':
			return isThai ? 'สำเนา' : 'Copy';
		case 'Original,Copy on Sequence':
			return isThai ? 'ต้นฉบับ' : 'Original';
		default:
			return '';
	}
});

const watermarkStyle = computed(() => {
	const wm = MainStore.watermark;
	if (!wm) return {};
	
	const baseStyle = {
		fontSize: `${wm.font_size || 24}px`,
		fontFamily: wm.font_family || 'Kanit',
		opacity: wm.opacity || 0.6,
	};
	
	// Apply margins (in mm for consistency with print)
	const top = wm.top || 10;
	const right = wm.right || 10;
	const bottom = wm.bottom || 10;
	const left = wm.left || 10;
	
	// Position based on selected position
	const pos = wm.position || 'Top Right';
	
	console.log('[WatermarkOverlay] Position:', pos, 'Margins - top:', top, 'right:', right, 'bottom:', bottom, 'left:', left);
	
	switch (pos) {
		case 'Top Left':
			return { ...baseStyle, top: `${top}mm`, left: `${left}mm` };
		case 'Top Right':
			return { ...baseStyle, top: `${top}mm`, right: `${right}mm` };
		case 'Center':
			return { ...baseStyle, top: '50%', left: '50%', transform: 'translate(-50%, -50%)' };
		case 'Bottom Left':
			return { ...baseStyle, bottom: `${bottom}mm`, left: `${left}mm` };
		case 'Bottom Right':
			return { ...baseStyle, bottom: `${bottom}mm`, right: `${right}mm` };
		default:
			return { ...baseStyle, top: `${top}mm`, right: `${right}mm` };
	}
});

const textStyle = computed(() => {
	const wm = MainStore.watermark;
	if (!wm) return {};
	
	return {
		color: wm.font_color || '#cccccc',
	};
});
</script>

<style scoped>
.watermark-overlay {
	position: absolute;
	pointer-events: none;
	z-index: 100;
	user-select: none;
}

.watermark-text {
	font-weight: bold;
	text-align: center;
	white-space: nowrap;
}
</style>
