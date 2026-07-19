import { watch } from "vue";
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

// Sync table column header labels when language changes
const syncTableColumnHeaderLabels = () => {
  const MainStore = useMainStore();
  const ElementStore = useElementStore();

  console.log(
    "[PD] syncTableColumnHeaderLabels called, Elements:",
    ElementStore.Elements.length,
  );

  const getTableChildLabel = (tableFieldname, columnFieldname) => {
    // Special case: "idx" is a virtual field added by Print Designer JS,
    // not from backend meta. It has no translation in the CSV files,
    // so translate inline based on previewLanguage.
    if (columnFieldname === "idx") {
      return MainStore.previewLanguage === "th" ? "เลขที่" : "No.";
    }
    const tableMeta = MainStore.metaFields.find(
      (meta) => meta.fieldname === tableFieldname,
    );
    if (!tableMeta?.childfields) return null;
    const childField = tableMeta.childfields.find(
      (child) => child.fieldname === columnFieldname,
    );
    return childField?.label || null;
  };

  // Iterate through all pages and their elements
  ElementStore.Elements.forEach((_page) => {
    const findTables = (elements) => {
      elements.forEach((el) => {
        if (el.type === "table" && el.columns && el.columns.length > 0) {
          // Build new columns array with translated labels
          const newColumns = el.columns.map((col) => {
            const fieldname = col.dynamicContent?.[0]?.fieldname;
            const tableFieldname = col.dynamicContent?.[0]?.tableName;

            if (fieldname) {
              const translatedLabel = tableFieldname
                ? getTableChildLabel(tableFieldname, fieldname)
                : MainStore.metaFields.find((m) => m.fieldname === fieldname)
                    ?.label;

              if (translatedLabel && translatedLabel !== col.label) {
                return { ...col, label: translatedLabel };
              }
            }
            return col;
          });

          // Replace the entire array to trigger Vue reactivity
          el.columns.splice(0, el.columns.length, ...newColumns);
        }
        // Recurse into childrens
        if (el.childrens) {
          findTables(el.childrens);
        }
      });
    };
    findTables(_page.childrens || []);
  });

  // Force re-render by incrementing the render key (used as Vue :key)
  MainStore.tableRenderKey++;
};

export const fetchMeta = async () => {
  const MainStore = useMainStore();
  MainStore.doctype = await getValue(
    "Print Format",
    MainStore.printDesignName,
    "doc_type",
  );
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
  syncDynamicLabels(MainStore);
  // Await fetchDoc so elements are loaded before syncing table column labels
  await fetchDoc();
  syncTableColumnHeaderLabels();
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
  const exculdeFields = ["Section Break", "Column Break", "Tab Break", "HTML"];
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

export const fetchDoc = async (id = null) => {
  const MainStore = useMainStore();
  const ElementStore = useElementStore();
  let doctype = MainStore.doctype;
  let doc;
  await ElementStore.loadElements(MainStore.printDesignName);
  if (MainStore.currentDoc == null) {
    if (!id) {
      let latestdoc = await frappe.db.get_list(doctype, {
        fields: ["name"],
        order_by: "modified desc",
        limit: 1,
      });
      MainStore.currentDoc = latestdoc[0]?.name;
    } else {
      MainStore.currentDoc = id;
    }
  }

  // Use a promise to properly await the async watch callback
  const fetchAndPreview = async () => {
    if (
      !(
        MainStore.currentDoc &&
        (await frappe.db.exists(MainStore.doctype, MainStore.currentDoc))
      )
    )
      return;
    doc = await frappe.db.get_doc(doctype, MainStore.currentDoc);
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
        method:
          "print_designer.print_designer.page.print_designer.print_designer.get_number_to_words_preview",
        args: {
          doctype: MainStore.doctype,
          docname: MainStore.currentDoc,
          print_format: MainStore.printDesignName,
          language: MainStore.previewLanguage,
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
        method:
          "print_designer.print_designer.page.print_designer.print_designer.translate_in_words_fields",
        args: {
          doctype: MainStore.doctype,
          docname: MainStore.currentDoc,
          language: MainStore.previewLanguage,
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

  // Trigger immediately AND set up reactive watcher
  await fetchAndPreview();
  watch(
    () => MainStore.currentDoc,
    async () => {
      await fetchAndPreview();
    },
  );
};
