"""Client side regression tests for the item driven WHT configuration.

The server side (``print_designer/custom/item_wht_config.py``) is
authoritative: it fills the WHT income type and the rate of a document from
the items of the document.  The client mirrors that behaviour so the form
shows the correct values while the user edits it.

The client scripts were not called on ``refresh``, so a document that never
fired the ``item_code`` handler of its child table (a document created from
another document, a draft that was loaded again, a document whose items were
entered programmatically) showed an empty income type and an empty rate -
even though "Subject to Withholding Tax" was already ticked, because that
flag is derived from the item group.

On the Sales Invoice the withholding tax amount was calculated *before* the
item driven configuration was applied, and it was not recalculated when the
item configuration arrived, so the form showed a rate of 3% next to an
amount of 0.

The tests below execute the real client scripts in a sandbox with a stubbed
``frappe`` and assert the resulting form.
"""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

CLIENT_DIR = Path(__file__).parents[1] / "public/js/thailand_wht"

CLIENT_FILES = {
    "Quotation": "thailand_wht_quotation.js",
    "Sales Order": "thailand_wht_sales_order.js",
    "Sales Invoice": "thailand_wht_sales_invoice.js",
}

ITEM_DOCTYPE = {
    "Quotation": "Quotation Item",
    "Sales Order": "Sales Order Item",
    "Sales Invoice": "Sales Invoice Item",
}

RESULT_MARKER = "__PD_RESULT__"

# The harness loads the helper and the doctype script into a fresh sandbox
# with a stubbed "frappe" and reports the resulting form.
HARNESS_JS = r"""
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const doctype = process.argv[2];
const scenario = process.argv[3];
const baseDir = process.argv[4];
const init = process.argv[5] ? JSON.parse(process.argv[5]) : {};

const FILE = {
	Quotation: 'thailand_wht_quotation.js',
	'Sales Order': 'thailand_wht_sales_order.js',
	'Sales Invoice': 'thailand_wht_sales_invoice.js',
};
const ITEM_DT = {
	Quotation: 'Quotation Item',
	'Sales Order': 'Sales Order Item',
	'Sales Invoice': 'Sales Invoice Item',
};

const handlers = {};
const alerts = [];

function makeFrappe() {
	return {
		boot: {lang: 'en'},
		show_alert: (opts) => alerts.push(opts.message),
		ui: {
			form: {
				on: (dt, obj) => {
					handlers[dt] = handlers[dt] || {};
					Object.assign(handlers[dt], obj);
				},
			},
		},
		model: {set_value: () => {}, set_value_original: null},
		db: {
			get_value: (dt, name, fields, cb) => {
				let payload;
				if (Array.isArray(fields)) {
					payload = {
						category_name: 'ค่าบริการ 3% (ภงด.53)',
						category_name_en: 'Service Fees 3% (PND53)',
					};
				} else {
					payload = {pd_custom_is_service_item: 0};
				}
				if (typeof cb === 'function') cb(payload);
				return Promise.resolve({message: payload});
			},
		},
		call: (opts) => {
			const method = opts.method || '';
			if (method.includes('item_wht_config')) {
				const message = {
					income_type: 'Service Fees 3% (PND53)',
					is_service_item: 0,
					wht_rate: 3,
					description: 'Service Fees 3% (PND53)',
					per_item: {},
				};
				if (opts.callback) opts.callback({message});
			} else if (method.includes('get_list')) {
				const message = [
					{name: 'Dashboard for BI', item_group: 'Services', pd_custom_is_service_item: 0},
				];
				if (opts.callback) opts.callback({message});
			} else if (method.includes('calculate_net_total_words')) {
				if (opts.callback) opts.callback({message: 'สองแสนเก้าหมื่นหนึ่งพันบาทถ้วน'});
			}
		},
	};
}

const sandbox = {
	console: {log: () => {}, warn: () => {}, error: () => {}},
	setTimeout,
	setInterval: () => 0,
	clearInterval: () => {},
	Promise,
	document: {addEventListener: () => {}},
	__: (msg, args) => (args ? msg.replace(/\{(\d+)\}/g, (m, i) => args[i]) : msg),
};
const jqStub = () => ({
	on: () => jqStub(),
	off: () => jqStub(),
	find: () => ({length: 0, text: () => '', click: () => {}}),
	each: () => {},
	length: 0,
});
sandbox.$ = jqStub;
sandbox.global = sandbox;
sandbox.window = sandbox;
sandbox.frappe = makeFrappe();
sandbox.locals = {};
vm.createContext(sandbox);

vm.runInContext(fs.readFileSync(path.join(baseDir, 'thailand_wht_vat_helper.js'), 'utf8'), sandbox);
vm.runInContext(fs.readFileSync(path.join(baseDir, FILE[doctype]), 'utf8'), sandbox);

const doc = Object.assign(
	{
		doctype,
		company: 'AWS Solution Ltd.',
		tax_category: '',
		items: [{item_code: 'Dashboard for BI', item_group: 'Services', qty: 40, rate: 7500}],
		total: 300000,
		pd_custom_wht_income_type: '',
		pd_custom_withholding_tax_pct: 0,
		pd_custom_vat_treatment: '',
		pd_custom_subject_to_wht: 0,
		pd_custom_wht_description: '',
		thailand_service_business: undefined,
		construction_service: undefined,
	},
	init
);

const frm = {
	doc,
	fields_dict: {},
	meta: {
		fields: [
			{fieldname: 'pd_custom_subject_to_wht', fieldtype: 'Check'},
			{fieldname: 'pd_custom_wht_income_type', fieldtype: 'Link'},
			{fieldname: 'pd_custom_withholding_tax_pct', fieldtype: 'Percent'},
			{fieldname: 'pd_custom_vat_treatment', fieldtype: 'Select'},
			{fieldname: 'pd_custom_wht_description', fieldtype: 'Data'},
		],
	},
	set_value(field, value) {
		this.doc[field] = value;
	},
	refresh() {},
	refresh_fields() {},
	is_new: () => true,
	is_dirty: () => false,
	perm: [{submit: 1}],
	page: {
		btn_primary: {text: () => 'Save', is: () => true},
		wrapper: {find: () => ({length: 0})},
	},
};
frm.events = {company: () => {}};

if (scenario === 'refresh') {
	handlers[doctype].refresh(frm);
} else if (scenario === 'item_code') {
	const idt = ITEM_DT[doctype];
	sandbox.locals[idt] = {1: frm.doc.items[0]};
	handlers[idt].item_code(frm, idt, 1);
} else if (scenario === 'items_remove') {
	handlers[ITEM_DT[doctype]].items_remove(frm);
} else if (scenario === 'income_type') {
	handlers[doctype].pd_custom_wht_income_type(frm);
}

// The client helpers are asynchronous (a frappe.call callback and a promise),
// so the microtask queue has to run before the result is read.
setTimeout(() => {
	const result = {
		doctype,
		scenario,
		income_type: frm.doc.pd_custom_wht_income_type,
		pct: frm.doc.pd_custom_withholding_tax_pct,
		vat_treatment: frm.doc.pd_custom_vat_treatment,
		subject_to_wht: frm.doc.pd_custom_subject_to_wht,
		description: frm.doc.pd_custom_wht_description,
		wht_amount: frm.doc.pd_custom_withholding_tax_amount,
		net_after_wht: frm.doc.pd_custom_net_total_after_wht,
		alerts,
	};
	process.stdout.write('__PD_RESULT__' + JSON.stringify(result) + '\n');
}, 50);
"""


def run_client(doctype, scenario, init=None, base_dir=None):
    """Run the client scripts and return the resulting form."""
    node = shutil.which("node")
    if not node:
        raise unittest.SkipTest("node is not available")

    with tempfile.TemporaryDirectory() as tmp:
        harness = Path(tmp) / "harness.js"
        harness.write_text(HARNESS_JS)

        completed = subprocess.run(
            [
                node,
                str(harness),
                doctype,
                scenario,
                str(base_dir or CLIENT_DIR),
                json.dumps(init or {}),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

    if completed.returncode != 0:
        raise AssertionError(f"the client harness failed:\n{completed.stdout}\n{completed.stderr}")

    for line in completed.stdout.splitlines():
        if line.startswith(RESULT_MARKER):
            return json.loads(line[len(RESULT_MARKER) :])

    raise AssertionError(f"the client harness produced no result:\n{completed.stdout}")


class TestItemDrivenWhtOnRefresh(unittest.TestCase):
    """The form has to show the WHT configuration on every refresh."""

    def test_refresh_fills_the_income_type_and_the_rate(self):
        for doctype in CLIENT_FILES:
            with self.subTest(doctype=doctype):
                result = run_client(doctype, "refresh")

                self.assertEqual(result["income_type"], "Service Fees 3% (PND53)")
                self.assertEqual(result["pct"], 3)
                self.assertEqual(result["description"], "Service Fees 3% (PND53)")

    def test_refresh_keeps_the_subject_to_wht_flag_in_sync(self):
        for doctype in CLIENT_FILES:
            with self.subTest(doctype=doctype):
                result = run_client(doctype, "refresh")

                self.assertEqual(result["subject_to_wht"], 1)

    def test_refresh_does_not_overwrite_a_manual_income_type(self):
        for doctype in CLIENT_FILES:
            with self.subTest(doctype=doctype):
                result = run_client(
                    doctype,
                    "refresh",
                    init={
                        "pd_custom_wht_income_type": "Contracting 3% (PND53)",
                        "pd_custom_withholding_tax_pct": 5,
                    },
                )

                self.assertEqual(result["income_type"], "Contracting 3% (PND53)")
                self.assertEqual(result["pct"], 5)

    def test_refresh_does_not_overwrite_a_manual_vat_treatment(self):
        for doctype in CLIENT_FILES:
            with self.subTest(doctype=doctype):
                result = run_client(
                    doctype,
                    "refresh",
                    init={"pd_custom_vat_treatment": "Exempt from VAT"},
                )

                self.assertEqual(result["vat_treatment"], "Exempt from VAT")


class TestItemDrivenWhtOnItemChange(unittest.TestCase):
    """The behaviour that already existed when an item row is edited."""

    def test_item_code_fills_the_income_type_and_the_rate(self):
        for doctype in CLIENT_FILES:
            with self.subTest(doctype=doctype):
                result = run_client(doctype, "item_code")

                self.assertEqual(result["income_type"], "Service Fees 3% (PND53)")
                self.assertEqual(result["pct"], 3)
                self.assertEqual(result["subject_to_wht"], 1)

    def test_item_code_does_not_overwrite_a_manual_income_type(self):
        for doctype in CLIENT_FILES:
            with self.subTest(doctype=doctype):
                result = run_client(
                    doctype,
                    "item_code",
                    init={"pd_custom_wht_income_type": "Contracting 3% (PND53)"},
                )

                self.assertEqual(result["income_type"], "Contracting 3% (PND53)")


class TestSubmittedDocumentIsNotModified(unittest.TestCase):
    """A submitted or cancelled document is never changed by the desk.

    Opening such a document must not tick the WHT flag, fill the income
    type, write the description, change the VAT treatment or recalculate an
    amount.  Only a display update (the preview section) is allowed.
    """

    def test_the_subject_to_wht_flag_is_not_ticked(self):
        for doctype in CLIENT_FILES:
            for docstatus in (1, 2):
                with self.subTest(doctype=doctype, docstatus=docstatus):
                    result = run_client(doctype, "refresh", {"docstatus": docstatus})

                    self.assertEqual(result["subject_to_wht"], 0)

    def test_the_income_type_and_the_rate_are_not_filled(self):
        for doctype in CLIENT_FILES:
            for docstatus in (1, 2):
                with self.subTest(doctype=doctype, docstatus=docstatus):
                    result = run_client(doctype, "refresh", {"docstatus": docstatus})

                    self.assertEqual(result["income_type"], "")
                    self.assertEqual(result["pct"], 0)

    def test_the_vat_treatment_is_not_changed(self):
        for doctype in CLIENT_FILES:
            for docstatus in (1, 2):
                with self.subTest(doctype=doctype, docstatus=docstatus):
                    result = run_client(doctype, "refresh", {"docstatus": docstatus})

                    self.assertEqual(result["vat_treatment"], "")

    def test_the_description_is_not_written(self):
        for doctype in CLIENT_FILES:
            for docstatus in (1, 2):
                with self.subTest(doctype=doctype, docstatus=docstatus):
                    result = run_client(doctype, "refresh", {"docstatus": docstatus})

                    self.assertEqual(result["description"], "")

    def test_no_alert_is_shown(self):
        for doctype in CLIENT_FILES:
            for docstatus in (1, 2):
                with self.subTest(doctype=doctype, docstatus=docstatus):
                    result = run_client(doctype, "refresh", {"docstatus": docstatus})

                    self.assertEqual(result["alerts"], [])

    def test_the_item_code_handler_does_not_change_the_document(self):
        for doctype in CLIENT_FILES:
            for docstatus in (1, 2):
                with self.subTest(doctype=doctype, docstatus=docstatus):
                    result = run_client(doctype, "item_code", {"docstatus": docstatus})

                    self.assertEqual(result["subject_to_wht"], 0)
                    self.assertEqual(result["income_type"], "")
                    self.assertEqual(result["pct"], 0)
                    self.assertEqual(result["vat_treatment"], "")

    def test_the_amounts_are_not_recalculated(self):
        # The harness only reports the amount fields when they were written.
        for docstatus in (1, 2):
            with self.subTest(docstatus=docstatus):
                result = run_client("Sales Invoice", "refresh", {"docstatus": docstatus})

                self.assertNotIn("wht_amount", result)
                self.assertNotIn("net_after_wht", result)

    def test_the_description_handler_does_not_write_on_a_submitted_document(self):
        for doctype in CLIENT_FILES:
            for docstatus in (1, 2):
                with self.subTest(doctype=doctype, docstatus=docstatus):
                    result = run_client(
                        doctype,
                        "income_type",
                        {
                            "docstatus": docstatus,
                            "pd_custom_wht_income_type": "Service Fees 3% (PND53)",
                            "pd_custom_subject_to_wht": 1,
                        },
                    )

                    self.assertEqual(result["description"], "")

    def test_the_description_is_filled_on_a_draft(self):
        for doctype in CLIENT_FILES:
            with self.subTest(doctype=doctype):
                result = run_client(
                    doctype,
                    "income_type",
                    {
                        "pd_custom_wht_income_type": "Service Fees 3% (PND53)",
                        "pd_custom_subject_to_wht": 1,
                    },
                )

                self.assertEqual(result["description"], "Service Fees 3% (PND53)")


class TestSalesInvoiceAmountOrdering(unittest.TestCase):
    """The amount has to be calculated with the rate of the item master."""

    def test_the_amount_is_calculated_after_the_configuration(self):
        result = run_client("Sales Invoice", "refresh")

        # 300000 * 3% = 9000
        self.assertEqual(result["wht_amount"], 9000)
        self.assertEqual(result["net_after_wht"], 291000)

    def test_the_amount_is_recalculated_when_an_item_is_selected(self):
        result = run_client("Sales Invoice", "item_code")

        self.assertEqual(result["wht_amount"], 9000)
        self.assertEqual(result["net_after_wht"], 291000)


if __name__ == "__main__":
    unittest.main()
