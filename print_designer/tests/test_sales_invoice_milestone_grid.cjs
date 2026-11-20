const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('print_designer/public/js/invoice_schedule/sales_invoice_milestone_grid.js', 'utf8');
const portion = 'pd_custom_invoice_portion';
let handler;
vm.runInNewContext(source, {frappe: {ui: {form: {on: (doctype, events) => { handler = events.refresh; }}}}});
function gridFor(saved, includePortion = true) {
  const fields = ['item_code','qty','rate','amount', ...(includePortion ? [portion] : [])];
  return {
    docfields: fields.map(fieldname => ({fieldname, in_list_view:1})), resets:0,
    setup_user_defined_columns() {this.user_defined_columns = saved || [];},
    reset_grid() {this.resets++; this.setup_user_defined_columns();},
  };
}
const saved = ['item_code','qty','rate','amount'].map((fieldname,i) => ({fieldname, columns: i ? 2 : 4}));
const before = JSON.stringify(saved);
const grid = gridFor(saved);
handler({fields_dict:{items:{grid}}});
assert.deepEqual(Array.from(grid.user_defined_columns, f=>f.fieldname), ['item_code','qty','rate',portion,'amount']);
assert.equal(grid.user_defined_columns.find(f=>f.fieldname===portion).columns,1);
assert.ok(grid.user_defined_columns.reduce((n,f)=>n+f.columns,0)<=10);
assert.equal(JSON.stringify(saved),before);
handler({fields_dict:{items:{grid}}});
assert.equal(grid.resets,1);
grid.setup_user_defined_columns();
assert.equal(grid.user_defined_columns.filter(f=>f.fieldname===portion).length,1);
const defaults=gridFor();
handler({fields_dict:{items:{grid:defaults}}});
assert.deepEqual(Array.from(defaults.user_defined_columns,f=>f.fieldname),['item_code','qty','rate',portion,'amount']);
const missing=gridFor(saved,false);
handler({fields_dict:{items:{grid:missing}}});
assert.equal(missing.resets,0);
console.log('PASS: saved/default layouts, width budget, repeated refresh, preferences preserved, missing-field guard');

// A global copy of the invoice script cannot access its DocType-local WHT helper.
assert.ok(!/^import\s+.*thailand_wht_sales_invoice/m.test(fs.readFileSync('print_designer/public/js/app.js','utf8')));
const hooks=fs.readFileSync('print_designer/hooks.py','utf8');
const invoiceHooks=hooks.split('"Sales Invoice": [')[1].split('],')[0];
assert.ok(invoiceHooks.includes('thailand_wht_vat_helper.js'));
assert.ok(invoiceHooks.includes('thailand_wht_sales_invoice.js'));
console.log('PASS: WHT runs only through its complete DocType hook');
