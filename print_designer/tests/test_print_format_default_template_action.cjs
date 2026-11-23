// The Desk actions of a saved Print Designer format.
//
// The plan of Phase 2 asks for three things on the Print Format form:
// the action "Export as Default Template", the existing backup action
// "Export Format" and the existing action "Import Format".  The menu of
// a saved Print Designer format carries each of them exactly once, and a
// format that is not a Print Designer format carries none of them.
//
// The export asks for the public format name, the filename and the
// destination category, and it sends them to the export endpoint of
// Print Designer.

const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync(
  "print_designer/public/js/print_format/print_format.js",
  "utf8",
);

let events = null;
const calls = [];
const dialogs = [];
let exportFails = false;

// The dialog of frappe offers disable_primary_action() and
// enable_primary_action().  A stub that invents another method would pass
// a client script that the browser refuses to run.
class Dialog {
  constructor(options) {
    this.options = options;
    this.hidden = false;
    this.primaryDisabled = false;
    dialogs.push(this);
  }

  show() {
    this.shown = true;
  }

  hide() {
    this.hidden = true;
  }

  disable_primary_action() {
    this.primaryDisabled = true;
  }

  enable_primary_action() {
    this.primaryDisabled = false;
  }
}

const frappe = {
  boot: {},
  ui: {
    form: {
      on: (doctype, handlers) => {
        assert.equal(doctype, "Print Format");
        events = handlers;
      },
    },
    Dialog,
  },
  xcall: () => Promise.resolve(JSON.stringify(["print_designer"])),
  user: { has_role: () => true },
  call: (options) => {
    calls.push(options);
    // The categories arrive before the dialog of the export is built.
    if (options.method.endsWith("get_categories")) {
      options.callback({
        message: [
          { value: "asean_business_suite", label: "ASEAN Business Suite" },
          { value: "generic", label: "Generic" },
        ],
      });
      return;
    }
    // The export answers with the template.  A call of an unknown method
    // is only recorded, so an endpoint that does not exist is visible in
    // the assertions on the calls.
    if (options.method.endsWith("export_as_default_template")) {
      if (exportFails) {
        if (options.error) options.error({});
        return;
      }
      options.callback({
        message: {
          filename: "receipt.json",
          template: { name: "ASEAN Receipt" },
        },
      });
    }
  },
  msgprint: () => {},
  show_alert: () => {},
  confirm: () => {},
  model: { can_write: () => false, with_doctype: () => {} },
  set_route: () => {},
};

vm.runInNewContext(source, {
  frappe,
  __: (text) => text,
  console,
  Blob: class {
    constructor(parts) {
      this.parts = parts;
    }
  },
  document: {
    body: {
      appendChild: () => {},
      removeChild: () => {},
    },
    createElement: () => ({
      href: "",
      download: "",
      click: () => {},
    }),
  },
  URL: {
    createObjectURL: () => "blob:pd-template",
    revokeObjectURL: () => {},
  },
});

function formFor({
  name = "PD Format / One",
  docType = "Payment Entry",
  printDesigner = 1,
  isNew = false,
} = {}) {
  const menu = [];

  return {
    menu,
    doc: {
      name,
      doc_type: docType,
      module: "Print Designer",
      print_designer: printDesigner,
      pd_custom_transaction_direction: "",
      pd_custom_transaction_type: "",
    },
    is_new: () => isNew,
    trigger: () => {},
    set_df_property: () => {},
    set_value: () => {},
    dashboard: { add_comment: () => {} },
    add_custom_button: () => ({ addClass: () => {} }),
    page: {
      add_menu_item: (label, callback) => {
        menu.push({ label, callback });
      },
    },
  };
}

function labels(form) {
  return form.menu.map((item) => item.label);
}

// A saved Print Designer format carries the three actions exactly once.
const saved = formFor();
events.refresh(saved);

// "Convert to Print Designer Export" is a pre-existing action of the same
// block.  It is listed here so that a duplicate of any action of the menu
// is caught.
assert.deepEqual(labels(saved), [
  "Export Format",
  "Import Format",
  "Convert to Print Designer Export",
  "Export as Default Template",
]);
console.log(
  "PASS: a saved Print Designer format carries the three actions once",
);

for (const label of [
  "Export Format",
  "Import Format",
  "Export as Default Template",
]) {
  const occurrences = labels(saved).filter((item) => item === label).length;
  assert.equal(occurrences, 1, `${label} appears ${occurrences} times`);
}
console.log("PASS: no action appears twice");

// A format that is not saved yet carries none of them.
const draft = formFor({ isNew: true });
events.refresh(draft);
assert.deepEqual(labels(draft), []);
console.log("PASS: a new format carries no action");

// A format that is not a Print Designer format carries none of them.
const plain = formFor({ printDesigner: 0 });
events.refresh(plain);
assert.deepEqual(labels(plain), []);
console.log(
  "PASS: a format that is not a Print Designer format carries no action",
);

// The backup action still exports the saved format.
calls.length = 0;
const backup = saved.menu.find((item) => item.label === "Export Format");
backup.callback();

assert.equal(calls.length, 1);
assert.equal(
  calls[0].method,
  "print_designer.api.print_format_export_import.export_print_format",
);
assert.equal(calls[0].args.print_format_name, "PD Format / One");
console.log("PASS: the backup export still calls the export of the format");

// The export asks for the public name, the filename and the category.
dialogs.length = 0;
const publish = saved.menu.find(
  (item) => item.label === "Export as Default Template",
);
publish.callback();

assert.equal(dialogs.length, 1);
const dialog = dialogs[0];
const fields = dialog.options.fields;
const byName = Object.fromEntries(
  fields.map((field) => [field.fieldname, field]),
);

assert.equal(byName.template_name.reqd, 1);
assert.equal(byName.filename.reqd, 1);
assert.ok(byName.category, "the export does not ask for a category");
// The arrays and the objects of the dialog come from the sandbox of the
// script, so they are copied into this realm before they are compared.
assert.deepEqual(
  [...byName.category.options],
  ["asean_business_suite", "generic"],
);
console.log(
  "PASS: the export asks for the public name, the filename and the category",
);

// The default file name is a file system friendly name.
assert.equal(byName.filename.default, "pd_format_one.json");
console.log("PASS: the default file name is a slug of the format name");

// The values of the dialog reach the export endpoint.
calls.length = 0;
dialog.options.primary_action({
  template_name: "ASEAN Receipt",
  filename: "receipt.json",
  category: "asean_business_suite",
  transaction_direction: "Receive",
  transaction_type: "Services",
});

assert.equal(calls.length, 1);
assert.equal(
  calls[0].method,
  "print_designer.api.default_template_export.export_as_default_template",
);
assert.deepEqual(
  { ...calls[0].args },
  {
    print_format_name: "PD Format / One",
    template_name: "ASEAN Receipt",
    category: "asean_business_suite",
    transaction_direction: "Receive",
    transaction_type: "Services",
  },
);
console.log("PASS: the chosen values reach the export endpoint");

// The dialog closes after an export that answers.
assert.equal(dialog.hidden, true);
console.log("PASS: the dialog closes after a successful export");

// A failed export leaves the dialog open and the button comes back, so
// the export can be tried again.
exportFails = true;
dialogs.length = 0;
calls.length = 0;

const retryForm = formFor();
events.refresh(retryForm);
retryForm.menu
  .find((item) => item.label === "Export as Default Template")
  .callback();

const retryDialog = dialogs[0];
retryDialog.options.primary_action({
  template_name: "ASEAN Receipt",
  filename: "receipt.json",
  category: "asean_business_suite",
});

assert.equal(
  retryDialog.primaryDisabled,
  false,
  "the button stays hidden after a failed export",
);
assert.equal(
  retryDialog.hidden,
  false,
  "the dialog closes after a failed export",
);
exportFails = false;
console.log("PASS: a failed export can be tried again");

// A format of a DocType without a profile hides the profile fields.
dialogs.length = 0;
const quotation = formFor({ docType: "Quotation" });
events.refresh(quotation);
quotation.menu
  .find((item) => item.label === "Export as Default Template")
  .callback();

const quotationFields = Object.fromEntries(
  dialogs[0].options.fields.map((field) => [field.fieldname, field]),
);

assert.equal(quotationFields.transaction_direction.hidden, true);
assert.equal(quotationFields.transaction_type.hidden, true);
console.log("PASS: a DocType without a profile hides the profile fields");
