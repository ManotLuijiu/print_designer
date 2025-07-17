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

const removePdfWatcher = watch(
	() => [pdfjsLibRef.value, MainStore.doctype, MainStore.printDesignName],
	async () => {
		let pdfjsLib = pdfjsLibRef.value;
		if (pdfjsLib && MainStore.doctype && MainStore.printDesignName) {
			console.time("PdfStart");
			let url = `/api/method/frappe.utils.print_format.download_pdf?doctype=${encodeURIComponent(
				MainStore.doctype
			)}&name=${encodeURIComponent(MainStore.currentDoc)}&format=${encodeURIComponent(
				MainStore.printDesignName
			)}&no_letterhead=1`;

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
				
				// Update page numbers in the original document for preview
				updatePageNumbersInPreview(pdfDoc.numPages);
				
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

/**
 * Update page numbers in the original document for preview mode
 */
function updatePageNumbersInPreview(totalPages) {
	// Update page number elements in the original document
	const currentPageElements = document.querySelectorAll('.page_info_page, .page');
	const totalPageElements = document.querySelectorAll('.page_info_topage, .topage');
	const fromPageElements = document.querySelectorAll('.page_info_frompage, .frompage');
	
	// Set page numbers (preview shows page 1 of totalPages)
	currentPageElements.forEach(el => {
		if (el.textContent.trim() === '' || el.textContent.trim() === '{{ page }}') {
			el.textContent = '1';
		}
	});
	totalPageElements.forEach(el => {
		if (el.textContent.trim() === '' || el.textContent.trim() === '{{ topage }}') {
			el.textContent = totalPages.toString();
		}
	});
	fromPageElements.forEach(el => {
		if (el.textContent.trim() === '' || el.textContent.trim() === '{{ frompage }}') {
			el.textContent = '1';
		}
	});
	
	// Set date/time elements
	const dateObj = new Date();
	const dateElements = document.querySelectorAll('.page_info_date, .date');
	const timeElements = document.querySelectorAll('.page_info_time, .time');
	const isodateElements = document.querySelectorAll('.page_info_isodate, .isodate');
	
	dateElements.forEach(el => {
		if (el.textContent.trim() === '' || el.textContent.trim().includes('{{ date }}')) {
			el.textContent = dateObj.toLocaleDateString();
		}
	});
	timeElements.forEach(el => {
		if (el.textContent.trim() === '' || el.textContent.trim().includes('{{ time }}')) {
			el.textContent = dateObj.toLocaleTimeString();
		}
	});
	isodateElements.forEach(el => {
		if (el.textContent.trim() === '' || el.textContent.trim().includes('{{ isodate }}')) {
			el.textContent = dateObj.toISOString();
		}
	});
}
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
