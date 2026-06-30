import { watch, markRaw } from "vue";
import { useMainStore } from "./MainStore";
import { useElementStore } from "./ElementStore";
export const fetchMeta = async () => {
  const MainStore = useMainStore();
  MainStore.doctype = await getValue(
    "Print Format",
    MainStore.printDesignName,
    "doc_type",
  );
  MainStore.rawMeta = await frappe.xcall(
    "print_designer.print_designer.page.print_designer.print_designer.get_meta",
    { doctype: MainStore.doctype },
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
  metaFields.map((field) => {
    if (field["fieldtype"] == "Table") {
      getMeta(field.options, field.fieldname);
    }
  });
  fetchDoc();
  !MainStore.getTableMetaFields.length &&
    (MainStore.controls.Table.isDisabled = true);
  return;
};

export const getMeta = async (doctype, parentField) => {
  const MainStore = useMainStore();
  const parentMetaField = MainStore.metaFields.find(
    (o) => o.fieldname == parentField,
  );
  if (
    MainStore.metaFields.find((o) => o.fieldname == parentField)["childfields"]
  ) {
    return MainStore.metaFields[parentField]["childfields"];
  }
  const exculdeFields = ["Section Break", "Column Break", "Tab Break", "HTML"];
  if (parentMetaField.fieldtype != "Table") {
    // Remove Link Field
    exculdeFields.push("Link");
  }
  const result = await frappe.xcall(
    "print_designer.print_designer.page.print_designer.print_designer.get_meta",
    { doctype },
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
  watch(
    () => MainStore.currentDoc,
    async () => {
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
      if (MainStore.numberToWordsFieldPairs.length) {
        const response = await frappe.call({
          method:
            "print_designer.print_designer.page.print_designer.print_designer.get_number_to_words_preview",
          args: {
            doctype: MainStore.doctype,
            docname: MainStore.currentDoc,
            print_format: MainStore.printDesignName,
          },
        });
        previewValues = response.message || {};
      }
      Object.assign(doc, previewValues);
      MainStore.docData = doc;
    },
    { immediate: true },
  );
};
