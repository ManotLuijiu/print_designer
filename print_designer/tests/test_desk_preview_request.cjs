const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../public/js/print.js'), 'utf8');
const start = source.indexOf('function patchDeskPreviewRenderer(');
const end = source.indexOf('// Start observing', start);

test('Desk preview forwards settings, language and letterhead; cancels obsolete request', () => {
  let request;
  let aborted = false;
  let rendered;
  class View { get_print_html() { throw new Error('unexpected fallback'); } }
  const context = { frappe: { call: (args) => { request = args; return 'request'; } }, console };
  vm.runInNewContext(source.slice(start, end) + '\nthis.patch = patchDeskPreviewRenderer;', context);
  context.patch(View);
  const view = new View();
  Object.assign(view, {
    get_print_format: () => ({}), frm: { doc: { name: 'TEST' } },
    selected_format: () => 'Quotation - AWS Solution',
    with_letterhead: () => false, get_letterhead: () => '', lang_code: 'th',
    additional_settings: { watermark_settings: 'Original on First Page', page_number_display: 'Show' },
    _req: { abort: () => { aborted = true; } },
  });
  view.get_print_html((out) => { rendered = out; });
  assert.equal(aborted, true);
  assert.equal(request.method, 'print_designer.api.desk_preview.get_html_and_style');
  assert.equal(request.args.settings, view.additional_settings);
  assert.equal(request.args._lang, 'th');
  assert.equal(request.args.no_letterhead, 1);
  request.callback({ message: { html: 'preview' } });
  assert.equal(rendered.html, 'preview');
  assert.equal(view._req, 'request');
});

test('raw printing retains the original renderer', () => {
  let called = false;
  class View { get_print_html(callback) { called = true; callback('raw'); } }
  const context = { frappe: { call: () => { throw new Error('unexpected RPC'); } }, console };
  vm.runInNewContext(source.slice(start, end) + '\nthis.patch = patchDeskPreviewRenderer;', context);
  context.patch(View);
  const view = new View();
  view.get_print_format = () => ({ raw_printing: true });
  view.get_print_html((out) => assert.equal(out, 'raw'));
  assert.equal(called, true);
});

test('unchanged sidebar defaults are sent without overwriting explicit off values', () => {
  const context = {};
  vm.runInNewContext(source.slice(start, end) + '\nthis.initialize = initializeDeskPreviewSettings;', context);
  const view = { additional_settings: { watermark_settings: 'None', enable_multiple_copies: 0 } };
  context.initialize(view, [
    { fieldname: 'watermark_settings', default: 'Original on First Page', fieldtype: 'Select' },
    { fieldname: 'page_number_display', default: 'Show', fieldtype: 'Select' },
    { fieldname: 'enable_multiple_copies', default: 1, fieldtype: 'Check' },
    { fieldname: 'watermark_left', default: 0, fieldtype: 'Int' },
    { fieldname: 'layout', default: 'ignored', fieldtype: 'Column Break' },
  ]);
  assert.equal(view.additional_settings.watermark_settings, 'None');
  assert.equal(view.additional_settings.enable_multiple_copies, 0);
  assert.equal(view.additional_settings.page_number_display, 'Show');
  assert.equal(view.additional_settings.watermark_left, 0);
  assert.equal(view.additional_settings.layout, undefined);
});
