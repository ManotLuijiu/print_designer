<template>
	<div class="canvas">
		<div
			id="preview-container"
			class="preview-container"
			:style="[MainStore.getPageSettings, 'height: unset;']"
		></div>
	</div>
</template>
<script setup>
import { onMounted, onUnmounted, watch, shallowRef } from "vue";
import { useMainStore } from "../../store/MainStore";
const MainStore = useMainStore();
const pdfjsLibRef = shallowRef(null);
const pdfDocumentTask = shallowRef(null);

// Helper function to convert watermark settings to URL parameters
function getWatermarkParams(watermarkSettings) {
	const params = new URLSearchParams();
	
	switch (watermarkSettings) {
		case 'Original on First Page':
			params.append('copy_count', '1');
			params.append('copy_labels', 'ต้นฉบับ/Original');
			params.append('copy_watermark', 'true');
			break;
		case 'Copy on All Pages':
			params.append('copy_count', '1');
			params.append('copy_labels', 'สำเนา/Copy');
			params.append('copy_watermark', 'true');
			break;
		case 'Original,Copy on Sequence':
			params.append('copy_count', '2');
			params.append('copy_labels', 'ต้นฉบับ/Original,สำเนา/Copy');
			params.append('copy_watermark', 'true');
			break;
		default:
			return null;
	}
	
	return params.toString();
}

const removePdfWatcher = watch(
	() => [pdfjsLibRef.value, MainStore.doctype, MainStore.printDesignName],
	async () => {
		let pdfjsLib = pdfjsLibRef.value;
		if (pdfjsLib && MainStore.doctype && MainStore.printDesignName) {
			console.time("PdfStart");
			
			// Get watermark settings from Print Settings
			let watermarkSettings = null;
			try {
				const printSettings = await frappe.db.get_doc('Print Settings');
				watermarkSettings = printSettings.watermark_settings;
				console.log('Watermark settings retrieved:', watermarkSettings);
			} catch (error) {
				console.warn('Could not fetch watermark settings:', error);
			}
			
			let url = `/api/method/frappe.utils.print_format.download_pdf?doctype=${encodeURIComponent(
				MainStore.doctype
			)}&name=${encodeURIComponent(MainStore.currentDoc)}&format=${encodeURIComponent(
				MainStore.printDesignName
			)}&no_letterhead=1`;
			
			// Add watermark parameters if watermark settings exist and are not "None"
			if (watermarkSettings && watermarkSettings !== 'None') {
				// Map watermark settings to appropriate parameters
				const watermarkParams = getWatermarkParams(watermarkSettings);
				console.log('Watermark parameters:', watermarkParams);
				if (watermarkParams) {
					url += `&${watermarkParams}`;
					console.log('Final PDF URL with watermarks:', url);
				}
			} else {
				console.log('No watermark settings or set to None:', watermarkSettings);
			}

			/**
			 * Get page info from document, resize canvas accordingly, and render page.
			 * @param num Page number.
			 */
			async function renderPage(num) {
				pageRendering = true;
				// Using promise to fetch the page
				let page = await pdfDoc.getPage(num);
				let canvasContainer = document.getElementById("preview-container");
				let canvas = document.createElement("canvas");
				canvasContainer.appendChild(canvas);
				ctx = canvas.getContext("2d");
				let viewport = page.getViewport({ scale: 1 });
				let scale = (MainStore.page.width / viewport.width) * window.devicePixelRatio;
				let scaledViewport = page.getViewport({ scale: scale });
				canvas.style.height = MainStore.page.height + "px";
				canvas.style.width = MainStore.page.width + "px";
				canvas.height = scaledViewport.height;
				canvas.width = scaledViewport.width;

				// Render PDF page into canvas context
				var renderContext = {
					canvasContext: ctx,
					viewport: scaledViewport,
					intent: "print",
				};
				page.render(renderContext);
			}

			/**
			 * Asynchronously downloads PDF.
			 */
			let pdfDoc = null;
			frappe.dom.freeze("Generating PDF Preview...");
			try {
				pdfDocumentTask.value = await pdfjsLib.getDocument(url);
				pdfDoc = await pdfDocumentTask.value.promise;
				console.timeEnd("PdfStart", pdfDoc);

				// Initial/first page rendering
				for (let pageno = 1; pageno <= pdfDoc.numPages; pageno++) {
					await renderPage(pageno);
				}
				frappe.dom.unfreeze();
			} catch {
				frappe.dom.unfreeze();
				frappe.show_alert(
					{
						message: "Unable to generate PDF",
						indicator: "red",
					},
					5
				);
				MainStore.mode = "editing";
			}

			removePdfWatcher();
		}
	}
);
onMounted(() => {
	let waitingForpdfJsLib = setInterval(() => {
		if (window.pdfjsLib) {
			pdfjsLibRef.value = window.pdfjsLib;
			clearInterval(waitingForpdfJsLib);
		}
	}, 10);
});
onUnmounted(() => {
	pdfDocumentTask.value.destroy();
});
</script>

<style lang="scss" scoped>
.preview-container {
	position: relative;
	margin: 50px auto;
	margin-top: calc((-1 * var(--print-margin-top)) + 50px);
	height: 100%;
	background-color: #f2f3f3;

	canvas {
		margin-top: 20px;
	}
}
</style>
