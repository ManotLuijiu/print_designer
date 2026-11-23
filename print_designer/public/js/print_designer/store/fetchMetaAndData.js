import { useMainStore } from "./MainStore";
import { useElementStore } from "./ElementStore";

const formatDynamicLabel = (field, translatedLabel) => {
	if (!translatedLabel) return field.label;
	return field.tableName ? translatedLabel : `${translatedLabel} :`;
};

const syncDynamicLabels = (MainStore) => {
	const getTranslatedLabel = (field) => {
		if (!field?.fieldname) return null;

		if (field.tableName) {
			const tableMeta = MainStore.metaFields.find(
				(metaField) => metaField.fieldname === field.tableName,
			);
			const childField = tableMeta?.childfields?.find(
				(child) => child.fieldname === field.fieldname,
			);
			return childField?.label || null;
		}

		const metaField = MainStore.metaFields.find(
			(meta) => meta.fieldname === field.fieldname,
		);
		return metaField?.label || null;
	};

	MainStore.dynamicData.forEach((field) => {
		if (field?.is_static) return;
		const translatedLabel = getTranslatedLabel(field);
		if (translatedLabel) {
			field.label = formatDynamicLabel(field, translatedLabel);
		}
	});
};

// An older layout can have a translated field label but no label mode.
const legacyDefaultColumnLabels = new WeakMap();

function getColumnFieldMeta(column, MainStore) {
	const field = column.dynamicContent?.[0];
	if (!field?.fieldname) return;
	const tableName = field.tableName?.fieldname || field.tableName;
	const fields = tableName
		? MainStore.metaFields.find((meta) => meta.fieldname === tableName)
				?.childfields
		: MainStore.metaFields;
	return fields?.find((meta) => meta.fieldname === field.fieldname);
}

function getTranslatedColumnLabel(column, MainStore) {
	if (column.dynamicContent?.[0]?.fieldname === "idx") {
		return getMappedColumnLabel("Order") || "Order";
	}
	return getColumnFieldMeta(column, MainStore)?.label;
}

function getMappedColumnLabel(label) {
	const labels = useMainStore().rawMeta?.print_designer_column_labels;
	return labels && Object.hasOwn(labels, label) ? labels[label] : undefined;
}

export function getTableColumnLabel(column) {
	const label = column.label || "";
	if (!label || column.labelIsCustom === true) return label;
	const override = getMappedColumnLabel(label);
	if (override) return override;
	if (
		column.labelIsCustom === false ||
		legacyDefaultColumnLabels.get(column) === label
	) {
		const translated = getTranslatedColumnLabel(column, useMainStore());
		return getMappedColumnLabel(translated) || translated || label;
	}
	return label;
}

const syncTableColumnHeaderLabels = () => {
	const MainStore = useMainStore();
	const ElementStore = useElementStore();

	console.log(
		"[PD] syncTableColumnHeaderLabels called, Elements:",
		ElementStore.Elements.length,
	);

	const findTables = (elements) => {
		for (const element of elements || []) {
			if (element.type === "table") {
				for (const column of element.columns || []) {
					if (
						column.labelIsCustom !== undefined ||
						legacyDefaultColumnLabels.has(column)
					) {
						continue;
					}
					const field = column.dynamicContent?.[0];
					const isDefault =
						field?.fieldname &&
						column.label &&
						(column.label === field.label ||
							column.label ===
								getTranslatedColumnLabel(column, MainStore));
					legacyDefaultColumnLabels.set(
						column,
						isDefault ? column.label : null,
					);
				}
			}
			findTables(element.childrens);
		}
	};
	for (const page of ElementStore.Elements) {
		findTables(page.header);
		findTables(page.childrens);
		findTables(page.footer);
	}

	// Force re-render by incrementing the render key (used as Vue :key)
	MainStore.tableRenderKey++;
};

export const fetchMeta = async ({ loadLayout = true } = {}) => {
	const MainStore = useMainStore();
	if (loadLayout) {
		MainStore.doctype = await getValue(
			"Print Format",
			MainStore.printDesignName,
			"doc_type",
		);
	}
	MainStore.rawMeta = await frappe.xcall(
		"print_designer.print_designer.page.print_designer.print_designer.get_meta",
		{ doctype: MainStore.doctype, _lang: MainStore.previewLanguage },
	);
	// MEMORY FIX: metaFields is a 172-entry array with nested childfields per
	// Table field. The original code pushed fresh entries on every visit
	// without clearing, so a long session collecting repeated reloads would
	// grow RAM unboundedly.
	MainStore.metaFields.length = 0;

	let metaFields = MainStore.rawMeta.fields.filter((df) => {
		if (
			["Section Break", "Column Break", "Tab Break", "Image"].includes(
				df.fieldtype,
			)
		) {
			return false;
		} else {
			return true;
		}
	});
	metaFields.map((field) => {
		let obj = {};
		["fieldname", "fieldtype", "label", "options", "print_hide"].forEach(
			(attr) => {
				obj[attr] = field[attr];
			},
		);
		MainStore.metaFields.push({ ...obj });
	});
	await Promise.all(
		metaFields.map((field) => {
			if (field["fieldtype"] == "Table") {
				return getMeta(field.options, field.fieldname);
			}
			return Promise.resolve();
		}),
	);
	if (loadLayout) {
		const ElementStore = useElementStore();
		await ElementStore.loadElements(MainStore.printDesignName);
		if (!MainStore.currentDoc) {
			const latestDocs = await frappe.db.get_list(MainStore.doctype, {
				fields: ["name"],
				order_by: "modified desc",
				limit: 1,
			});
			MainStore.currentDoc = latestDocs[0]?.name;
		}
	}
	await fetchDoc();
	syncTableColumnHeaderLabels();
	syncDynamicLabels(MainStore);
	!MainStore.getTableMetaFields.length &&
		(MainStore.controls.Table.isDisabled = true);
	return;
};

export const getMeta = async (doctype, parentField) => {
	const MainStore = useMainStore();
	const parentMetaField = MainStore.metaFields.find(
		(o) => o.fieldname == parentField,
	);
	if (parentMetaField?.["childfields"]) {
		return parentMetaField["childfields"];
	}
	const exculdeFields = [
		"Section Break",
		"Column Break",
		"Tab Break",
		"HTML",
	];
	if (parentMetaField.fieldtype != "Table") {
		// Remove Link Field
		exculdeFields.push("Link");
	}
	const result = await frappe.xcall(
		"print_designer.print_designer.page.print_designer.print_designer.get_meta",
		{ doctype, _lang: MainStore.previewLanguage },
	);
	let childfields = result.fields.filter((df) => {
		if (
			exculdeFields.includes(df.fieldtype) ||
			(parentMetaField.fieldtype != "Table" && df.print_hide == 1)
		) {
			return false;
		} else {
			return true;
		}
	});

	let fields = [];
	childfields.map((field) => {
		let obj = {};
		[
			"fieldname",
			"fieldtype",
			"label",
			"options",
			"print_hide",
			"is_virtual",
			"in_list_view",
		].forEach((attr) => {
			obj[attr] = field[attr];
		});
		fields.push({ ...obj });
	});
	childfields.sort((a, b) => a.print_hide - b.print_hide);
	parentMetaField["childfields"] = fields;
	return fields;
};
export const getValue = async (doctype, name, fieldname) => {
	const result = await frappe.db.get_value(doctype, name, fieldname);

	const value = await result.message[fieldname];
	return value;
};

export const fetchDoc = async () => {
	const MainStore = useMainStore();
	const { doctype, currentDoc, previewLanguage } = MainStore;
	if (!currentDoc || !(await frappe.db.exists(doctype, currentDoc))) return;
	const doc = await frappe.db.get_doc(doctype, currentDoc);
	Object.keys(doc).forEach((element) => {
		if (
			!MainStore.metaFields.find((o) => o.fieldname == element) &&
			["name"].indexOf(element) == -1
		) {
			delete doc[element];
		}
	});
	let previewValues = {};
	console.log(
		"[PD] numberToWordsFieldPairs length:",
		MainStore.numberToWordsFieldPairs.length,
	);
	if (MainStore.numberToWordsFieldPairs.length) {
		console.log("[PD] Using get_number_to_words_preview");
		const response = await frappe.call({
			method: "print_designer.print_designer.page.print_designer.print_designer.get_number_to_words_preview",
			args: {
				doctype: MainStore.doctype,
				docname: currentDoc,
				print_format: MainStore.printDesignName,
				language: previewLanguage,
			},
		});
		console.log(
			"[PD] get_number_to_words_preview response:",
			response.message,
		);
		previewValues = response.message || {};
	} else {
		console.log("[PD] Using translate_in_words_fields");
		// ERPNext stores in_words fields in English - regenerate in requested language
		const inWordsResponse = await frappe.call({
			method: "print_designer.print_designer.page.print_designer.print_designer.translate_in_words_fields",
			args: {
				doctype: MainStore.doctype,
				docname: currentDoc,
				language: previewLanguage,
			},
		});
		console.log(
			"[PD] translate_in_words_fields response:",
			inWordsResponse.message,
		);
		if (inWordsResponse.message) {
			Object.assign(previewValues, inWordsResponse.message);
		}
	}
	if (
		currentDoc !== MainStore.currentDoc ||
		previewLanguage !== MainStore.previewLanguage
	) {
		return;
	}
	Object.assign(doc, previewValues);
	// Force Vue reactivity: reassign docData reference so watchers detect change
	MainStore.docData = { ...doc };
	console.log(
		"[PD] docData updated, in_words:",
		MainStore.docData.in_words,
		"base_in_words:",
		MainStore.docData.base_in_words,
	);
};
