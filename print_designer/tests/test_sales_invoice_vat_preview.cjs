const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync(
  "print_designer/public/js/sales_invoice/vat_preview.js",
  "utf8",
);

let handler;
let lastCall = null;
let dialog = null;

class MockDialog {
  constructor(options) {
    this.options = options;
    this.html = {};
    this.shown = false;
    dialog = this;
  }
  show() {
    this.shown = true;
  }
  set_df_property(fieldname, property, value) {
    this.html[fieldname] = value;
  }
  hide() {
    this.shown = false;
  }
}

const frappe = {
  ui: {
    form: {
      on: (doctype, events) => {
        assert.equal(doctype, "Sales Invoice");
        handler = events.refresh;
      },
    },
    Dialog: MockDialog,
  },
  call: (options) => {
    lastCall = options;
    options.callback({ message: previewData });
  },
  utils: {
    escape_html: (value) =>
      String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;"),
  },
};

let previewData = {};

vm.runInNewContext(source, {
  frappe,
  __: (text) => text,
  format_currency: (value) => `THB ${value}`,
});

function formFor({ docstatus = 0, isNew = false } = {}) {
  return {
    doc: { docstatus, name: "ACC-SINV-2601-00001" },
    is_new: () => isNew,
    buttons: [],
    add_custom_button(label, callback, group) {
      this.buttons.push({ label, callback, group });
    },
  };
}

function labels(form) {
  return form.buttons.map((button) => button.label);
}

// A saved draft gets the two preview buttons of the Preview group.
const draft = formFor();
handler(draft);
assert.deepEqual(labels(draft), [
  "Output VAT Report",
  "Output VAT Undue Report",
]);
assert.ok(draft.buttons.every((button) => button.group === "Preview"));
console.log(
  "PASS: a saved draft gets both preview buttons in the Preview group",
);

// A new invoice has no stored values yet and a submitted invoice has its
// own reports, so neither gets the buttons.
const fresh = formFor({ isNew: true });
handler(fresh);
assert.deepEqual(labels(fresh), []);

const submitted = formFor({ docstatus: 1 });
handler(submitted);
assert.deepEqual(labels(submitted), []);
console.log("PASS: a new and a submitted invoice get no preview buttons");

// The button reads the projection of the draft of that invoice.
previewData = {
  marker: "Draft Preview — Not Posted",
  note: "This is a proposal of the VAT of a draft invoice. It is not a posted ledger, not a tax invoice, not a filing and not a recognition event.",
  sales_invoice: "ACC-SINV-2601-00001",
  company: "AWS Solution Co., Ltd.",
  posting_date: "2026-01-31",
  customer: "Customer",
  treatment: "VAT Undue",
  treatment_reason: "Deferred Service",
  classification: "services",
  is_tracked: true,
  status: "Pending",
  service_base_amount: 1000,
  vat_amount: 70,
  due_vat_amount: 0,
  undue_vat_amount: 70,
  warnings: ["A note of the decision"],
};

const button = draft.buttons[0];
button.callback();
assert.equal(
  lastCall.method,
  "print_designer.api.sales_invoice_vat_preview.get_draft_vat_preview",
);
assert.equal(lastCall.args.sales_invoice, "ACC-SINV-2601-00001");
assert.ok(dialog.shown);
assert.ok(dialog.html.banner.includes("Draft Preview"));
assert.ok(dialog.html.banner.includes("not a tax invoice"));
assert.ok(dialog.html.preview.includes("ACC-SINV-2601-00001"));
assert.ok(dialog.html.preview.includes("VAT due now"));
assert.ok(dialog.html.warnings.includes("A note of the decision"));
console.log(
  "PASS: the button reads the projection and shows it as a draft preview",
);

// The undue part of the preview is the one of the Output VAT Undue Report.
draft.buttons[1].callback();
assert.ok(dialog.html.preview.includes("Prospective undue VAT"));
assert.ok(dialog.html.preview.includes("Status of the tracking"));
console.log("PASS: the undue preview shows the prospective undue VAT");

// The script is loaded for the Sales Invoice through its DocType hook.
const hooks = fs.readFileSync("print_designer/hooks.py", "utf8");
const invoiceHooks = hooks.split('"Sales Invoice": [')[1].split("],")[0];
assert.ok(invoiceHooks.includes("public/js/sales_invoice/vat_preview.js"));
console.log("PASS: the preview script runs through its DocType hook");
