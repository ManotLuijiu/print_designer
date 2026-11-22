const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync(
  "print_designer/public/js/sales_invoice/output_vat_report.js",
  "utf8",
);

let handler = null;
let route = null;

const frappe = {
  boot: {},
  ui: {
    form: {
      on: (doctype, events) => {
        assert.equal(doctype, "Sales Invoice");
        handler = events.refresh;
      },
    },
  },
  set_route: (route_name, report, filters) => {
    route = { route: route_name, report, filters };
  },
};

vm.runInNewContext(source, {
  frappe,
  __: (text) => text,
});

function formFor({ docstatus = 0, isNew = false } = {}) {
  return {
    doc: {
      docstatus,
      name: "ACC-SINV-2601-00001",
      company: "Moo Coding Co., Ltd.",
      posting_date: "2026-01-31",
    },
    is_new: () => isNew,
    buttons: [],
    removed: [],
    add_custom_button(label, callback, group) {
      this.buttons.push({ label, callback, group });
    },
    remove_custom_button(label, group) {
      this.removed.push({ label, group });
    },
  };
}

function groups(form) {
  return form.buttons.map((button) => button.group);
}

// A submitted invoice gets the action in the View group, and the old
// registration of the Tools group is removed.
frappe.boot = {
  print_designer_output_vat_report: {
    report: "Output VAT Report",
    available: true,
  },
  print_designer_output_vat_undue_report: {
    report: "Output VAT Undue Report",
    available: true,
  },
};

const submitted = formFor({ docstatus: 1 });
handler(submitted);

assert.deepEqual(
  submitted.buttons.map((button) => button.label),
  ["Output VAT Report", "Output VAT Undue Report"],
);
assert.deepEqual(groups(submitted), ["View", "View"]);
assert.deepEqual(submitted.removed, [
  { label: "Output VAT Report", group: "Tools" },
]);
console.log("PASS: a submitted invoice gets the action in the View group");

// The action opens the report of the output VAT with the invoice context.
for (const button of submitted.buttons) {
  button.callback();
  assert.equal(route.route, "query-report");
  assert.equal(route.report, button.label);
  assert.deepEqual({ ...route.filters }, {
    company: "Moo Coding Co., Ltd.",
    invoice_name: "ACC-SINV-2601-00001",
  });
}
console.log("PASS: both reports open with invoice context across all periods");

// A draft and a cancelled invoice get no action of the submitted report.
for (const docstatus of [0, 2]) {
  const other = formFor({ docstatus });
  handler(other);

  assert.deepEqual(other.buttons, []);
  assert.deepEqual(other.removed, []);
}
console.log("PASS: a draft and a cancelled invoice get no action");

// A site without the report gets no button, but the old registration of the
// Tools group is still removed.
frappe.boot = { print_designer_output_vat_report: { available: false } };

const withoutReport = formFor({ docstatus: 1 });
handler(withoutReport);

assert.deepEqual(withoutReport.buttons, []);
assert.deepEqual(withoutReport.removed, [
  { label: "Output VAT Report", group: "Tools" },
]);
console.log("PASS: a site without the report gets no button");

// A boot without the information of the report gets no button either.
frappe.boot = {};

const withoutBoot = formFor({ docstatus: 1 });
handler(withoutBoot);

assert.deepEqual(withoutBoot.buttons, []);
console.log("PASS: a boot without the report gets no button");
