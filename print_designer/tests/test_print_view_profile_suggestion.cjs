// The advisory profile suggestion of the print view.
//
// The plan of Phase 2 asks that the print view preselects a matching
// format "only when nothing else was chosen" and that it "never
// overwrites the selection of the user".
//
// The server side of the suggestion is covered by the Python tests.  This
// proof runs the real client script of the print view in a sandbox and
// covers the behaviour of the client:
//
//   - a matching format is preselected,
//   - the default print format of the DocType does not block the
//     suggestion, because the core puts it into the selector and it is
//     not a choice of the user,
//   - a format that the user chose is never overwritten, not even when
//     the choice was made while the request was in flight,
//   - a transaction without a matching format keeps the selection,
//   - a document that is not saved is never suggested,
//   - one request is made per document.

const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync("print_designer/public/js/print.js", "utf8");

// The calls of the client and the callbacks that wait for an answer.
const calls = [];
const pending = [];

// The formats of the doctype, as the client asks for them.
let availableFormats = [];

class PrintView {
  constructor(frm, selector) {
    this.frm = frm;
    this.print_format_selector = selector;
  }

  // The core puts the default print format of the DocType into the
  // selector.  It does not fire a change event, so the default is not a
  // choice of the user.
  set_default_print_format() {
    this.print_format_selector.val(this.frm.doc.default_print_format || "");
  }

  refresh_print_format() {}

  setup_print_format_dom() {}

  set_default_print_language() {}

  render_page() {}
}

const frappe = {
  xcall: () => Promise.resolve("{}"),
  ui: { form: { PrintView } },
  get_route: () => ["form"],
  meta: {
    get_print_formats: () => availableFormats,
  },
  call: (options) => {
    calls.push(options);
    if (options.method.endsWith("get_print_format_suggestions")) {
      // The answer of the server is given by the proof, so a request may
      // stay in flight while the user chooses a format.
      pending.push(options.callback);
    }
  },
};

// A print format selector of the print view.
function makeSelector(value) {
  const handlers = {};
  const attributes = {};

  return {
    length: 1,
    val(next) {
      if (next === undefined) return this._value;
      this._value = next;
      return this;
    },
    attr(name, next) {
      if (next === undefined) return attributes[name];
      attributes[name] = next;
      return this;
    },
    on(event, handler) {
      handlers[event] = handlers[event] || [];
      handlers[event].push(handler);
      return this;
    },
    trigger(event) {
      for (const handler of handlers[event] || []) handler();
      return this;
    },
    _value: value,
  };
}

// A document of the site and the print view of the document.
function makePrintView({
  name = "PE-0001",
  doctype = "Payment Entry",
  defaultPrintFormat = "Standard",
  isLocal = false,
} = {}) {
  const selector = makeSelector(defaultPrintFormat);
  const frm = {
    doctype,
    doc: {
      name,
      doctype,
      default_print_format: defaultPrintFormat,
      __islocal: isLocal,
    },
  };

  return new PrintView(frm, selector);
}

// The answer of the server to the pending requests.
function answerPending(message) {
  const callbacks = pending.splice(0, pending.length);
  for (const callback of callbacks) callback({ message });
}

const jquery = () => ({
  on: () => {},
  ready: () => {},
  find: () => jquery(),
  attr: () => "",
  0: { offsetHeight: 0 },
});

vm.runInNewContext(source, {
  frappe,
  $: jquery,
  __: (text) => text,
  console,
  document: {
    readyState: "complete",
    body: {},
    addEventListener: () => {},
    createElement: () => ({ style: {}, classList: { contains: () => false } }),
  },
  window: { location: { search: "" }, frames: [] },
  localStorage: { getItem: () => null, setItem: () => {} },
  MutationObserver: class {
    observe() {}
    disconnect() {}
  },
  requestAnimationFrame: () => 0,
  setTimeout: () => 0,
  clearTimeout: () => {},
  URLSearchParams: class {
    get() {
      return null;
    }
  },
});

// The endpoint of the suggestion.
const suggestionCalls = () =>
  calls.filter((call) => call.method.endsWith("get_print_format_suggestions"));

// A matching format is preselected, and the default of the DocType does
// not block the suggestion.
availableFormats = ["Standard", "PD Receive Services"];
const first = makePrintView();
first.set_default_print_format();
assert.equal(first.print_format_selector.val(), "Standard");
answerPending({
  available: true,
  suggestions: ["PD Receive Services"],
  profile: { direction: "Receive", transaction_type: "Services" },
});
assert.equal(first.print_format_selector.val(), "PD Receive Services");
assert.equal(first.print_format_selector.attr("data-pd-suggested"), "1");
console.log("PASS: a matching format is preselected");

// The choice of the user is never overwritten, not even when it was made
// while the request was in flight.
const second = makePrintView();
second.set_default_print_format();
second.print_format_selector.val("My Own Format");
second.print_format_selector.trigger("change");
answerPending({
  available: true,
  suggestions: ["PD Receive Services"],
  profile: { direction: "Receive", transaction_type: "Services" },
});
assert.equal(second.print_format_selector.val(), "My Own Format");
assert.equal(second.print_format_selector.attr("data-pd-suggested"), undefined);
console.log("PASS: the choice of the user is never overwritten");

// A transaction without a matching format keeps the selection.
const third = makePrintView();
third.set_default_print_format();
answerPending({
  available: true,
  suggestions: [],
  profile: { direction: null, transaction_type: null },
});
assert.equal(third.print_format_selector.val(), "Standard");
console.log(
  "PASS: a transaction without a matching format keeps the selection",
);

// A suggestion that is not among the formats of the doctype is not
// selected.
const fourth = makePrintView();
fourth.set_default_print_format();
answerPending({
  available: true,
  suggestions: ["PD Format Of Another Site"],
  profile: { direction: "Receive", transaction_type: "Services" },
});
assert.equal(fourth.print_format_selector.val(), "Standard");
console.log("PASS: a format of another site is not selected");

// A document that is not saved is never suggested.
const beforeDraft = suggestionCalls().length;
const draft = makePrintView({ name: "new-payment-entry", isLocal: true });
draft.set_default_print_format();
assert.equal(suggestionCalls().length, beforeDraft);
console.log("PASS: a document that is not saved is never suggested");

// One request is made per document, the selector is set up more than
// once.
const sixth = makePrintView();
const before = suggestionCalls().length;
sixth.set_default_print_format();
sixth.set_default_print_format();
assert.equal(suggestionCalls().length, before + 1);
console.log("PASS: one request is made per document");

console.log("PASS: the advisory suggestion of the print view behaves");
