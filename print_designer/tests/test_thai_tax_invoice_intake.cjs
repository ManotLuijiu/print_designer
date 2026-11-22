const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync(
  "print_designer/print_designer/doctype/thai_tax_invoice_intake/thai_tax_invoice_intake.js",
  "utf8",
);

let handler = null;
const calls = [];

const frappe = {
  ui: {
    form: {
      on: (doctype, events) => {
        assert.equal(doctype, "Thai Tax Invoice Intake");
        handler = events;
      },
    },
  },
};

vm.runInNewContext(source, {
  frappe,
  __: (text) => text,
});

function formFor(doc = {}) {
  const properties = [];
  return {
    doc: {
      name: "TTI-6911-00001",
      verification_status: "Pending",
      sync_status: "Pending",
      purchase_invoice: "",
      ...doc,
    },
    is_new: () => false,
    properties,
    calls: [],
    set_df_property(fieldname, property, value) {
      properties.push({ fieldname, property, value });
    },
    call(options) {
      this.calls.push(options);
      calls.push(options);
      return options;
    },
    reload_doc() {
      this.reloaded = true;
    },
  };
}

// The verify step calls the server method of the document with a POST.
const form = formFor();
handler.verify_invoice(form);

assert.equal(form.calls.length, 1);
assert.equal(form.calls[0].method, "set_verification_status");
assert.deepEqual({ ...form.calls[0].args }, { status: "Verified" });
assert.equal(form.calls[0].type, "POST");
assert.equal(form.calls[0].doc, form.doc);
assert.equal(form.calls[0].freeze, true);
console.log("PASS: the verify step is a POST on the document");

// The reject step carries the rejected state.
const rejecting = formFor();
handler.reject_invoice(rejecting);

assert.equal(rejecting.calls[0].method, "set_verification_status");
assert.deepEqual({ ...rejecting.calls[0].args }, { status: "Rejected" });
assert.equal(rejecting.calls[0].type, "POST");
console.log("PASS: the reject step is a POST on the document");

// The synchronization step calls the server method of the document.
const syncing = formFor();
handler.create_purchase_invoice(syncing);

assert.equal(syncing.calls[0].method, "sync_to_purchase_invoice");
assert.equal(syncing.calls[0].type, "POST");
console.log("PASS: the synchronization step is a POST on the document");

// The form is reloaded after a step, so the states of the form and of the
// database are the same.
calls[0].callback();
assert.equal(form.reloaded, true);
console.log("PASS: the form is reloaded after a step");

// A new intake has no step of the workflow.
const fresh = formFor();
fresh.is_new = () => true;
handler.refresh(fresh);
assert.deepEqual(fresh.properties, []);
console.log("PASS: a new intake offers no step of the workflow");

// A pending intake offers the verification and the rejection, and not the
// synchronization.
const pending = formFor();
handler.refresh(pending);

const hiddenOf = (form, fieldname) =>
  form.properties.find(
    (property) =>
      property.fieldname === fieldname && property.property === "hidden",
  ).value;

assert.equal(hiddenOf(pending, "verify_invoice"), false);
assert.equal(hiddenOf(pending, "reject_invoice"), false);
assert.equal(hiddenOf(pending, "create_purchase_invoice"), true);
console.log("PASS: a pending intake offers the verification and the rejection");

// A verified intake offers the synchronization and the rejection.
const verified = formFor({ verification_status: "Verified" });
handler.refresh(verified);

assert.equal(hiddenOf(verified, "verify_invoice"), true);
assert.equal(hiddenOf(verified, "reject_invoice"), false);
assert.equal(hiddenOf(verified, "create_purchase_invoice"), false);
console.log("PASS: a verified intake offers the synchronization");

// A rejected intake offers the verification again and no synchronization.
const rejected = formFor({ verification_status: "Rejected" });
handler.refresh(rejected);

assert.equal(hiddenOf(rejected, "verify_invoice"), false);
assert.equal(hiddenOf(rejected, "reject_invoice"), true);
assert.equal(hiddenOf(rejected, "create_purchase_invoice"), true);
console.log("PASS: a rejected intake offers the verification again");

// A synchronized intake offers no step of the workflow.
const synchronized = formFor({
  verification_status: "Verified",
  purchase_invoice: "ACC-PINV-2026-00001",
});
handler.refresh(synchronized);

assert.equal(hiddenOf(synchronized, "verify_invoice"), true);
assert.equal(hiddenOf(synchronized, "reject_invoice"), true);
assert.equal(hiddenOf(synchronized, "create_purchase_invoice"), true);
console.log("PASS: a synchronized intake offers no step of the workflow");
