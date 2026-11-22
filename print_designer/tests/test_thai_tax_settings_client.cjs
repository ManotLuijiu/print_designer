const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync(
  "print_designer/print_designer/doctype/thai_tax_settings/thai_tax_settings.js",
  "utf8",
);

let settingsHandler = null;
let rateHandler = null;
const calls = [];
const printed = [];

const ACCOUNT_FIELDS = [
  "default_wht_payable_account",
  "default_wht_receivable_account",
  "default_vat_input_account",
  "default_vat_output_account",
];

const frappe = {
  ui: {
    form: {
      on: (doctype, events) => {
        if (doctype === "Thai Tax Settings") {
          settingsHandler = events;
        } else {
          rateHandler = events;
        }
      },
    },
  },
  call: (options) => {
    calls.push(options);
    return options;
  },
  msgprint: (options) => {
    printed.push(options);
  },
  defaults: {
    get_user_default: () => "Demo Company",
  },
  db: {
    get_value: (...args) => {
      const callback = args[args.length - 1];
      if (typeof callback === "function") {
        callback({ name: "Demo Company", account_type: "Tax" });
      }
    },
  },
  model: {
    set_value: (doctype, name, fieldname, value) => {
      if (locals[doctype] && locals[doctype][name]) {
        locals[doctype][name][fieldname] = value;
      }
    },
  },
};

const locals = {
  "Thai WHT Rate Setting": {
    "row-1": { tax_rate: 120 },
    "row-2": { tax_rate: 5 },
  },
};

vm.runInNewContext(source, {
  frappe,
  locals,
  __: (text) => text,
});

function formFor(doc = {}) {
  const form = {
    doc: {
      name: "Thai Tax Settings",
      auto_create_accounts: 0,
      vat_rate: 7,
      default_wht_rates: [],
      ...doc,
    },
    meta: {
      has_field: (fieldname) => ACCOUNT_FIELDS.includes(fieldname),
    },
    fields_dict: Object.fromEntries(
      ACCOUNT_FIELDS.map((fieldname) => [
        fieldname,
        {
          $wrapper: {
            find: () => ({
              append: () => {},
            }),
          },
        },
      ]),
    ),
    buttons: [],
    is_new: () => false,
    set_value: (fieldname, value) => {
      form.doc[fieldname] = value;
    },
    dashboard: {
      comments: [],
      add_comment(text, color, permanent) {
        form.dashboard.comments.push({ text, color, permanent });
      },
    },
    add_custom_button(label, callback, group) {
      form.buttons.push({ label, callback, group });
    },
  };

  return form;
}

// A saved document of the settings offers the four actions of the workflow.
const form = formFor();
settingsHandler.refresh(form);

assert.deepEqual(
  form.buttons.map((button) => button.label),
  [
    "Create Thai Tax Accounts",
    "Validate Setup",
    "Install Thai Tax Fields",
    "Check System Status",
  ],
);
assert.deepEqual(
  form.buttons.map((button) => button.group),
  ["Actions", "Actions", "Setup", "Setup"],
);
console.log("PASS: a saved document offers the four actions of the workflow");

// A new document offers no action, because the settings are not saved yet.
const fresh = formFor();
fresh.is_new = () => true;
settingsHandler.refresh(fresh);

assert.deepEqual(fresh.buttons, []);
console.log("PASS: a new document offers no action");

// The creation of the accounts calls the endpoint of Print Designer.
const creating = formFor();
settingsHandler.refresh(creating);
creating.buttons[0].callback();

assert.equal(
  calls[0].method,
  "print_designer.print_designer.doctype.thai_tax_settings.thai_tax_settings.create_thai_tax_accounts",
);
assert.deepEqual({ ...calls[0].args }, { company: "Demo Company" });
assert.equal(calls[0].freeze, true);
console.log(
  "PASS: the creation of the accounts calls the endpoint of Print Designer",
);

// The installation of the fields calls the endpoint of Print Designer.
const installing = formFor();
settingsHandler.refresh(installing);
installing.buttons[2].callback();

assert.equal(
  calls[1].method,
  "print_designer.print_designer.doctype.thai_tax_settings.thai_tax_settings.install_thai_tax_fields",
);
assert.equal(calls[1].freeze, true);
console.log(
  "PASS: the installation of the fields calls the endpoint of Print Designer",
);

// The check of the system calls the endpoint of Print Designer and reads
// the answer of the server.
const checking = formFor();
settingsHandler.refresh(checking);
checking.buttons[3].callback();

assert.equal(
  calls[2].method,
  "print_designer.print_designer.doctype.thai_tax_settings.thai_tax_settings.check_thai_tax_system",
);
assert.equal(calls[2].freeze, true);
console.log(
  "PASS: the check of the system calls the endpoint of Print Designer",
);

// The answer of the check is shown to the accountant.
printed.length = 0;
calls[2].callback({
  message: {
    thai_tax_settings_exists: true,
    total_fields: 10,
    installed_fields: 10,
    missing_fields: [],
    configured_accounts: {
      wht_payable: "Payable - DC",
      wht_receivable: "Receivable - DC",
      vat_input: "VAT - DC",
      vat_output: "VAT - DC",
    },
    all_fields_installed: true,
    accounts_configured: true,
    status: "ok",
  },
});

assert.equal(printed.length, 1);
assert.equal(printed[0].indicator, "green");
assert.ok(printed[0].message.includes("Payable - DC"));
console.log("PASS: the answer of the check is shown to the accountant");

// A site that is not set up yet is answered with a warning.
printed.length = 0;
calls[2].callback({
  message: {
    thai_tax_settings_exists: true,
    total_fields: 10,
    installed_fields: 8,
    missing_fields: ["default_vat_input_account"],
    configured_accounts: {},
    all_fields_installed: false,
    accounts_configured: false,
    status: "ok",
  },
});

assert.equal(printed[0].indicator, "yellow");
assert.ok(printed[0].message.includes("default_vat_input_account"));
console.log("PASS: a site that is not set up yet is answered with a warning");

// The validation of the setup names the accounts that are missing.
printed.length = 0;
const incomplete = formFor();
settingsHandler.refresh(incomplete);
incomplete.buttons[1].callback();

assert.equal(printed.length, 1);
assert.equal(printed[0].indicator, "red");
assert.ok(printed[0].message.includes("Default WHT Payable Account"));
assert.ok(printed[0].message.includes("Default VAT Output Account"));
console.log(
  "PASS: the validation of the setup names the accounts that are missing",
);

// A setup that carries its accounts and its rates is answered with a green
// light.
printed.length = 0;
const complete = formFor({
  default_wht_payable_account: "Payable - DC",
  default_wht_receivable_account: "Receivable - DC",
  default_vat_input_account: "VAT - DC",
  default_vat_output_account: "VAT - DC",
  default_wht_rates: [{ tax_rate: 3 }],
});
settingsHandler.refresh(complete);
complete.buttons[1].callback();

assert.equal(printed[0].indicator, "green");
console.log(
  "PASS: a setup that carries its accounts is answered with a green light",
);

// A setup without the rates is warned about, even when the accounts are
// there.
printed.length = 0;
const withoutRates = formFor({
  default_wht_payable_account: "Payable - DC",
  default_wht_receivable_account: "Receivable - DC",
  default_vat_input_account: "VAT - DC",
  default_vat_output_account: "VAT - DC",
});
settingsHandler.refresh(withoutRates);
withoutRates.buttons[1].callback();

assert.equal(printed[0].indicator, "yellow");
assert.ok(printed[0].message.includes("No default WHT rates configured"));
console.log("PASS: a setup without the rates is warned about");

// The rate of the withholding tax of a row is checked when it is out of the
// range, and the row is set to the rate of the law.
rateHandler.tax_rate({}, "Thai WHT Rate Setting", "row-1");
assert.equal(locals["Thai WHT Rate Setting"]["row-1"].tax_rate, 3);
console.log("PASS: a rate out of the range is set to the rate of the law");

// A rate that is inside the range is left alone.
rateHandler.tax_rate({}, "Thai WHT Rate Setting", "row-2");
assert.equal(locals["Thai WHT Rate Setting"]["row-2"].tax_rate, 5);
console.log("PASS: a rate inside the range is left alone");
