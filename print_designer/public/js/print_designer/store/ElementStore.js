import { defineStore } from "pinia";
import { useMainStore } from "./MainStore";
import {
	createText,
	createRectangle,
	createDynamicText,
	createImage,
	createTable,
	createBarcode,
} from "../defaultObjects";
import {
	handlePrintFonts,
	setCurrentElement,
	createHeaderFooterElement,
	getParentPage,
} from "../utils";

import html2canvas from "html2canvas";

<<<<<<< HEAD
=======
// Enhanced layout types
const LAYOUT_TYPES = {
	ABSOLUTE: "absolute", // Current behavior - precise positioning
	RELATIVE: "relative", // New - flows with content
	FLEX_ROW: "flex-row", // New - horizontal flow
	FLEX_COLUMN: "flex-col", // New - vertical flow
	GRID: "grid", // New - grid layout
};

>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
export const useElementStore = defineStore("ElementStore", {
	state: () => ({
		Elements: new Array(),
		Headers: new Array(),
		Footers: new Array(),
<<<<<<< HEAD
=======
		// Add layout types to state
		layoutTypes: LAYOUT_TYPES,
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
	}),
	actions: {
		createNewObject(event, element) {
			let newElement;
			const MainStore = useMainStore();
<<<<<<< HEAD
			if (MainStore.activeControl == "text") {
				if (MainStore.textControlType == "static") {
=======
			if (MainStore.activeControl === "text") {
				if (MainStore.textControlType === "static") {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
					newElement = createText(event, element);
				} else {
					newElement = createDynamicText(event, element);
				}
<<<<<<< HEAD
			} else if (MainStore.activeControl == "rectangle") {
				newElement = createRectangle(event, element);
			} else if (MainStore.activeControl == "image") {
				newElement = createImage(event, element);
			} else if (MainStore.activeControl == "table") {
				newElement = createTable(event, element);
			} else if (MainStore.activeControl == "barcode") {
				newElement = createBarcode(event, element);
			}
			return newElement;
		},
=======
			} else if (MainStore.activeControl === "rectangle") {
				newElement = createRectangle(event, element);
			} else if (MainStore.activeControl === "image") {
				newElement = createImage(event, element);
			} else if (MainStore.activeControl === "table") {
				newElement = createTable(event, element);
			} else if (MainStore.activeControl === "barcode") {
				newElement = createBarcode(event, element);
			}

			// Set default layout type based on parent
			if (newElement && element?.layoutType) {
				newElement.layoutType = this.determineChildLayoutType(
					element.layoutType,
				);
				newElement.positioning = this.determinePositioning(element.layoutType);
			}

			return newElement;
		},

		// Enhanced version of existing method
		// Modify createWrapperElement function
		createWrapperElement(dimensions, parent) {
			const MainStore = useMainStore();
			const coordinates = {};

			// Determine positioning strategy based on parent layout type
			const parentLayoutType = parent.layoutType || LAYOUT_TYPES.ABSOLUTE;
			const positioning = this.determinePositioning(parentLayoutType);

			if (
				positioning === "relative" ||
				parentLayoutType === LAYOUT_TYPES.FLEX_COLUMN
			) {
				// Relative positioning - content flows naturally
				if (parent.type === "page") {
					coordinates["startX"] = dimensions.top;
					coordinates["pageY"] = dimensions.top;
					coordinates["startX"] = 0;
					coordinates["pageX"] = 0;
				} else if (parent.layoutType === "row") {
					coordinates["startY"] = 0;
					coordinates["pageY"] = 0;
					coordinates["startX"] = dimensions.left;
					coordinates["pageX"] = dimensions.left;
				} else {
					// For flex column - stack vertically
					coordinates["startY"] = this.calculateNextFlowPosition(
						parent,
						"vertical",
					);
					coordinates["pageY"] = coordinates["startY"];
					coordinates["startX"] = dimensions.left || 0;
					coordinates["pageX"] = coordinates["startX"];
				}
			} else if (parentLayoutType === LAYOUT_TYPES.FLEX_ROW) {
				// Horizontal flow positioning
				coordinates["startY"] = 0;
				coordinates["pageY"] = 0;
				coordinates["startX"] = this.calculateNextFlowPosition(
					parent,
					"horizontal",
				);
				coordinates["pageX"] = coordinates["startX"];
			} else {
				// Default absolute positioning (current behavior)
				if (parent.type === "page") {
					coordinates["startY"] = dimensions.top;
					coordinates["pageY"] = dimensions.top;
					coordinates["startX"] = 0;
					coordinates["pageX"] = 0;
				} else if (parent.layoutType === "row") {
					coordinates["startY"] = 0;
					coordinates["pageY"] = 0;
					coordinates["startX"] = dimensions.left;
					coordinates["pageX"] = dimensions.left;
				} else {
					coordinates["startY"] = dimensions.top;
					coordinates["pageY"] = dimensions.top;
					coordinates["startX"] = dimensions.left;
					coordinates["pageX"] = dimensions.left;
				}
			}

			const wrapper = createRectangle(coordinates, parent);

			// Set layout properties
			wrapper.layoutType = parent.layoutType === "row" ? "column" : "row";
			wrapper.positioning = positioning;
			wrapper.flowDirection =
				parentLayoutType === LAYOUT_TYPES.FLEX_ROW ? "row" : "column";

			// Configure wrapper based on layout type
			if (wrapper.layoutType === "column") {
				wrapper.width = dimensions.right - dimensions.left;
				wrapper.height = parent.height || 0;
				wrapper.classes = wrapper.classes.filter(
					(c) => c !== "relative-column",
				);
				wrapper.classes.push("relative-column");
				wrapper.relativeColumn = true;
			} else {
				wrapper.width =
					parent.width ||
					MainStore.page.width -
						MainStore.page.marginLeft -
						MainStore.page.marginRight;
				wrapper.height = dimensions.bottom - dimensions.top;
				wrapper.classes = wrapper.classes.filter((c) => c !== "relative-row");
				wrapper.classes.push("relative-row");
				wrapper.classes.push(wrapper.id);
			}

			// Add flow-specific classes
			if (positioning === "relative") {
				wrapper.classes.push("flow-container");
				wrapper.classes.push(`layout-${parentLayoutType}`);
			}
			return wrapper;
		},

		// NEW HELPER METHODS
		determinePositioning(layoutType) {
			switch (layoutType) {
				case LAYOUT_TYPES.RELATIVE:
				case LAYOUT_TYPES.FLEX_ROW:
				case LAYOUT_TYPES.FLEX_COLUMN:
				case LAYOUT_TYPES.GRID:
					return "relative";
				default:
					return "absolute";
			}
		},

		determineChildLayoutType(parentLayoutType) {
			// Child elements inherit appropriate layout type from parent
			switch (parentLayoutType) {
				case LAYOUT_TYPES.FLEX_ROW:
					return LAYOUT_TYPES.RELATIVE;
				case LAYOUT_TYPES.FLEX_COLUMN:
					return LAYOUT_TYPES.RELATIVE;
				case LAYOUT_TYPES.GRID:
					return LAYOUT_TYPES.RELATIVE;
				default:
					return LAYOUT_TYPES.ABSOLUTE;
			}
		},

		calculateNextFlowPosition(parent, direction) {
			if (!parent.childrens || parent.childrens.length === 0) {
				return 0;
			}

			const children = parent.childrens;

			if (direction === "vertical") {
				// Stack vertically - find the bottom of the last child
				let maxBottom = 0;
				children.forEach((child) => {
					const childBottom =
						(child.startY || 0) +
						(child.height || 0) +
						(child.marginBottom || 0);
					if (childBottom > maxBottom) {
						maxBottom = childBottom;
					}
				});
				return maxBottom;
			} else if (direction === "horizontal") {
				// Place horizontally - find the right edge of the last child
				let maxRight = 0;
				children.forEach((child) => {
					const childRight =
						(child.startX || 0) + (child.width || 0) + (child.marginRight || 0);
					if (childRight > maxRight) {
						maxRight = childRight;
					}
				});
				return maxRight;
			}

			return 0;
		},

		// Enhanced save method to handle new layout types
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
		computeLayoutForSave() {
			this.handleHeaderFooterOverlapping();

			const { header, body, footer } = this.computeMainLayout();
<<<<<<< HEAD
			// before modifying save json object that is used by loadElements and UI.
			const objectToSave = {
				print_designer_header: JSON.stringify(header || []),
				print_designer_body: JSON.stringify(body),
				print_designer_footer: JSON.stringify(footer || []),
				print_designer_after_table: null,
			};
=======

			// Enhanced layout computation for flow containers
			const processFlowContainers = (elements) => {
				return elements.map((element) => {
					if (
						element.layoutType &&
						element.layoutType !== LAYOUT_TYPES.ABSOLUTE
					) {
						// Add flow layout metadata
						element.flowLayoutMeta = {
							layoutType: element.layoutType,
							positioning: element.positioning,
							flowDirection: element.flowDirection,
							isFlowContainer: true,
						};
					}
					return element;
				});
			};

			const objectToSave = {
				print_designer_header: JSON.stringify(
					header ? processFlowContainers(header) : [],
				),
				print_designer_body: JSON.stringify(processFlowContainers(body)),
				print_designer_footer: JSON.stringify(
					footer ? processFlowContainers(footer) : [],
				),
				print_designer_after_table: null,
			};

			// Rest of the existing layout computation logic...
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			const layout = {
				header: [],
				body: [],
				footer: [],
			};
<<<<<<< HEAD
			let headerElements = [];
			let bodyElements = [];
			let footerElements = [];
			if (header) {
				const headerArray = header.map((h) => {
					h.childrens = this.computeRowLayout(h.childrens, headerElements, "header");
=======

			let headerElements = [];
			let bodyElements = [];
			let footerElements = [];

			if (header) {
				const headerArray = header.map((h) => {
					h.childrens = this.computeRowLayout(
						h.childrens,
						headerElements,
						"header",
					);
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
					return h;
				});
				layout.header = {
					firstPage: headerArray.find((h) => h.firstPage).childrens,
					oddPage: headerArray.find((h) => h.oddPage).childrens,
					evenPage: headerArray.find((h) => h.evenPage).childrens,
					lastPage: headerArray.find((h) => h.lastPage).childrens,
				};
			}
<<<<<<< HEAD
			// it will throw error if body is empty so no need to check here
=======

>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			layout.body = body.map((b) => {
				b.childrens = this.computeRowLayout(b.childrens, bodyElements, "body");
				return b;
			});
<<<<<<< HEAD
			if (footer) {
				const footerArray = footer.map((f) => {
					f.childrens = this.computeRowLayout(f.childrens, footerElements, "footer");
					return f;
				});
=======

			if (footer) {
				const footerArray = footer.map((f) => {
					f.childrens = this.computeRowLayout(
						f.childrens,
						footerElements,
						"footer",
					);
					return f;
				});

>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				layout.footer = {
					firstPage: footerArray.find((h) => h.firstPage).childrens,
					oddPage: footerArray.find((h) => h.oddPage).childrens,
					evenPage: footerArray.find((h) => h.evenPage).childrens,
					lastPage: footerArray.find((h) => h.lastPage).childrens,
				};
			}
			// WARNING: lines below are for debugging purpose only.
			// this.Elements.length = 0;
			// this.Headers.length = 0;
			// this.Footers.length = 0;
			// this.Headers.push(...header);
			// this.Elements.push(...body);
			// this.Footers.push(...footer);
			// this.Elements.forEach((page, index) => {
			// 	page.header = [createHeaderFooterElement(this.getHeaderObject(index).childrens, "header")];
			// 	page.footer = [createHeaderFooterElement(this.getFooterObject(index).childrens, "footer")]
			// });
			// End of debugging code
			objectToSave.print_designer_print_format = JSON.stringify(layout);

			// update fonts in store
			const MainStore = useMainStore();
			MainStore.currentFonts.length = 0;
			MainStore.currentFonts.push(
				...Object.keys({
					...(MainStore.printHeaderFonts || {}),
					...(MainStore.printBodyFonts || {}),
					...(MainStore.printFooterFonts || {}),
<<<<<<< HEAD
				})
			);
			return objectToSave;
		},
=======
				}),
			);
			return objectToSave;
		},

		// Enhanced load method to restore layout types
		childrensLoad(element, parent) {
			element.parent = parent;
			element.DOMRef = null;
			delete element.printY;
			element.isDraggable = true;
			element.isResizable = true;

			// Restore flow layout properties
			if (element.flowLayoutMeta) {
				element.layoutType = element.flowLayoutMeta.layoutType;
				element.positioning = element.flowLayoutMeta.positioning;
				element.flowDirection = element.flowLayoutMeta.flowDirection;
				element.isFlowContainer = element.flowLayoutMeta.isFlowContainer;
			}

			this.handleDynamicContent(element);

			if (element.type === "rectangle" || element.type === "page") {
				element.isDropZone = true;
				const childrensArray = element.childrens;
				element.childrens = [];
				childrensArray.forEach((el) => {
					const child = this.childrensLoad(el, element);
					child && element.childrens.push(child);
				});
			} else if (element.type === "text" && !element.isDynamic) {
				element.contenteditable = false;
			}

			return element;
		},

		// Add method to change layout type of existing elements
		changeElementLayoutType(element, newLayoutType) {
			if (!element) return;

			element.layoutType = newLayoutType;
			element.positioning = this.determinePositioning(newLayoutType);

			// Update classes
			element.classes = element.classes.filter(
				(c) => !c.startsWith("layout-") && c !== "flow-container",
			);

			if (this.determinePositioning(newLayoutType) === "relative") {
				element.classes.push("flow-container");
				element.classes.push(`layout-${newLayoutType}`);
			}

			// Recalculate positions for child elements if needed
			if (element.childrens && element.childrens.length > 0) {
				this.recalculateChildPositions(element);
			}
		},

		recalculateChildPositions(parent) {
			if (!parent.childrens) return;

			parent.childrens.forEach((child, index) => {
				if (parent.layoutType === LAYOUT_TYPES.FLEX_COLUMN) {
					// Stack vertically
					if (index === 0) {
						child.startY = 0;
					} else {
						const prevChild = parent.childrens[index - 1];
						child.startY =
							prevChild.startY +
							prevChild.height +
							(prevChild.marginBottom || 0);
					}
					child.startX = child.marginLeft || 0;
				} else if (parent.layoutType === LAYOUT_TYPES.FLEX_ROW) {
					// Place horizontally
					if (index === 0) {
						child.startX = 0;
					} else {
						const prevChild = parent.childrens[index - 1];
						child.startX =
							prevChild.startX + prevChild.width + (prevChild.marginRight || 0);
					}
					child.startY = child.marginTop || 0;
				}
			});
		},

>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
		// This is modified version of upload function used in frappe/FileUploader.vue
		async upload_file(file) {
			const MainStore = useMainStore();
			MainStore.print_designer_preview_img = null;
			return new Promise((resolve, reject) => {
<<<<<<< HEAD
				let xhr = new XMLHttpRequest();
				xhr.onreadystatechange = () => {
					if (xhr.readyState == XMLHttpRequest.DONE) {
=======
				console.log("upload_file_resolve", resolve);
				console.log("upload_file_reject", reject);

				const xhr = new XMLHttpRequest();
				xhr.onreadystatechange = () => {
					if (xhr.readyState === XMLHttpRequest.DONE) {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
						if (xhr.status === 200) {
							try {
								r = JSON.parse(xhr.responseText);
								if (r.message.doctype === "File") {
									file_url = r.message.file_url;
									frappe.db.set_value(
										"Print Format",
										MainStore.printDesignName,
										"print_designer_preview_img",
<<<<<<< HEAD
										file_url
									);
								}
							} catch (e) {
=======
										file_url,
									);
								}
							} catch (e) {
								console.error("upload_file_error", e);
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
								r = xhr.responseText;
							}
						}
					}
				};
				xhr.open("POST", "/api/method/upload_file", true);
				xhr.setRequestHeader("Accept", "application/json");
				xhr.setRequestHeader("X-Frappe-CSRF-Token", frappe.csrf_token);

<<<<<<< HEAD
				let form_data = new FormData();
=======
				const form_data = new FormData();
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				if (file.file_obj) {
					form_data.append("file", file.file_obj, file.name);
				}
				form_data.append("is_private", 1);

				form_data.append("doctype", "Print Format");
				form_data.append("docname", MainStore.printDesignName);

				form_data.append("fieldname", "print_designer_preview_img");

				if (file.optimize) {
					form_data.append("optimize", true);
				}
				xhr.send(form_data);
			});
		},
		async generatePreview() {
			const MainStore = useMainStore();
			// first delete old preview image
			const filter = {
				attached_to_doctype: "Print Format",
				attached_to_name: MainStore.printDesignName,
				attached_to_field: "print_designer_preview_img",
			};
			// get filename before uploading new file
			let old_filename = await frappe.db.get_value("File", filter, "name");
			old_filename = old_filename.message.name;
			if (old_filename) {
				frappe.db.delete_doc("File", old_filename);
			}

			const options = {
				backgroundColor: "#ffffff",
				height: MainStore.page.height,
				width: MainStore.page.width,
			};
			const print_stylesheet = document.createElement("style");
			print_stylesheet.rel = "stylesheet";
<<<<<<< HEAD
			let st = `.main-container::after {
				display: none;
			}`;
			document.getElementsByClassName("main-container")[0].appendChild(print_stylesheet);
			print_stylesheet.sheet.insertRule(st, 0);
			const preview_canvas = await html2canvas(
				document.getElementsByClassName("main-container")[0],
				options
			);
			document.getElementsByClassName("main-container")[0].removeChild(print_stylesheet);
=======
			const st = `.main-container::after {
				display: none;
			}`;
			document
				.getElementsByClassName("main-container")[0]
				.appendChild(print_stylesheet);
			print_stylesheet.sheet.insertRule(st, 0);
			const preview_canvas = await html2canvas(
				document.getElementsByClassName("main-container")[0],
				options,
			);
			document
				.getElementsByClassName("main-container")[0]
				.removeChild(print_stylesheet);
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			preview_canvas.toBlob(async (blob) => {
				const file = new File(
					[blob],
					`print_designer-${frappe.scrub(MainStore.printDesignName)}-preview.jpg`,
<<<<<<< HEAD
					{ type: "image/jpeg" }
=======
					{ type: "image/jpeg" },
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				);
				const file_data = {
					file_obj: file,
					optimize: 1,
					name: file.name,
					private: true,
				};
				await this.upload_file(file_data);
			});
		},
		async saveElements() {
			const MainStore = useMainStore();
			if (this.checkIfAnyTableIsEmpty()) return;
<<<<<<< HEAD
			let is_standard = await frappe.db.get_value(
				"Print Format",
				MainStore.printDesignName,
				"standard"
			);
			MainStore.is_standard = is_standard.message.standard == "Yes";
=======
			const is_standard = await frappe.db.get_value(
				"Print Format",
				MainStore.printDesignName,
				"standard",
			);
			MainStore.is_standard = is_standard.message.standard === "Yes";
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			// Update the header and footer height with margin
			MainStore.page.headerHeightWithMargin =
				MainStore.page.headerHeight + MainStore.page.marginTop;
			MainStore.page.footerHeightWithMargin =
				MainStore.page.footerHeight + MainStore.page.marginBottom;
			const objectToSave = this.computeLayoutForSave();
			if (!objectToSave) return;
			const updatedPage = { ...MainStore.page };
			const settingsForSave = {
				page: updatedPage,
				pdfPrintDPI: MainStore.pdfPrintDPI,
				globalStyles: MainStore.globalStyles,
				currentPageSize: MainStore.currentPageSize,
				isHeaderFooterAuto: MainStore.isHeaderFooterAuto,
				currentDoc: MainStore.currentDoc,
				textControlType: MainStore.textControlType,
				currentFonts: MainStore.currentFonts,
				printHeaderFonts: MainStore.printHeaderFonts,
				printFooterFonts: MainStore.printFooterFonts,
				printBodyFonts: MainStore.printBodyFonts,
				userProvidedJinja: MainStore.userProvidedJinja,
				schema_version: MainStore.schema_version,
			};
			const convertCsstoString = (stylesheet) => {
<<<<<<< HEAD
				let cssRule = Array.from(stylesheet.cssRules)
=======
				const cssRule = Array.from(stylesheet.cssRules)
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
					.map((rule) => rule.cssText || "")
					.join(" ");
				return stylesheet.cssRules ? cssRule : "";
			};
			const css =
				convertCsstoString(MainStore.screenStyleSheet) +
				convertCsstoString(MainStore.printStyleSheet);

			objectToSave.print_designer_settings = JSON.stringify(settingsForSave);
			objectToSave.print_designer_after_table = null;
			objectToSave.css = css;
			if (MainStore.isOlderSchema("1.3.0")) {
				await this.printFormatCopyOnOlderSchema(objectToSave);
			} else {
<<<<<<< HEAD
				await frappe.db.set_value("Print Format", MainStore.printDesignName, objectToSave);
=======
				await frappe.db.set_value(
					"Print Format",
					MainStore.printDesignName,
					objectToSave,
				);
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				frappe.show_alert(
					{
						message: `Print Format Saved Successfully`,
						indicator: "green",
					},
<<<<<<< HEAD
					5
=======
					5,
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				);
				await this.generatePreview();
			}
		},
		checkIfAnyTableIsEmpty() {
<<<<<<< HEAD
			const emptyTable = this.Elements.find((el) => el.type == "table" && el.table == null);
			if (emptyTable) {
				let message = __("You have Empty Table. Please add table fields or remove table.");
=======
			const emptyTable = this.Elements.find(
				(el) => el.type === "table" && el.table == null,
			);
			if (emptyTable) {
				const message = __(
					"You have Empty Table. Please add table fields or remove table.",
				);
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				setCurrentElement({}, emptyTable);
				frappe.show_alert(
					{
						message: message,
						indicator: "red",
					},
<<<<<<< HEAD
					5
=======
					5,
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				);
				return true;
			}
			return false;
		},
		computeMainLayout() {
<<<<<<< HEAD
			let header = [];
			let body = [];
			let footer = [];
=======
			const header = [];
			const body = [];
			const footer = [];
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			const pages = [...this.Elements];
			const headerArray = [...this.Headers];
			const footerArray = [...this.Footers];
			headerArray.forEach((h) => {
				const headerCopy = { ...h };
				delete headerCopy.DOMRef;
				delete headerCopy.parent;
				h.childrens = this.cleanUpElementsForSave(h.childrens, "header") || [];
				header.push(headerCopy);
			});
			pages.forEach((page) => {
				const pageCopy = { ...page };
				delete pageCopy.DOMRef;
				delete pageCopy.parent;
				delete pageCopy.header;
				delete pageCopy.footer;
				pageCopy.childrens.sort((a, b) => {
					return a.startY < b.startY ? -1 : 1;
				});
<<<<<<< HEAD
				pageCopy.childrens = this.cleanUpElementsForSave(pageCopy.childrens, "body");
=======
				pageCopy.childrens = this.cleanUpElementsForSave(
					pageCopy.childrens,
					"body",
				);
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				body.push(pageCopy);
			});
			footerArray.forEach((f) => {
				const footerCopy = { ...f };
				delete footerCopy.DOMRef;
				delete footerCopy.parent;
<<<<<<< HEAD
				footerCopy.childrens = this.cleanUpElementsForSave(f.childrens, "footer") || [];
=======
				footerCopy.childrens =
					this.cleanUpElementsForSave(f.childrens, "footer") || [];
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				footer.push(footerCopy);
			});
			return { header, body, footer };
		},
		// TODO: Refactor this function
		computeRowLayout(column, parentContainer = null, type = "row") {
			const MainStore = useMainStore();
			const rowElements = [];
			let prevDimension = null;
			column.sort((a, b) => (a.startY < b.startY ? -1 : 1));
			const rows = column.reduce((currentRow, currentEl) => {
<<<<<<< HEAD
				if (currentRow.length == 0) {
=======
				if (currentRow.length === 0) {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
					currentRow.push(currentEl);
					return currentRow;
				}
				// replace with .at() after checking compatibility for our user base.
				const el = currentRow.at(-1);
				const currentStartY = parseInt(currentEl.startY);
				const currentEndY = parseInt(currentEl.startY + currentEl.height);
				const maxEndY = parseInt(el.startY + el.height);

				if (currentStartY >= maxEndY) {
					const dimension = this.computeRowElementDimensions(
						currentRow,
						rowElements.length,
						prevDimension,
<<<<<<< HEAD
						type
=======
						type,
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
					);
					prevDimension = dimension;
					const wrapper = this.createRowWrapperElement(
						dimension,
						currentRow,
<<<<<<< HEAD
						parentContainer
=======
						parentContainer,
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
					);
					rowElements.push(wrapper);
					currentRow.length = 0;
					currentRow.push(currentEl);
					return currentRow;
				}

				if (currentEndY > maxEndY) {
					currentRow.push(currentEl);
				} else {
					currentRow.splice(-1, 0, currentEl);
				}
				return currentRow;
			}, []);
			// don't create row if it is there is only one row and parent is column
<<<<<<< HEAD
			if (parentContainer?.layoutType == "column" && rowElements.length == 0) {
				return;
			}
			if (rows.length != 0) {
=======
			if (
				parentContainer?.layoutType === "column" &&
				rowElements.length === 0
			) {
				return;
			}
			if (rows.length !== 0) {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				const dimension = this.computeRowElementDimensions(
					rows,
					rowElements.length,
					prevDimension,
<<<<<<< HEAD
					type
				);
				if (parentContainer.layoutType == "column") {
					dimension.bottom = parentContainer.height;
				}
				prevDimension = dimension;
				const wrapper = this.createRowWrapperElement(dimension, rows, parentContainer);
				rowElements.push(wrapper);
			}
			rowElements.sort((a, b) => (a.startY < b.startY ? -1 : 1));
			if (type == "header" && rowElements.length) {
				const lastHeaderRow = rowElements[rowElements.length - 1];
				lastHeaderRow.height =
					MainStore.page.headerHeight - MainStore.page.marginTop - lastHeaderRow.startY;
			} else if (type == "footer" && rowElements.length) {
				const lastFooterRow = rowElements[rowElements.length - 1];
				lastFooterRow.height = MainStore.page.footerHeight - lastFooterRow.startY;
=======
					type,
				);
				if (parentContainer.layoutType === "column") {
					dimension.bottom = parentContainer.height;
				}
				prevDimension = dimension;
				const wrapper = this.createRowWrapperElement(
					dimension,
					rows,
					parentContainer,
				);
				rowElements.push(wrapper);
			}
			rowElements.sort((a, b) => (a.startY < b.startY ? -1 : 1));
			if (type === "header" && rowElements.length) {
				const lastHeaderRow = rowElements[rowElements.length - 1];
				lastHeaderRow.height =
					MainStore.page.headerHeight -
					MainStore.page.marginTop -
					lastHeaderRow.startY;
			} else if (type === "footer" && rowElements.length) {
				const lastFooterRow = rowElements[rowElements.length - 1];
				lastFooterRow.height =
					MainStore.page.footerHeight - lastFooterRow.startY;
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			}
			return rowElements;
		},
		// TODO: extract repeated code to a function
		computeColumnLayout(row, parentContainer) {
			const columnElements = [];
			let prevDimension = null;
			row.sort((a, b) => (a.startX < b.startX ? -1 : 1));
			const columns = row.reduce((currentColumn, currentEl) => {
<<<<<<< HEAD
				if (currentColumn.length == 0) {
=======
				if (currentColumn.length === 0) {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
					currentColumn.push(currentEl);
					return currentColumn;
				}
				const el = currentColumn.at(-1);
				const currentStartX = parseInt(currentEl.startX);
				const currentEndX = parseInt(currentEl.startX + currentEl.width);
				const maxEndX = parseInt(el.startX + el.width);
				if (currentStartX >= maxEndX) {
					const dimension = this.computeColumnElementDimensions(
						currentColumn,
						columnElements.length,
<<<<<<< HEAD
						prevDimension
=======
						prevDimension,
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
					);
					prevDimension = dimension;
					const wrapper = this.createColumnWrapperElement(
						dimension,
						currentColumn,
<<<<<<< HEAD
						parentContainer
=======
						parentContainer,
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
					);
					columnElements.push(wrapper);
					currentColumn.length = 0;
					currentColumn.push(currentEl);
					return currentColumn;
				}
				if (currentEndX > maxEndX) {
					currentColumn.push(currentEl);
				} else {
					currentColumn.splice(-1, 0, currentEl);
				}
				return currentColumn;
			}, []);
<<<<<<< HEAD
			if (columnElements.length == 0) {
				return;
			}
			if (columns.length != 0) {
=======
			if (columnElements.length === 0) {
				return;
			}
			if (columns.length !== 0) {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				// column is defined so now run row layout
				const dimension = this.computeColumnElementDimensions(
					columns,
					columnElements.length,
<<<<<<< HEAD
					prevDimension
				);
				// if parent is row then set right to parent width else page width
				if (parentContainer.layoutType == "row") {
=======
					prevDimension,
				);
				// if parent is row then set right to parent width else page width
				if (parentContainer.layoutType === "row") {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
					dimension.right = parentContainer.width;
				} else {
					dimension.right =
						MainStore.page.width -
						MainStore.page.marginLeft -
						MainStore.page.marginRight;
				}
				prevDimension = dimension;
				const wrapper = this.createColumnWrapperElement(
					dimension,
					columns,
<<<<<<< HEAD
					parentContainer
=======
					parentContainer,
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				);
				columnElements.push(wrapper);
			}
			return columnElements;
		},
		computeLayoutInsideRectangle(childElements) {
<<<<<<< HEAD
			if (childElements.at(-1).type == "rectangle") {
				const el = childElements.at(-1);
				if (el.type == "rectangle") {
					el.childrens = this.computeRowLayout(el.childrens, el);
					el.layoutType = "column";
					el.classes = el.classes.filter((c) => c != "relative-column");
					el.rectangleContainer = true;
					if (el.childrens.some((e) => e.heightType == "auto-min-height")) {
						el.heightType = "auto-min-height";
					} else if (el.childrens.some((e) => e.heightType == "auto")) {
=======
			if (childElements.at(-1).type === "rectangle") {
				const el = childElements.at(-1);
				if (el.type === "rectangle") {
					el.childrens = this.computeRowLayout(el.childrens, el);
					el.layoutType = "column";
					el.classes = el.classes.filter((c) => c !== "relative-column");
					el.rectangleContainer = true;
					if (el.childrens.some((e) => e.heightType === "auto-min-height")) {
						el.heightType = "auto-min-height";
					} else if (el.childrens.some((e) => e.heightType === "auto")) {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
						el.heightType = "auto";
					} else {
						el.heightType = "fixed";
					}
				}
			}
		},
		handleHeaderFooterOverlapping() {
			const elements = this.Elements;
			const MainStore = useMainStore();

			const throwOverlappingError = (type) => {
				let message = __(`Please resolve overlapping elements `);
				const messageType = Object.freeze({
					header: "<b>" + __("in header") + "</b>",
					footer: "<b>" + __("in footer") + "</b>",
					auto: __("in table, auto layout failed"),
				});
				message += messageType[type];
				frappe.show_alert(
					{
						message: message,
						indicator: "red",
					},
<<<<<<< HEAD
					6
=======
					6,
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				);
				throw new Error(message);
			};

<<<<<<< HEAD
			const tableElement = this.Elements.filter((el) => el.type == "table");

			if (tableElement.length == 1 && MainStore.isHeaderFooterAuto) {
=======
			const tableElement = this.Elements.filter((el) => el.type === "table");

			if (tableElement.length === 1 && MainStore.isHeaderFooterAuto) {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				if (!this.autoCalculateHeaderFooter(tableElement[0])) {
					throwOverlappingError("auto");
				}
			} else {
				elements.forEach((element) => {
					if (
						element.startY < MainStore.page.headerHeight &&
						element.startY + element.height > MainStore.page.headerHeight
					) {
						throwOverlappingError("header");
					} else if (
						element.startY <
							MainStore.page.height -
								MainStore.page.footerHeight -
								MainStore.page.marginTop -
								MainStore.page.marginBottom &&
						element.startY + element.height >
							MainStore.page.height -
								MainStore.page.footerHeight -
								MainStore.page.marginTop -
								MainStore.page.marginBottom
					) {
						throwOverlappingError("footer");
					}
				});
			}
		},
		autoCalculateHeaderFooter(tableEl) {
			const MainStore = useMainStore();

			if (this.isElementOverlapping(tableEl)) return false;

			MainStore.page.headerHeight = tableEl.startY - 1;
			MainStore.page.footerHeight =
				MainStore.page.height +
				1 -
				(tableEl.startY +
					tableEl.height +
					MainStore.page.marginTop +
					MainStore.page.marginBottom);

			return true;
		},
<<<<<<< HEAD
		computeRowElementDimensions(row, index, prevDimensions = null, containerType = "row") {
=======
		computeRowElementDimensions(
			row,
			index,
			prevDimensions = null,
			containerType = "row",
		) {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			const MainStore = useMainStore();
			if (!prevDimensions) {
				prevDimensions = {
					left:
						MainStore.page.width -
						MainStore.page.marginRight -
						MainStore.page.marginLeft,
					bottom: 0,
				};
			}
			return this.calculateWrapperElementDimensions(
				prevDimensions,
				row,
				containerType,
<<<<<<< HEAD
				index
=======
				index,
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			);
		},
		computeColumnElementDimensions(column, index, prevDimensions = null) {
			if (!prevDimensions) {
				prevDimensions = {
					right: 0,
				};
			}
<<<<<<< HEAD
			return this.calculateWrapperElementDimensions(prevDimensions, column, "column", index);
		},
		// TODO: move logic to computeRowElementDimensions
		calculateWrapperElementDimensions(prevDimensions, children, containerType, index) {
=======
			return this.calculateWrapperElementDimensions(
				prevDimensions,
				column,
				"column",
				index,
			);
		},
		// TODO: move logic to computeRowElementDimensions
		calculateWrapperElementDimensions(
			prevDimensions,
			children,
			containerType,
			index,
		) {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			// basically returns lowest left - top  highest right - bottom from all of the children elements
			const MainStore = useMainStore();
			const parentRect = {
				top: 0,
				left: 0,
				width:
<<<<<<< HEAD
					MainStore.page.width - MainStore.page.marginLeft - MainStore.page.marginRight,
				height:
					MainStore.page.height - MainStore.page.marginTop - MainStore.page.marginBottom,
			};
			let offsetRect = children.reduce(
				(offset, currentElement) => {
					let currentElementRect = {
=======
					MainStore.page.width -
					MainStore.page.marginLeft -
					MainStore.page.marginRight,
				height:
					MainStore.page.height -
					MainStore.page.marginTop -
					MainStore.page.marginBottom,
			};
			const offsetRect = children.reduce(
				(offset, currentElement) => {
					const currentElementRect = {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
						top: currentElement.startY,
						left: currentElement.startX,
						right: currentElement.startX + currentElement.width,
						bottom: currentElement.startY + currentElement.height,
					};
<<<<<<< HEAD
					currentElementRect.left < offset.left &&
						(offset.left = currentElementRect.left);
					currentElementRect.top < offset.top && (offset.top = currentElementRect.top);
					currentElementRect.right > offset.right &&
						(offset.right = currentElementRect.right);
					currentElementRect.bottom > offset.bottom &&
						(offset.bottom = currentElementRect.bottom);
					return offset;
				},
				{ left: 9999, top: 9999, right: 0, bottom: 0 }
			);
			(offsetRect.top -= parentRect.top), (offsetRect.left -= parentRect.left);
			(offsetRect.right -= parentRect.left), (offsetRect.bottom -= parentRect.top);

			if (containerType == "header" && index == 0) {
				offsetRect.top = 0;
			}
			if (containerType == "body") {
				if (index == 0 && offsetRect.top >= MainStore.page.headerHeight) {
=======
					if (currentElementRect.left < offset.left) {
						offset.left = currentElementRect.left;
					}
					if (currentElementRect.top < offset.top) {
						offset.top = currentElementRect.top;
					}
					if (currentElementRect.right > offset.right) {
						offset.right = currentElementRect.right;
					}
					if (currentElementRect.bottom > offset.bottom) {
						offset.bottom = currentElementRect.bottom;
					}
					return offset;
				},
				{ left: 9999, top: 9999, right: 0, bottom: 0 },
			);
			offsetRect.top -= parentRect.top;
			offsetRect.left -= parentRect.left;
			offsetRect.right -= parentRect.left;
			offsetRect.bottom -= parentRect.top;

			if (containerType === "header" && index === 0) {
				offsetRect.top = 0;
			}
			if (containerType === "body") {
				if (index === 0 && offsetRect.top >= MainStore.page.headerHeight) {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
					offsetRect.top = MainStore.page.headerHeight;
				}
			}
			// element is parent level row.
			if (index > 0 && ["header", "body", "footer"].includes(containerType)) {
				offsetRect.top = prevDimensions.bottom;
			}
<<<<<<< HEAD
			if (containerType == "column") {
				offsetRect.left = prevDimensions.right;
				offsetRect.top = 0;
			}
			if (containerType == "row") {
				if (index == 0) {
=======
			if (containerType === "column") {
				offsetRect.left = prevDimensions.right;
				offsetRect.top = 0;
			}
			if (containerType === "row") {
				if (index === 0) {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
					offsetRect.top = 0;
				} else {
					offsetRect.top = prevDimensions.bottom;
				}
			}
			return offsetRect;
		},
		cleanUpElementsForSave(rows, type) {
			if (this.checkIfPrintFormatIsEmpty(rows, type)) return;
			const MainStore = useMainStore();
			const fontsObject = {};
			switch (type) {
				case "header":
					MainStore.printHeaderFonts = fontsObject;
					break;
				case "body":
					MainStore.printBodyFonts = fontsObject;
					break;
				case "footer":
					MainStore.printFooterFonts = fontsObject;
			}
			return rows.map((element) => {
<<<<<<< HEAD
				let newElement = this.childrensSave(element, fontsObject);
				newElement.classes = newElement.classes.filter(
					(name) => ["inHeaderFooter", "overlappingHeaderFooter"].indexOf(name) == -1
=======
				const newElement = this.childrensSave(element, fontsObject);
				newElement.classes = newElement.classes.filter(
					(name) =>
						["inHeaderFooter", "overlappingHeaderFooter"].indexOf(name) === -1,
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				);
				return newElement;
			});
		},
		checkIfPrintFormatIsEmpty(elements, type) {
			const MainStore = useMainStore();
<<<<<<< HEAD
			if (elements.length == 0) {
=======
			if (elements.length === 0) {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				switch (type) {
					case "header":
						MainStore.printHeaderFonts = null;
						break;
<<<<<<< HEAD
					case "body":
						MainStore.printBodyFonts = null;
						let message = __("Atleast 1 element is required inside body");
=======
					case "body": {
						MainStore.printBodyFonts = null;
						const message = __("At least 1 element is required inside body");
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
						frappe.show_alert(
							{
								message: message,
								indicator: "red",
							},
<<<<<<< HEAD
							5
						);
						// This is intentionally using throw to stop the execution
						throw new Error(message);
=======
							5,
						);
						// This is intentionally using throw to stop the execution
						throw new Error(message);
					}
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
					case "footer":
						MainStore.printFooterFonts = null;
						break;
				}
				return true;
			}
			return false;
		},
		childrensSave(element, printFonts = null) {
<<<<<<< HEAD
			let saveEl = { ...element };
=======
			const saveEl = { ...element };
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			delete saveEl.DOMRef;
			delete saveEl.snapPoints;
			delete saveEl.snapEdges;
			delete saveEl.parent;
			this.cleanUpDynamicContent(saveEl);
<<<<<<< HEAD
			if (saveEl.type == "table") {
=======
			if (saveEl.type === "table") {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				saveEl.table = { ...saveEl.table };
				delete saveEl.table.childfields;
				delete saveEl.table.default_layout;
			}
<<<<<<< HEAD
			if (printFonts && ["text", "table"].indexOf(saveEl.type) != -1) {
				handlePrintFonts(saveEl, printFonts);
			}
			if (saveEl.type == "rectangle" || saveEl.type == "page") {
=======
			if (printFonts && ["text", "table"].indexOf(saveEl.type) !== -1) {
				handlePrintFonts(saveEl, printFonts);
			}
			if (saveEl.type === "rectangle" || saveEl.type === "page") {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				const childrensArray = saveEl.childrens;
				saveEl.childrens = [];
				childrensArray.forEach((el) => {
					const child = this.childrensSave(el, printFonts);
					child && saveEl.childrens.push(child);
				});
			}

			return saveEl;
		},
		cleanUpDynamicContent(element) {
			const MainStore = useMainStore();
			if (
				["table", "image"].includes(element.type) ||
				(["text", "barcode"].includes(element.type) && element.isDynamic)
			) {
<<<<<<< HEAD
				if (["text", "barcode"].indexOf(element.type) != -1) {
=======
				if (["text", "barcode"].indexOf(element.type) !== -1) {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
					element.dynamicContent = [
						...element.dynamicContent.map((el) => {
							const newEl = { ...el };
							if (!el.is_static) {
								newEl.value = "";
							}
							return newEl;
						}),
					];
					element.selectedDynamicText = null;
				} else if (element.type === "table") {
					element.columns = [
						...element.columns.map((el) => {
							const newEl = { ...el };
							delete newEl.DOMRef;
							return newEl;
						}),
					];
					element.columns.forEach((col) => {
						if (!col.dynamicContent) return;
						col.dynamicContent = [
							...col.dynamicContent.map((el) => {
								const newEl = { ...el };
								if (!el.is_static) {
									newEl.value = "";
								}
								return newEl;
							}),
						];
						col.selectedDynamicText = null;
					});
				} else {
					element.image = { ...element.image };
					if (MainStore.is_standard) {
						// remove file_url and file_name if format is standard
<<<<<<< HEAD
						["value", "name", "file_name", "file_url", "modified"].forEach((key) => {
							element.image[key] = "";
						});
=======
						["value", "name", "file_name", "file_url", "modified"].forEach(
							(key) => {
								element.image[key] = "";
							},
						);
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
					}
				}
			}
		},
<<<<<<< HEAD
		createWrapperElement(dimensions, parent) {
			const MainStore = useMainStore();
			const coordinates = {};
			if (parent.type == "page") {
				coordinates["startY"] = dimensions.top;
				coordinates["pageY"] = dimensions.top;
				coordinates["startX"] = 0;
				coordinates["pageX"] = 0;
			} else if (parent.layoutType == "row") {
				coordinates["startY"] = 0;
				coordinates["pageY"] = 0;
				coordinates["startX"] = dimensions.left;
				coordinates["pageX"] = dimensions.left;
			} else {
				coordinates["startY"] = dimensions.top;
				coordinates["pageY"] = dimensions.top;
				coordinates["startX"] = dimensions.left;
				coordinates["pageX"] = dimensions.left;
			}
			const wrapper = createRectangle(coordinates, parent);
			wrapper.layoutType = parent.layoutType == "row" ? "column" : "row";
			if (wrapper.layoutType == "column") {
				wrapper.width = dimensions.right - dimensions.left;
				wrapper.height = parent.height || 0;
				wrapper.classes = wrapper.classes.filter((c) => c != "relative-column");
				wrapper.classes.push("relative-column");
				wrapper.relativeColumn = true;
			} else {
				wrapper.width =
					parent.width ||
					MainStore.page.width - MainStore.page.marginLeft - MainStore.page.marginRight;
				wrapper.height = dimensions.bottom - dimensions.top;
				wrapper.classes = wrapper.classes.filter((c) => c != "relative-row");
				wrapper.classes.push("relative-row");
				wrapper.classes.push(wrapper.id);
			}
			return wrapper;
		},
		updateChildrenInRowWrapper(wrapper, children) {
			wrapper.childrens = children;
			if (
				(wrapper.childrens.length == 1 &&
					wrapper.childrens[0].heightType == "auto-min-height") ||
				wrapper.childrens.some(
					(el) =>
						["row", "column"].includes(el.layoutType) &&
						el.heightType == "auto-min-height"
=======
		// createWrapperElement(dimensions, parent) {
		// 	const MainStore = useMainStore();
		// 	const coordinates = {};
		// 	if (parent.type == "page") {
		// 		coordinates["startY"] = dimensions.top;
		// 		coordinates["pageY"] = dimensions.top;
		// 		coordinates["startX"] = 0;
		// 		coordinates["pageX"] = 0;
		// 	} else if (parent.layoutType == "row") {
		// 		coordinates["startY"] = 0;
		// 		coordinates["pageY"] = 0;
		// 		coordinates["startX"] = dimensions.left;
		// 		coordinates["pageX"] = dimensions.left;
		// 	} else {
		// 		coordinates["startY"] = dimensions.top;
		// 		coordinates["pageY"] = dimensions.top;
		// 		coordinates["startX"] = dimensions.left;
		// 		coordinates["pageX"] = dimensions.left;
		// 	}
		// 	const wrapper = createRectangle(coordinates, parent);
		// 	wrapper.layoutType = parent.layoutType == "row" ? "column" : "row";
		// 	if (wrapper.layoutType == "column") {
		// 		wrapper.width = dimensions.right - dimensions.left;
		// 		wrapper.height = parent.height || 0;
		// 		wrapper.classes = wrapper.classes.filter((c) => c != "relative-column");
		// 		wrapper.classes.push("relative-column");
		// 		wrapper.relativeColumn = true;
		// 	} else {
		// 		wrapper.width =
		// 			parent.width ||
		// 			MainStore.page.width - MainStore.page.marginLeft - MainStore.page.marginRight;
		// 		wrapper.height = dimensions.bottom - dimensions.top;
		// 		wrapper.classes = wrapper.classes.filter((c) => c != "relative-row");
		// 		wrapper.classes.push("relative-row");
		// 		wrapper.classes.push(wrapper.id);
		// 	}
		// 	return wrapper;
		// },
		updateChildrenInRowWrapper(wrapper, children) {
			wrapper.childrens = children;
			if (
				(wrapper.childrens.length === 1 &&
					wrapper.childrens[0].heightType === "auto-min-height") ||
				wrapper.childrens.some(
					(el) =>
						["row", "column"].includes(el.layoutType) &&
						el.heightType === "auto-min-height",
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				)
			) {
				wrapper.heightType = "auto-min-height";
			} else if (
<<<<<<< HEAD
				(wrapper.childrens.length == 1 && wrapper.childrens[0].heightType == "auto") ||
				wrapper.childrens.some(
					(el) => ["row", "column"].includes(el.layoutType) && el.heightType == "auto"
=======
				(wrapper.childrens.length === 1 &&
					wrapper.childrens[0].heightType === "auto") ||
				wrapper.childrens.some(
					(el) =>
						["row", "column"].includes(el.layoutType) &&
						el.heightType === "auto",
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				)
			) {
				wrapper.heightType = "auto";
			} else {
				wrapper.heightType = "fixed";
			}
			wrapper.childrens.sort((a, b) => (a.startY < b.startY ? -1 : 1));
			wrapper.startX = 0;
			return;
		},
		updateRowChildrenDimensions(wrapper, children, parent) {
<<<<<<< HEAD
			if (parent.type == "page") {
=======
			if (parent.type === "page") {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				children.forEach((el) => {
					el.startY -= wrapper.startY;
				});
				return;
			}
			children.forEach((el) => {
				el.startY -= wrapper.startY;
			});
		},
		updateColumnChildrenDimensions(wrapper, children) {
			children.sort((a, b) => (a.startX < b.startX ? -1 : 1));

			children.forEach((el) => {
				el.startY -= wrapper.startY;
				el.startX -= wrapper.startX;
			});
		},
		updateChildrenInColumnWrapper(wrapper, children) {
			wrapper.childrens = children;
			wrapper.childrens.forEach((el) => {
				el.startY += wrapper.startY;
			});
			// TODO: add better control for dynamic height
			wrapper.startY = 0;
			if (
				wrapper.childrens.some(
<<<<<<< HEAD
					(el) => el.layoutType == "row" || el.heightType == "auto-min-height"
=======
					(el) =>
						el.layoutType === "row" || el.heightType === "auto-min-height",
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				)
			) {
				wrapper.heightType = "auto-min-height";
			} else if (
				wrapper.childrens.some(
<<<<<<< HEAD
					(el) => el.layoutType == "column" || el.heightType == "auto"
=======
					(el) => el.layoutType === "column" || el.heightType === "auto",
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				)
			) {
				wrapper.heightType = "auto";
			} else {
				wrapper.heightType = "fixed";
			}
		},
		createRowWrapperElement(dimension, currentRow, parent) {
			const MainStore = useMainStore();
			const coordinates = {};
<<<<<<< HEAD
			if (parent.type == "page") {
=======
			if (parent.type === "page") {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				coordinates["startY"] = dimension.top;
				coordinates["pageY"] = dimension.top;
				coordinates["startX"] = 0;
				coordinates["pageX"] = 0;
			} else {
				coordinates["startY"] = dimension.top;
				coordinates["pageY"] = dimension.top;
				coordinates["startX"] = dimension.left;
				coordinates["pageX"] = dimension.left;
			}
			const wrapper = createRectangle(coordinates, parent);
			wrapper.layoutType = "row";
			wrapper.width =
				parent.width ||
<<<<<<< HEAD
				MainStore.page.width - MainStore.page.marginLeft - MainStore.page.marginRight;
			wrapper.height = dimension.bottom - dimension.top;
			wrapper.classes = wrapper.classes.filter((c) => c != "relative-row");
=======
				MainStore.page.width -
					MainStore.page.marginLeft -
					MainStore.page.marginRight;
			wrapper.height = dimension.bottom - dimension.top;
			wrapper.classes = wrapper.classes.filter((c) => c !== "relative-row");
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			wrapper.classes.push("relative-row");
			delete wrapper.parent;
			this.updateRowElement(wrapper, currentRow, parent);
			return wrapper;
		},
		updateRowElement(wrapper, currentRow, parent) {
			wrapper.layoutType = "row";
			this.updateRowChildrenDimensions(wrapper, currentRow, parent);
			let childElements = [...currentRow];
			const columnEls = this.computeColumnLayout(childElements, wrapper);
			if (columnEls) {
				childElements = columnEls;
			} else {
				this.computeLayoutInsideRectangle(childElements);
			}
			this.updateChildrenInRowWrapper(wrapper, childElements);
			if (
<<<<<<< HEAD
				(childElements.length == 1 && childElements[0].heightType == "auto-min-height") ||
				childElements.some(
					(el) =>
						["row", "column"].includes(el.layoutType) &&
						el.heightType == "auto-min-height"
=======
				(childElements.length === 1 &&
					childElements[0].heightType === "auto-min-height") ||
				childElements.some(
					(el) =>
						["row", "column"].includes(el.layoutType) &&
						el.heightType === "auto-min-height",
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				)
			) {
				wrapper.heightType = "auto-min-height";
			} else if (
<<<<<<< HEAD
				(childElements.length == 1 && childElements[0].heightType == "auto") ||
				childElements.some(
					(el) => ["row", "column"].includes(el.layoutType) && el.heightType == "auto"
=======
				(childElements.length === 1 &&
					childElements[0].heightType === "auto") ||
				childElements.some(
					(el) =>
						["row", "column"].includes(el.layoutType) &&
						el.heightType === "auto",
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				)
			) {
				wrapper.heightType = "auto";
			} else {
				wrapper.heightType = "fixed";
			}
<<<<<<< HEAD
			if (
				(childElements.length == 1 && childElements[0].style.breakInside == "avoid") ||
				childElements.some(
					(el) =>
						["row", "column"].includes(el.layoutType) &&
						el.style.breakInside == "avoid"
				)
			) {
				wrapper.breakInside = "avoid";
			}
=======
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
		},
		createColumnWrapperElement(dimension, currentColumn, parent) {
			const coordinates = {
				startY: dimension.top,
				pageY: dimension.top,
				startX: dimension.left,
				pageX: dimension.left,
			};
			const wrapper = createRectangle(coordinates, parent);
			wrapper.layoutType = "column";
			wrapper.width = dimension.right - dimension.left;
			wrapper.height = parent.height;
<<<<<<< HEAD
			wrapper.classes = wrapper.classes.filter((c) => c != "relative-column");
=======
			wrapper.classes = wrapper.classes.filter((c) => c !== "relative-column");
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			wrapper.classes.push("relative-column");
			wrapper.relativeColumn = true;
			delete wrapper.parent;
			this.updateColumnElement(wrapper, currentColumn);
			return wrapper;
		},
		updateColumnElement(wrapper, currentColumn) {
			wrapper.layoutType = "column";
			this.updateColumnChildrenDimensions(wrapper, currentColumn);
			let childElements = [...currentColumn];
			const rowEls = this.computeRowLayout(childElements, wrapper);
			if (rowEls) {
				childElements = rowEls;
			} else {
				this.computeLayoutInsideRectangle(childElements);
			}
			this.updateChildrenInColumnWrapper(wrapper, childElements);
			if (
<<<<<<< HEAD
				(childElements.length == 1 && childElements[0].heightType == "auto-min-height") ||
				childElements.some(
					(el) =>
						["row", "column"].includes(el.layoutType) &&
						el.heightType == "auto-min-height"
=======
				(childElements.length === 1 &&
					childElements[0].heightType === "auto-min-height") ||
				childElements.some(
					(el) =>
						["row", "column"].includes(el.layoutType) &&
						el.heightType === "auto-min-height",
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				)
			) {
				wrapper.heightType = "auto-min-height";
			} else if (
<<<<<<< HEAD
				(childElements.length == 1 && childElements[0].heightType == "auto") ||
				childElements.some(
					(el) => ["row", "column"].includes(el.layoutType) && el.heightType == "auto"
=======
				(childElements.length === 1 &&
					childElements[0].heightType === "auto") ||
				childElements.some(
					(el) =>
						["row", "column"].includes(el.layoutType) &&
						el.heightType === "auto",
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				)
			) {
				wrapper.heightType = "auto";
			} else {
				wrapper.heightType = "fixed";
			}
<<<<<<< HEAD
			if (
				(childElements.length == 1 && childElements[0].style.breakInside == "avoid") ||
				childElements.some(
					(el) => ["row", "column"].includes(el.layoutType) && el.style.breakInside == "avoid"
				)
			) {
				wrapper.breakInside = "avoid";
			}
=======
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
		},
		async printFormatCopyOnOlderSchema(objectToSave) {
			// TODO: have better message.
			let message = __(
<<<<<<< HEAD
				"<b>This Print Format was created from older version of Print Designer.</b>"
			);
			message += "<hr />";
			message += __(
				"It is not compatible with current version so instead make copy of this format using new version"
=======
				"<b>This Print Format was created from older version of Print Designer.</b>",
			);
			message += "<hr />";
			message += __(
				"It is not compatible with current version so instead make copy of this format using new version",
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			);
			message += "<hr />";
			message += __(`Do you want to save copy of it ?`);

			frappe.confirm(
				message,
				async () => {
					this.promptUserForNewFormatName(objectToSave);
				},
				async () => {
					frappe.show_alert(
						{
							message: `Print Format not saved`,
							indicator: "red",
						},
<<<<<<< HEAD
						5
					);
					// intentionally throwing error to stop the saving the format
					throw new Error(__("Print Format not saved"));
				}
=======
						5,
					);
					// intentionally throwing error to stop the saving the format
					throw new Error(__("Print Format not saved"));
				},
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			);
		},
		async promptUserForNewFormatName(objectToSave) {
			const MainStore = useMainStore();
			let nextFormatCopyNumber = 0;
			for (let i = 0; i < 100; i++) {
				const pf_exists = await frappe.db.exists(
					"Print Format",
<<<<<<< HEAD
					MainStore.printDesignName + " ( Copy " + (i ? i : "") + " )"
=======
					`${MainStore.printDesignName} ( Copy ${i ? i : ""} )`,
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				);
				if (pf_exists) continue;
				nextFormatCopyNumber = i;
				break;
			}
			// This is just default value for the new print format name
<<<<<<< HEAD
			const print_format_name =
				MainStore.printDesignName +
				" ( Copy " +
				(nextFormatCopyNumber ? nextFormatCopyNumber : "") +
				" )";

			let d = new frappe.ui.Dialog({
=======
			const print_format_name = `${MainStore.printDesignName} ( Copy ${
				nextFormatCopyNumber ? nextFormatCopyNumber : ""
			} )`;

			const d = new frappe.ui.Dialog({
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				title: "New Print Format",
				fields: [
					{
						label: "Name",
						fieldname: "print_format_name",
						fieldtype: "Data",
						reqd: 1,
						default: print_format_name,
					},
				],
				size: "small",
				primary_action_label: "Save",
				static: true,
				async primary_action(values) {
					try {
						await frappe.db.insert({
							doctype: "Print Format",
							name: values.print_format_name,
							doc_type: MainStore.doctype,
							print_designer: 1,
							print_designer_header: objectToSave.print_designer_header,
							print_designer_body: objectToSave.print_designer_body,
							print_designer_after_table: null,
							print_designer_footer: objectToSave.print_designer_footer,
<<<<<<< HEAD
							print_designer_print_format: objectToSave.print_designer_print_format,
=======
							print_designer_print_format:
								objectToSave.print_designer_print_format,
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
							print_designer_settings: objectToSave.print_designer_settings,
						});
						d.hide();
						frappe.set_route("print-designer", values.print_format_name);
					} catch (error) {
						console.error(error);
					}
				},
			});
			d.get_close_btn().on("click", () => {
				frappe.show_alert(
					{
						message: `Print Format not saved`,
						indicator: "red",
					},
<<<<<<< HEAD
					5
=======
					5,
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				);
			});
			d.show();
		},
		handleDynamicContent(element) {
			const MainStore = useMainStore();
			if (
<<<<<<< HEAD
				element.type == "table" ||
				(["text", "image", "barcode"].indexOf(element.type) != -1 && element.isDynamic)
			) {
				if (["text", "barcode"].indexOf(element.type) != -1) {
=======
				element.type === "table" ||
				(["text", "image", "barcode"].includes(element.type) &&
					element.isDynamic)
			) {
				if (["text", "barcode"].includes(element.type)) {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
					element.dynamicContent = [
						...element.dynamicContent.map((el) => {
							const newEl = { ...el };
							if (!el.is_static) {
								newEl.value = "";
							}
							return newEl;
						}),
					];
					element.selectedDynamicText = null;
					MainStore.dynamicData.push(...element.dynamicContent);
				} else if (element.type === "table") {
					if (element.table) {
						const mf = MainStore.metaFields.find(
<<<<<<< HEAD
							(field) => field.fieldname == element.table.fieldname
=======
							(field) => field.fieldname === element.table.fieldname,
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
						);
						if (mf) {
							element.table = mf;
						}
					}

					element.columns = [
						...element.columns.map((el) => {
							return { ...el };
						}),
					];
					element.columns.forEach((col) => {
						if (!col.dynamicContent) return;
						col.dynamicContent = [
							...col.dynamicContent.map((el) => {
								const newEl = { ...el };
								if (!el.is_static) {
									newEl.value = "";
								}
								return newEl;
							}),
						];
						col.selectedDynamicText = null;
						MainStore.dynamicData.push(...col.dynamicContent);
					});
				} else {
					element.image = { ...element.image };
					MainStore.dynamicData.push(element.image);
				}
			}
		},
<<<<<<< HEAD
		childrensLoad(element, parent) {
			element.parent = parent;
			element.DOMRef = null;
			delete element.printY;
			element.isDraggable = true;
			element.isResizable = true;
			this.handleDynamicContent(element);
			if (element.type == "rectangle" || element.type == "page") {
				element.isDropZone = true;
				const childrensArray = element.childrens;
				element.childrens = [];
				childrensArray.forEach((el) => {
					const child = this.childrensLoad(el, element);
					child && element.childrens.push(child);
				});
			} else if (element.type == "text" && !element.isDynamic) {
				element.contenteditable = false;
			}

			return element;
		},
=======

		// childrensLoad(element, parent) {
		// 	element.parent = parent;
		// 	element.DOMRef = null;
		// 	delete element.printY;
		// 	element.isDraggable = true;
		// 	element.isResizable = true;
		// 	this.handleDynamicContent(element);
		// 	if (element.type === "rectangle" || element.type === "page") {
		// 		element.isDropZone = true;
		// 		const childrensArray = element.childrens;
		// 		element.childrens = [];
		// 		childrensArray.forEach((el) => {
		// 			const child = this.childrensLoad(el, element);
		// 			child && element.childrens.push(child);
		// 		});
		// 	} else if (element.type === "text" && !element.isDynamic) {
		// 		element.contenteditable = false;
		// 	}

		// 	return element;
		// },

>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
		loadSettings(settings) {
			const MainStore = useMainStore();
			if (!settings) return;
			Object.keys(settings).forEach((key) => {
				switch (key) {
					case "schema_version":
<<<<<<< HEAD
						MainStore.old_schema_version = settings["schema_version"];
					case "currentDoc":
						frappe.db
							.exists(MainStore.doctype, settings["currentDoc"])
							.then((exists) => {
								if (exists) {
									MainStore.currentDoc = settings["currentDoc"];
=======
						MainStore.old_schema_version = settings.schema_version;
						break;
					case "currentDoc":
						frappe.db
							.exists(MainStore.doctype, settings.currentDoc)
							.then((exists) => {
								if (exists) {
									MainStore.currentDoc = settings.currentDoc;
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
								}
							});
						break;
					default:
						MainStore[key] = settings[key];
						break;
				}
			});
			return;
		},
		getHeaderObject(index) {
<<<<<<< HEAD
			if (index == 0) {
				return this.Headers.find((header) => header.firstPage == true);
			} else if (index == this.Elements.length - 1) {
				return this.Headers.find((header) => header.lastPage == true);
			} else if (index % 2 != 0) {
				return this.Headers.find((header) => header.oddPage == true);
			} else {
				return this.Headers.find((header) => header.evenPage == true);
			}
		},
		getFooterObject(index) {
			if (index == 0) {
				return this.Footers.find((footer) => footer.firstPage == true);
			} else if (index == this.Elements.length - 1) {
				return this.Footers.find((footer) => footer.lastPage == true);
			} else if (index % 2 != 0) {
				return this.Footers.find((footer) => footer.oddPage == true);
			} else {
				return this.Footers.find((footer) => footer.evenPage == true);
			}
=======
			if (index === 0) {
				return this.Headers.find((header) => header.firstPage);
			}
			if (index === this.Elements.length - 1) {
				return this.Headers.find((header) => header.lastPage);
			}
			if (index % 2 !== 0) {
				return this.Headers.find((header) => header.oddPage);
			}
			return this.Headers.find((header) => header.evenPage);
		},
		getFooterObject(index) {
			if (index === 0) {
				return this.Footers.find((footer) => footer.firstPage);
			}
			if (index === this.Elements.length - 1) {
				return this.Footers.find((footer) => footer.lastPage);
			}
			if (index % 2 !== 0) {
				return this.Footers.find((footer) => footer.oddPage);
			}
			return this.Footers.find((footer) => footer.evenPage);
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
		},
		setElementProperties(parent) {
			parent.childrens.map((element) => {
				element.DOMRef = null;
				element.parent = parent;
				delete element.printY;
				element.isDraggable = true;
				element.isResizable = true;
				this.handleDynamicContent(element);
<<<<<<< HEAD
				if (element.type == "rectangle" || element.type == "page") {
					element.isDropZone = true;
					if (element.childrens.length) {
						let childrensArray = element.childrens;
=======
				if (element.type === "rectangle" || element.type === "page") {
					element.isDropZone = true;
					if (element.childrens.length) {
						const childrensArray = element.childrens;
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
						element.childrens = [];
						childrensArray.forEach((el) => {
							element.childrens.push(this.childrensLoad(el, element));
						});
					}
<<<<<<< HEAD
				} else if (element.type == "text" && !element.isDynamic) {
=======
				} else if (element.type === "text" && !element.isDynamic) {
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
					element.contenteditable = false;
				}
				return element;
			});
		},
		createPageElement(element, type) {
			return {
				type: "page",
				childrens: [...element],
				firstPage: true,
				oddPage: true,
				evenPage: true,
				lastPage: true,
				DOMRef: null,
			};
		},
		async loadElements(printDesignName) {
			frappe.dom.freeze(__("Loading Print Format"));
<<<<<<< HEAD
			const printFormat = await frappe.db.get_value("Print Format", printDesignName, [
				"print_designer_header",
				"print_designer_body",
				"print_designer_after_table",
				"print_designer_footer",
				"print_designer_settings",
			]);
=======
			const printFormat = await frappe.db.get_value(
				"Print Format",
				printDesignName,
				[
					"print_designer_header",
					"print_designer_body",
					"print_designer_after_table",
					"print_designer_footer",
					"print_designer_settings",
				],
			);
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			let settings = JSON.parse(printFormat.message.print_designer_settings);
			this.loadSettings(settings);

			let ElementsBody = JSON.parse(printFormat.message.print_designer_body);
<<<<<<< HEAD
			let ElementsAfterTable = JSON.parse(printFormat.message.print_designer_after_table);
=======
			let ElementsAfterTable = JSON.parse(
				printFormat.message.print_designer_after_table,
			);
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			const headers = JSON.parse(printFormat.message.print_designer_header);
			const footers = JSON.parse(printFormat.message.print_designer_footer);
			headers.forEach((header) => {
				this.Headers.push(header);
			});
			footers.forEach((footer) => {
				this.Footers.push(footer);
			});
			// backwards compatibility :(
			if (ElementsAfterTable && ElementsAfterTable.length) {
				ElementsBody[0].childrens.push(...ElementsAfterTable);
			}
			this.Elements.length = 0;
			this.Elements.push(...ElementsBody);
			ElementsBody.forEach((page, index) => {
				page.header = [
<<<<<<< HEAD
					createHeaderFooterElement(this.getHeaderObject(index).childrens, "header"),
				];
				page.footer = [
					createHeaderFooterElement(this.getFooterObject(index).childrens, "footer"),
=======
					createHeaderFooterElement(
						this.getHeaderObject(index).childrens,
						"header",
					),
				];
				page.footer = [
					createHeaderFooterElement(
						this.getFooterObject(index).childrens,
						"footer",
					),
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
				];
			});
			this.Elements.forEach((page) => this.setElementProperties(page));
			frappe.dom.unfreeze();
		},
		setPrimaryTable(tableEl, value) {
			if (!value) {
				tableEl.isPrimaryTable = value;
				return;
			}
<<<<<<< HEAD
			tables = this.Elements.filter((el) => el.type == "table");
			tables.forEach((t) => {
				t.isPrimaryTable = t == tableEl;
=======
			const tables = this.Elements.filter((el) => el.type === "table");
			tables.forEach((t) => {
				t.isPrimaryTable = t === tableEl;
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			});
		},
		// This is called to check if the element is overlapping with any other element (row only)
		// TODO: add column calculations
		isElementOverlapping(currentEl, elements = null) {
			const MainStore = useMainStore();
			MainStore.activePage = getParentPage(currentEl.parent);
			if (!elements) {
				elements = MainStore.activePage.childrens;
			}
<<<<<<< HEAD
			const currentElIndex = currentEl.index || elements.findIndex((el) => el === currentEl);
=======
			const currentElIndex =
				currentEl.index ?? elements.findIndex((el) => el === currentEl);
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			const currentStartY = parseInt(currentEl.startY);
			const currentStartX = parseInt(currentEl.startX);
			const currentEndY = parseInt(currentEl.startY + currentEl.height);
			const currentEndX = parseInt(currentEl.startX + currentEl.width);
			return (
				elements.findIndex((el, index) => {
<<<<<<< HEAD
					if (index == currentElIndex) return false;
=======
					if (index === currentElIndex) return false;
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
					const elStartY = parseInt(el.startY);
					const elEndY = parseInt(el.startY + el.height);
					const elStartX = parseInt(el.startX);
					const elEndX = parseInt(el.startX + el.width);
					if (
						currentStartY <= elStartY &&
						elStartY <= currentEndY &&
						!(currentStartY <= elEndY && elEndY <= currentEndY) &&
						currentStartX <= elStartX &&
						elStartX <= currentEndX &&
						!(currentStartX <= elEndX && elEndX <= currentEndX)
					) {
						return true;
					} else if (
						!(currentStartY <= elStartY && elStartY <= currentEndY) &&
						currentStartY <= elEndY &&
						elEndY <= currentEndY &&
						!(currentStartX <= elStartX && elStartX <= currentEndX) &&
						currentStartX <= elEndX &&
						elEndX <= currentEndX
					) {
						return true;
					} else if (
						elStartY <= currentStartY &&
						currentStartY <= elEndY &&
						elStartY <= currentEndY &&
						currentEndY <= elEndY &&
						elStartX <= currentStartX &&
						currentStartX <= elEndX &&
						elStartX <= currentEndX &&
						currentEndX <= elEndX
					) {
						return true;
<<<<<<< HEAD
					} else {
						return false;
					}
				}) != -1
=======
					}
					return false;
				}) !== -1
>>>>>>> 39ca001769177d07a16b71422cd7a0845858f8fd
			);
		},
	},
});
